param(
  [string]$Region = "us-east-1",
  [string]$Tag = "latest",
  [string]$TerraformDir = "infra/terraform"
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
  throw "AWS CLI is required."
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  throw "Docker is required."
}

$TerraformCommand = Get-Command terraform -ErrorAction SilentlyContinue
if ($TerraformCommand) {
  $TerraformExe = $TerraformCommand.Source
} else {
  $TerraformExe = Get-ChildItem -Path "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" -Recurse -Filter terraform.exe -ErrorAction SilentlyContinue |
    Select-Object -First 1 -ExpandProperty FullName
}

if (-not $TerraformExe) {
  throw "Terraform is required. Install it with: winget install Hashicorp.Terraform"
}

Push-Location $TerraformDir
$frontendRepo = & $TerraformExe output -raw frontend_ecr_repository_url
$backendRepo = & $TerraformExe output -raw backend_ecr_repository_url
Pop-Location

$accountId = aws sts get-caller-identity --query Account --output text
$registry = "$accountId.dkr.ecr.$Region.amazonaws.com"

function Invoke-Native {
  param(
    [Parameter(Mandatory = $true)]
    [string]$FilePath,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
  )

  & $FilePath @Arguments
  if ($LASTEXITCODE -ne 0) {
    throw "$FilePath failed with exit code $LASTEXITCODE"
  }
}

$password = aws ecr get-login-password --region $Region
if ($LASTEXITCODE -ne 0) {
  throw "aws ecr get-login-password failed with exit code $LASTEXITCODE"
}

$password | docker login --username AWS --password-stdin $registry
if ($LASTEXITCODE -ne 0) {
  throw "docker login failed with exit code $LASTEXITCODE"
}

Invoke-Native docker build `
  --build-arg NEXT_PUBLIC_API_BASE_URL=/api `
  -t "${frontendRepo}:${Tag}" `
  ./frontend

Invoke-Native docker build `
  -t "${backendRepo}:${Tag}" `
  ./backend

Invoke-Native docker push "${frontendRepo}:${Tag}"
Invoke-Native docker push "${backendRepo}:${Tag}"

Write-Host "Pushed:"
Write-Host "  ${frontendRepo}:${Tag}"
Write-Host "  ${backendRepo}:${Tag}"
