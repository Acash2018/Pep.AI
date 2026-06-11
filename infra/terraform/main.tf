data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  name             = var.project_name
  azs              = slice(data.aws_availability_zones.available.names, 0, 2)
  frontend_image   = "${aws_ecr_repository.frontend.repository_url}:${var.image_tag}"
  backend_image    = "${aws_ecr_repository.backend.repository_url}:${var.image_tag}"
  chroma_directory = "/app/chromadb"
  ollama_directory = "/root/.ollama"
  s3_object_created_event_detail = merge(
    {
      bucket = {
        name = [aws_s3_bucket.ingestion.bucket]
      }
    },
    var.s3_sns_notification_prefix == null ? {} : {
      object = {
        key = [{ prefix = var.s3_sns_notification_prefix }]
      }
    }
  )
}

resource "aws_ecr_repository" "frontend" {
  name                 = "${local.name}-frontend"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "backend" {
  name                 = "${local.name}-backend"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_vpc" "main" {
  cidr_block           = "10.40.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${local.name}-vpc"
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${local.name}-igw"
  }
}

resource "aws_subnet" "public" {
  for_each = {
    for index, az in local.azs : az => index
  }

  vpc_id                  = aws_vpc.main.id
  availability_zone       = each.key
  cidr_block              = cidrsubnet(aws_vpc.main.cidr_block, 8, each.value)
  map_public_ip_on_launch = true

  tags = {
    Name = "${local.name}-public-${each.value + 1}"
  }
}

resource "aws_subnet" "private" {
  for_each = {
    for index, az in local.azs : az => index
  }

  vpc_id            = aws_vpc.main.id
  availability_zone = each.key
  cidr_block        = cidrsubnet(aws_vpc.main.cidr_block, 8, each.value + 10)

  tags = {
    Name = "${local.name}-private-${each.value + 1}"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "${local.name}-public-rt"
  }
}

resource "aws_route_table_association" "public" {
  for_each       = aws_subnet.public
  subnet_id      = each.value.id
  route_table_id = aws_route_table.public.id
}

resource "aws_security_group" "alb" {
  name        = "${local.name}-alb-sg"
  description = "Allow public HTTP traffic to the ALB."
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "frontend" {
  name        = "${local.name}-frontend-sg"
  description = "Allow ALB traffic to frontend tasks."
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 3000
    to_port         = 3000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "backend" {
  name        = "${local.name}-backend-sg"
  description = "Allow ALB traffic to backend tasks."
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "rds" {
  name        = "${local.name}-rds-sg"
  description = "Allow backend tasks to reach PostgreSQL."
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.backend.id]
  }

  ingress {
    description     = "PostgreSQL from S3 ingestion Lambda"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.lambda_ingest.id]
  }
}

resource "aws_security_group" "lambda_ingest" {
  name        = "${local.name}-lambda-ingest-sg"
  description = "Allow S3 ingestion Lambda to reach PostgreSQL."
  vpc_id      = aws_vpc.main.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "vpc_endpoint" {
  name        = "${local.name}-vpc-endpoint-sg"
  description = "Allow Lambda to reach private AWS service endpoints."
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "HTTPS from Lambda ingestion"
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.lambda_ingest.id, aws_security_group.backend.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${var.aws_region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [aws_vpc.main.default_route_table_id]

  tags = {
    Name = "${local.name}-s3-endpoint"
  }
}

resource "aws_vpc_endpoint" "secretsmanager" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.aws_region}.secretsmanager"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [for subnet in aws_subnet.private : subnet.id]
  security_group_ids  = [aws_security_group.vpc_endpoint.id]
  private_dns_enabled = true

  tags = {
    Name = "${local.name}-secretsmanager-endpoint"
  }
}

resource "aws_security_group" "efs" {
  name        = "${local.name}-efs-sg"
  description = "Allow backend tasks to mount EFS for ChromaDB persistence."
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 2049
    to_port         = 2049
    protocol        = "tcp"
    security_groups = [aws_security_group.backend.id]
  }
}

resource "aws_db_subnet_group" "main" {
  name       = "${local.name}-db-subnets"
  subnet_ids = [for subnet in aws_subnet.private : subnet.id]
}

resource "aws_db_instance" "postgres" {
  identifier             = "${local.name}-postgres"
  engine                 = "postgres"
  engine_version         = "16"
  instance_class         = "db.t4g.micro"
  allocated_storage      = 20
  storage_type           = "gp3"
  db_name                = var.db_name
  username               = var.db_username
  password               = var.db_password
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false
  skip_final_snapshot    = true
  apply_immediately      = true
}

