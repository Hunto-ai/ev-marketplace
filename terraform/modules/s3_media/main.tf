locals {
  name_prefix = "${var.project_slug}-${var.environment}"
  bucket_name = replace("${local.name_prefix}-media", "_", "-")
}

resource "aws_s3_bucket" "media" {
  bucket        = local.bucket_name
  force_destroy = var.force_destroy

  tags = {
    Name = local.bucket_name
  }
}

resource "aws_s3_bucket_ownership_controls" "media" {
  bucket = aws_s3_bucket.media.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_public_access_block" "media" {
  bucket = aws_s3_bucket.media.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "media" {
  bucket = aws_s3_bucket.media.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

output "bucket_name" {
  value = aws_s3_bucket.media.bucket
}

output "bucket_arn" {
  value = aws_s3_bucket.media.arn
}

output "bucket_domain" {
  value = aws_s3_bucket.media.bucket_regional_domain_name
}
