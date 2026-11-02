# Try it on a personal GitHub account (public repo, no AWS)

Everything runs except the parts that need company systems:

| Part | On your personal account |
|---|---|
| account-request workflow → bot opens the PR | ✅ works |
| Checks: tests, fmt, validate, tflint, checkov | ✅ works |
| Plan comment on the PR | ✅ practice note instead of a real plan (no AWS) |
| Ruleset: merge blocked until approved | ✅ works (1 approval: yours) |
| terraform-apply after merge | ✅ runs in practice mode: no account is created |
| ServiceNow updates | ⏭ skipped with a warning (optional: free developer instance, step 8) |
| Teams cards | ⏭ skipped with a warning (Teams needs a work account) |

It's a **public** repo, so only placeholders go in it: no company OU IDs, emails, tag
standards or secrets. Secrets go in GitHub's encrypted secrets, never in files.

## Quick way: one script

`scripts/create_repo.sh` does steps 1, 2, 4 and 5 for you:

```bash
brew install gh && gh auth login                 # once, if you don't have the GitHub CLI
# download aws-account-vending-github-folder.zip from the chat to ~/Downloads, then:
bash ~/MyLearning/AGENT/aws-account-vending/scripts/create_repo.sh create
#  -> create the GitHub App in the browser (step 3 below)
cd ~/MyLearning/aws-account-vending
bash scripts/create_repo.sh connect-bot          # asks for the App ID and the .pem file
bash scripts/create_repo.sh test                 # sends a test request, watches the run
```

The manual steps below do the same thing, if you prefer them or something goes wrong.

## 1. Prepare the folder (once)

The folder currently sits inside your `AGENT` git repo. Give it a home of its own:

```bash
cp -R ~/MyLearning/AGENT/aws-account-vending ~/MyLearning/aws-account-vending
cd ~/MyLearning/aws-account-vending
unzip ~/Downloads/aws-account-vending-github-folder.zip    # the .github folder, if not done yet
bash scripts/setup_personal.sh <your-github-username>        # CODEOWNERS -> you
```

Install the GitHub CLI if you don't have it: `brew install gh`, then `gh auth login`.

## 2. Create the repo and push

```bash
git init -b master
git add .
git commit -m "AWS account vending: first version"
gh repo create aws-account-vending --public --source . --push
```

This keeps the default branch as `master`, which the workflows and the ruleset expect.

## 3. Create the bot (a GitHub App)

The bot opens the PRs. Because the bot is the PR author, you're allowed to approve its PRs.
GitHub never counts the author's own approval, so a token in your own name wouldn't work here.

1. github.com → your picture → **Settings → Developer settings → GitHub Apps → New GitHub App**
2. Name: something unique, e.g. `<username>-account-bot`. Homepage URL: your repo URL.
3. **Webhook:** untick *Active*.
4. **Repository permissions:** Contents *Read and write*, Pull requests *Read and write*,
   Issues *Read and write*. Leave the rest as is.
5. *Where can this app be installed:* **Only on this account** → **Create GitHub App**.
6. Note the **App ID** at the top of the page.
7. Scroll down → **Generate a private key**. A `.pem` file downloads. Keep it out of the repo
   (`*.pem` is in `.gitignore`).
8. Left menu → **Install App** → your account → *Only select repositories* →
   `aws-account-vending` → Install.

## 4. Give the workflows the bot's details

```bash
gh variable set ACCOUNT_BOT_APP_ID --body "<App ID>"
gh secret set ACCOUNT_BOT_PRIVATE_KEY < ~/Downloads/<your-app>.private-key.pem
```

Leave `AWS_PLAN_ROLE_ARN`, `AWS_APPLY_ROLE_ARN`, `SN_*` and `TEAMS_WEBHOOK_URL` **unset**.
That's what turns on practice mode and skips ServiceNow and Teams. Then delete the `.pem`
from Downloads, or keep it somewhere safe.

## 5. First run

Send the same request ServiceNow will send later:

```bash
gh api repos/<username>/aws-account-vending/dispatches --method POST --input - <<'EOF'
{"event_type": "aws-account-request",
 "client_payload": {"ritm": "RITM0000001", "sctask": "SCTASK0000001",
  "account_name": "demo-sbx", "app_team_name": "Demo", "support_group": "Demo Support",
  "technical_owner": "you@example.com", "budget_approver": "manager@example.com",
  "requested_for": "you@example.com"}}
EOF
```

Or: **Actions → account-request → Run workflow** and fill in the form.

Check:
- Actions shows an **account-request** run, then a **terraform-pr** run.
- A PR **"Add AWS account demo-sbx (RITM0000001)"** opened by your bot, with the
  `aws-account-request` label and the file `terraform/account_demo-sbx.tf`.
- Checks **validate** and **plan** are green, and the PR has a plan comment saying practice mode.

## 6. Turn on the approval rule

The ruleset names the `validate` and `plan` checks, so add it after they've run once:

```bash
gh api repos/<username>/aws-account-vending/rulesets --method POST \
  --input .github/rulesets/master-personal.json
```

Check it under **Settings → Rules → Rulesets**. On the PR, the merge button now says review
is required.

## 7. Approve, merge, watch the apply

1. On the PR: **Files changed → Review changes → Approve**.
2. **Merge pull request**.
3. Actions shows **terraform-apply** with the notice *Practice mode … terraform apply
   skipped*, and the log line `closed 1 request(s)` (ServiceNow skipped).

Try the safety features too:
- Run step 5 again with the same RITM: no second PR.
- Use `"account_name": "aws"`: the run fails with "too generic".
- Push a commit to the PR branch after approving: your approval is dismissed.

## 8. Optional: a free ServiceNow developer instance

Get a free instance from the ServiceNow Developer Program (developer.servicenow.com). Then:

1. Create a catalog task by hand (`sc_task.do`), note its number, and use it as `sctask` in step 5.
2. `gh secret set SN_INSTANCE --body "https://devXXXXX.service-now.com"`, then do the same for
   `SN_USERNAME` and `SN_PASSWORD`. Use the instance admin or an integration user.
3. Run steps 5–7 again. The task gets a work note with the PR link, then closes after merge.

## 9. Moving to the company repo later

- Use `.github/rulesets/master.json` (2 approvals) and CODEOWNERS `@YOUR-ORG/cloud-engineering`.
- Make the repo **private** in your GitHub Enterprise organisation.
- Fill in `config/account-defaults.json` and `terraform/backend.tf` with the real values.
- Set the AWS role variables (practice mode turns off by itself), plus the ServiceNow and
  Teams secrets, as in the README.
- Create a new GitHub App in the organisation, not a personal one.