resource "aws_efs_file_system" "chroma" {
  creation_token = "${local.name}-chroma"
  encrypted      = true

  tags = {
    Name = "${local.name}-chroma"
  }
}

resource "aws_efs_mount_target" "chroma" {
  for_each        = aws_subnet.private
  file_system_id  = aws_efs_file_system.chroma.id
  subnet_id       = each.value.id
  security_groups = [aws_security_group.efs.id]
}

resource "aws_cloudwatch_log_group" "frontend" {
  name              = "/ecs/${local.name}/frontend"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "backend" {
  name              = "/ecs/${local.name}/backend"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "ollama" {
  name              = "/ecs/${local.name}/ollama"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "lambda_ingest" {
  count             = var.enable_s3_lambda_ingestion ? 1 : 0
  name              = "/aws/lambda/${local.name}-s3-player-ingest"
  retention_in_days = 14
}

resource "aws_iam_role" "ecs_task_execution" {
  name = "${local.name}-ecs-task-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "ecs_task_execution_secrets" {
  name = "${local.name}-ecs-secrets"
  role = aws_iam_role.ecs_task_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "secretsmanager:GetSecretValue"
      ]
      Resource = [
        aws_secretsmanager_secret.database_url.arn
      ]
    }]
  })
}

resource "aws_iam_role" "ecs_task" {
  name = "${local.name}-ecs-task"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_secretsmanager_secret" "database_url" {
  name = "${local.name}/database-url"
}

resource "aws_secretsmanager_secret_version" "database_url" {
  secret_id     = aws_secretsmanager_secret.database_url.id
  secret_string = "postgresql+psycopg://${var.db_username}:${var.db_password}@${aws_db_instance.postgres.address}:5432/${var.db_name}"
}

resource "aws_s3_bucket" "ingestion" {
  bucket_prefix = "${local.name}-player-ingestion-"
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "ingestion" {
  bucket                  = aws_s3_bucket.ingestion.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "ingestion" {
  bucket = aws_s3_bucket.ingestion.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_sns_topic" "s3_object_created" {
  count = var.enable_s3_sns_notifications ? 1 : 0
  name  = "${local.name}-s3-object-created"
}

resource "aws_sns_topic_policy" "s3_object_created" {
  count = var.enable_s3_sns_notifications ? 1 : 0
  arn   = aws_sns_topic.s3_object_created[0].arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "AllowEventBridgePublish"
      Effect = "Allow"
      Principal = {
        Service = "events.amazonaws.com"
      }
      Action   = "sns:Publish"
      Resource = aws_sns_topic.s3_object_created[0].arn
      Condition = {
        ArnLike = {
          "aws:SourceArn" = aws_cloudwatch_event_rule.s3_object_created[0].arn
        }
      }
    }]
  })
}

resource "aws_sns_topic_subscription" "s3_object_created_email" {
  count     = var.enable_s3_sns_notifications && var.s3_sns_notification_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.s3_object_created[0].arn
  protocol  = "email"
  endpoint  = var.s3_sns_notification_email
}

resource "aws_cloudwatch_event_rule" "s3_object_created" {
  count       = var.enable_s3_sns_notifications ? 1 : 0
  name        = "${local.name}-s3-object-created"
  description = "Publishes production S3 object-created events to SNS."

  event_pattern = jsonencode({
    source        = ["aws.s3"]
    "detail-type" = ["Object Created"]
    detail        = local.s3_object_created_event_detail
  })
}

resource "aws_cloudwatch_event_target" "s3_object_created_sns" {
  count     = var.enable_s3_sns_notifications ? 1 : 0
  rule      = aws_cloudwatch_event_rule.s3_object_created[0].name
  target_id = "sns"
  arn       = aws_sns_topic.s3_object_created[0].arn

  input_transformer {
    input_paths = {
      bucket     = "$.detail.bucket.name"
      event_time = "$.time"
      key        = "$.detail.object.key"
      reason     = "$.detail.reason"
      region     = "$.region"
      size       = "$.detail.object.size"
    }

    input_template = <<-EOT
      {
        "title": "Pep.AI S3 Upload Received",
        "message": "A new file was dropped into the production ingestion bucket.",
        "bucket": <bucket>,
        "key": <key>,
        "size_bytes": <size>,
        "region": <region>,
        "event_time": <event_time>,
        "reason": <reason>,
        "production_ingestion_prefix": "uploads/"
      }
    EOT
  }

  depends_on = [aws_sns_topic_policy.s3_object_created]
}

