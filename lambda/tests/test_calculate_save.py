# lambda/tests/test_calculate_save.py
"""Tests for /calculate — save=true path (DynamoDB write)."""
import json
import pytest
from moto import mock_aws

from tests.conftest import _make_event, FakeContext, TEST_USER, TEST_TABLE


@pytest.fixture(autouse=True)
def use_dynamo(dynamo_table):
    """Pull in the mocked table for every test in this module."""
    yield dynamo_table


def _call(body: dict) -> dict:
    from calculate.handler import lambda_handler
    event = _make_event(body=body)
    resp = lambda_handler(event, FakeContext())
    resp["_json"] = json.loads(resp["body"])
    return resp


# ── save=true response shape ──────────────────────────────────────────────────

def test_save_true_returns_200(use_dynamo):
    resp = _call({"save": True})
    assert resp["statusCode"] == 200


def test_save_true_returns_calculation_id(use_dynamo):
    resp = _call({"save": True})
    assert "calculation_id" in resp["_json"]


def test_save_true_flag_in_response(use_dynamo):
    resp = _call({"save": True})
    assert resp["_json"]["saved"] is True


def test_calculation_id_is_uuid(use_dynamo):
    import re
    calc_id = _call({"save": True})["_json"]["calculation_id"]
    uuid_re = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
    )
    assert uuid_re.match(calc_id), f"Not a valid UUID4: {calc_id}"


# ── DynamoDB item ─────────────────────────────────────────────────────────────

def test_item_written_to_dynamo(use_dynamo):
    resp = _call({"save": True, "label": "my scenario"})
    calc_id = resp["_json"]["calculation_id"]
    result = use_dynamo.scan()
    assert result["Count"] == 1
    item = result["Items"][0]
    assert item["calculation_id"] == calc_id


def test_item_pk_format(use_dynamo):
    _call({"save": True})
    item = use_dynamo.scan()["Items"][0]
    assert item["PK"] == f"userId#{TEST_USER}"


def test_item_sk_format(use_dynamo):
    _call({"save": True})
    item = use_dynamo.scan()["Items"][0]
    assert item["SK"].startswith("record#")


def test_item_label_stored(use_dynamo):
    _call({"save": True, "label": "test label"})
    item = use_dynamo.scan()["Items"][0]
    assert item["label"] == "test label"


def test_item_label_empty_when_omitted(use_dynamo):
    _call({"save": True})
    item = use_dynamo.scan()["Items"][0]
    assert item["label"] == ""


def test_item_has_inputs_snapshot(use_dynamo):
    _call({"save": True})
    item = use_dynamo.scan()["Items"][0]
    assert "inputs" in item
    assert "land_price" in item["inputs"]


def test_item_has_scenarios(use_dynamo):
    _call({"save": True})
    item = use_dynamo.scan()["Items"][0]
    assert "scenarios" in item
    assert "exit_after_plan" in item["scenarios"]


def test_item_has_ttl(use_dynamo):
    import time
    _call({"save": True})
    item = use_dynamo.scan()["Items"][0]
    assert "ttl" in item
    # TTL should be ~90 days from now
    now = int(time.time())
    assert item["ttl"] > now + (89 * 86400)
    assert item["ttl"] < now + (91 * 86400)


def test_item_created_at_is_iso(use_dynamo):
    from datetime import datetime
    _call({"save": True})
    item = use_dynamo.scan()["Items"][0]
    # Should parse without error
    datetime.fromisoformat(item["created_at"])


# ── save=false does not write ─────────────────────────────────────────────────

def test_save_false_does_not_write(use_dynamo):
    _call({"save": False})
    assert use_dynamo.scan()["Count"] == 0
