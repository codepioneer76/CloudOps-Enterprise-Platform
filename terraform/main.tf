terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = "production"
      ManagedBy   = "Terraform"
    }
  }
}

# -----------------------------------------------------------------------------
# Data Sources
# -----------------------------------------------------------------------------

# Query the latest official Amazon Linux 2023 AMI (x86_64)
data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
}

# -----------------------------------------------------------------------------
# Networking: VPC, Subnet, Internet Gateway & Routing
# -----------------------------------------------------------------------------

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name    = "${var.project_name}-vpc"
    Project = var.project_name
  }
}

resource "aws_internet_gateway" "gw" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name    = "${var.project_name}-igw"
    Project = var.project_name
  }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true

  tags = {
    Name    = "${var.project_name}-public-subnet"
    Project = var.project_name
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gw.id
  }

  tags = {
    Name    = "${var.project_name}-public-rt"
    Project = var.project_name
  }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# -----------------------------------------------------------------------------
# Security Group
# NOTE: PostgreSQL port (5432) is intentionally NOT exposed publicly.
# Only SSH (from trusted IP) and HTTP port 8000 are accessible.
# -----------------------------------------------------------------------------

resource "aws_security_group" "app_sg" {
  name        = "${var.project_name}-app-sg"
  description = "Security group for CloudOps Enterprise Platform application"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "SSH access from trusted administrator CIDR only"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.trusted_ssh_cidr]
  }

  ingress {
    description = "CloudOps web application HTTP traffic"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "${var.project_name}-app-sg"
    Project = var.project_name
  }
}

# -----------------------------------------------------------------------------
# Compute: EC2 Instance & User Data
# -----------------------------------------------------------------------------

resource "aws_instance" "app_server" {
  ami                         = data.aws_ami.amazon_linux_2023.id
  instance_type               = var.instance_type
  subnet_id                   = aws_subnet.public.id
  vpc_security_group_ids      = [aws_security_group.app_sg.id]
  key_name                    = var.key_pair_name
  associate_public_ip_address = true

  user_data = <<-EOF
              #!/bin/bash
              set -euo pipefail

              # Update system packages
              dnf update -y

              # Install and start Docker daemon
              dnf install -y docker
              systemctl enable docker
              systemctl start docker

              # Grant ec2-user permissions to interact with Docker
              usermod -aG docker ec2-user

              # Create isolated docker bridge network for platform containers
              docker network create cloudops-net || true

              # Run internal PostgreSQL container (not published to host ports, isolated to cloudops-net)
              docker run -d \
                --name cloudops-postgres \
                --network cloudops-net \
                --restart unless-stopped \
                -e POSTGRES_DB=cloudops_db \
                -e POSTGRES_USER=cloudops_user \
                -e POSTGRES_PASSWORD='${var.db_password}' \
                postgres:16-alpine || true

              # Pull and run the CloudOps Enterprise Platform application container
              # Port 8000 is published to host; Database communication remains internal on cloudops-net
              docker run -d \
                --name cloudops-enterprise-platform \
                --network cloudops-net \
                --restart unless-stopped \
                -p 8000:8000 \
                -e APP_NAME="CloudOps Enterprise Platform" \
                -e APP_ENV=production \
                -e DEBUG=false \
                -e DB_BACKEND=postgres \
                -e DB_HOST=cloudops-postgres \
                -e DB_PORT=5432 \
                -e DB_NAME=cloudops_db \
                -e DB_USER=cloudops_user \
                -e DB_PASSWORD='${var.db_password}' \
                cloudops-enterprise-platform:latest || true
              EOF

  user_data_replace_on_change = true

  root_block_device {
    volume_size           = 20
    volume_type           = "gp3"
    delete_on_termination = true
    encrypted             = true
    tags = {
      Name    = "${var.project_name}-root-volume"
      Project = var.project_name
    }
  }

  tags = {
    Name    = "${var.project_name}-app-server"
    Project = var.project_name
  }
}
