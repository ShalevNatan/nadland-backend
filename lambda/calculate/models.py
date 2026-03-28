# lambda/calculate/models.py
from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Inputs:
    # Entry (land) side
    land_price: float = 620_000.0
    purchase_tax_rate: float = 0.06
    lawyer_fee: float = 14_570.0
    entrepreneur_fee_in: float = 0.0

    # Time & values
    plan_years: int = 4
    approved_land_value: float = 1_075_000.0
    build_license_years: int = 4
    licensed_land_value: float = 1_300_000.0
    build_years: int = 4
    current_apartment_price_today: float = 3_200_000.0
    annual_appreciation: float = 0.03

    # Management fee
    mgmt_fee_pct: float = 0.025
    vat_rate: float = 0.18
    apply_management_fee: bool = True

    # Betterment levy
    betterment_levy: float = 300_000.0
    apply_betterment_at_key: bool = True

    # Construction
    construction_cost: float = 1_300_000.0
    annual_construction_rate: float = 0.05
    draw_linear: bool = True

    # IRR solver params (not user-facing, not in API body)
    irr_max_iter: int = 200
    irr_tol: float = 1e-8

    @classmethod
    def from_dict(cls, data: dict) -> "Inputs":
        """Build Inputs from a request body dict. Unknown keys are ignored."""
        allowed = {f_name for f_name in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        filtered = {k: v for k, v in data.items() if k in allowed}
        return cls(**filtered)

    def to_dict(self) -> dict:
        """Return a plain dict suitable for DynamoDB storage (Decimal-safe)."""
        out = {}
        for f_name in self.__dataclass_fields__:  # type: ignore[attr-defined]
            val = getattr(self, f_name)
            if isinstance(val, float):
                out[f_name] = Decimal(str(val))
            else:
                out[f_name] = val
        return out
