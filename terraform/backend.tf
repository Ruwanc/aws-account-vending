# Remote state. Replace the placeholders with your state bucket and lock table.
terraform {
  backend "s3" {
    bucket         = "REPLACE-terraform-state-bucket"
    key            = "aws-account-vending/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "REPLACE-terraform-locks"
    encrypt        = true
  }
}
