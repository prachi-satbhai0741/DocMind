# AWS Services & Cost

## Services Used

### Amazon S3
- **Upload bucket** — stores raw PDF/image files uploaded by users
- **Frontend bucket** — hosts static HTML/JS frontend (public read)
- **Why S3:** Zero-ops storage, event triggers, presigned URL support, and permanent free tier (5 GB)

### AWS Lambda
- **`process_document.py`** — triggered by S3 ObjectCreated → calls Textract → writes to DynamoDB
- **`fetch_results.py`** — triggered by API Gateway GET → reads from DynamoDB → returns JSON
- **Runtime:** Python 3.11
- **Why Lambda:** No servers to manage, scales to zero, 1M free requests/month **forever**

### Amazon Textract
- Extracts text blocks, tables (rows + cells), and form key-value pairs from PDFs and images
- Supports JPG, PNG, TIFF, PDF
- **Why Textract:** Purpose-built for documents — far more accurate than raw OCR for structured data like invoices and forms

### Amazon DynamoDB
- Table: `docmind-documents`
- Partition key: `file_id` (UUID)
- Stores: filename, raw text, tables JSON, key-value pairs JSON, timestamp, processing status
- **Why DynamoDB:** Schemaless (each document can have different fields), permanent free tier (25 GB)

### Amazon API Gateway
- REST API with two routes:
  - `POST /upload` — returns presigned S3 URL
  - `GET /results/{file_id}` — returns extracted data for a document
- **Why API Gateway:** Connects frontend to Lambda without managing any server

### AWS IAM
- Least-privilege Lambda execution role with only required permissions (see below)
- No wildcard `*` actions

### Amazon CloudWatch
- Automatic Lambda logs → `/aws/lambda/docmind-*`
- Useful for debugging Textract responses and DynamoDB writes

---

## IAM Permissions (Lambda Role)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject"],
      "Resource": "arn:aws:s3:::docmind-uploads/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "textract:DetectDocumentText",
        "textract:AnalyzeDocument"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:UpdateItem"
      ],
      "Resource": "arn:aws:dynamodb:ap-south-1:*:table/docmind-documents"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## Cost Estimate

| Service | Free Tier | Free Tier Duration | After Free Tier |
|---|---|---|---|
| **Textract** | 1,000 pages/month | First 3 months only | ~$1.50 / 1,000 pages |
| **Lambda** | 1M requests + 400,000 GB-s/month | **Forever** | Practically $0 |
| **DynamoDB** | 25 GB + 200M requests/month | **Forever** | Practically $0 |
| **S3** | 5 GB storage + 20K GET + 2K PUT | First 12 months | ~$0.023 / GB |
| **API Gateway** | 1M API calls/month | First 12 months | ~$3.50 / 1M calls |
| **CloudWatch** | 10 custom metrics, 5 GB logs | First 12 months | ~$0.50 / GB logs |

> **Bottom line:** For a GitHub portfolio project with low traffic, this costs ~$0/month even after the Free Tier expires. The only realistic charge is Textract if you process thousands of pages.
