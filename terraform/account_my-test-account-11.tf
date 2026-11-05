# AWS account requested in ServiceNow RITM0010016 / SCTASK0010021
# Requested for: t@t.com
# Written by scripts/new_account.py. Change it through a new request, not by hand.
module "account_my_test_account_11" {
  source = "./modules/aws-account"

  account_name = "my-test-account-11"
  email        = "aws+my-test-account-11@REPLACE-company.com"
  parent_ou_id = "ou-REPLACE-xxxxxxxx"

  tags = {
    "Technical:ApplicationName" = "test-team"
    "Technical:PlatformOwner"   = "ac@t.com"
    "Business:BudgetApprover"   = "b@t.com"
    "Business:SupportGroup"     = "Test SNOW team"
    "ServiceNow:RITM"           = "RITM0010016"
  }
}

output "account_my_test_account_11_id" {
  description = "Account ID of my-test-account-11"
  value       = module.account_my_test_account_11.account_id
}
