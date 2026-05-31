# Getting Started with DocMiner

## Prerequisites

Before you begin, make sure you have:

- An **AWS Account** (Free Tier is enough)
- **AWS CLI** installed and configured (`aws configure`)
- **Python 3.11+** installed
- **AWS SAM CLI** installed — [install guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)

---

## 1. Clone the Repository

```bash
git clone https://github.com/prachi-satbhai0741/DocMind.git
cd DocMind
```

---

## 2. Configure Environment Variables

```bash
cp .env.example .env
```

Open `.env` and fill in:

```env
AWS_REGION=ap-south-1
UPLOAD_BUCKET_NAME=docminer-uploads-yourname
FRONTEND_BUCKET_NAME=docminer-frontend-yourname
DYNAMODB_TABLE_NAME=docminer-documents
```

> ⚠️ S3 bucket names are globally unique — add your name or a random suffix.

---

## 3. Deploy Infrastructure

```bash
cd infra
chmod +x deploy.sh
./deploy.sh
```

This single script will:

- Create the S3 uploads bucket with event notifications enabled
- Create the S3 frontend bucket configured for static website hosting
- Deploy both Lambda functions (`process_document`, `fetch_results`)
- Set up the API Gateway REST endpoint
- Create the DynamoDB `docminer-documents` table
- Attach all required IAM roles and policies

---

## 4. Deploy the Frontend

Once infrastructure is up, sync the frontend files to S3:

```bash
aws s3 sync frontend/ s3://YOUR-FRONTEND-BUCKET-NAME --acl public-read
```

Your frontend URL will be:
```
http://YOUR-FRONTEND-BUCKET-NAME.s3-website.REGION.amazonaws.com
```

---

## 5. Test DocMiner

1. Open the frontend URL in your browser
2. Upload any PDF or image (try the samples in `sample-docs/`)
3. Wait 3–5 seconds
4. View the extracted text, tables, and key-value pairs

---

## Project Structure

```
DocMind/
├── lambda/
│   ├── process_document.py     # S3 trigger → calls Textract → writes DynamoDB
│   ├── fetch_results.py        # API Gateway → reads DynamoDB → returns JSON
│   ├── presign.py              # Generates presigned S3 URL for browser uploads
│   └── requirements.txt
│
├── frontend/
│   ├── index.html              # Upload UI with drag & drop
│   ├── results.html            # Extracted results viewer
│   ├── app.js                  # Upload flow + API Gateway calls
│   └── style.css               # Dark theme UI
│
├── infra/
│   ├── template.yaml           # AWS SAM template — all infra as code
│   └── deploy.sh               # One-command deployment script
│
├── docs/                       # Extended documentation
├── .env.example
└── README.md
```

---

## Cleanup (Avoid Surprise Bills)

To delete all AWS resources when you're done:

```bash
aws cloudformation delete-stack --stack-name docminer-stack
aws s3 rb s3://YOUR-UPLOAD-BUCKET --force
aws s3 rb s3://YOUR-FRONTEND-BUCKET --force
```
