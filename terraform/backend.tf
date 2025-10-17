terraform {
  backend "s3" {
    bucket               = "evmarket-tf-state"
    key                  = "global/terraform.tfstate"
    workspace_key_prefix = "env"
    region               = "us-east-2"
    dynamodb_table       = "evmarket-tf-locks"
    encrypt              = true
  }
}
