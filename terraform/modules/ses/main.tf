resource "aws_ses_domain_identity" "this" {
  domain = var.domain
}

resource "aws_route53_record" "ses_verification" {
  count   = var.hosted_zone_id == "" ? 0 : 1
  zone_id = var.hosted_zone_id
  name    = "${aws_ses_domain_identity.this.domain}."
  type    = "TXT"
  ttl     = 600
  records = [aws_ses_domain_identity.this.verification_token]
}

resource "aws_ses_domain_dkim" "this" {
  domain = var.domain
}

resource "aws_route53_record" "ses_dkim" {
  count   = var.hosted_zone_id == "" ? 0 : 3
  zone_id = var.hosted_zone_id
  name    = "${element(aws_ses_domain_dkim.this.dkim_tokens, count.index)}._domainkey"
  type    = "CNAME"
  ttl     = 600
  records = ["${element(aws_ses_domain_dkim.this.dkim_tokens, count.index)}.dkim.amazonses.com"]
}

output "identity_arn" {
  value = aws_ses_domain_identity.this.arn
}

output "domain" {
  value = aws_ses_domain_identity.this.domain
}

output "dkim_tokens" {
  value = aws_ses_domain_dkim.this.dkim_tokens
}
