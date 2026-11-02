"""Update a ServiceNow catalog task (SCTASK) from GitHub Actions.

    python scripts/servicenow.py note  --sctask SCTASK0012345 --text "PR opened: <url>"
    python scripts/servicenow.py start --sctask SCTASK0012345 --text "..."   # -> Work in Progress
    python scripts/servicenow.py close --sctask SCTASK0012345 --text "..."   # -> Closed Complete

Settings (GitHub secrets -> environment): SN_INSTANCE, SN_USERNAME, SN_PASSWORD.
If they are not set, the script prints a warning and exits 0, so the pipeline still
works before the ServiceNow side is ready.
"""
import argparse
import os
import sys

STATES = {"start": "2", "close": "3"}      # sc_task: 2 = Work in Progress, 3 = Closed Complete


def settings():
    s = {k: os.environ.get(k, "").strip() for k in ("SN_INSTANCE", "SN_USERNAME", "SN_PASSWORD")}
    s["SN_INSTANCE"] = s["SN_INSTANCE"].rstrip("/")
    return s if all(s.values()) else None


class ServiceNow:
    def __init__(self, instance, username, password, http=None, timeout=30):
        import requests
        self.base, self.timeout = instance, timeout
        self.http = http or requests.Session()
        self.http.auth = (username, password)
        self.http.headers.update({"Accept": "application/json", "Content-Type": "application/json"})

    def _call(self, method, path, **kw):
        r = self.http.request(method, self.base + path, timeout=self.timeout, **kw)
        if r.status_code >= 400:
            raise RuntimeError(f"ServiceNow {r.status_code} on {path}: {r.text[:200]}")
        return r.json()

    def task_id(self, number):
        rows = self._call("GET", "/api/now/table/sc_task", params={
            "sysparm_query": f"number={number}", "sysparm_fields": "sys_id", "sysparm_limit": "1"})["result"]
        if not rows:
            raise RuntimeError(f"{number} not found in ServiceNow")
        return rows[0]["sys_id"]

    def update(self, number, text, action="note"):
        body = {"work_notes": text}
        if action in STATES:
            body["state"] = STATES[action]
        if action == "close":
            body["close_notes"] = text
        return self._call("PATCH", f"/api/now/table/sc_task/{self.task_id(number)}", json=body)


def main(argv=None):
    p = argparse.ArgumentParser(description="Update a ServiceNow SCTASK")
    p.add_argument("action", choices=["note", "start", "close"])
    p.add_argument("--sctask", required=True)
    p.add_argument("--text", required=True)
    a = p.parse_args(argv)
    s = settings()
    if not s:
        print("::warning::ServiceNow secrets not set (SN_INSTANCE/SN_USERNAME/SN_PASSWORD); skipped update")
        return 0
    try:
        ServiceNow(s["SN_INSTANCE"], s["SN_USERNAME"], s["SN_PASSWORD"]).update(a.sctask, a.text, a.action)
    except Exception as e:                       # never fail the pipeline over a status update
        print(f"::warning::Could not update {a.sctask}: {e}")
        return 0
    print(f"{a.sctask}: {a.action} done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
