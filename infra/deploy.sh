#!/bin/bash
# 
# DocMind — One-command deployment script
# Run from the project root: bash infra/deploy.sh
# 

set -e  # exit immediately on any error

#  Config 
STACK_NAME="docmind-stack"
REGION="${AWS_REGION:-ap-south-1}"
SAM_BUCKET="docmind-sam-artifacts-$(aws sts get-caller-identity --query Account --output text)"

echo ""
echo ""
echo "        DocMind — Deploying to AWS        "
echo ""
echo ""
echo "  Stack  : $STACK_NAME"
echo "  Region : $REGION"
echo ""

#  Step 1: Create SAM artifact bucket if it doesn't exist 
echo " [1/4] Checking SAM artifact bucket..."
if ! aws s3 ls "s3://$SAM_BUCKET" 2>/dev/null; then
  echo "  Creating bucket: $SAM_BUCKET"
  aws s3 mb "s3://$SAM_BUCKET" --region "$REGION"
fi
echo "   Artifact bucket ready"

#  Step 2: Build Lambda packages 
echo ""
echo " [2/4] Building Lambda functions..."
sam build \
  --template-file infra/template.yaml \
  --build-dir .aws-sam/build
echo "   Build complete"

#  Step 3: Package & deploy via SAM 
echo ""
echo " [3/4] Deploying stack to AWS..."
sam deploy \
  --template-file .aws-sam/build/template.yaml \
  --stack-name "$STACK_NAME" \
  --s3-bucket "$SAM_BUCKET" \
  --region "$REGION" \
  --capabilities CAPABILITY_IAM \
  --no-fail-on-empty-changeset \
  --parameter-overrides \
      ProjectName=docmind \
      Environment=prod
echo "   Stack deployed"

#  Step 4: Print outputs 
echo ""
echo " [4/4] Fetching deployment outputs..."
echo ""

API_URL=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='ApiBaseUrl'].OutputValue" \
  --output text)

FRONTEND_URL=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='FrontendUrl'].OutputValue" \
  --output text)

UPLOAD_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='UploadsBucketName'].OutputValue" \
  --output text)

echo ""
echo "                  Deployment Complete                   "
echo ""
echo ""
echo "  API URL      : $API_URL"
echo "  Frontend URL : $FRONTEND_URL"
echo "  Upload Bucket: $UPLOAD_BUCKET"
echo ""
echo ""
echo "  Next step — deploy the frontend:"
echo ""
echo "  aws s3 sync frontend/ s3://$UPLOAD_BUCKET-frontend \\"
echo "    --acl public-read"
echo ""
echo "  Then paste the API URL into frontend/app.js"
echo ""
echo ""
