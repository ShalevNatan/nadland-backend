# lambda/tests/conftest.py
import importlib.util
import os
import sys

import boto3
import pytest
from moto import mock_aws

# ── path setup ────────────────────────────────────────────────────────────────
# Add each function directory to sys.path so models.py, scenarios.py etc.
# are importable as top-level modules — matching the flat Lambda zip structure.
_LAMBDA_DIR = os.path.dirname(os.path.dirname(__file__))
for _subdir in ("calculate", "get_history", "health"):
    _p = os.path.join(_LAMBDA_DIR, _subdir)
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Pre-register each handler under a unique dotted name so test imports
# (from calculate.handler import ...) work without __init__.py in function dirs,
# and without 'handler' module-name collisions across test files.
def _load_handler(alias: str, subdir: str) -> None:
    path = os.path.join(_LAMBDA_DIR, subdir, "handler.py")
    spec = importlib.util.spec_from_file_location(alias, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[alias] = mod
    spec.loader.exec_module(mod)

_load_handler("calculate.handler", "calculate")
_load_handler("get_history.handler", "get_history")
_load_handler("health.handler", "health")

# ── constants ─────────────────────────────────────────────────────────────────
TEST_TABLE  = "nadland-test"
TEST_USER   = "test-user-sub-123"
TEST_REGION = "us-east-1"


def _make_event(user_id: str = TEST_USER, body: dict | None = None,
                query_params: dict | None = None) -> dict:
    import json as _json
    event: dict = {
        "requestContext": {
            "authorizer": {
                "jwt": {"claims": {"sub": user_id}}
            }
        },
        "queryStringParameters": query_params,
        "body": None,
    }
    if body is not None:
        event["body"] = _json.dumps(body)
    return event


class FakeContext:
    aws_request_id = "test-request-id"


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS credentials so moto never hits real AWS."""
    os.environ["AWS_ACCESS_KEY_ID"]     = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"]    = "testing"
    os.environ["AWS_SESSION_TOKEN"]     = "testing"
    os.environ["AWS_DEFAULT_REGION"]    = TEST_REGION


@pytest.fixture(scope="function")
def dynamo_table(aws_credentials):
    """Create a fresh mocked DynamoDB table for each test."""
    with mock_aws():
        client = boto3.client("dynamodb", region_name=TEST_REGION)
        client.create_table(
            TableName=TEST_TABLE,
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK",  "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK",  "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        os.environ["TABLE_NAME"]   = TEST_TABLE
        os.environ["ENVIRONMENT"]  = "test"
        yield boto3.resource("dynamodb", region_name=TEST_REGION).Table(TEST_TABLE)
        # Reset handler module cache between tests
        ch = sys.modules.get("calculate.handler")
        gh = sys.modules.get("get_history.handler")
        if ch:
            ch._table = None
            ch._dynamo_resource = None
        if gh:
            gh._table = None
            gh._dynamo_resource = None