resource "aws_iam_role" "lambda_ingest" {
  count = var.enable_s3_lambda_ingestion ? 1 : 0
  name  = "${local.name}-s3-player-ingest"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_ingest_basic" {
  count      = var.enable_s3_lambda_ingestion ? 1 : 0
  role       = aws_iam_role.lambda_ingest[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_ingest_vpc" {
  count      = var.enable_s3_lambda_ingestion ? 1 : 0
  role       = aws_iam_role.lambda_ingest[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

resource "aws_iam_role_policy" "lambda_ingest_data_access" {
  count = var.enable_s3_lambda_ingestion ? 1 : 0
  name  = "${local.name}-s3-player-ingest-data-access"
  role  = aws_iam_role.lambda_ingest[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject"
        ]
        Resource = "${aws_s3_bucket.ingestion.arn}/${var.lambda_ingest_prefix}*"
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = aws_secretsmanager_secret.database_url.arn
      }
    ]
  })
}

resource "aws_lambda_function" "s3_player_ingest" {
  count            = var.enable_s3_lambda_ingestion ? 1 : 0
  function_name    = "${local.name}-s3-player-ingest"
  role             = aws_iam_role.lambda_ingest[0].arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  filename         = var.lambda_ingest_zip_path
  source_code_hash = filebase64sha256(var.lambda_ingest_zip_path)
  timeout          = 60

  environment {
    variables = {
      DATABASE_SECRET_ARN = aws_secretsmanager_secret.database_url.arn
    }
  }

  vpc_config {
    subnet_ids         = [for subnet in aws_subnet.private : subnet.id]
    security_group_ids = [aws_security_group.lambda_ingest.id]
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda_ingest,
    aws_iam_role_policy_attachment.lambda_ingest_basic,
    aws_iam_role_policy_attachment.lambda_ingest_vpc,
    aws_iam_role_policy.lambda_ingest_data_access,
    aws_security_group.rds
  ]
}

resource "aws_lambda_permission" "allow_s3_ingestion" {
  count         = var.enable_s3_lambda_ingestion ? 1 : 0
  statement_id  = "AllowExecutionFromS3"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.s3_player_ingest[0].function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.ingestion.arn
}

resource "aws_s3_bucket_notification" "ingestion" {
  count       = var.enable_s3_lambda_ingestion || var.enable_s3_sns_notifications ? 1 : 0
  bucket      = aws_s3_bucket.ingestion.id
  eventbridge = var.enable_s3_sns_notifications

  dynamic "lambda_function" {
    for_each = var.enable_s3_lambda_ingestion ? [1] : []

    content {
      lambda_function_arn = aws_lambda_function.s3_player_ingest[0].arn
      events              = ["s3:ObjectCreated:*"]
      filter_prefix       = var.lambda_ingest_prefix
    }
  }

  depends_on = [
    aws_lambda_permission.allow_s3_ingestion,
    aws_cloudwatch_event_rule.s3_object_created
  ]
}

resource "aws_lb" "main" {
  name               = "${local.name}-alb"
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = [for subnet in aws_subnet.public : subnet.id]
}

resource "aws_wafv2_ip_set" "allowed_clients" {
  name               = "${local.name}-allowed-clients"
  description        = "Client IPs allowed to access the Pep.AI ALB."
  scope              = "REGIONAL"
  ip_address_version = "IPV4"
  addresses          = var.allowed_ip_cidrs
}

resource "aws_wafv2_web_acl" "alb" {
  name        = "${local.name}-alb-waf"
  description = "Restricts Pep.AI ALB access to allowed clients and rate-limits requests."
  scope       = "REGIONAL"

  default_action {
    block {}
  }

  rule {
    name     = "rate-limit-allowed-clients"
    priority = 0

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = var.waf_rate_limit
        aggregate_key_type = "IP"

        scope_down_statement {
          and_statement {
            statement {
              ip_set_reference_statement {
                arn = aws_wafv2_ip_set.allowed_clients.arn
              }
            }

            statement {
              geo_match_statement {
                country_codes = ["US"]
              }
            }
          }
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.name}-rate-limit-allowed-clients"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "allow-approved-us-clients"
    priority = 1

    action {
      allow {}
    }

    statement {
      and_statement {
        statement {
          ip_set_reference_statement {
            arn = aws_wafv2_ip_set.allowed_clients.arn
          }
        }

        statement {
          geo_match_statement {
            country_codes = ["US"]
          }
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.name}-allow-approved-us-clients"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${local.name}-alb-waf"
    sampled_requests_enabled   = true
  }
}

resource "aws_wafv2_web_acl_association" "alb" {
  resource_arn = aws_lb.main.arn
  web_acl_arn  = aws_wafv2_web_acl.alb.arn
}

resource "aws_lb_target_group" "frontend" {
  name        = "${local.name}-frontend"
  port        = 3000
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = aws_vpc.main.id

  health_check {
    path                = "/"
    matcher             = "200-399"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }
}

resource "aws_lb_target_group" "backend" {
  name        = "${local.name}-backend"
  port        = 8000
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = aws_vpc.main.id

  health_check {
    path                = "/api/health"
    matcher             = "200-399"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend.arn
  }
}

resource "aws_lb_listener_rule" "api" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 10

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }

  condition {
    path_pattern {
      values = ["/api/*"]
    }
  }
}

