from pydantic import BaseModel, field_validator, model_validator
from typing import List, Optional, Union, Any
from datetime import datetime

# --- Points Report Schemas ---

def coerce_numeric_balance(value: Any, field_name: str) -> Optional[float]:
    """Normalize a balance field from QingLong scripts.

    Accepts int / float / numeric string (including "0", "0.0", "0.1").
    None stays None (dimension not reported). Rejects empty/non-numeric/bool.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be a number")
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError(f"{field_name} must not be empty")
        try:
            return float(text)
        except ValueError as exc:
            raise ValueError(f"{field_name} is not a valid number: {value!r}") from exc
    raise ValueError(f"{field_name} must be a number, got {type(value).__name__}")


class ProgramPointsData(BaseModel):
    program_id: str
    program_name: Optional[str] = None
    # Optional so pure-cash scripts can omit points. At least one of points/cash required.
    current_points: Optional[float] = None
    # Optional cash balance in yuan (e.g. 0.1 / 12.34). Old scripts omit this.
    current_cash: Optional[float] = None
    # Optional channel type: code | token | app. Used by APP 列表 (auth_type=app).
    auth_type: Optional[str] = None
    last_updated: Optional[datetime] = None

    @field_validator("current_points", mode="before")
    @classmethod
    def coerce_current_points(cls, value: Union[int, float, str, None]):
        return coerce_numeric_balance(value, "current_points")

    @field_validator("current_cash", mode="before")
    @classmethod
    def coerce_current_cash(cls, value: Union[int, float, str, None]):
        return coerce_numeric_balance(value, "current_cash")

    @model_validator(mode="after")
    def require_points_or_cash(self):
        if self.current_points is None and self.current_cash is None:
            raise ValueError("at least one of current_points or current_cash is required")
        return self

class WechatAccountData(BaseModel):
    # Historical field name: for APP scripts this is often a phone number.
    # Prefer also sending `phone` explicitly; backend will store phone in phone column.
    wechat_id: str
    nickname: Optional[str] = None
    phone: Optional[str] = None
    points_data: List[ProgramPointsData]

class PointsReportData(BaseModel):
    wechat_accounts: List[WechatAccountData]

class PointsReportRequest(BaseModel):
    script_id: str
    execution_time: Optional[datetime] = None
    data: PointsReportData

# --- Stock Report Schemas ---

class ProductData(BaseModel):
    product_id: Optional[str] = None
    product_name: str
    image_url: Optional[str] = None
    stock: Optional[int] = 0
    # Required points for redeem. Pure-points products only send this (legacy compatible).
    points: Optional[int] = 0
    # Optional cash cost in yuan for 积分加钱购 (e.g. 100 points + 9.9 yuan).
    # Omit or 0 for pure-points products. Old scripts that only send points stay compatible.
    cash: Optional[float] = 0
    last_updated: Optional[datetime] = None

    @field_validator("cash", mode="before")
    @classmethod
    def coerce_product_cash(cls, value: Union[int, float, str, None]):
        # None / empty → 0 so pure-points reports stay simple.
        if value is None or value == "":
            return 0.0
        coerced = coerce_numeric_balance(value, "cash")
        return 0.0 if coerced is None else float(coerced)

    @field_validator("points", mode="before")
    @classmethod
    def coerce_product_points(cls, value: Union[int, float, str, None]):
        if value is None or value == "":
            return 0
        if isinstance(value, bool):
            raise ValueError("points must be a number")
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return 0
            try:
                return int(float(text))
            except ValueError as exc:
                raise ValueError(f"points is not a valid number: {value!r}") from exc
        raise ValueError(f"points must be a number, got {type(value).__name__}")

class StockReportRequest(BaseModel):
    program_id: str
    products: List[ProductData]
