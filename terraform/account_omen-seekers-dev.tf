# AWS account requested in ServiceNow RITM0010011 / SCTASK0010016
# Requested for: t@t.com
# Written by scripts/new_account.py. Change it through a new request, not by hand.
module "account_omen_seekers_dev" {
  source = "./modules/aws-account"

  account_name = "omen-seekers-dev"
  email        = "aws+omen-seekers-dev@REPLACE-company.com"
  parent_ou_id = "ou-REPLACE-xxxxxxxx"

  tags = {
    "Technical:ApplicationName" = "ocen-seekers"
    "Technical:PlatformOwner"   = "t@t.com"
    "Business:BudgetApprover"   = "b@t.com"
    "Business:SupportGroup"     = "Ocen Seekers"
    "ServiceNow:RITM"           = "RITM0010011"
  }
}

output "account_omen_seekers_dev_id" {
  description = "Account ID of omen-seekers-dev"
  value       = module.account_omen_seekers_dev.account_id
}
