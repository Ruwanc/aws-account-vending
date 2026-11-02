# Sample module: replace with your organisation's real account module if you have one
# (set module_source in config/account-defaults.json).
resource "aws_organizations_account" "this" {
  name                       = var.account_name
  email                      = var.email
  parent_id                  = var.parent_ou_id
  role_name                  = "OrganizationAccountAccessRole"
  iam_user_access_to_billing = "ALLOW"
  close_on_deletion          = false
  tags                       = var.tags

  lifecycle {
    # Removing an account file must never close a real AWS account by accident.
    prevent_destroy = true
    # role_name can't be read back from AWS, so ignore it after creation.
    ignore_changes = [role_name]
  }
}
