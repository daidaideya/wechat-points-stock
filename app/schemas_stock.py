from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# --- Stock Management Schemas ---

class ProductBase(BaseModel):
    product_name: str
    image_url: Optional[str] = None
    points: int = 0
    stock: Optional[int] = 0

class ProductCreateUpdate(ProductBase):
    program_id: str
    product_id: Optional[str] = None # Optional for create (auto-generated from name if missing), required for explicit update if we want to change name

class ProductResponse(ProductBase):
    id: int
    product_id: str
    program_id: str
    image_local_path: Optional[str] = None
    
    class Config:
        from_attributes = True

class ProgramStockSummary(BaseModel):
    program_id: str
    program_name: str
    product_count: int
    total_stock: int
    
    class Config:
        from_attributes = True

class PaginatedProducts(BaseModel):
    total: int
    page: int
    size: int
    items: List[ProductResponse]
