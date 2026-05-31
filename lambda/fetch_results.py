import json
import boto3
import logging
from boto3.dynamodb.conditions import Key
from decimal import Decimal

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb   = boto3.resource("dynamodb")
TABLE_NAME = "docmind-documents"


def decimal_to_native(obj):
    """DynamoDB returns Decimals — convert to int/float for JSON."""
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    raise TypeError


def build_response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type":                "application/json",
            "Access-Control-Allow-Origin": "*",   # allow frontend on S3
        },
        "body": json.dumps(body, default=decimal_to_native),
    }


def get_document(doc_id):
    """Fetch a single document by doc_id."""
    table  = dynamodb.Table(TABLE_NAME)
    result = table.get_item(Key={"doc_id": doc_id})
    item   = result.get("Item")

    if not item:
        return build_response(404, {"error": f"Document '{doc_id}' not found"})

    # Parse tables JSON string back to list
    if "tables" in item and isinstance(item["tables"], str):
        item["tables"] = json.loads(item["tables"])

    return build_response(200, item)


def list_documents():
    """Scan DynamoDB and return all documents (metadata only — no raw text)."""
    table  = dynamodb.Table(TABLE_NAME)
    result = table.scan(
        ProjectionExpression="doc_id, file_name, uploaded_at, #st",
        ExpressionAttributeNames={"#st": "status"},  # 'status' is a reserved word
    )
    items = result.get("Items", [])

    # Sort newest first
    items.sort(key=lambda x: x.get("uploaded_at", ""), reverse=True)
    return build_response(200, {"documents": items, "count": len(items)})


def handler(event, context):
    """
    GET /documents        → list all documents
    GET /documents/{id}   → get one document with full extracted content
    """
    try:
        http_method = event.get("httpMethod", "GET")
        path_params = event.get("pathParameters") or {}
        doc_id      = path_params.get("doc_id")

        if http_method != "GET":
            return build_response(405, {"error": "Method not allowed"})

        if doc_id:
            logger.info(f"Fetching doc_id={doc_id}")
            return get_document(doc_id)
        else:
            logger.info("Listing all documents")
            return list_documents()

    except Exception as e:
        logger.exception("Unexpected error in fetch_results")
        return build_response(500, {"error": str(e)})
