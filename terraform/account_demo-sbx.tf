# AWS account requested in ServiceNow RITM0000001 / SCTASK0000001
# Requested for: abc@test.com
# Written by scripts/new_account.py. Change it through a new request, not by hand.
module "account_demo_sbx" {
  source = "./modules/aws-account"

  account_name = "demo-sbx"
  email        = "aws+demo-sbx@REPLACE-company.com"
  parent_ou_id = "ou-REPLACE-xxxxxxxx"

  tags = {
    "Technical:ApplicationName" = "Demo Team"
    "Technical:PlatformOwner"   = "t@t.com"
    "Business:BudgetApprover"   = "b@t.com"
    "Business:SupportGroup"     = "Demo ServiceNow"
    "ServiceNow:RITM"           = "RITM0000001"
  }
}

output "account_demo_sbx_id" {
  description = "Account ID of demo-sbx"
  value       = module.account_demo_sbx.account_id
}
