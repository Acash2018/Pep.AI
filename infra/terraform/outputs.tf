output "alb_dns_name" {
  description = "Public DNS name for the Application Load Balancer."
  value       = aws_lb.main.dns_name
}

output "frontend_ecr_repository_url" {
  description = "ECR repository URL for the frontend image."
  value       = aws_ecr_repository.frontend.repository_url
}

output "backend_ecr_repository_url" {
  description = "ECR repository URL for the backend image."
  value       = aws_ecr_repository.backend.repository_url
}

output "ecs_cluster_name" {
  description = "ECS cluster name."
  value       = aws_ecs_cluster.main.name
}

output "frontend_service_name" {
  description = "Frontend ECS service name."
  value       = aws_ecs_service.frontend.name
}

output "backend_service_name" {
  description = "Backend ECS service name."
  value       = aws_ecs_service.backend.name
}

output "rds_endpoint" {
  description = "Private RDS PostgreSQL endpoint."
  value       = aws_db_instance.postgres.address
}

output "waf_web_acl_name" {
  description = "AWS WAF Web ACL attached to the ALB."
  value       = aws_wafv2_web_acl.alb.name
}

output "waf_allowed_ip_set_name" {
  description = "AWS WAF IP set containing client CIDRs allowed to access the ALB."
  value       = aws_wafv2_ip_set.allowed_clients.name
}

output "s3_ingestion_bucket_name" {
  description = "S3 bucket for player JSON/CSV ingestion uploads."
  value       = aws_s3_bucket.ingestion.bucket
}

output "s3_ingestion_upload_prefix" {
  description = "S3 prefix that triggers the ingestion Lambda when Lambda ingestion is enabled."
  value       = var.lambda_ingest_prefix
}

output "s3_player_ingest_lambda_name" {
  description = "Name of the S3 player ingestion Lambda, when enabled."
  value       = var.enable_s3_lambda_ingestion ? aws_lambda_function.s3_player_ingest[0].function_name : null
}

output "s3_object_created_sns_topic_arn" {
  description = "SNS topic ARN that receives S3 object-created events, when enabled."
  value       = var.enable_s3_sns_notifications ? aws_sns_topic.s3_object_created[0].arn : null
}

output "s3_object_created_sns_email_subscription" {
  description = "Email endpoint subscribed to S3 object-created notifications, when configured."
  value       = var.s3_sns_notification_email != "" ? var.s3_sns_notification_email : null
}
