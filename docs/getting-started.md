# Getting Started

## Prerequisites

- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) configured (`aws configure`)
- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)
- Python 3.11+
- An AWS account (Free Tier works fine)

---

## Setup Steps

### 1. Clone the repo

```bash
git clone https://github.com/prachi-satbhai0741/DocMind.git
cd docmind
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your AWS region and bucket names
```

### 3. Deploy the backend

```bash
cd infra
./deploy.sh
```

> This deploys Lambda, DynamoDB table, S3 upload bucket, and API Gateway via SAM/CloudFormation.

### 4. Deploy the frontend

```bash
aws s3 sync ../frontend/ s3://YOUR-FRONTEND-BUCKET --acl public-read
```

### 5. Test it

Upload a PDF or image to your S3 upload bucket and watch the pipeline run:

```bash
aws s3 cp sample-docs/sample-invoice.pdf s3://YOUR-UPLOAD-BUCKET/
```

Check DynamoDB for extracted results:

```bash
aws dynamodb scan --table-name docmind-documents --region ap-south-1
```

---

## Local Development

### Test Lambda locally with SAM

```bash
sam local invoke ProcessDocumentFunction --event events/s3-event.json
```

### Run a quick Textract test without deploying

```bash
cd lambda
python test_textract.py --file ../sample-docs/sample-invoice.pdf
```

---

## Cleanup (Avoid Surprise Bills)

To delete all AWS resources when you're done:

```bash
aws cloudformation delete-stack --stack-name docmind-stack
aws s3 rb s3://YOUR-UPLOAD-BUCKET --force
aws s3 rb s3://YOUR-FRONTEND-BUCKET --force
```
