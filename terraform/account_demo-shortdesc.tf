# AWS account requested in ServiceNow RITM0010024 / SCTASK0010028
# Requested for: t@t.com
# Written by scripts/new_account.py. Change it through a new request, not by hand.
module "account_demo_shortdesc" {
  source = "./modules/aws-account"

  account_name = "demo-shortdesc"
  email        = "aws+demo-shortdesc@REPLACE-company.com"
  parent_ou_id = "ou-REPLACE-xxxxxxxx"

  tags = {
    "Technical:ApplicationName" = "Demo"
    "Technical:PlatformOwner"   = "jane.doe@corp.com"
    "Business:BudgetApprover"   = "kurt.brochu@corp.com"
    "Business:SupportGroup"     = "Demo Support"
    "ServiceNow:RITM"           = "RITM0010024"
  }
}

output "account_demo_shortdesc_id" {
  description = "Account ID of demo-shortdesc"
  value       = module.account_demo_shortdesc.account_id
}
