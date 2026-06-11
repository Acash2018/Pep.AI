variable "aws_region" {
  description = "AWS region for the ECS/Fargate deployment."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Name prefix for AWS resources."
  type        = string
  default     = "pep-ai"
}

variable "image_tag" {
  description = "Container image tag used by ECS task definitions."
  type        = string
  default     = "latest"
}

variable "db_name" {
  description = "RDS PostgreSQL database name."
  type        = string
  default     = "pep_ai"
}

variable "db_username" {
  description = "RDS PostgreSQL username."
  type        = string
  default     = "pep_user"
}

variable "db_password" {
  description = "RDS PostgreSQL password. Pass with TF_VAR_db_password or a tfvars file."
  type        = string
  sensitive   = true
}

variable "frontend_cpu" {
  description = "Fargate CPU units for the frontend task."
  type        = number
  default     = 256
}

variable "frontend_memory" {
  description = "Fargate memory MiB for the frontend task."
  type        = number
  default     = 512
}

variable "backend_cpu" {
  description = "Fargate CPU units for the backend task, including the Ollama sidecar."
  type        = number
  default     = 2048
}

variable "backend_memory" {
  description = "Fargate memory MiB for the backend task, including the Ollama sidecar."
  type        = number
  default     = 8192
}

variable "desired_count" {
  description = "Number of frontend and backend tasks."
  type        = number
  default     = 1
}

variable "allowed_ip_cidrs" {
  description = "IPv4 CIDR blocks allowed to access the ALB through AWS WAF."
  type        = list(string)
  default     = []
}

variable "waf_rate_limit" {
  description = "Maximum requests per 5-minute window per source IP before AWS WAF blocks the caller."
  type        = number
  default     = 100
}

variable "ollama_base_url" {
  description = "Ollama endpoint used by the backend. The ECS deployment runs Ollama as a sidecar in the backend task."
  type        = string
  default     = "http://127.0.0.1:11434"
}

variable "ollama_image" {
  description = "Ollama container image used as the backend ECS sidecar."
  type        = string
  default     = "ollama/ollama:latest"
}

variable "ollama_model" {
  description = "Ollama reasoning model name passed to the backend."
  type        = string
  default     = "llama3.2:3b"
}

variable "ollama_embedding_model" {
  description = "Ollama embedding model name passed to the backend."
  type        = string
  default     = "nomic-embed-text"
}

variable "enable_s3_lambda_ingestion" {
  description = "Whether to deploy the S3-triggered Lambda that ingests player JSON/CSV files into PostgreSQL."
  type        = bool
  default     = false
}

variable "lambda_ingest_zip_path" {
  description = "Path to the built Lambda deployment zip for S3 player ingestion. Required when enable_s3_lambda_ingestion is true."
  type        = string
  default     = ""
}

variable "lambda_ingest_prefix" {
  description = "S3 object prefix that triggers player ingestion."
  type        = string
  default     = "uploads/"
}

variable "enable_s3_sns_notifications" {
  description = "Whether to publish S3 object-created notifications to SNS for production upload testing."
  type        = bool
  default     = false
}

variable "s3_sns_notification_email" {
  description = "Optional email address to subscribe to S3 object-created SNS notifications. The recipient must confirm the subscription email."
  type        = string
  default     = ""
}

variable "s3_sns_notification_prefix" {
  description = "Optional S3 object prefix that publishes SNS notifications. Null watches the whole bucket."
  type        = string
  default     = null
}
