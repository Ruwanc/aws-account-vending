"""After `terraform apply` on master: close the ServiceNow task of every account PR in this push.

    python scripts/close_requests.py --sha <merge commit> --outputs outputs.json

1. Ask GitHub which merged PR(s) produced the commit (gh api .../commits/<sha>/pulls).
2. Read the markers new_account.py put in the PR body (sctask, ritm, account).
3. Find the new account ID in `terraform output -json` (output "account_<name>_id").
4. Close the SCTASK with the ID, and post to Teams.
"""
import argparse
import json
import os
import re
import subprocess
import sys

MARKER = re.compile(r"<!--\s*(ritm|sctask|account):\s*([A-Za-z0-9-]+)\s*-->")


def markers(body):
    return {k: v for k, v in MARKER.findall(body or "")}


def account_id(outputs, account_name):
    key = "account_" + account_name.replace("-", "_") + "_id"
    return (outputs.get(key) or {}).get("value")


def merged_prs(sha):
    repo = os.environ["GITHUB_REPOSITORY"]
    out = subprocess.run(["gh", "api", f"repos/{repo}/commits/{sha}/pulls"],
                         check=True, capture_output=True, text=True).stdout
    return json.loads(out)


def main(argv=None, prs=None):
    p = argparse.ArgumentParser()
    p.add_argument("--sha", required=True)
    p.add_argument("--outputs", required=True)
    p.add_argument("--practice", action="store_true",
                   help="no AWS: report 'not created' instead of an account ID")
    a = p.parse_args(argv)
    outputs = json.load(open(a.outputs, encoding="utf-8"))
    prs = merged_prs(a.sha) if prs is None else prs
    done = 0
    for pr in prs:
        m = markers(pr.get("body"))
        if not {"sctask", "account"} <= set(m):
            continue                                   # not an account request PR
        acct = "not created (practice mode, no AWS)" if a.practice else account_id(outputs, m["account"])
        if not acct:
            print(f"::warning::No account ID for {m['account']} in terraform outputs")
            continue
        verb = "merged" if a.practice else "created"
        text = (f"AWS account {m['account']} {verb}: {acct}. "
                f"PR: {pr.get('html_url', '')}. Run: {run_url()}")
        here = os.path.dirname(os.path.abspath(__file__))
        subprocess.run([sys.executable, os.path.join(here, "servicenow.py"), "close",
                        "--sctask", m["sctask"], "--text", text], check=False)
        subprocess.run([sys.executable, os.path.join(here, "teams_notify.py"),
                        "--title", f"AWS account {verb}: {m['account']}",
                        "--fact", f"Account ID={acct}", "--fact", f"ServiceNow={m.get('ritm', '')} / {m['sctask']}",
                        "--url", pr.get("html_url", ""), "--button", "Open PR"], check=False)
        done += 1
    print(f"closed {done} request(s)")
    return 0


def run_url():
    s, r, i = (os.environ.get(k, "") for k in ("GITHUB_SERVER_URL", "GITHUB_REPOSITORY", "GITHUB_RUN_ID"))
    return f"{s}/{r}/actions/runs/{i}" if i else ""


if __name__ == "__main__":
    sys.exit(main())
