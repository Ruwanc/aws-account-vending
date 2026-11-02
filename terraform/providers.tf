# Runs in the AWS Organizations management account (or a delegated admin account).
# Credentials come from GitHub Actions OIDC (see README), never from stored keys.
provider "aws" {
  region = "us-east-1"

  default_tags {
    tags = {
      "ManagedBy" = "terraform/aws-account-vending"
    }
  }
}
