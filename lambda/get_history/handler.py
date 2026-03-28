# lambda/get_history/handler.py
import json
import logging
import os
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(logging.INFO)

_dynamo_resource = None
_table = None


def _get_table():
    global _dynamo_resource, _table
    if _table is None:
        _dynamo_resource = boto3.resource("dynamodb")
        _table = _dynamo_resource.Table(os.environ["TABLE_NAME"])
    return _table


def _json_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Not serializable: {type(obj)}")


def _log(event_name: str, request_id: str, user_id: str, **extra):
    logger.info(json.dumps({
        "event": event_name,
        "request_id": request_id,
        "user_id": user_id,
        "env": os.environ.get("ENVIRONMENT", "unknown"),
        **extra,
    }))


def _resp(status: int, body: dict) -> dict:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, default=_json_default),
    }


def lambda_handler(event, context):
    request_id = context.aws_request_id if context else "local"
    user_id = event["requestContext"]["authorizer"]["jwt"]["claims"]["sub"]

    params = event.get("queryStringParameters") or {}
    limit = min(int(params.get("limit", 20)), 100)

    _log("get_history.start", request_id, user_id, limit=limit)

    try:
        response = _get_table().query(
            KeyConditionExpression=Key("PK").eq(f"userId#{user_id}"),
            ScanIndexForward=False,
            Limit=limit,
        )
    except Exception as exc:
        _log("get_history.error", request_id, user_id, error=str(exc))
        return _resp(500, {"error": "Internal server error"})

    items = []
    for record in response.get("Items", []):
        items.append({
            "calculation_id": record.get("calculation_id", ""),
            "label": record.get("label", ""),
            "created_at": record.get("created_at", ""),
            "scenarios": record.get("scenarios", {}),
            "inputs": record.get("inputs", {}),
        })

    _log("get_history.complete", request_id, user_id, count=len(items))
    return _resp(200, {"items": items, "count": len(items)})
