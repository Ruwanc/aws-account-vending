"""Turn one approved AWS account request into terraform/account_<name>.tf (+ a PR body).

Used by .github/workflows/account-request.yml; can also be run by hand:

    python scripts/new_account.py --ritm RITM0012345 --sctask SCTASK0012345 \
        --account-name rme-orders-nonprod --app-team-name RME --support-group "RME Support" \
        --technical-owner tom.lee@corp.com --budget-approver ann.wu@corp.com \
        --requested-for jane.doe@corp.com

    python scripts/new_account.py --from-env      # values from REQ_* environment variables

Deterministic on purpose: no AI writes Terraform. The same request always produces the
same file, so re-running the workflow for a RITM is safe.

Result (printed, and written to $GITHUB_OUTPUT with --output-github):
    status = created | exists       exit code 0
    file, branch, account_name, module_name, pr_body
Invalid input or a clash with another request -> message on stderr, exit code 1.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TF_DIR = ROOT / "terraform"
DEFAULTS = ROOT / "config" / "account-defaults.json"

FIELDS = ["ritm", "sctask", "account_name", "app_team_name", "support_group",
          "technical_owner", "budget_approver", "requested_for"]
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+'-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
NAME_RE = re.compile(r"^[a-z][a-z0-9-]{1,38}[a-z0-9]$")
NOT_ALLOWED = {"test", "account", "aws", "new", "temp", "my-account", "aws-account", "new-account"}
TAG_VALUE_RE = re.compile(r"^[\w\s+\-=.:/@]{0,256}$")      # characters AWS accepts in tag values
TICKET_RE = {"ritm": re.compile(r"^RITM\d{7,10}$"), "sctask": re.compile(r"^SCTASK\d{7,10}$")}


class RequestError(ValueError):
    pass


# ---------------------------------------------------------------- validation
def validate(req):
    """Check and normalise a request dict. Returns a cleaned copy or raises RequestError."""
    r = {k: str(req.get(k, "") or "").strip() for k in FIELDS}
    missing = [k for k in FIELDS if not r[k]]
    if missing:
        raise RequestError(f"missing values: {', '.join(missing)}")
    for k, pattern in TICKET_RE.items():
        r[k] = r[k].upper()
        if not pattern.match(r[k]):
            raise RequestError(f"{k} looks wrong: {r[k]!r}")
    r["account_name"] = re.sub(r"[\s_]+", "-", r["account_name"].lower())
    if not NAME_RE.match(r["account_name"]) or "--" in r["account_name"]:
        raise RequestError(f"account_name {r['account_name']!r}: 3-40 chars, lowercase letters, "
                           "numbers and single hyphens, starting with a letter")
    if r["account_name"] in NOT_ALLOWED:
        raise RequestError(f"account_name {r['account_name']!r} is too generic")
    for k in ("technical_owner", "budget_approver", "requested_for"):
        r[k] = r[k].lower()
        if not EMAIL_RE.match(r[k]):
            raise RequestError(f"{k} is not a single valid email address: {r[k]!r}")
    for k in ("app_team_name", "support_group"):
        if not TAG_VALUE_RE.match(r[k]):
            raise RequestError(f"{k} has characters AWS tags don't allow: {r[k]!r}")
    return r


# ---------------------------------------------------------------- rendering
def hcl_string(value):
    """Quote a value for HCL (escape \\ and \", and stop ${ } / %{ } templates)."""
    v = value.replace("\\", "\\\\").replace('"', '\\"')
    v = v.replace("${", "$${").replace("%{", "%%{")
    return f'"{v}"'


def module_name(account_name):
    return "account_" + account_name.replace("-", "_")


def render(r, defaults):
    """The Terraform file for one account."""
    name = module_name(r["account_name"])
    email = defaults["email_pattern"].format(account_name=r["account_name"])
    if len(email) > 64 or not EMAIL_RE.match(email):
        raise RequestError(f"account root email {email!r} is invalid or longer than 64 characters")
    tags = {k: v.format(**r) for k, v in defaults.get("tags", {}).items()}
    width = max((len(hcl_string(k)) for k in tags), default=0)
    tag_lines = "\n".join(f"    {hcl_string(k).ljust(width)} = {hcl_string(v)}" for k, v in tags.items())
    return f'''# AWS account requested in ServiceNow {r["ritm"]} / {r["sctask"]}
# Requested for: {r["requested_for"]}
# Written by scripts/new_account.py. Change it through a new request, not by hand.
module "{name}" {{
  source = {hcl_string(defaults["module_source"])}

  account_name = {hcl_string(r["account_name"])}
  email        = {hcl_string(email)}
  parent_ou_id = {hcl_string(defaults["parent_ou_id"])}

  tags = {{
{tag_lines}
  }}
}}

output "{name}_id" {{
  description = "Account ID of {r["account_name"]}"
  value       = module.{name}.account_id
}}
'''


def pr_body(r, file_rel):
    """PR description. The HTML comments are read back by close_requests.py after merge."""
    return f"""## New AWS account: `{r["account_name"]}`

Approved in ServiceNow by the requester's manager. Created by the account-request workflow.

| | |
|---|---|
| ServiceNow | {r["ritm"]} / {r["sctask"]} |
| Requested for | {r["requested_for"]} |
| App / Team | {r["app_team_name"]} |
| Support group | {r["support_group"]} |
| Technical owner | {r["technical_owner"]} |
| Budget approver | {r["budget_approver"]} |
| File | `{file_rel}` |

### Reviewers (Cloud Engineering)
- [ ] Account name and OU are right
- [ ] `terraform plan` (comment below) creates exactly **1** account and changes nothing else
- [ ] Checks are green

Two approvals from Cloud Engineering are required. Merging creates the account.

<!-- ritm: {r["ritm"]} -->
<!-- sctask: {r["sctask"]} -->
<!-- account: {r["account_name"]} -->
"""


# ---------------------------------------------------------------- main logic
def create(req, tf_dir=TF_DIR, defaults=None):
    """Validate, then write the account file unless it already exists for this RITM."""
    defaults = defaults or json.loads(DEFAULTS.read_text(encoding="utf-8"))
    r = validate(req)
    path = Path(tf_dir) / f"account_{r['account_name']}.tf"
    content = render(r, defaults)
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if f"ServiceNow {r['ritm']} " not in existing:
            raise RequestError(f"an account named {r['account_name']!r} already exists "
                               f"({path.name}, from another request)")
        status = "exists"                      # same RITM: re-run of the workflow, nothing to do
    else:
        path.write_text(content, encoding="utf-8")
        status = "created"
    rel = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
    return {"status": status, "file": str(rel), "account_name": r["account_name"],
            "module_name": module_name(r["account_name"]),
            "branch": f"account/{r['ritm']}-{r['account_name']}",
            "pr_title": f"Add AWS account {r['account_name']} ({r['ritm']})",
            "body": pr_body(r, rel), "request": r}


def main(argv=None):
    p = argparse.ArgumentParser(description="Write terraform/account_<name>.tf for one request")
    for k in FIELDS:
        p.add_argument("--" + k.replace("_", "-"), dest=k)
    p.add_argument("--from-env", action="store_true", help="read REQ_<FIELD> environment variables")
    p.add_argument("--output-github", action="store_true", help="also write $GITHUB_OUTPUT")
    p.add_argument("--pr-body-file", default="pr_body.md")
    a = p.parse_args(argv)
    req = {k: (os.environ.get("REQ_" + k.upper(), "") if a.from_env else getattr(a, k)) for k in FIELDS}
    try:
        result = create(req)
    except RequestError as e:
        print(f"::error::{e}" if os.environ.get("GITHUB_ACTIONS") else f"Error: {e}", file=sys.stderr)
        return 1
    Path(a.pr_body_file).write_text(result["body"], encoding="utf-8")
    keys = ["status", "file", "account_name", "module_name", "branch", "pr_title"]
    for k in keys:
        print(f"{k}={result[k]}")
    if a.output_github and os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as out:
            for k in keys:
                out.write(f"{k}={result[k]}\n")
            out.write(f"pr_body={a.pr_body_file}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
