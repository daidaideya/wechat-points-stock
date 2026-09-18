from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.database import Base
from app.routers import web


@pytest.fixture()
def points_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    db.add_all([
        models.MiniProgram(program_id="program-1", program_name="程序一"),
        models.MiniProgram(program_id="program-2", program_name="程序二"),
        models.WechatAccount(wechat_id="wechat-1", nickname="账号一"),
    ])
    db.commit()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_equal_report_time_uses_highest_id_for_latest_balances(points_db):
    report_time = datetime(2025, 1, 1, 12, 0, 0)
    older = models.PointsHistory(
        program_id="program-1",
        wechat_id="wechat-1",
        points=100,
        cash=10,
        report_time=report_time,
    )
    newer = models.PointsHistory(
        program_id="program-1",
        wechat_id="wechat-1",
        points=40,
        cash=4,
        report_time=report_time,
    )
    points_db.add_all([older, newer])
    points_db.commit()

    grouped = web.fetch_points_history_grouped(points_db, ["wechat-1"])
    assert grouped["wechat-1"][0].id == newer.id
    assert web.get_latest_points_records_for_program(points_db, "program-1")["wechat-1"].id == newer.id

    account = points_db.query(models.WechatAccount).filter_by(wechat_id="wechat-1").one()
    program = points_db.query(models.MiniProgram).filter_by(program_id="program-1").one()
    summary = web.build_account_points_summary(
        points_db,
        account,
        [program],
        user_points=grouped["wechat-1"],
    )
    item = next(item for item in summary["points"] if item["program_id"] == "program-1")
    assert item["points"] == 40
    assert item["cash"] == 4

    assert web.get_program_max_user_points_map(points_db, ["program-1"]) == {"program-1": 40.0}
    assert web.get_program_max_user_cash_map(points_db, ["program-1"]) == {"program-1": 4.0}

    stock_payload = web.get_program_stock("program-1", points_db)
    assert stock_payload["max_user_points"] == 40
    assert stock_payload["max_user_cash"] == 4


def test_single_program_balance_does_not_mix_other_program(points_db):
    report_time = datetime(2025, 1, 1, 12, 0, 0)
    points_db.add_all([
        models.PointsHistory(
            program_id="program-1",
            wechat_id="wechat-1",
            points=100,
            cash=5,
            report_time=report_time,
        ),
        models.PointsHistory(
            program_id="program-2",
            wechat_id="wechat-1",
            points=1000,
            cash=100,
            report_time=report_time,
        ),
    ])
    points_db.commit()

    payload = web.get_program_stock("program-1", points_db)
    assert payload["max_user_points"] == 100
    assert payload["max_user_cash"] == 5
