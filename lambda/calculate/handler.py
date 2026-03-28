# lambda/calculate/handler.py
import json
import logging
import os
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal

import boto3

from models import Inputs
import scenarios as sc

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


def _decimalize(obj):
    """Recursively convert floats to Decimal for DynamoDB storage."""
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, dict):
        return {k: _decimalize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_decimalize(v) for v in obj]
    return obj


def lambda_handler(event, context):
    request_id = context.aws_request_id if context else "local"
    user_id = event["requestContext"]["authorizer"]["jwt"]["claims"]["sub"]

    _log("calculate.start", request_id, user_id)

    try:
        raw = json.loads(event.get("body") or "{}")
    except (json.JSONDecodeError, TypeError):
        return _resp(400, {"error": "Invalid JSON body"})

    save = bool(raw.get("save", False))
    label = str(raw.get("label", "")) if save else ""
    inputs_raw = raw.get("inputs", {})

    try:
        p = Inputs.from_dict(inputs_raw)
    except (TypeError, ValueError) as exc:
        return _resp(400, {"error": f"Invalid inputs: {exc}"})

    result = sc.run_all(p)

    response_body: dict = {"saved": save, "scenarios": result}

    if save:
        calc_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        ttl = int((now + timedelta(days=90)).timestamp())
        item = {
            "PK": f"userId#{user_id}",
            "SK": f"record#{now.isoformat()}",
            "calculation_id": calc_id,
            "label": label,
            "inputs": p.to_dict(),
            "scenarios": _decimalize(result),
            "created_at": now.isoformat(),
            "ttl": ttl,
        }
        _get_table().put_item(Item=item)
        response_body["calculation_id"] = calc_id
        _log("calculate.saved", request_id, user_id, calculation_id=calc_id)

    _log("calculate.complete", request_id, user_id, saved=save)
    return _resp(200, response_body)
