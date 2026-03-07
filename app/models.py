from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class SystemSettings(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    max_log_entries = Column(Integer, default=10000)
    max_retention_days = Column(Integer, default=30)
    updated_at = Column(DateTime, default=datetime.utcnow)

class WechatAccount(Base):
    __tablename__ = "wechat_accounts"

    id = Column(Integer, primary_key=True, index=True)
    wechat_id = Column(String(50), unique=True, nullable=False)
    nickname = Column(String(100))
    device = Column(String(100))
    phone = Column(String(20), index=True)
    sort_order = Column(Integer, default=0)

    points = relationship("PointsHistory", back_populates="account")

class MiniProgram(Base):
    __tablename__ = "mini_programs"

    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(String(100), unique=True, nullable=False)
    program_name = Column(String(200))
    auth_type = Column(String(20), default="code")  # code, token, app
    sort_order = Column(Integer, default=0) # Kept for backward compatibility if needed, or repurposed
    is_favorite = Column(Integer, default=0) # 0: False, 1: True
    note = Column(String, nullable=True) # Personal notes/remarks for the program
    tags = Column(String, nullable=True) # Comma-separated personal tags for the program

    points = relationship("PointsHistory", back_populates="program")
    products = relationship("Product", back_populates="program")

class PointsHistory(Base):
    __tablename__ = "points_history"

    id = Column(Integer, primary_key=True, index=True)
    wechat_id = Column(String(50), ForeignKey("wechat_accounts.wechat_id"))
    program_id = Column(String(100), ForeignKey("mini_programs.program_id"))
    points = Column(Integer)
    report_time = Column(DateTime, default=datetime.utcnow)
    batch_id = Column(String(50))

    account = relationship("WechatAccount", back_populates="points")
    program = relationship("MiniProgram", back_populates="points")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(String(100), ForeignKey("mini_programs.program_id"))
    product_id = Column(String(100))
    product_name = Column(String(200))
    image_local_path = Column(String)
    image_url = Column(String)
    points = Column(Integer, default=0)
    stock = Column(Integer, default=0)
    is_hidden = Column(Integer, default=0)
    hidden_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint('program_id', 'product_id', name='uix_program_product'),
    )

    program = relationship("MiniProgram", back_populates="products")

class StockHistory(Base):
    __tablename__ = "stock_history"

    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(String(100))
    product_id = Column(String(100))
    old_stock = Column(Integer)
    new_stock = Column(Integer)
    change_time = Column(DateTime, default=datetime.utcnow)
    
    # Note: Foreign Key logic for composite keys is complex in simple models, 
    # and the doc didn't strictly enforce FK on stock_history to products (it did in the detailed version, 
    # but let's keep it simple as per the simplified doc which just lists columns).
    # However, to be safe, I won't add strict FK constraint here unless necessary 
    # to avoid complexity with composite FKs in SQLAlchemy for this quick setup.
    # The simplified doc just lists columns.
