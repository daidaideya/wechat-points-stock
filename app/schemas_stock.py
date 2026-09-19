from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, field_validator
from datetime import datetime

from app.money import normalize_cash_amount

# --- Stock Management Schemas ---

class StockSchemaBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")


def normalize_optional_text(value: Any) -> Any:
    """Keep omitted optional strings compatible with the legacy UI payloads."""
    if value is None or not isinstance(value, str):
        return value
    text = value.strip()
    return text or None


class ProductBase(StockSchemaBase):
    product_name: str = Field(..., min_length=1, max_length=200)
    image_url: Optional[str] = Field(default=None, max_length=2048)
    points: int = Field(default=0, ge=0)
    # Cash cost in yuan for 积分加钱购; 0/None = pure points product.
    cash: Optional[FiniteFloat] = Field(default=0, ge=0)
    stock: Optional[int] = Field(default=0, ge=0)

    @field_validator("image_url", mode="before")
    @classmethod
    def normalize_optional_image_url(cls, value: Any):
        return normalize_optional_text(value)

    @field_validator("points", "stock", mode="before")
    @classmethod
    def reject_boolean_numbers(cls, value: Any):
        if isinstance(value, bool):
            raise ValueError("numeric fields must not be boolean")
        return value

    @field_validator("cash", mode="before")
    @classmethod
    def normalize_cash(cls, value: Any):
        return normalize_cash_amount(value, default=0.0)


class ProductCreateUpdate(ProductBase):
    program_id: str = Field(..., min_length=1, max_length=100)
    # Optional for create (auto-generated from name if missing).
    product_id: Optional[str] = Field(default=None, max_length=100)

    @field_validator("product_id", mode="before")
    @classmethod
    def normalize_optional_product_id(cls, value: Any):
        return normalize_optional_text(value)

class ProductResponse(ProductBase):
    id: int
    product_id: str = Field(..., min_length=1, max_length=100)
    program_id: str = Field(..., min_length=1, max_length=100)
    image_local_path: Optional[str] = None
    is_hidden: Optional[int] = 0
    hidden_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True, extra="ignore")


class ProgramStockSummary(StockSchemaBase):
    program_id: str = Field(..., min_length=1, max_length=100)
    program_name: str = Field(..., min_length=1, max_length=200)
    product_count: int = Field(..., ge=0)
    total_stock: int = Field(..., ge=0)

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True, extra="ignore")


class PaginatedProducts(StockSchemaBase):
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    size: int = Field(..., ge=1, le=100)
    items: List[ProductResponse] = Field(max_length=100)
