# ServiceNow flow for the AWS account request (for the ServiceNow admins)

Goal: after the requester's **manager approves**, create an **SCTASK under the same RITM**
for **Cloud Engineering** and start the GitHub automation. GitHub then updates and closes
that SCTASK itself.

## 1. Catalog item: "AWS account request"

Variables. The CET Agent sends these names; tell Cloud Engineering if you use different ones.

| Variable name | Type | Mandatory |
|---|---|---|
| `account_name` | Single line text | yes |
| `app_team_name` | Single line text | yes |
| `support_group` | Single line text (or Reference → sys_user_group) | yes |
| `technical_owner` | Single line text (email) or Reference → sys_user | yes |
| `budget_approver` | Single line text (email) or Reference → sys_user | yes |

`Requested for` is the standard field on the request (the agent sets it). The user records
need **Manager** filled in, or the approval has nobody to go to.

Give Cloud Engineering the item's **sys_id**; the agent needs it (`SN_CATALOG_ITEM_SYS_ID`).

## 2. Flow (Flow Designer), attached to the catalog item

Trigger: **Service Catalog** (this item).

1. **Ask for Approval** on the RITM
   - Approver: `Requested Item → Requested for → Manager`
   - Rule: approve when anyone approves; reject when anyone rejects
   - Optional: a due date and a reminder after 2 days
2. **If rejected** → Update RITM: State = Closed Incomplete, with work notes. The requester is notified.
3. **If approved** → **Create Catalog Task**
   - Assignment group: **Cloud Engineering**
   - Short description: `Create AWS account: {account_name}`
   - Copy the catalog variables to the task
   - "Wait" unchecked, so the flow continues
4. **REST step** (IntegrationHub), right after the task is created:

   ```
   POST https://api.github.com/repos/YOUR-ORG/aws-account-vending/dispatches
   Headers:
     Accept: application/vnd.github+json
     Authorization: Bearer <credential>
     X-GitHub-Api-Version: 2022-11-28
   Body:
   {
     "event_type": "aws-account-request",
     "client_payload": {
       "ritm":            "<RITM number>",
       "sctask":          "<SCTASK number from step 3>",
       "account_name":    "<variable account_name>",
       "app_team_name":   "<variable app_team_name>",
       "support_group":   "<variable support_group, display value>",
       "technical_owner": "<technical_owner email>",
       "budget_approver": "<budget_approver email>",
       "requested_for":   "<Requested for → Email>"
     }
   }
   ```
   - Success: GitHub answers **204 No Content**. Then add a work note to the SCTASK:
     "Sent to GitHub automation".
   - Failure: add a work note with the error and leave the task with Cloud Engineering.
   - For reference fields, send the **email or display value**, not the sys_id. GitHub
     checks every value and rejects anything that doesn't match.
   - `client_payload` allows at most 10 top-level keys; this uses 8.
5. **Wait for the SCTASK to close.** GitHub closes it (Closed Complete, with the account ID in
   the work notes) after the account is created, and the RITM then closes as usual.

## 3. Credential for the REST step

GitHub Enterprise **Cloud**, API host `api.github.com`. If your enterprise uses a dedicated
`*.ghe.com` domain, the host is `api.<your-subdomain>.ghe.com`. Pick one of these:

- **Start here: fine-grained personal access token** of a service account, limited to the
  one repo, permission **Contents: read & write**, with an expiry date. Store it in a
  ServiceNow Credential (API Key / Bearer) and set a reminder to rotate it.
- **Later: GitHub App** via the IntegrationHub **GitHub spoke**. It uses short-lived tokens,
  with nothing to rotate by hand.

No MID Server is needed for GitHub Enterprise Cloud.

## 4. Integration user for GitHub → ServiceNow

GitHub Actions updates the SCTASK through the Table API. It needs a ServiceNow user (web
service access only) that can read and write **sc_task** (`work_notes`, `state`,
`close_notes`) on tasks for Cloud Engineering. Cloud Engineering stores its login as
GitHub secrets.

## 5. Test

1. Raise a request for a test user who has a manager → approve as the manager.
2. Check that the SCTASK is created for Cloud Engineering and that a PR appears in
   `aws-account-vending` within a minute.
3. Check the SCTASK work notes for the PR link and state = Work in Progress.
