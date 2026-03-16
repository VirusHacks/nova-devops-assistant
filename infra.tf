# infra.tf
provider "aws" {
  region = "us-east-1"
}

# 1. EXPENSIVE RESOURCE: A very large EC2 instance
resource "aws_instance" "app_server" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "m5.24xlarge"
  tags = {
    Name = "Dev-Environment"
  }
}

# 2. TECH DEBT: NAT Gateway (High data processing costs)
# CloudZero identifies this as common tech debt; VPC Endpoints are often cheaper.
resource "aws_nat_gateway" "example" {
  allocation_id = aws_eip.example.id
  subnet_id     = aws_subnet.example.id
}

resource "aws_eip" "example" {
  domain = "vpc"
}
