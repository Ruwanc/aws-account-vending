# AWS account requested in ServiceNow RITM0010014 / SCTASK0010019
# Requested for: t@t.com
# Written by scripts/new_account.py. Change it through a new request, not by hand.
module "account_dream_team" {
  source = "./modules/aws-account"

  account_name = "dream-team"
  email        = "aws+dream-team@REPLACE-company.com"
  parent_ou_id = "ou-REPLACE-xxxxxxxx"

  tags = {
    "Technical:ApplicationName" = "dream team"
    "Technical:PlatformOwner"   = "a@t.com"
    "Business:BudgetApprover"   = "b@t.com"
    "Business:SupportGroup"     = "Dream Team Support"
    "ServiceNow:RITM"           = "RITM0010014"
  }
}

output "account_dream_team_id" {
  description = "Account ID of dream-team"
  value       = module.account_dream_team.account_id
}
