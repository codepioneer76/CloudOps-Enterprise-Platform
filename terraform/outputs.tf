output "instance_public_ip" {
  description = "Public IPv4 address assigned to the CloudOps EC2 instance."
  value       = aws_instance.app_server.public_ip
}

output "instance_id" {
  description = "EC2 instance identifier."
  value       = aws_instance.app_server.id
}

output "vpc_id" {
  description = "Identifier of the created VPC."
  value       = aws_vpc.main.id
}

output "public_subnet_id" {
  description = "Identifier of the public subnet."
  value       = aws_subnet.public.id
}

output "security_group_id" {
  description = "Identifier of the application security group."
  value       = aws_security_group.app_sg.id
}

output "app_url" {
  description = "Public URL to access the CloudOps Enterprise Platform application."
  value       = "http://${aws_instance.app_server.public_ip}:8000"
}
