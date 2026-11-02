"""Tests for the generator and helper scripts (no AWS, GitHub or ServiceNow needed)."""
import json
import sys
from pathlib import Path

import hcl2
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import close_requests  # noqa: E402
import new_account  # noqa: E402
import servicenow  # noqa: E402
import teams_notify  # noqa: E402

DEFAULTS = json.loads((ROOT / "config" / "account-defaults.json").read_text())
REQ = {"ritm": "RITM0012345", "sctask": "SCTASK0012345", "account_name": "rme-orders-nonprod",
       "app_team_name": "RME", "support_group": "RME Support", "technical_owner": "tom.lee@corp.com",
       "budget_approver": "ann.wu@corp.com", "requested_for": "jane.doe@corp.com"}


def _clean(x):
    """Make python-hcl2 output the same across versions.

    < 5 wraps values in lists; 8.x keeps the quotes around names and strings
    and adds __is_block__ markers. This returns plain dicts and strings.
    """
    if isinstance(x, list):
        return _clean(x[0]) if len(x) == 1 else [_clean(i) for i in x]
    if isinstance(x, dict):
        return {_clean(k): _clean(v) for k, v in x.items() if not str(k).startswith("__")}
    if isinstance(x, str) and len(x) >= 2 and x[0] == x[-1] == '"':
        return x[1:-1]
    return x


def test_creates_valid_terraform(tmp_path):
    r = new_account.create(REQ, tf_dir=tmp_path, defaults=DEFAULTS)
    assert r["status"] == "created" and r["branch"] == "account/RITM0012345-rme-orders-nonprod"
    # tf = hcl2.loads((tmp_path / "account_rme-orders-nonprod.tf").read_text())
    # module = tf["module"][0]["account_rme_orders_nonprod"]
    # assert _v(module["source"]) == "./modules/aws-account"
    # assert _v(module["account_name"]) == "rme-orders-nonprod"
    # assert _v(module["email"]) == "aws+rme-orders-nonprod@REPLACE-company.com"
    # tags = _v(module["tags"])
    # assert tags["Technical:PlatformOwner"] == "tom.lee@corp.com" and tags["ServiceNow:RITM"] == "RITM0012345"
    # assert "account_rme_orders_nonprod_id" in tf["output"][0]
    tf = _clean(hcl2.loads((tmp_path / "account_rme-orders-nonprod.tf").read_text()))
    module = tf["module"]["account_rme_orders_nonprod"]
    assert module["source"] == "./modules/aws-account"
    assert module["account_name"] == "rme-orders-nonprod"
    assert module["email"] == "aws+rme-orders-nonprod@REPLACE-company.com"
    assert module["tags"]["Technical:PlatformOwner"] == "tom.lee@corp.com"
    assert module["tags"]["ServiceNow:RITM"] == "RITM0012345"
    assert "account_rme_orders_nonprod_id" in tf["output"]


def test_rerun_for_same_ritm_is_safe(tmp_path):
    new_account.create(REQ, tf_dir=tmp_path, defaults=DEFAULTS)
    assert new_account.create(REQ, tf_dir=tmp_path, defaults=DEFAULTS)["status"] == "exists"


def test_same_name_from_another_request_is_refused(tmp_path):
    new_account.create(REQ, tf_dir=tmp_path, defaults=DEFAULTS)
    with pytest.raises(new_account.RequestError, match="already exists"):
        new_account.create({**REQ, "ritm": "RITM0099999"}, tf_dir=tmp_path, defaults=DEFAULTS)


@pytest.mark.parametrize("field, value, message", [
    ("account_name", "AWS", "too generic"),
    ("account_name", "a", "3-40"),
    ("account_name", "rme--x", "3-40"),
    ("technical_owner", "a@x.com, b@x.com", "single valid email"),
    ("ritm", "12345", "looks wrong"),
    ("app_team_name", 'RME"; rm -rf /', "characters"),
    ("support_group", "", "missing"),
])
def test_bad_requests_are_rejected(tmp_path, field, value, message):
    with pytest.raises(new_account.RequestError, match=message):
        new_account.create({**REQ, field: value}, tf_dir=tmp_path, defaults=DEFAULTS)
    assert list(tmp_path.iterdir()) == []


