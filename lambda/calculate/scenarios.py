# lambda/calculate/scenarios.py
from decimal import Decimal

from models import Inputs


# ── helpers ──────────────────────────────────────────────────────────────────

def _irr_monthly(cashflows: list[float], tol: float = 1e-8, max_iter: int = 200) -> float:
    r = 0.01
    for _ in range(max_iter):
        npv = 0.0
        d = 0.0
        for t, cf in enumerate(cashflows):
            denom = (1 + r) ** t
            npv += cf / denom
            d -= (t * cf) / (denom * (1 + r)) if denom != 0 else 0.0
        if abs(npv) < tol:
            break
        step = (-npv / d) if d != 0 else -npv * 1e-4
        r += step
        if r <= -0.99:
            r = -0.99
    return r


def _annualize(r_month: float) -> float:
    return (1 + r_month) ** 12 - 1


def _upfront_outlay(p: Inputs) -> float:
    return p.land_price * (1 + p.purchase_tax_rate) + p.lawyer_fee + p.entrepreneur_fee_in


def _mgmt_fee_at_plan(p: Inputs) -> float:
    if not p.apply_management_fee:
        return 0.0
    return p.mgmt_fee_pct * p.approved_land_value * (1 + p.vat_rate)


def _apt_value_at_license(p: Inputs) -> float:
    years = p.plan_years + p.build_license_years
    return p.current_apartment_price_today * ((1 + p.annual_appreciation) ** years)


def _mgmt_fee_at_license(p: Inputs) -> float:
    if not p.apply_management_fee:
        return 0.0
    return p.mgmt_fee_pct * _apt_value_at_license(p) * (1 + p.vat_rate)


# ── scenarios ─────────────────────────────────────────────────────────────────

def exit_after_plan(p: Inputs) -> dict:
    months = p.plan_years * 12
    flows = [0.0] * (months + 1)
    upfront = _upfront_outlay(p)
    flows[0] = -upfront
    Y = _mgmt_fee_at_plan(p)
    flows[months] -= Y
    flows[months] += p.approved_land_value
    irr_y = _annualize(_irr_monthly(flows, tol=p.irr_tol, max_iter=p.irr_max_iter))
    return {
        "tag": "Exit after PLAN",
        "duration_years": months / 12.0,
        "upfront_outlay": upfront,
        "mgmt_fee_paid": Y,
        "exit_value": p.approved_land_value,
        "profit": sum(flows),
        "irr": irr_y,
    }


def exit_after_license(p: Inputs) -> dict:
    months_plan = p.plan_years * 12
    months_license = (p.plan_years + p.build_license_years) * 12
    flows = [0.0] * (months_license + 1)
    upfront = _upfront_outlay(p)
    flows[0] = -upfront
    Y = _mgmt_fee_at_plan(p)
    flows[months_plan] -= Y
    X = _mgmt_fee_at_license(p)
    top_up = max(0.0, X - Y)
    flows[months_license] -= top_up
    flows[months_license] += p.licensed_land_value
    irr_y = _annualize(_irr_monthly(flows, tol=p.irr_tol, max_iter=p.irr_max_iter))
    return {
        "tag": "Exit after LICENSE",
        "duration_years": months_license / 12.0,
        "upfront_outlay": upfront,
        "mgmt_fee_paid": Y + top_up,
        "mgmt_breakdown": {"at_plan": Y, "top_up": top_up, "total_mgmt": Y + top_up},
        "exit_value": p.licensed_land_value,
        "profit": sum(flows),
        "irr": irr_y,
    }


def key_with_construction_loan(p: Inputs) -> dict:
    months_plan = p.plan_years * 12
    months_license = (p.plan_years + p.build_license_years) * 12
    months_build = p.build_years * 12
    months_total = months_license + months_build
    flows = [0.0] * (months_total + 1)
    upfront = _upfront_outlay(p)
    flows[0] = -upfront
    Y = _mgmt_fee_at_plan(p)
    flows[months_plan] -= Y
    X = _mgmt_fee_at_license(p)
    top_up = max(0.0, X - Y)
    flows[months_license] -= top_up
    r_m = p.annual_construction_rate / 12.0
    interest_paid = 0.0
    for k in range(1, months_build + 1):
        outstanding = p.construction_cost * (k / months_build)
        interest = outstanding * r_m
        flows[months_license + k] -= interest
        interest_paid += interest
    apt_value_key = p.current_apartment_price_today * (
        (1 + p.annual_appreciation) ** (p.plan_years + p.build_license_years + p.build_years)
    )
    betterment = p.betterment_levy if p.apply_betterment_at_key else 0.0
    flows[months_total] -= betterment
    flows[months_total] += apt_value_key
    flows[months_total] -= p.construction_cost
    irr_y = _annualize(_irr_monthly(flows, tol=p.irr_tol, max_iter=p.irr_max_iter))
    return {
        "tag": "KEY (Build + Construction Loan)",
        "duration_years": months_total / 12.0,
        "upfront_outlay": upfront,
        "mgmt_fee_paid": Y + top_up,
        "mgmt_breakdown": {"at_plan": Y, "top_up": top_up, "total_mgmt": Y + top_up},
        "interest_paid_during_build": interest_paid,
        "principal_repaid_at_sale": p.construction_cost,
        "betterment_paid": betterment,
        "exit_value_gross_at_key": apt_value_key,
        "profit": sum(flows),
        "irr": irr_y,
    }


def run_all(p: Inputs) -> dict:
    return {
        "exit_after_plan": exit_after_plan(p),
        "exit_after_license": exit_after_license(p),
        "key_with_construction_loan": key_with_construction_loan(p),
    }
