import math
from typing import List, Optional, Union, Any
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, field_validator, model_validator


# These limits are intentionally high enough for normal QingLong reports while
# preventing an accidentally unbounded JSON array from monopolising the worker.
# Keep them in the schema module so the API contract and its tests share one
# source of truth.
MAX_WECHAT_ACCOUNTS_PER_REPORT = 100
MAX_PROGRAMS_PER_ACCOUNT = 500
MAX_POINTS_ROWS_PER_REPORT = 5_000
MAX_PRODUCTS_PER_STOCK_REPORT = 2_000


class SchemaBase(BaseModel):
    # Keep Pydantic's historical ``extra=ignore`` behaviour for old scripts,
    # while making identifiers/names deterministic before persistence.
    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")


def normalize_optional_text(value: Any) -> Any:
    """Treat an optional blank string as an omitted value.

    Older reporters commonly sent ``""`` for optional product IDs, image URLs,
    or names.  The service already treated those values as absent, so converting
    them to ``None`` preserves that compatibility while required fields still
    fail their minimum-length constraint.
    """
    if value is None or not isinstance(value, str):
        return value
    text = value.strip()
    return text or None

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
        try:
            number = float(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f"{field_name} must be a finite number") from exc
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError(f"{field_name} must not be empty")
        try:
            number = float(text)
        except ValueError as exc:
            raise ValueError(f"{field_name} is not a valid number: {value!r}") from exc
    else:
        raise ValueError(f"{field_name} must be a number, got {type(value).__name__}")

    if not math.isfinite(number):
        raise ValueError(f"{field_name} must be finite")
    if number < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return number


def coerce_nonnegative_integer(value: Any, field_name: str) -> int:
    """Accept legacy integer-like values without truncating invalid fractions."""
    if value is None or value == "":
        return 0
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be an integer")

    if isinstance(value, (int, float)):
        try:
            number = float(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f"{field_name} must be a finite integer") from exc
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            return 0
        try:
            number = float(text)
        except ValueError as exc:
            raise ValueError(f"{field_name} is not a valid number: {value!r}") from exc
    else:
        raise ValueError(f"{field_name} must be an integer, got {type(value).__name__}")

    if not math.isfinite(number):
        raise ValueError(f"{field_name} must be finite")
    if number < 0:
        raise ValueError(f"{field_name} must be non-negative")
    if not number.is_integer():
        raise ValueError(f"{field_name} must be an integer")
    return int(number)


class ProgramPointsData(SchemaBase):
    program_id: str = Field(..., min_length=1, max_length=100)
    program_name: Optional[str] = Field(default=None, max_length=200)
    # Optional so pure-cash scripts can omit points. At least one of points/cash required.
    current_points: Optional[FiniteFloat] = None
    # Optional cash balance in yuan (e.g. 0.1 / 12.34). Old scripts omit this.
    current_cash: Optional[FiniteFloat] = None
    # Optional channel type: code | token | app. Used by APP 列表 (auth_type=app).
    auth_type: Optional[str] = Field(default=None, max_length=20)
    last_updated: Optional[datetime] = None

    @field_validator("program_name", "auth_type", mode="before")
    @classmethod
    def normalize_optional_fields(cls, value: Any):
        return normalize_optional_text(value)

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

class WechatAccountData(SchemaBase):
    # Historical field name: for APP scripts this is often a phone number.
    # Prefer also sending `phone` explicitly; backend will store phone in phone column.
    wechat_id: str = Field(..., min_length=1, max_length=50)
    nickname: Optional[str] = Field(default=None, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=20)
    points_data: List[ProgramPointsData] = Field(max_length=MAX_PROGRAMS_PER_ACCOUNT)

    @field_validator("nickname", "phone", mode="before")
    @classmethod
    def normalize_optional_fields(cls, value: Any):
        return normalize_optional_text(value)

class PointsReportData(SchemaBase):
    wechat_accounts: List[WechatAccountData] = Field(max_length=MAX_WECHAT_ACCOUNTS_PER_REPORT)

    @model_validator(mode="after")
    def enforce_total_points_rows(self):
        total_rows = sum(len(account.points_data) for account in self.wechat_accounts)
        if total_rows > MAX_POINTS_ROWS_PER_REPORT:
            raise ValueError(
                f"points report contains too many program rows; maximum is {MAX_POINTS_ROWS_PER_REPORT}"
            )
        return self

class PointsReportRequest(SchemaBase):
    script_id: str = Field(..., min_length=1, max_length=255)
    execution_time: Optional[datetime] = None
    data: PointsReportData

# --- Stock Report Schemas ---

class ProductData(SchemaBase):
    product_id: Optional[str] = Field(default=None, max_length=100)
    product_name: str = Field(..., min_length=1, max_length=200)
    image_url: Optional[str] = Field(default=None, max_length=2048)
    stock: Optional[int] = Field(default=0, ge=0)
    # Required points for redeem. Pure-points products only send this (legacy compatible).
    points: Optional[int] = Field(default=0, ge=0)
    # Optional cash cost in yuan for 积分加钱购 (e.g. 100 points + 9.9 yuan).
    # Omit or 0 for pure-points products. Old scripts that only send points stay compatible.
    cash: Optional[FiniteFloat] = Field(default=0, ge=0)
    last_updated: Optional[datetime] = None

    @field_validator("product_id", "image_url", mode="before")
    @classmethod
    def normalize_optional_fields(cls, value: Any):
        return normalize_optional_text(value)

    @field_validator("stock", mode="before")
    @classmethod
    def reject_boolean_stock(cls, value: Any):
        if isinstance(value, bool):
            raise ValueError("stock must be an integer")
        return value

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
        return coerce_nonnegative_integer(value, "points")

class StockReportRequest(SchemaBase):
    program_id: str = Field(..., min_length=1, max_length=100)
    # Empty is meaningful: the service deliberately skips auto-unlisting for
    # an empty snapshot, so only the upper bound is constrained.
    products: List[ProductData] = Field(max_length=MAX_PRODUCTS_PER_STOCK_REPORT)
    # New reporters can explicitly mark a partial fetch. Legacy reporters omit
    # this field and retain the historical complete-snapshot behavior.
    snapshot_id: Optional[str] = Field(default=None, max_length=100)
    snapshot_complete: bool = True
    # When supplied, a count mismatch is treated as an incomplete snapshot and
    # therefore cannot auto-unlist products.
    expected_product_count: Optional[int] = Field(
        default=None,
        ge=0,
        le=MAX_PRODUCTS_PER_STOCK_REPORT,
    )

    @field_validator("snapshot_id", mode="before")
    @classmethod
    def normalize_snapshot_id(cls, value: Any):
        return normalize_optional_text(value)

    @field_validator("expected_product_count", mode="before")
    @classmethod
    def coerce_expected_product_count(cls, value: Union[int, float, str, None]):
        if value is None or value == "":
            return None
        return coerce_nonnegative_integer(value, "expected_product_count")


# --- Access audit query schemas ---

class AccessAuditEventItem(SchemaBase):
    """Public, credential-free representation of one access audit event."""

    event_type: str = Field(..., min_length=1, max_length=40)
    client_id: Optional[str] = Field(default=None, max_length=128)
    request_id: Optional[str] = Field(default=None, max_length=128)
    # The database column is nullable for compatibility with legacy rows.
    event_time: Optional[datetime] = None


class AccessAuditEventPage(SchemaBase):
    """Paginated access audit response metadata and safe event items."""

    items: List[AccessAuditEventItem]
    page: int = Field(..., ge=1)
    size: int = Field(..., ge=1, le=100)
    total: int = Field(..., ge=0)
    has_more: bool
