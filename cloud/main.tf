terraform {
    backend "s3" {
        bucket                          = "cumberland-cloud-terraform-state"
        key                             = "web/elara/terraform.tfstate"
        region                          = "us-east-1"
    }
}

provider "aws" {
    region                              = "us-east-1"
}

locals {
    platform                            = {
        client                          = "CUMBERLAND CLOUD"
        environment                     = "PRODUCTION"
    }
    kms                                 = {
        aws_managed                     = true
    }
}