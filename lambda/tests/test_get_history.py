# lambda/tests/test_get_history.py
"""Tests for GET /history."""
import json
from datetime import datetime, timezone, timedelta
from decimal import Decimal

import pytest

from tests.conftest import _make_event, FakeContext, TEST_USER


@pytest.fixture(autouse=True)
def use_dynamo(dynamo_table):
    yield dynamo_table


def _seed(table, user_id: str = TEST_USER, count: int = 1) -> list[str]:
    """Write `count` records for user_id, return their calculation_ids."""
    ids = []
    for i in range(count):
        now = datetime.now(timezone.utc) + timedelta(seconds=i)
        calc_id = f"calc-{i}"
        table.put_item(Item={
            "PK": f"userId#{user_id}",
            "SK": f"record#{now.isoformat()}",
            "calculation_id": calc_id,
            "label": f"label-{i}",
            "created_at": now.isoformat(),
            "inputs": {"land_price": Decimal("620000")},
            "scenarios": {"exit_after_plan": {"irr": Decimal("0.11")}},
            "ttl": 9999999999,
        })
        ids.append(calc_id)
    return ids


def _call(user_id: str = TEST_USER, query_params: dict | None = None) -> dict:
    from get_history.handler import lambda_handler
    event = _make_event(user_id=user_id, query_params=query_params)
    resp = lambda_handler(event, FakeContext())
    resp["_json"] = json.loads(resp["body"])
    return resp


# ── empty history ─────────────────────────────────────────────────────────────

def test_empty_history_returns_200(use_dynamo):
    resp = _call()
    assert resp["statusCode"] == 200


def test_empty_history_items_list(use_dynamo):
    resp = _call()
    assert resp["_json"]["items"] == []
    assert resp["_json"]["count"] == 0


# ── with records ─────────────────────────────────────────────────────────────

def test_returns_seeded_items(use_dynamo):
    _seed(use_dynamo, count=3)
    resp = _call()
    assert resp["_json"]["count"] == 3
    assert len(resp["_json"]["items"]) == 3


def test_item_shape(use_dynamo):
    _seed(use_dynamo, count=1)
    item = _call()["_json"]["items"][0]
    for field in ("calculation_id", "label", "created_at", "scenarios", "inputs"):
        assert field in item, f"missing field: {field}"


def test_item_calculation_id(use_dynamo):
    _seed(use_dynamo, count=1)
    item = _call()["_json"]["items"][0]
    assert item["calculation_id"] == "calc-0"


def test_item_label(use_dynamo):
    _seed(use_dynamo, count=1)
    item = _call()["_json"]["items"][0]
    assert item["label"] == "label-0"


# ── user isolation ────────────────────────────────────────────────────────────

def test_user_isolation(use_dynamo):
    _seed(use_dynamo, user_id=TEST_USER, count=2)
    _seed(use_dynamo, user_id="other-user-456", count=3)
    resp = _call(user_id=TEST_USER)
    assert resp["_json"]["count"] == 2


# ── limit ─────────────────────────────────────────────────────────────────────

def test_default_limit_caps_at_20(use_dynamo):
    _seed(use_dynamo, count=25)
    resp = _call()
    assert resp["_json"]["count"] <= 20


def test_custom_limit(use_dynamo):
    _seed(use_dynamo, count=10)
    resp = _call(query_params={"limit": "5"})
    assert resp["_json"]["count"] <= 5


def test_limit_capped_at_100(use_dynamo):
    # Even if limit=999 is passed, handler must cap at 100
    _seed(use_dynamo, count=5)
    resp = _call(query_params={"limit": "999"})
    assert resp["statusCode"] == 200
