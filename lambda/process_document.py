import json
import boto3
import uuid
import logging
from datetime import datetime, timezone

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client       = boto3.client("s3")
textract_client = boto3.client("textract")
dynamodb        = boto3.resource("dynamodb")

TABLE_NAME = "docmind-documents"


def extract_text(blocks):
    """Pull raw lines from Textract LINE blocks."""
    return "\n".join(
        b["Text"] for b in blocks if b["BlockType"] == "LINE"
    )


def extract_key_values(blocks):
    """Build a dict of KEY → VALUE pairs from Textract form blocks."""
    block_map = {b["Id"]: b for b in blocks}
    key_values = {}

    for block in blocks:
        if block["BlockType"] != "KEY_VALUE_SET":
            continue
        if "KEY" not in block.get("EntityTypes", []):
            continue

        # Collect key text
        key_text = ""
        for rel in block.get("Relationships", []):
            if rel["Type"] == "CHILD":
                key_text = " ".join(
                    block_map[i].get("Text", "")
                    for i in rel["Ids"]
                    if block_map[i]["BlockType"] == "WORD"
                )

        # Collect value text
        value_text = ""
        for rel in block.get("Relationships", []):
            if rel["Type"] == "VALUE":
                for val_id in rel["Ids"]:
                    val_block = block_map.get(val_id, {})
                    for vrel in val_block.get("Relationships", []):
                        if vrel["Type"] == "CHILD":
                            value_text = " ".join(
                                block_map[i].get("Text", "")
                                for i in vrel["Ids"]
                                if block_map[i]["BlockType"] == "WORD"
                            )

        if key_text:
            key_values[key_text.strip()] = value_text.strip()

    return key_values


def extract_tables(blocks):
    """Extract tables as list of rows (list of lists)."""
    block_map = {b["Id"]: b for b in blocks}
    tables = []
    cells  = {}

    # Map TABLE → CELLs
    for block in blocks:
        if block["BlockType"] != "TABLE":
            continue
        table_cells = {}
        for rel in block.get("Relationships", []):
            if rel["Type"] == "CHILD":
                for cell_id in rel["Ids"]:
                    cell = block_map.get(cell_id)
                    if cell and cell["BlockType"] == "CELL":
                        row = cell["RowIndex"]
                        col = cell["ColumnIndex"]
                        text = " ".join(
                            block_map[i].get("Text", "")
                            for r in cell.get("Relationships", [])
                            if r["Type"] == "CHILD"
                            for i in r["Ids"]
                            if block_map[i]["BlockType"] == "WORD"
                        )
                        table_cells.setdefault(row, {})[col] = text
        if table_cells:
            max_row = max(table_cells)
            max_col = max(c for r in table_cells.values() for c in r)
            rows = [
                [table_cells.get(r, {}).get(c, "") for c in range(1, max_col + 1)]
                for r in range(1, max_row + 1)
            ]
            tables.append(rows)

    return tables


def handler(event, context):
    """
    Triggered by S3 PutObject event.
    Calls Textract, parses results, writes to DynamoDB.
    """
    try:
        record     = event["Records"][0]
        bucket     = record["s3"]["bucket"]["name"]
        key        = record["s3"]["object"]["key"]
        doc_id     = str(uuid.uuid4())
        file_name  = key.split("/")[-1]
        uploaded_at = datetime.now(timezone.utc).isoformat()

        logger.info(f"Processing: s3://{bucket}/{key}")

        # Call Textract
        response = textract_client.analyze_document(
            Document={"S3Object": {"Bucket": bucket, "Name": key}},
            FeatureTypes=["TABLES", "FORMS"],
        )

        blocks     = response.get("Blocks", [])
        raw_text   = extract_text(blocks)
        key_values = extract_key_values(blocks)
        tables     = extract_tables(blocks)

        # Write to DynamoDB
        table = dynamodb.Table(TABLE_NAME)
        table.put_item(
            Item={
                "doc_id":      doc_id,
                "file_name":   file_name,
                "s3_key":      key,
                "uploaded_at": uploaded_at,
                "raw_text":    raw_text,
                "key_values":  key_values,
                "tables":      json.dumps(tables),   # stored as JSON string
                "status":      "completed",
            }
        )

        logger.info(f"Saved doc_id={doc_id} to DynamoDB")
        return {"statusCode": 200, "body": json.dumps({"doc_id": doc_id})}

    except Exception as e:
        logger.exception("Failed to process document")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
