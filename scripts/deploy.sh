#!/bin/bash
# Deployment script for Ticket Bot Application
# This script builds, pushes, and deploys the application to Google Cloud Run

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="ticket-bot-orchestrator"
IMAGE_NAME="ticket-bot"

# Function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."

    if ! command -v gcloud &> /dev/null; then
        print_error "gcloud CLI not found. Please install Google Cloud SDK."
        exit 1
    fi

    if ! command -v docker &> /dev/null; then
        print_error "docker not found. Please install Docker."
        exit 1
    fi

    if [ -z "$PROJECT_ID" ]; then
        print_error "GCP_PROJECT_ID environment variable not set."
        echo "Usage: GCP_PROJECT_ID=your-project-id $0"
        exit 1
    fi

    print_info "All prerequisites met."
}

# Build the Docker image
build_image() {
    print_info "Building Docker image..."

    # Get git commit hash for tagging
    GIT_COMMIT=$(git rev-parse --short HEAD || echo "unknown")
    TIMESTAMP=$(date +%Y%m%d-%H%M%S)

    # Build with multiple tags
    docker build \
        -t "gcr.io/${PROJECT_ID}/${IMAGE_NAME}:latest" \
        -t "gcr.io/${PROJECT_ID}/${IMAGE_NAME}:${GIT_COMMIT}" \
        -t "gcr.io/${PROJECT_ID}/${IMAGE_NAME}:${TIMESTAMP}" \
        .

    print_info "Docker image built successfully."
}

# Push the image to Google Container Registry
push_image() {
    print_info "Pushing image to GCR..."

    # Configure Docker to use gcloud as credential helper
    gcloud auth configure-docker --quiet

    # Push all tags
    docker push "gcr.io/${PROJECT_ID}/${IMAGE_NAME}:latest"
    docker push "gcr.io/${PROJECT_ID}/${IMAGE_NAME}:${GIT_COMMIT}"
    docker push "gcr.io/${PROJECT_ID}/${IMAGE_NAME}:${TIMESTAMP}"

    print_info "Image pushed to gcr.io/${PROJECT_ID}/${IMAGE_NAME}"
}

# Deploy to Cloud Run using Terraform
deploy_with_terraform() {
    print_info "Deploying with Terraform..."

    cd terraform

    # Initialize if needed
    if [ ! -d ".terraform" ]; then
        terraform init
    fi

    # Apply with the new image
    terraform apply \
        -var="project_id=${PROJECT_ID}" \
        -var="container_image=gcr.io/${PROJECT_ID}/${IMAGE_NAME}:latest" \
        -auto-approve

    cd ..

    print_info "Deployment complete!"
}

# Deploy directly to Cloud Run (alternative to Terraform)
deploy_direct() {
    print_info "Deploying directly to Cloud Run..."

    gcloud run deploy "${SERVICE_NAME}" \
        --image "gcr.io/${PROJECT_ID}/${IMAGE_NAME}:latest" \
        --platform managed \
        --region "${REGION}" \
        --allow-unauthenticated \
        --set-env-vars "ENVIRONMENT=production" \
        --set-secrets "JIRA_CLIENT_ID=jira-client-id:latest,JIRA_CLIENT_SECRET=jira-client-secret:latest,CLAUDE_API_KEY=claude-api-key:latest,OPENAI_API_KEY=openai-api-key:latest" \
        --memory 1Gi \
        --cpu 2 \
        --min-instances 0 \
        --max-instances 10

    # Get the service URL
    SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
        --platform managed \
        --region "${REGION}" \
        --format 'value(status.url)')

    print_info "Service deployed at: ${SERVICE_URL}"
}

# Main deployment flow
main() {
    print_info "Starting deployment for project: ${PROJECT_ID}"

    check_prerequisites
    build_image
    push_image

    # Choose deployment method
    if [ -f "terraform/main.tf" ] && [ "${USE_TERRAFORM:-true}" = "true" ]; then
        deploy_with_terraform
    else
        deploy_direct
    fi

    print_info "✅ Deployment completed successfully!"
}

# Run main function
main "$@"
