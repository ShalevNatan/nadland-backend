# lambda/tests/test_calculate.py
"""Tests for /calculate — stateless (save=false) path."""
import json

import pytest

from tests.conftest import _make_event, FakeContext, TEST_USER


def _call(body: dict | None = None) -> dict:
    from calculate.handler import lambda_handler
    event = _make_event(body=body)
    resp = lambda_handler(event, FakeContext())
    resp["_json"] = json.loads(resp["body"])
    return resp


# ── default inputs ────────────────────────────────────────────────────────────

def test_default_inputs_returns_200():
    resp = _call({})
    assert resp["statusCode"] == 200


def test_default_inputs_saved_false():
    resp = _call({})
    assert resp["_json"]["saved"] is False


def test_default_inputs_no_calculation_id():
    resp = _call({})
    assert "calculation_id" not in resp["_json"]


def test_all_three_scenarios_present():
    resp = _call({})
    scenarios = resp["_json"]["scenarios"]
    assert set(scenarios.keys()) == {
        "exit_after_plan",
        "exit_after_license",
        "key_with_construction_loan",
    }


# ── scenario shape ────────────────────────────────────────────────────────────

def test_exit_after_plan_fields():
    sc = _call({})["_json"]["scenarios"]["exit_after_plan"]
    for field in ("tag", "duration_years", "upfront_outlay", "mgmt_fee_paid",
                  "exit_value", "profit", "irr"):
        assert field in sc, f"missing field: {field}"


def test_exit_after_license_fields():
    sc = _call({})["_json"]["scenarios"]["exit_after_license"]
    for field in ("tag", "duration_years", "upfront_outlay", "mgmt_fee_paid",
                  "mgmt_breakdown", "exit_value", "profit", "irr"):
        assert field in sc, f"missing field: {field}"


def test_key_with_construction_loan_fields():
    sc = _call({})["_json"]["scenarios"]["key_with_construction_loan"]
    for field in ("tag", "duration_years", "upfront_outlay", "mgmt_fee_paid",
                  "mgmt_breakdown", "interest_paid_during_build",
                  "principal_repaid_at_sale", "betterment_paid",
                  "exit_value_gross_at_key", "profit", "irr"):
        assert field in sc, f"missing field: {field}"


# ── known values (default inputs) ─────────────────────────────────────────────

def test_upfront_outlay_default():
    # 620000 * 1.06 + 14570 + 0 = 671770
    # (spec example 671970 appears to include a non-zero entrepreneur_fee_in)
    sc = _call({})["_json"]["scenarios"]["exit_after_plan"]
    assert abs(sc["upfront_outlay"] - 671770.0) < 1.0


def test_exit_after_plan_duration():
    sc = _call({})["_json"]["scenarios"]["exit_after_plan"]
    assert sc["duration_years"] == 4.0


def test_exit_after_license_duration():
    sc = _call({})["_json"]["scenarios"]["exit_after_license"]
    assert sc["duration_years"] == 8.0


def test_key_duration():
    sc = _call({})["_json"]["scenarios"]["key_with_construction_loan"]
    assert sc["duration_years"] == 12.0


def test_irr_is_float():
    sc = _call({})["_json"]["scenarios"]["exit_after_plan"]
    assert isinstance(sc["irr"], float)


# ── custom inputs ─────────────────────────────────────────────────────────────

def test_custom_land_price_changes_upfront():
    resp_default = _call({})["_json"]["scenarios"]["exit_after_plan"]["upfront_outlay"]
    resp_custom  = _call({"inputs": {"land_price": 500000}})["_json"]["scenarios"]["exit_after_plan"]["upfront_outlay"]
    assert resp_custom < resp_default


def test_apply_management_fee_false_zeroes_fee():
    sc = _call({"inputs": {"apply_management_fee": False}})["_json"]["scenarios"]["exit_after_plan"]
    assert sc["mgmt_fee_paid"] == 0.0


# ── error handling ────────────────────────────────────────────────────────────

def test_invalid_json_body_returns_400():
    from calculate.handler import lambda_handler
    event = _make_event()
    event["body"] = "not-json{"
    resp = lambda_handler(event, FakeContext())
    assert resp["statusCode"] == 400


def test_save_false_does_not_require_dynamo(monkeypatch):
    """save=false must complete without touching DynamoDB at all."""
    import calculate.handler as h
    monkeypatch.setattr(h, "_get_table", lambda: (_ for _ in ()).throw(
        RuntimeError("DynamoDB should not be called")
    ))
    resp = _call({"save": False})
    assert resp["statusCode"] == 200
