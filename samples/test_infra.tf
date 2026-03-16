provider "aws" {
  region = "us-east-1"
}

# ⚠️ COST RISK: Using a very expensive instance type
resource "aws_instance" "high_cost_instance" {
  ami           = "ami-12345678"
  instance_type = "p3.16xlarge" # Very expensive!

  tags = {
    Name = "Experimental-Worker"
    # ⚠️ MISSING: CostCenter or Owner tag
  }
}

# ⚠️ SECURITY/COST RISK: Large unencrypted volume
resource "aws_ebs_volume" "over_provisioned" {
  availability_zone = "us-east-1a"
  size              = 1000 # 1TB might be excessive
  encrypted         = false

  tags = {
    Name = "DataVolume"
  }
}

# ⚠️ COST RISK: Provisioned IOPS (PIOPS) volumes are expensive
resource "aws_ebs_volume" "expensive_io" {
  availability_zone = "us-east-1a"
  size              = 100
  type              = "io2"
  iops              = 10000
}
