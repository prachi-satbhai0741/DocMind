# DocMind — Serverless Document Intelligence on AWS

> Upload a PDF or image. Get structured text, tables, and form fields back — instantly. No servers.

![AWS](https://img.shields.io/badge/AWS-Serverless-FF9900?style=for-the-badge&logo=amazon-aws&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge)

---

## What is DocMind?

**DocMind** is a fully serverless document intelligence pipeline on AWS. Upload a PDF or image → **Amazon Textract** extracts text, tables, and key-value pairs → **Lambda** processes it → **DynamoDB** stores it → results appear in a static frontend hosted on **S3**.

No EC2. No containers. No ops overhead.

---

## Quick Start

```bash
git clone https://github.com/prachi-satbhai0741/DocMind.git
cd DocMind/infra && ./deploy.sh
aws s3 sync ../frontend/ s3://YOUR-FRONTEND-BUCKET --acl public-read
```

→ Full setup guide: [docs/getting-started.md](docs/getting-started.md)

---

## Pipeline Overview

```
Upload (S3) → Lambda → Textract → DynamoDB → API Gateway → Frontend
```

→ Detailed architecture + design decisions: [docs/architecture.md](docs/architecture.md)

---

## AWS Services Used

S3 · Lambda · Textract · DynamoDB · API Gateway · IAM · CloudWatch

→ Service breakdown + cost estimate: [docs/aws-services.md](docs/aws-services.md)

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
│   ├── results.html            # Extracted results viewer (text / KV / tables)
│   ├── app.js                  # Upload flow + API Gateway calls
│   └── style.css               # Dark theme UI
│
├── infra/
│   ├── template.yaml           # AWS SAM template — all infra as code
│   └── deploy.sh               # One-command deployment script
│
├── docs/                       # Documentation
├── .env.example
└── README.md
```

---

## Docs

| Document | Description |
|---|---|
| [Getting Started](docs/getting-started.md) | Prerequisites, setup, deploy, cleanup |
| [Architecture](docs/architecture.md) | System diagram, flow, design decisions |
| [AWS Services & Cost](docs/aws-services.md) | Services used, IAM permissions, pricing |
---

## License

MIT — see [LICENSE](LICENSE)

---

> *Built with 100% serverless AWS.*
