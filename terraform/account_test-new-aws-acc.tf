# AWS account requested in ServiceNow RITM0010013 / SCTASK0010018
# Requested for: t@t.com
# Written by scripts/new_account.py. Change it through a new request, not by hand.
module "account_test_new_aws_acc" {
  source = "./modules/aws-account"

  account_name = "test-new-aws-acc"
  email        = "aws+test-new-aws-acc@REPLACE-company.com"
  parent_ou_id = "ou-REPLACE-xxxxxxxx"

  tags = {
    "Technical:ApplicationName" = "test team"
    "Technical:PlatformOwner"   = "t@ab.com"
    "Business:BudgetApprover"   = "b@t.com"
    "Business:SupportGroup"     = "Test Snow Team"
    "ServiceNow:RITM"           = "RITM0010013"
  }
}

output "account_test_new_aws_acc_id" {
  description = "Account ID of test-new-aws-acc"
  value       = module.account_test_new_aws_acc.account_id
}
