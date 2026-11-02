# aws-account-vending

Creates AWS accounts from approved ServiceNow requests, through a reviewed Terraform PR.

```
CET Agent / ServiceNow portal
        │  RITM (AWS account request)
        ▼
ServiceNow flow (built by the ServiceNow admins, see docs/servicenow-flow.md)
  1. approval: requester's manager ──rejected──► RITM closed, requester told
        │ approved
  2. SCTASK created under the RITM, assigned to Cloud Engineering
  3. POST /repos/<org>/aws-account-vending/dispatches  (event "aws-account-request")
        ▼
GitHub Actions: account-request.yml
  writes terraform/account_<name>.tf ─► branch account/<RITM>-<name> ─► PR
  SCTASK → Work in Progress + PR link
        ▼
GitHub Actions: terraform-pr.yml (every PR)
  Teams card to CET ─ validate (tests, fmt, validate, tflint, checkov) ─ plan as PR comment
        ▼
Ruleset on master: 2 approvals, code owners (Cloud Engineering), checks green
        ▼  merge
GitHub Actions: terraform-apply.yml
  terraform apply (AWS via OIDC) ─► SCTASK Closed Complete with account ID ─► Teams card
  (ServiceNow closes the RITM when its last task closes)
```

No AI writes Terraform here: `scripts/new_account.py` turns the request into the same file
every time, and people approve it. The CET Agent stays the front door (collecting requests,
and later answering "what's the status of my request?").

## Layout

```
aws-account-vending/
├── terraform/                     root stack (one state)
│   ├── versions.tf · providers.tf · backend.tf
│   ├── accounts.tf                note only; accounts are the account_*.tf files
│   ├── account_<name>.tf          one per account, written by new_account.py
│   └── modules/aws-account/       sample module (swap for your real module)
├── config/account-defaults.json   module source, OU, root email pattern, tags
├── scripts/
│   ├── new_account.py             request -> account file + PR body (validated, idempotent)
│   ├── servicenow.py              SCTASK work note / start / close
│   ├── teams_notify.py            card to the CET Teams channel
│   ├── close_requests.py          after apply: close SCTASKs with the account IDs
│   └── setup_personal.sh          one-time setup for a personal test repo
├── tests/test_scripts.py          18 tests, no AWS/GitHub/ServiceNow needed
├── .github/
│   ├── workflows/account-request.yml · terraform-pr.yml · terraform-apply.yml
│   ├── CODEOWNERS                 @YOUR-ORG/cloud-engineering
│   └── rulesets/master.json · master-personal.json   2 approvals (company) · 1 (personal test)
└── docs/
    ├── servicenow-flow.md         what the ServiceNow admins build
    └── personal-setup.md          try it on a personal GitHub account
```

## Try it first on a personal GitHub account

[docs/personal-setup.md](docs/personal-setup.md): public repo, no AWS (practice mode), you approve.
About 20 minutes; nothing touches company systems.

## Set up (once)

Replace `YOUR-ORG` with your GitHub organisation everywhere below.

**1. Repo and team**
- Create `YOUR-ORG/aws-account-vending` (private) on GitHub Enterprise and push this folder.
  Default branch: `master`.
- Team `cloud-engineering` with **write** access and at least 3 people (2 approve; the
  author can't approve their own PR).
- Edit `.github/CODEOWNERS` with your real org and team.

**2. Settings for your stack**
- `config/account-defaults.json`: your OU ID, root email pattern (each account needs a unique
  email; a `+` alias of one mailbox is common), tags, and `module_source` if you already have
  an account module (e.g. `git::https://github.com/YOUR-ORG/terraform-aws-account.git?ref=v1.4.0`).
- `terraform/backend.tf`: your state bucket and lock table.

**3. GitHub App "cet-account-bot"** (org settings → Developer settings → GitHub Apps)
- Repository permissions: Contents **read & write**, Pull requests **read & write**,
  Issues **read & write** (for the label), Metadata read. No webhook needed.
- Install it on this repo only. Generate a private key.
- Repo variable `ACCOUNT_BOT_APP_ID`, repo secret `ACCOUNT_BOT_PRIVATE_KEY`.
- Why an App: PRs opened with the built-in `GITHUB_TOKEN` don't trigger other workflows,
  so the checks and Teams card wouldn't run.

**4. AWS (OIDC, no stored keys)**, in the Organizations management account (or delegated admin)
- IAM OIDC provider for `token.actions.githubusercontent.com` (audience `sts.amazonaws.com`).
- Role for **plan** (read-only + state read), trust limited to this repo's pull requests:
  `"token.actions.githubusercontent.com:sub": "repo:YOUR-ORG/aws-account-vending:pull_request"`
- Role for **apply** (organizations:CreateAccount, Describe*, TagResource, MoveAccount + state
  read/write), trust limited to the production environment:
  `"token.actions.githubusercontent.com:sub": "repo:YOUR-ORG/aws-account-vending:environment:production"`
- Repo variables `AWS_PLAN_ROLE_ARN`, `AWS_APPLY_ROLE_ARN`.
- Environment `production` (Settings → Environments). Optionally add required reviewers for
  a final check before apply.

**5. Teams**
- In the CET channel: Workflows app → "Post to a channel when a webhook request is received".
  Copy the URL into repo secret `TEAMS_WEBHOOK_URL`.

**6. ServiceNow → GitHub, and GitHub → ServiceNow**
- Repo secrets `SN_INSTANCE`, `SN_USERNAME`, `SN_PASSWORD`: a ServiceNow integration user
  that can read and update `sc_task`. Until they're set, the workflows skip ServiceNow updates
  with a warning instead of failing.
- Give `docs/servicenow-flow.md` to the ServiceNow admins.

**7. Ruleset (2 approvals)**, after the workflows have run once so the check names exist:

```bash
gh api repos/YOUR-ORG/aws-account-vending/rulesets --method POST --input .github/rulesets/master.json
```

It needs 2 approvals including Cloud Engineering (code owners). It also dismisses approvals
when new commits are pushed, needs approval after the last push, and needs the `validate` and
`plan` checks to pass. Nobody can bypass it. To review or change it later, go to
Settings → Rules → Rulesets.

## Test it without ServiceNow

1. Actions → **account-request** → *Run workflow* → fill in the fields (made-up RITM/SCTASK numbers are fine).
2. A PR appears, Teams gets a card, `validate` and `plan` run, and the plan comment shows `Plan: 1 to add`.
3. Two Cloud Engineering members approve → merge → **terraform-apply** creates the account.
   Try this against a sandbox OU first.

Local checks:
```bash
pip install -r requirements-dev.txt
python -m pytest -q
python scripts/new_account.py --ritm RITM0000001 --sctask SCTASK0000001 --account-name demo-sbx \
  --app-team-name Demo --support-group "Demo Support" --technical-owner a@corp.com \
  --budget-approver b@corp.com --requested-for c@corp.com     # writes terraform/account_demo-sbx.tf
```

## Safety built in

- **Request values can't run as code:** they reach the shell only through environment
  variables, and `new_account.py` checks every value before writing HCL.
- **Re-running is safe:** a re-run for the same RITM finds the open PR. A second request with
  an existing account name is refused.
- **Accounts can't be closed by accident:** `prevent_destroy` in the module means deleting an
  account file can't close a real account.
- **Least privilege:** plan and apply use separate AWS roles. Apply credentials exist only in
  the `production` environment after merge.
- **Failures are reported:** ServiceNow gets a work note when the automation fails, and Teams
  gets a card when apply fails.
