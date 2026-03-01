from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# --- Points Report Schemas ---

class ProgramPointsData(BaseModel):
    program_id: str
    program_name: Optional[str] = None
    current_points: int
    last_updated: Optional[datetime] = None

class WechatAccountData(BaseModel):
    wechat_id: str
    nickname: Optional[str] = None
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
    points: Optional[int] = 0
    last_updated: Optional[datetime] = None

class StockReportRequest(BaseModel):
    program_id: str
    products: List[ProductData]
