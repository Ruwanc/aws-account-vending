# AWS account requested in ServiceNow RITM0010018 / SCTASK0010023
# Requested for: t@t.com
# Written by scripts/new_account.py. Change it through a new request, not by hand.
module "account_payments_nonprod" {
  source = "./modules/aws-account"

  account_name = "payments-nonprod"
  email        = "aws+payments-nonprod@REPLACE-company.com"
  parent_ou_id = "ou-REPLACE-xxxxxxxx"

  tags = {
    "Technical:ApplicationName" = "Payments"
    "Technical:PlatformOwner"   = "jane.doe@corp.com"
    "Business:BudgetApprover"   = "kurt.brochu@corp.com"
    "Business:SupportGroup"     = "Payments-AppSupport"
    "ServiceNow:RITM"           = "RITM0010018"
  }
}

output "account_payments_nonprod_id" {
  description = "Account ID of payments-nonprod"
  value       = module.account_payments_nonprod.account_id
}
