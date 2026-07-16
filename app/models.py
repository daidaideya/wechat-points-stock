from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class SystemSettings(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    max_log_entries = Column(Integer, default=10000)
    max_retention_days = Column(Integer, default=30)
    access_protection_enabled = Column(Integer, default=0)
    access_key = Column(String(255), nullable=True)
    # QingLong OpenAPI credentials (display-only cron enable/disable sync)
    ql_base_url = Column(String(255), nullable=True)
    ql_client_id = Column(String(100), nullable=True)
    ql_client_secret = Column(String(255), nullable=True)
    ql_last_sync_at = Column(DateTime, nullable=True)
    ql_last_sync_status = Column(String(255), nullable=True)
    # Bark push for daily unreported mini-programs
    bark_enabled = Column(Integer, default=0)
    bark_server = Column(String(255), nullable=True)  # e.g. https://api.day.app
    bark_device_key = Column(String(255), nullable=True)
    bark_push_time = Column(String(16), nullable=True)  # HH:MM local time, default 20:00
    bark_last_push_at = Column(DateTime, nullable=True)
    bark_last_push_status = Column(String(255), nullable=True)
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
    is_archived = Column(Integer, default=0) # 0: False, 1: True. Archived programs are hidden from default views.
    archived_at = Column(DateTime, nullable=True)
    # Cached QingLong cron match (read-only sync from panel OpenAPI)
    ql_cron_id = Column(Integer, nullable=True)
    ql_cron_name = Column(String(200), nullable=True)
    ql_is_disabled = Column(Integer, nullable=True)  # 0 enabled, 1 disabled, NULL unmatched
    ql_matched_at = Column(DateTime, nullable=True)
    ql_command = Column(String(500), nullable=True)
    ql_schedule = Column(String(100), nullable=True)  # crontab expression, e.g. "0 9 * * *"

    points = relationship("PointsHistory", back_populates="program")
    products = relationship("Product", back_populates="program")

class PointsHistory(Base):
    __tablename__ = "points_history"

    id = Column(Integer, primary_key=True, index=True)
    wechat_id = Column(String(50), ForeignKey("wechat_accounts.wechat_id"))
    program_id = Column(String(100), ForeignKey("mini_programs.program_id"))
    # Float to support fractional balances (e.g. 0.1 points + cash products).
    # Either points or cash (or both) may be set per report; NULL = dimension not reported.
    # SQLite INTEGER affinity still stores fractional values as REAL; no table rebuild needed.
    points = Column(Float, nullable=True)
    cash = Column(Float, nullable=True)
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
    is_hidden = Column(Integer, default=0)  # 用户手动隐藏
    hidden_at = Column(DateTime, nullable=True)
    is_unlisted = Column(Integer, default=0)  # 系统自动检测到的下架（与是否手动隐藏独立）
    unlisted_at = Column(DateTime, nullable=True)

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