def test_names_are_normalised(tmp_path):
    r = new_account.create({**REQ, "account_name": "RME Orders NonProd", "ritm": "ritm0012345"},
                           tf_dir=tmp_path, defaults=DEFAULTS)
    assert r["account_name"] == "rme-orders-nonprod" and r["request"]["ritm"] == "RITM0012345"


def test_hcl_string_escapes_templates():
    assert new_account.hcl_string('a"b${x}%{y}\\') == '"a\\"b$${x}%%{y}\\\\"'


def test_pr_body_markers_round_trip(tmp_path):
    r = new_account.create(REQ, tf_dir=tmp_path, defaults=DEFAULTS)
    assert close_requests.markers(r["body"]) == {"ritm": "RITM0012345", "sctask": "SCTASK0012345",
                                                 "account": "rme-orders-nonprod"}


def test_close_requests_finds_account_id(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(close_requests.subprocess, "run", lambda cmd, check: calls.append(cmd))
    outputs = tmp_path / "outputs.json"
    outputs.write_text(json.dumps({"account_rme_orders_nonprod_id": {"value": "123456789012"}}))
    body = new_account.pr_body(new_account.validate(REQ), "terraform/x.tf")
    prs = [{"body": body, "html_url": "https://github.com/o/r/pull/7"}, {"body": "unrelated PR"}]
    close_requests.main(["--sha", "abc", "--outputs", str(outputs)], prs=prs)
    sn = next(c for c in calls if c[1].endswith("servicenow.py"))
    assert sn[2:5] == ["close", "--sctask", "SCTASK0012345"] and "123456789012" in sn[-1]
    assert any(c[1].endswith("teams_notify.py") for c in calls)


def test_teams_card_shape():
    c = teams_notify.card("Review needed", facts=[("Author", "bot")], url="https://x", button="Review")
    content = c["attachments"][0]["content"]
    assert content["type"] == "AdaptiveCard" and content["actions"][0]["url"] == "https://x"


def test_scripts_skip_quietly_without_secrets(monkeypatch, capsys):
    for k in ("SN_INSTANCE", "SN_USERNAME", "SN_PASSWORD", "TEAMS_WEBHOOK_URL"):
        monkeypatch.delenv(k, raising=False)
    assert servicenow.main(["note", "--sctask", "SCTASK0012345", "--text", "hi"]) == 0
    assert teams_notify.main(["--title", "hi"]) == 0
    assert capsys.readouterr().out.count("::warning::") == 2


class FakeHTTP:
    def __init__(self):
        self.calls, self.headers, self.auth = [], {}, None

    def request(self, method, url, timeout, **kw):
        self.calls.append((method, url, kw))
        class R:
            status_code = 200
            text = ""
            def json(self_inner):
                return {"result": [{"sys_id": "T1"}]} if method == "GET" else {"result": {}}
        return R()


def test_servicenow_close_sets_state_and_notes():
    http = FakeHTTP()
    servicenow.ServiceNow("https://dev.service-now.com", "u", "p", http=http).update(
        "SCTASK0012345", "done: 123", "close")
    method, url, kw = http.calls[-1]
    assert method == "PATCH" and url.endswith("/sc_task/T1")
    assert kw["json"] == {"work_notes": "done: 123", "state": "3", "close_notes": "done: 123"}


def test_close_requests_practice_mode_needs_no_outputs(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(close_requests.subprocess, "run", lambda cmd, check: calls.append(cmd))
    outputs = tmp_path / "outputs.json"
    outputs.write_text("{}")
    body = new_account.pr_body(new_account.validate(REQ), "terraform/x.tf")
    close_requests.main(["--sha", "abc", "--outputs", str(outputs), "--practice"],
                        prs=[{"body": body, "html_url": "https://github.com/u/r/pull/1"}])
    sn = next(c for c in calls if c[1].endswith("servicenow.py"))
    assert "practice mode" in sn[-1] and "merged" in sn[-1]
