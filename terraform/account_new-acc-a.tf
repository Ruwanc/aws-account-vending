# AWS account requested in ServiceNow RITM0010015 / SCTASK0010020
# Requested for: t@t.com
# Written by scripts/new_account.py. Change it through a new request, not by hand.
module "account_new_acc_a" {
  source = "./modules/aws-account"

  account_name = "new-acc-a"
  email        = "aws+new-acc-a@REPLACE-company.com"
  parent_ou_id = "ou-REPLACE-xxxxxxxx"

  tags = {
    "Technical:ApplicationName" = "app-team"
    "Technical:PlatformOwner"   = "a@t.com"
    "Business:BudgetApprover"   = "b@t.com"
    "Business:SupportGroup"     = "App Team Support"
    "ServiceNow:RITM"           = "RITM0010015"
  }
}

output "account_new_acc_a_id" {
  description = "Account ID of new-acc-a"
  value       = module.account_new_acc_a.account_id
}
