from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models, timeutil
from app.database import Base
from app.routers import web


SHANGHAI = timezone(timedelta(hours=8), name="Asia/Shanghai")


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
        models.MiniProgram(
            program_id="program-1",
            program_name="程序一",
            auth_type="code",
            is_archived=0,
        ),
        models.MiniProgram(
            program_id="program-2",
            program_name="程序二",
            auth_type="app",
            is_archived=0,
        ),
        models.MiniProgram(
            program_id="archived-program",
            program_name="已归档",
            auth_type="code",
            is_archived=1,
        ),
        models.WechatAccount(wechat_id="wechat-1", nickname="账号一"),
        models.WechatAccount(wechat_id="wechat-2", nickname="账号二"),
    ])
    db.commit()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def fixed_business_day(monkeypatch):
    monkeypatch.setattr(
        timeutil,
        "now_local",
        lambda: datetime(2025, 1, 2, 12, 0, tzinfo=SHANGHAI),
    )


def test_grouped_history_is_bounded_and_uses_database_windows(
    points_db,
    fixed_business_day,
):
    # 2025-01-02 00:00 Asia/Shanghai is 2025-01-01 16:00 UTC.  The
    # pre-day row is deliberately followed by a large amount of older data.
    points_db.add_all([
        models.PointsHistory(
            program_id="program-1",
            wechat_id="wechat-1",
            points=100,
            cash=10,
            report_time=datetime(2025, 1, 1, 15, 59),
        ),
        models.PointsHistory(
            program_id="program-1",
            wechat_id="wechat-1",
            points=20,
            cash=2,
            report_time=datetime(2025, 1, 2, 1, 0),
        ),
        models.PointsHistory(
            program_id="program-1",
            wechat_id="wechat-1",
            points=30,
            cash=3,
            report_time=datetime(2025, 1, 2, 1, 0),
        ),
        models.PointsHistory(
            program_id="program-2",
            wechat_id="wechat-1",
            points=7,
            cash=1.5,
            report_time=datetime(2025, 1, 2, 2, 0),
        ),
        models.PointsHistory(
            program_id="program-1",
            wechat_id="wechat-2",
            points=8,
            cash=0,
            report_time=datetime(2025, 1, 1, 15, 0),
        ),
    ])
    points_db.add_all([
        models.PointsHistory(
            program_id="program-1",
            wechat_id="wechat-1",
            points=index,
            cash=index / 10,
            report_time=datetime(2024, 1, 1) + timedelta(days=index),
        )
        for index in range(1, 151)
    ])
    points_db.commit()

    statements = []

    def capture_select(_conn, _cursor, statement, _parameters, _context, _executemany):
        if statement.lstrip().upper().startswith("SELECT") and "points_history" in statement.lower():
            statements.append(statement)

    event.listen(points_db.bind, "before_cursor_execute", capture_select)
    try:
        grouped = web.fetch_points_history_grouped(
            points_db,
            ["wechat-1", "wechat-1", "wechat-2"],
        )
    finally:
        event.remove(points_db.bind, "before_cursor_execute", capture_select)

    # One latest window plus one pre-business-day baseline window, regardless
    # of how many historical rows exist.
    assert len(statements) == 2
    assert len(grouped["wechat-1"]) == 3
    assert len(grouped["wechat-2"]) == 1

    program_one_rows = [
        row for row in grouped["wechat-1"] if row.program_id == "program-1"
    ]
    assert [row.points for row in program_one_rows] == [30, 100]
    assert program_one_rows[0].id > program_one_rows[1].id

    program_two_rows = [
        row for row in grouped["wechat-1"] if row.program_id == "program-2"
    ]
    assert [row.points for row in program_two_rows] == [7]


def test_summary_contract_keeps_tie_breaker_diff_and_missing_programs(
    points_db,
    fixed_business_day,
):
    points_db.add_all([
        models.PointsHistory(
            program_id="program-1",
            wechat_id="wechat-1",
            points=100,
            cash=10,
            report_time=datetime(2025, 1, 1, 15, 0),
        ),
        models.PointsHistory(
            program_id="program-1",
            wechat_id="wechat-1",
            points=120,
            cash=12,
            report_time=datetime(2025, 1, 2, 1, 0),
        ),
        models.PointsHistory(
            program_id="program-1",
            wechat_id="wechat-1",
            points=140,
            cash=14,
            report_time=datetime(2025, 1, 2, 1, 0),
        ),
        # No pre-day row: the first report today has no comparable diff.
        models.PointsHistory(
            program_id="program-2",
            wechat_id="wechat-1",
            points=7,
            cash=2.5,
            report_time=datetime(2025, 1, 2, 2, 0),
        ),
        # Archived programs stay out of the active summary.
        models.PointsHistory(
            program_id="archived-program",
            wechat_id="wechat-1",
            points=999,
            cash=99,
            report_time=datetime(2025, 1, 2, 3, 0),
        ),
        # A history row whose program metadata is missing is still surfaced,
        # matching the existing "missing program" fallback behavior.
        models.PointsHistory(
            program_id="missing-program",
            wechat_id="wechat-1",
            points=5,
            cash=1,
            report_time=datetime(2025, 1, 2, 4, 0),
        ),
    ])
    points_db.commit()

    account = points_db.query(models.WechatAccount).filter_by(
        wechat_id="wechat-1",
    ).one()
    programs = points_db.query(models.MiniProgram).filter(
        models.MiniProgram.is_archived == 0,
    ).order_by(models.MiniProgram.id.asc()).all()
    archived_ids = {"archived-program"}

    summary = web.build_account_points_summary(
        points_db,
        account,
        programs,
        archived_program_ids=archived_ids,
        program_name_map={
            program.program_id: program.program_name
            for program in points_db.query(models.MiniProgram).all()
        },
    )
    items = {item["program_id"]: item for item in summary["points"]}

    assert items["program-1"]["points"] == 140
    assert items["program-1"]["cash"] == 14
    assert items["program-1"]["diff"] == 40
    assert items["program-1"]["cash_diff"] == 4
    assert items["program-2"]["points"] == 7
    assert items["program-2"]["cash"] == 2.5
    assert items["program-2"]["diff"] == 0
    assert items["program-2"]["cash_diff"] == 0
    assert items["missing-program"]["program_name"] == "missing-program"
    assert "archived-program" not in items

    assert summary["active_program_count"] == 2
    assert summary["active_app_count"] == 1


def test_summary_direct_path_reads_only_two_rows_per_pair(
    points_db,
    fixed_business_day,
):
    points_db.add_all([
        models.PointsHistory(
            program_id="program-1",
            wechat_id="wechat-1",
            points=index,
            report_time=datetime(2024, 1, 1) + timedelta(days=index),
        )
        for index in range(1, 101)
    ])
    points_db.commit()

    account = points_db.query(models.WechatAccount).filter_by(
        wechat_id="wechat-1",
    ).one()
    program = points_db.query(models.MiniProgram).filter_by(
        program_id="program-1",
    ).one()

    statements = []

    def capture_select(_conn, _cursor, statement, _parameters, _context, _executemany):
        if statement.lstrip().upper().startswith("SELECT") and "points_history" in statement.lower():
            statements.append(statement)

    event.listen(points_db.bind, "before_cursor_execute", capture_select)
    try:
        summary = web.build_account_points_summary(
            points_db,
            account,
            [program],
        )
    finally:
        event.remove(points_db.bind, "before_cursor_execute", capture_select)

    assert len(statements) == 2
    item = next(item for item in summary["points"] if item["program_id"] == "program-1")
    assert item["points"] == 100
    assert item["diff"] == 0
