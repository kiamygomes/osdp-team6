# Terraform Infrastructure for Ticket Bot

This directory contains Infrastructure as Code (IaC) for deploying the Ticket Bot application to Google Cloud Platform.

## Prerequisites

1. **Terraform** (>= 1.0)
   ```bash
   brew install terraform  # macOS
   # or download from https://www.terraform.io/downloads
   ```

2. **Google Cloud SDK**
   ```bash
   brew install google-cloud-sdk  # macOS
   # or download from https://cloud.google.com/sdk/docs/install
   ```

3. **GCP Project** with billing enabled

4. **GCP APIs enabled**:
   - Cloud Run API
   - Secret Manager API
   - Container Registry API

## Setup

### 1. Authenticate with GCP

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

### 2. Configure Variables

Copy the example variables file and fill in your values:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:
```hcl
project_id       = "your-gcp-project-id"
region           = "us-central1"
environment      = "production"
container_image  = "gcr.io/your-gcp-project-id/ticket-bot:latest"
jira_project_key = "OSDP"
ai_provider      = "claude"
```

### 3. Set Up Secrets

Before deploying, you need to populate the secrets in Google Secret Manager:

```bash
# Set Jira OAuth credentials
echo -n "YOUR_JIRA_CLIENT_ID" | gcloud secrets create jira-client-id --data-file=-
echo -n "YOUR_JIRA_CLIENT_SECRET" | gcloud secrets create jira-client-secret --data-file=-

# Set AI API keys
echo -n "YOUR_CLAUDE_API_KEY" | gcloud secrets create claude-api-key --data-file=-
echo -n "YOUR_OPENAI_API_KEY" | gcloud secrets create openai-api-key --data-file=-
```

Or update existing secrets:
```bash
echo -n "NEW_VALUE" | gcloud secrets versions add SECRET_NAME --data-file=-
```

## Deployment

### Initialize Terraform

```bash
terraform init
```

### Plan the Deployment

```bash
terraform plan
```

Review the planned changes to ensure they match your expectations.

### Apply the Infrastructure

```bash
terraform apply
```

Type `yes` when prompted to confirm.

### Get the Service URL

After deployment completes:

```bash
terraform output service_url
```

## Managing the Infrastructure

### Update the Application

After building and pushing a new container image:

```bash
terraform apply -var="container_image=gcr.io/PROJECT_ID/ticket-bot:v2"
```

### View Current State

```bash
terraform show
```

### Destroy All Resources

**Warning: This will delete all resources created by Terraform**

```bash
terraform destroy
```

## Security Best Practices

1. **Never commit `terraform.tfvars`** - It contains sensitive project IDs
2. **Use Secret Manager** for all credentials (already configured)
3. **Restrict public access** - Set `allow_public_access = false` in production
4. **Use service accounts** - The terraform creates a dedicated service account with minimal permissions
5. **Enable audit logging** - Monitor access to secrets and services

## Troubleshooting

### Secret Access Errors

If the Cloud Run service can't access secrets:

```bash
# Verify IAM bindings
gcloud secrets get-iam-policy jira-client-id

# Add service account access if needed
gcloud secrets add-iam-policy-binding jira-client-id \
  --member="serviceAccount:ticket-bot-sa@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Cloud Run Deployment Fails

Check the logs:

```bash
gcloud run services logs read ticket-bot-orchestrator --region=us-central1
```

### API Not Enabled

Enable required APIs:

```bash
gcloud services enable run.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

## Architecture

The Terraform configuration provisions:

- **Cloud Run Service**: Serverless container platform for the application
- **Service Account**: Dedicated identity with minimal permissions
- **Secret Manager**: Secure storage for API keys and credentials
- **IAM Bindings**: Least-privilege access to secrets
- **Auto-scaling**: 0-10 instances based on load

## Cost Optimization

- **Min instances = 0**: No cost when idle
- **Max instances = 10**: Cap maximum cost
- **CPU allocation**: Only charged when processing requests
- **Free tier**: First 2 million requests/month are free

## Next Steps

1. Build and push your container image (see `../Dockerfile`)
2. Set up monitoring and alerting
3. Configure custom domain (if needed)
4. Set up CI/CD pipeline to automate deployments
