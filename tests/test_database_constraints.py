import os
from pathlib import Path
import subprocess
import sys


def test_sqlite_foreign_keys_are_enabled_and_points_history_constraints_work(tmp_path):
    database_path = tmp_path / "constraints.db"
    repository_root = Path(__file__).resolve().parents[1]
    script = """
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app import database, models


database.Base.metadata.create_all(database.engine)

with database.engine.connect() as connection:
    assert connection.execute(text("PRAGMA foreign_keys")).scalar_one() == 1

session = database.SessionLocal()
try:
    session.add_all([
        models.MiniProgram(program_id="program-1", program_name="程序一"),
        models.WechatAccount(wechat_id="wechat-1", nickname="账号一"),
    ])
    session.flush()
    session.add(
        models.PointsHistory(
            program_id="program-1",
            wechat_id="wechat-1",
            points=100,
        )
    )
    session.commit()

    session.add(
        models.PointsHistory(
            program_id="program-1",
            wechat_id="missing-wechat",
            points=1,
        )
    )
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
    else:
        raise AssertionError("PointsHistory accepted a missing WeChat account")

    assert session.query(models.PointsHistory).count() == 1
finally:
    session.close()
    database.engine.dispose()
"""
    environment = os.environ.copy()
    environment["DATABASE_URL"] = f"sqlite:///{database_path.as_posix()}"

    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=repository_root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
