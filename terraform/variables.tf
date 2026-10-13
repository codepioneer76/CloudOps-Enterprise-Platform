variable "aws_region" {
  description = "The AWS region where resources will be created."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "The project name prefix used for resource naming and tagging."
  type        = string
  default     = "cloudops-enterprise"
}

variable "instance_type" {
  description = "The EC2 instance type for running the application workload."
  type        = string
  default     = "t2.micro"
}

variable "trusted_ssh_cidr" {
  description = "Trusted IPv4 CIDR block allowed to connect via SSH (set to your IP/32, e.g., 203.0.113.50/32)."
  type        = string
}

variable "key_pair_name" {
  description = "Name of an existing AWS EC2 Key Pair used for SSH authentication."
  type        = string
}

variable "db_password" {
  description = "Secure password for PostgreSQL database service."
  type        = string
  sensitive   = true
}
