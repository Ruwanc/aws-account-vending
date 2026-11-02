"""Post a card to the CET Microsoft Teams channel.

Uses a Teams "Workflows" webhook (Workflows app > "Post to a channel when a webhook
request is received"), because the old Office 365 connector webhooks are retired.

    python scripts/teams_notify.py --title "New PR: Add AWS account x" --url <pr url> \
        --fact "Requested for=jane@corp.com" --fact "ServiceNow=RITM0012345"

Setting: TEAMS_WEBHOOK_URL (GitHub secret). Not set -> warning, exit 0.
"""
import argparse
import json
import os
import sys
import urllib.request


def card(title, text="", facts=(), url="", button="Open"):
    body = [{"type": "TextBlock", "size": "Medium", "weight": "Bolder", "text": title, "wrap": True}]
    if text:
        body.append({"type": "TextBlock", "text": text, "wrap": True})
    if facts:
        body.append({"type": "FactSet", "facts": [{"title": k, "value": v} for k, v in facts]})
    content = {"$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
               "type": "AdaptiveCard", "version": "1.4", "body": body}
    if url:
        content["actions"] = [{"type": "Action.OpenUrl", "title": button, "url": url}]
    return {"type": "message", "attachments": [
        {"contentType": "application/vnd.microsoft.card.adaptive", "content": content}]}


def main(argv=None):
    p = argparse.ArgumentParser(description="Notify the CET Teams channel")
    p.add_argument("--title", required=True)
    p.add_argument("--text", default="")
    p.add_argument("--url", default="")
    p.add_argument("--button", default="Open")
    p.add_argument("--fact", action="append", default=[], help="Name=Value (repeatable)")
    a = p.parse_args(argv)
    facts = [tuple(f.split("=", 1)) for f in a.fact if "=" in f]
    payload = card(a.title, a.text, facts, a.url, a.button)
    hook = os.environ.get("TEAMS_WEBHOOK_URL", "").strip()
    if not hook:
        print("::warning::TEAMS_WEBHOOK_URL not set; Teams message skipped")
        print(json.dumps(payload, indent=2))
        return 0
    req = urllib.request.Request(hook, data=json.dumps(payload).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(f"Teams: HTTP {r.status}")
    except Exception as e:                       # a missed chat message must not fail the pipeline
        print(f"::warning::Teams message failed: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
