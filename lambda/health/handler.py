# lambda/health/handler.py
import json
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    request_id = context.aws_request_id if context else "local"
    env = os.environ.get("ENVIRONMENT", "unknown")
    logger.info(json.dumps({
        "event": "health.check",
        "request_id": request_id,
        "user_id": "anonymous",
        "env": env,
    }))
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"status": "healthy", "env": env}),
    }
