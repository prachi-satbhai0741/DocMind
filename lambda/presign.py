import json
import boto3
import uuid
import os
import logging

logger      = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client   = boto3.client("s3")
BUCKET_NAME = os.environ["UPLOAD_BUCKET"]
EXPIRY      = 300  # seconds — presigned URL valid for 5 minutes


def handler(event, context):
    """
    GET /presign?file_name=invoice.pdf&content_type=application/pdf
    Returns a presigned S3 PUT URL so the browser can upload directly to S3.
    """
    try:
        params       = event.get("queryStringParameters") or {}
        file_name    = params.get("file_name", "upload")
        content_type = params.get("content_type", "application/octet-stream")

        # Unique key so files never overwrite each other
        doc_id   = str(uuid.uuid4())
        s3_key   = f"uploads/{doc_id}/{file_name}"

        upload_url = s3_client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket":      BUCKET_NAME,
                "Key":         s3_key,
                "ContentType": content_type,
            },
            ExpiresIn=EXPIRY,
        )

        logger.info(f"Presigned URL generated for doc_id={doc_id}")

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type":                "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({
                "upload_url": upload_url,
                "doc_id":     doc_id,
                "s3_key":     s3_key,
            }),
        }

    except Exception as e:
        logger.exception("Failed to generate presigned URL")
        return {
            "statusCode": 500,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"error": str(e)}),
        }
