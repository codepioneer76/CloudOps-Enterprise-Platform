# CloudOps Enterprise Platform - AWS Terraform Deployment

Production-grade modular Terraform configuration for deploying the CloudOps Enterprise Platform on Amazon Web Services (AWS).

---

## Architecture Overview

This Terraform setup deploys the following infrastructure components in AWS:
- **Custom Virtual Private Cloud (VPC)**: Isolated network space (`10.0.0.0/16`) with DNS resolution and hostnames enabled.
- **Public Subnet**: Subnet (`10.0.1.0/24`) configured with auto-assigned public IPs.
- **Internet Gateway & Routing**: Internet Gateway (IGW) attached to the VPC with default route (`0.0.0.0/0`) directing public traffic.
- **Security Group (`app-sg`)**:
  - **SSH (Port 22)**: Restricted exclusively to administrator's trusted CIDR (`var.trusted_ssh_cidr`).
  - **Application (Port 8000)**: Ingress permitted for HTTP web traffic.
  - **PostgreSQL (Port 5432)**: **Strictly NOT exposed** to the public internet or external networks; database access operates entirely within internal container networking.
  - **Egress**: Unrestricted outbound connectivity.
- **EC2 Compute Instance**:
  - Automatically queries the latest official Amazon Linux 2023 AMI via data source.
  - Automated `user_data` bootstrap that installs Docker, initiates services, creates an isolated bridge network, starts PostgreSQL internally, and runs the CloudOps Enterprise Platform container.
  - Root volume configured with encrypted EBS `gp3`.

---

## Prerequisites

Before deploying this infrastructure, ensure you have:
1. **Terraform CLI**: Version `>= 1.0` installed. Check with:
   ```bash
   terraform version
   ```
2. **AWS CLI & Credentials**: Configured with valid programmatic credentials and sufficient IAM permissions (EC2, VPC, Internet Gateways, Route Tables, Security Groups):
   ```bash
   aws sts get-caller-identity
   ```
3. **AWS EC2 Key Pair**: An existing Key Pair created in your target AWS region (e.g. `us-east-1`) to enable SSH access.
4. **Public IP Address**: Your current public IP formatted with `/32` (e.g., `203.0.113.50/32`) for the SSH ingress whitelist.

---

## Configuration & Variables

1. Copy the example variables file:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

2. Edit `terraform.tfvars` with your environment values:
   - `aws_region`: AWS Region (default: `us-east-1`)
   - `project_name`: Resource naming prefix (default: `cloudops-enterprise`)
   - `instance_type`: Compute sizing (default: `t2.micro`)
   - `trusted_ssh_cidr`: Your IP with `/32` (e.g., `"203.0.113.50/32"`)
   - `key_pair_name`: Name of your existing EC2 Key Pair
   - `db_password`: High-entropy database password

---

## Deployment Workflow

> [!CAUTION]
> **Explicit Approval Required**: Never execute `terraform apply` or create paid cloud infrastructure without explicit authorization and careful review of the execution plan.

### 1. Initialize Working Directory
Downloads required provider plugins (`hashicorp/aws ~> 5.0`) and prepares the state backend:
```bash
terraform init
```

### 2. Validate Syntax and Structure
Verifies that configuration files are syntactically valid and internally consistent:
```bash
terraform validate
```

### 3. Review Execution Plan
Generates an execution plan showing the exact resources that will be created or modified:
```bash
terraform plan -out=tfplan
```
Review the proposed plan carefully to confirm resource counts and parameter definitions.

### 4. Apply Changes (Requires Explicit Approval)
Apply the validated plan to provision infrastructure:
```bash
terraform apply tfplan
```
Once provisioning completes, Terraform outputs the instance public IP and the application access URL (`http://<instance_ip>:8000`).

### 5. Destroy Infrastructure
To avoid recurring costs when infrastructure is no longer needed, tear down all provisioned resources:
```bash
terraform destroy
```

---

## Security Considerations

- **SSH Access Control**: SSH (port 22) is restricted exclusively to `var.trusted_ssh_cidr`. Do **not** use `0.0.0.0/0`.
- **Database Isolation**: PostgreSQL (port 5432) is never exposed via the AWS Security Group or published on the host network. Communication between the platform container and PostgreSQL occurs through an internal Docker bridge network (`cloudops-net`).
- **Secret Management**: Sensitive parameters (such as `db_password`) are marked `sensitive = true` in Terraform to prevent leakage into console logs and CLI outputs.
- **State File Protection**: `terraform.tfstate`, `terraform.tfstate.backup`, and `terraform.tfvars` contain sensitive values and must **never** be committed to version control. Confirm they are listed in your repository `.gitignore`.

---

## Cost & Resource Management

- Resources provisioned by this module (EC2 instances, EBS volumes, public IPv4 addresses) incur AWS charges.
- While `t2.micro` falls within the AWS Free Tier for eligible accounts, running instances continuously or exceeding Free Tier limits will incur charges.
- Always execute `terraform destroy` when platform validation or testing is complete.