resource "aws_ecs_cluster" "main" {
  name = "${local.name}-cluster"
}

resource "aws_ecs_task_definition" "frontend" {
  family                   = "${local.name}-frontend"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.frontend_cpu
  memory                   = var.frontend_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name      = "frontend"
    image     = local.frontend_image
    essential = true
    portMappings = [{
      containerPort = 3000
      hostPort      = 3000
      protocol      = "tcp"
    }]
    environment = [
      { name = "HOSTNAME", value = "0.0.0.0" },
      { name = "NEXT_PUBLIC_API_BASE_URL", value = "/api" }
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = aws_cloudwatch_log_group.frontend.name
        awslogs-region        = var.aws_region
        awslogs-stream-prefix = "ecs"
      }
    }
  }])
}

resource "aws_ecs_task_definition" "backend" {
  family                   = "${local.name}-backend"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.backend_cpu
  memory                   = var.backend_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  volume {
    name = "chroma"

    efs_volume_configuration {
      file_system_id     = aws_efs_file_system.chroma.id
      transit_encryption = "ENABLED"
    }
  }

  container_definitions = jsonencode([
    {
      name      = "ollama"
      image     = var.ollama_image
      essential = true
      entryPoint = [
        "sh",
        "-c"
      ]
      command = [
        "ollama serve & until ollama list >/dev/null 2>&1; do sleep 2; done; ollama pull $OLLAMA_MODEL; wait"
      ]
      portMappings = [{
        containerPort = 11434
        hostPort      = 11434
        protocol      = "tcp"
      }]
      environment = [
        { name = "OLLAMA_HOST", value = "0.0.0.0:11434" },
        { name = "OLLAMA_MODEL", value = var.ollama_model }
      ]
      mountPoints = [{
        sourceVolume  = "chroma"
        containerPath = local.ollama_directory
        readOnly      = false
      }]
      healthCheck = {
        command     = ["CMD-SHELL", "ollama list >/dev/null 2>&1 || exit 1"]
        interval    = 30
        timeout     = 10
        retries     = 5
        startPeriod = 120
      }
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.ollama.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
    },
    {
      name      = "backend"
      image     = local.backend_image
      essential = true
      dependsOn = [{
        containerName = "ollama"
        condition     = "HEALTHY"
      }]
      portMappings = [{
        containerPort = 8000
        hostPort      = 8000
        protocol      = "tcp"
      }]
      environment = [
        { name = "CHROMA_PERSIST_DIR", value = local.chroma_directory },
        { name = "OLLAMA_BASE_URL", value = var.ollama_base_url },
        { name = "OLLAMA_MODEL", value = var.ollama_model },
        { name = "OLLAMA_EMBEDDING_MODEL", value = var.ollama_embedding_model }
      ]
      secrets = [
        { name = "DATABASE_URL", valueFrom = aws_secretsmanager_secret.database_url.arn }
      ]
      mountPoints = [{
        sourceVolume  = "chroma"
        containerPath = local.chroma_directory
        readOnly      = false
      }]
      healthCheck = {
        command     = ["CMD-SHELL", "curl -fsS http://localhost:8000/api/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 30
      }
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.backend.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])

  depends_on = [
    aws_efs_mount_target.chroma
  ]
}

resource "aws_ecs_service" "frontend" {
  name            = "${local.name}-frontend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.frontend.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = [for subnet in aws_subnet.public : subnet.id]
    security_groups  = [aws_security_group.frontend.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.frontend.arn
    container_name   = "frontend"
    container_port   = 3000
  }

  depends_on = [aws_lb_listener.http]
}

resource "aws_ecs_service" "backend" {
  name            = "${local.name}-backend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = [for subnet in aws_subnet.public : subnet.id]
    security_groups  = [aws_security_group.backend.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = "backend"
    container_port   = 8000
  }

  depends_on = [
    aws_lb_listener_rule.api,
    aws_db_instance.postgres,
    aws_secretsmanager_secret_version.database_url,
    aws_efs_mount_target.chroma
  ]
}
