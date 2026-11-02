variable "account_name" {
  description = "Short account name, e.g. rme-orders-nonprod."
  type        = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{1,38}[a-z0-9]$", var.account_name))
    error_message = "account_name: 3-40 chars, lowercase letters, numbers and hyphens, starting with a letter."
  }
}

variable "email" {
  description = "Unique root email address for the new account."
  type        = string
}

variable "parent_ou_id" {
  description = "Organizational unit (ou-xxxx-xxxxxxxx) or root (r-xxxx) the account is placed in."
  type        = string
}

variable "tags" {
  description = "Tags for the account."
  type        = map(string)
  default     = {}
}
