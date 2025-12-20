# Deploy Ticket Service to Render
Terraform deployment using Render + Docker + SQLite.

## What You Get

## Quick Start

### 1. Get Render Credentials

1. Sign up at https://render.com (free)
2. Get API key: https://dashboard.render.com/account → "API Keys"
3. Get Owner ID from URL: `https://dashboard.render.com/tea-xxxxx` (the `tea-xxxxx` part)

### 2. Configure

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

### 3. Deploy

```bash
terraform init
terraform plan
terraform apply

### 4. Done
```bash
terraform output service_url