# AWS account requested in ServiceNow RITM0000002 / SCTASK0000002
# Requested for: test@t.com
# Written by scripts/new_account.py. Change it through a new request, not by hand.
module "account_demo_sbx_2" {
  source = "./modules/aws-account"

  account_name = "demo-sbx-2"
  email        = "aws+demo-sbx-2@REPLACE-company.com"
  parent_ou_id = "ou-REPLACE-xxxxxxxx"

  tags = {
    "Technical:ApplicationName" = "demo-team-2"
    "Technical:PlatformOwner"   = "t@t.com"
    "Business:BudgetApprover"   = "b@t.com"
    "Business:SupportGroup"     = "Demo SnowGroup"
    "ServiceNow:RITM"           = "RITM0000002"
  }
}

output "account_demo_sbx_2_id" {
  description = "Account ID of demo-sbx-2"
  value       = module.account_demo_sbx_2.account_id
}
