"""Seed a disposable SQLite database for the real-backend Playwright smoke."""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))


def main() -> None:
    database_url = os.getenv("DATABASE_URL", "")
    if not database_url or "database.db" in database_url:
        raise SystemExit("DATABASE_URL must point to a disposable Playwright database")

    from app import models
    from app.database import Base, SessionLocal, engine

    Base.metadata.create_all(bind=engine)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    db = SessionLocal()
    try:
        account = models.WechatAccount(
            wechat_id="e2e-user",
            nickname="真实用户",
            phone="13800000000",
            device="Playwright",
            sort_order=0,
        )
        program = models.MiniProgram(
            program_id="e2e-program",
            program_name="真实数据小程序",
            auth_type="code",
            is_favorite=1,
            tags="测试,回归",
            note="真实后端 E2E 数据",
            ql_schedule="0 9 * * *",
            ql_is_disabled=0,
            sort_order=0,
        )
        db.add_all([account, program])
        db.flush()

        history = models.PointsHistory(
            wechat_id=account.wechat_id,
            program_id=program.program_id,
            points=123.0,
            cash=4.5,
            report_time=now,
            batch_id="playwright-e2e",
        )
        db.add(history)
        db.flush()
        db.add(
            models.CurrentPointBalance(
                wechat_id=account.wechat_id,
                program_id=program.program_id,
                points=history.points,
                cash=history.cash,
                last_report_time=history.report_time,
                history_id=history.id,
                updated_at=now,
            )
        )
        db.add(
            models.Product(
                program_id=program.program_id,
                product_id="e2e-product",
                product_name="真实商品",
                points=100,
                cash=0,
                stock=7,
            )
        )
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
