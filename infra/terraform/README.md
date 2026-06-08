# Pep.AI ECS/Fargate Deployment

This Terraform stack deploys Pep.AI to AWS with:

- Amazon ECS on Fargate for the frontend and backend containers
- Amazon ECR repositories for Docker images
- Application Load Balancer with path-based routing
- Amazon RDS PostgreSQL for persistent scouting memory
- Amazon EFS for persistent ChromaDB vector storage
- Ollama as a backend ECS sidecar for local LLM reasoning
- AWS Secrets Manager for the backend `DATABASE_URL`
- CloudWatch Logs for frontend and backend task logs
- Optional S3-triggered Lambda ingestion for player JSON/CSV uploads

## Architecture

```text
Browser
  -> Application Load Balancer
      /api/* -> FastAPI backend ECS service
      /*     -> Next.js frontend ECS service

Backend ECS service
  -> RDS PostgreSQL
  -> EFS-mounted /app/chromadb
  -> Ollama sidecar at http://127.0.0.1:11434

Optional ingestion path
  -> S3 upload under uploads/
  -> Lambda
  -> RDS PostgreSQL players table
```

## Cost Notes

This is more production-like than the EC2 Docker Compose deployment, but it costs more.
The stack intentionally avoids NAT Gateways by running Fargate tasks in public subnets with locked-down security groups. The only public inbound traffic is HTTP to the ALB.

Ollama runs inside the backend ECS task as a sidecar container. That makes the project demo stronger because the deployed app uses local model reasoning instead of only deterministic fallback, but it increases Fargate cost. The default backend task size is `2 vCPU / 8 GB` so `llama3.2:3b` has enough memory to run reliably on CPU.

The first backend deployment after enabling Ollama can take several minutes because the sidecar pulls the model. Model files are stored on EFS at `/root/.ollama`, so future task restarts do not need to download everything again unless the EFS volume is deleted.

## AWS WAF Access Control

The ALB is protected by AWS WAF:

- default action is `block`
- only CIDRs in `allowed_ip_cidrs` are allowed
- allowed clients must also geolocate to the United States
- allowed clients are rate-limited after `waf_rate_limit` requests per 5-minute window per IP

Find your current public IP:

```powershell
curl.exe https://checkip.amazonaws.com
```

Set it in `terraform.tfvars`:

```hcl
allowed_ip_cidrs = ["YOUR_PUBLIC_IP/32"]
waf_rate_limit   = 100
```

Then apply:

```powershell
terraform apply
```

If the browser cannot reach the app later, your public IP may have changed. Update `allowed_ip_cidrs` and re-apply Terraform.

## First-Time Deploy

From the repo root:

```powershell
cd infra/terraform
terraform init
```

Create only the ECR repositories first:

```powershell
Copy-Item terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars and set db_password.

terraform apply `
  -target=aws_ecr_repository.frontend `
  -target=aws_ecr_repository.backend
```

Push the images:

```powershell
cd ..\..
.\deploy\ecs\push-images.ps1 -Region us-east-1
```

Deploy the full stack:

```powershell
cd infra/terraform
terraform apply
```

The backend task runs two containers:

- `backend`: FastAPI, LangGraph, ChromaDB retrieval, SQLAlchemy persistence
- `ollama`: local model server used by the backend at `http://127.0.0.1:11434`

Get the app URL:

```powershell
terraform output alb_dns_name
```

Open:

```text
http://ALB_DNS_NAME
```

## Optional S3/Lambda Player Ingestion

Build the Lambda artifact from the repo root:

```powershell
cd backend\lambda_ingest
python -m pip install -r requirements.txt -t package
Copy-Item handler.py package\
Compress-Archive -Path package\* -DestinationPath lambda_ingest.zip -Force
```

Then enable the Lambda in `terraform.tfvars`:

```hcl
enable_s3_lambda_ingestion = true
lambda_ingest_zip_path     = "../../backend/lambda_ingest/lambda_ingest.zip"
lambda_ingest_prefix       = "uploads/"
```

Apply Terraform and upload `.json` or `.csv` files to the output bucket under the trigger prefix:

```powershell
terraform apply
terraform output s3_ingestion_bucket_name
aws s3 cp players.json s3://BUCKET_NAME/uploads/players.json
```

The file should contain either a JSON list, a JSON object with a `players` list, or a CSV with columns such as:

```text
id,name,position,club,nationality,age,estimatedValue
```

## Update Images

After code changes:

```powershell
.\deploy\ecs\push-images.ps1 -Region us-east-1
cd infra/terraform
terraform apply
```

You can also force ECS to recycle tasks:

```powershell
aws ecs update-service `
  --cluster pep-ai-cluster `
  --service pep-ai-frontend `
  --force-new-deployment

aws ecs update-service `
  --cluster pep-ai-cluster `
  --service pep-ai-backend `
  --force-new-deployment
```

## Destroy

To avoid ongoing costs:

```powershell
terraform destroy
```

This deletes the ALB, ECS services, RDS instance, EFS file system, and ECR repositories.
