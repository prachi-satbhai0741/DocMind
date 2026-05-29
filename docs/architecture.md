# Architecture

## Full Pipeline Diagram

```
┌──────────────┐
│   Browser    │  User uploads PDF/image via frontend
└──────┬───────┘
       │ HTTP PUT (presigned URL)
       ▼
┌──────────────┐
│  S3 Bucket   │  docmind-uploads — stores raw files
└──────┬───────┘
       │ S3 Event Trigger (ObjectCreated)
       ▼
┌──────────────┐
│    Lambda    │  process_document.py
│  (Processor) │  - Reads file from S3
│              │  - Calls Amazon Textract
└──────┬───────┘
       │ Textract API call
       ▼
┌──────────────┐
│   Textract   │  Extracts:
│              │  - Raw text blocks
│              │  - Tables (rows + cells)
│              │  - Key-value pairs (forms)
└──────┬───────┘
       │ JSON response
       ▼
┌──────────────┐
│   DynamoDB   │  docmind-documents table
│              │  Stores: file_id, filename, extracted_text,
│              │  tables, kv_pairs, timestamp, status
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌──────────────┐
│ API Gateway  │────▶│    Lambda    │  fetch_results.py
│  (REST API)  │     │  (Fetcher)   │  - Reads from DynamoDB
└──────────────┘     └──────┬───────┘  - Returns JSON to frontend
                            │
                            ▼
                   ┌──────────────┐
                   │  S3 Frontend │  results.html renders
                   │  (Static)    │  extracted text + tables
                   └──────────────┘
```

---

## Step-by-Step Flow

1. **User opens** `index.html` hosted on S3
2. **Frontend requests** a presigned S3 URL from API Gateway
3. **Lambda generates** a presigned URL and returns it
4. **Browser uploads** the file directly to S3 using the presigned URL (no file goes through Lambda)
5. **S3 triggers** `process_document.py` Lambda via ObjectCreated event
6. **Lambda calls** Textract — synchronous for single-page, async job for multi-page PDFs
7. **Textract returns** structured blocks: LINE, WORD, TABLE, CELL, KEY_VALUE_SET
8. **Lambda parses** and writes clean results to DynamoDB with a `file_id` (UUID)
9. **User opens** `results.html` — fetches data via API Gateway → `fetch_results.py` → DynamoDB
10. **Results rendered** as structured text, table grid, and key-value list

---

## Design Decisions

### Why S3 presigned URLs for upload?
Direct browser-to-S3 upload avoids sending large files through Lambda (which has a 6MB payload limit for synchronous invocations). Presigned URLs expire in 5 minutes for security.

### Why DynamoDB over RDS?
No joins needed — each document is a self-contained JSON record. DynamoDB's free tier (25 GB + 200M requests/month, **permanent**) means this project stays free long after the AWS Free Tier period ends.

### Why synchronous Textract for now?
Synchronous Textract (`detect_document_text` / `analyze_document`) works for single-page files and returns results instantly. Multi-page async jobs (`start_document_analysis`) are planned for v1.1.

### Why no containers?
Lambda cold starts for this workload are under 500ms. No container orchestration, no Dockerfile, no ECR costs. Pure serverless keeps the project beginner-friendly and cost at zero.
