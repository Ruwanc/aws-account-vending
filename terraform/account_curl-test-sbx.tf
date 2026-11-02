# AWS account requested in ServiceNow RITM0000002 / SCTASK0000002
# Requested for: you@example.com
# Written by scripts/new_account.py. Change it through a new request, not by hand.
module "account_curl_test_sbx" {
  source = "./modules/aws-account"

  account_name = "curl-test-sbx"
  email        = "aws+curl-test-sbx@REPLACE-company.com"
  parent_ou_id = "ou-REPLACE-xxxxxxxx"

  tags = {
    "Technical:ApplicationName" = "Demo"
    "Technical:PlatformOwner"   = "you@example.com"
    "Business:BudgetApprover"   = "manager@example.com"
    "Business:SupportGroup"     = "Demo Support"
    "ServiceNow:RITM"           = "RITM0000002"
  }
}

output "account_curl_test_sbx_id" {
  description = "Account ID of curl-test-sbx"
  value       = module.account_curl_test_sbx.account_id
}
