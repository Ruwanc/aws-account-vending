# AWS account requested in ServiceNow RITM0010010 / SCTASK0010015
# Requested for: t@t.com
# Written by scripts/new_account.py. Change it through a new request, not by hand.
module "account_sn_flow_test_sbx" {
  source = "./modules/aws-account"

  account_name = "sn-flow-test-sbx"
  email        = "aws+sn-flow-test-sbx@REPLACE-company.com"
  parent_ou_id = "ou-REPLACE-xxxxxxxx"

  tags = {
    "Technical:ApplicationName" = "Demo"
    "Technical:PlatformOwner"   = "tom.lee@example.com"
    "Business:BudgetApprover"   = "ann.wu@example.com"
    "Business:SupportGroup"     = "Demo Support"
    "ServiceNow:RITM"           = "RITM0010010"
  }
}

output "account_sn_flow_test_sbx_id" {
  description = "Account ID of sn-flow-test-sbx"
  value       = module.account_sn_flow_test_sbx.account_id
}
