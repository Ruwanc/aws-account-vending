# AWS account requested in ServiceNow RITM0010012 / SCTASK0010017
# Requested for: t@t.com
# Written by scripts/new_account.py. Change it through a new request, not by hand.
module "account_new_demo_account1" {
  source = "./modules/aws-account"

  account_name = "new-demo-account1"
  email        = "aws+new-demo-account1@REPLACE-company.com"
  parent_ou_id = "ou-REPLACE-xxxxxxxx"

  tags = {
    "Technical:ApplicationName" = "demo team"
    "Technical:PlatformOwner"   = "t@t.com"
    "Business:BudgetApprover"   = "b@t.com"
    "Business:SupportGroup"     = "Demo SNOW"
    "ServiceNow:RITM"           = "RITM0010012"
  }
}

output "account_new_demo_account1_id" {
  description = "Account ID of new-demo-account1"
  value       = module.account_new_demo_account1.account_id
}
