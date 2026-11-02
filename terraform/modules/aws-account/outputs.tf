output "account_id" {
  description = "The new AWS account ID."
  value       = aws_organizations_account.this.id
}

output "arn" {
  description = "The new AWS account ARN."
  value       = aws_organizations_account.this.arn
}
