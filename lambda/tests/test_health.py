# lambda/tests/test_health.py
"""Tests for GET /health — no auth, no DynamoDB."""
import json
import os

import pytest

from tests.conftest import FakeContext


def _call() -> dict:
    from health.handler import lambda_handler
    event = {"requestContext": {}, "queryStringParameters": None, "body": None}
    resp = lambda_handler(event, FakeContext())
    resp["_json"] = json.loads(resp["body"])
    return resp


def test_health_returns_200():
    resp = _call()
    assert resp["statusCode"] == 200


def test_health_status_healthy():
    resp = _call()
    assert resp["_json"]["status"] == "healthy"


def test_health_returns_env():
    os.environ["ENVIRONMENT"] = "test"
    resp = _call()
    assert resp["_json"]["env"] == "test"


def test_health_content_type():
    resp = _call()
    assert resp["headers"]["Content-Type"] == "application/json"


def test_health_no_dynamo_required():
    """Health endpoint must not import or touch boto3/DynamoDB."""
    import health.handler as h
    assert not hasattr(h, "_get_table"), "health handler must not have _get_table"
