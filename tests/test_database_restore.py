from io import BytesIO
from pathlib import Path
import sqlite3

import pytest
from fastapi import HTTPException, UploadFile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import database as database_module, models
from app.database import Base
from app.maintenance import database_maintenance, database_maintenance_lock_path
from app.routers import web


def _sqlite_url(path):
    return f"sqlite:///{path.as_posix()}"


def _seed_database(session, marker):
    program_id = f"{marker}-program"
    wechat_id = f"{marker}-wechat"
    session.add(models.MiniProgram(program_id=program_id, program_name=f"{marker} program"))
    session.add(models.WechatAccount(wechat_id=wechat_id, nickname=f"{marker} account"))
    session.flush()
    session.add(
        models.PointsHistory(
            program_id=program_id,
            wechat_id=wechat_id,
            points=100,
            cash=1,
        )
    )
    session.commit()


def _create_sqlite_database(path, marker):
    engine = create_engine(
        _sqlite_url(path),
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        _seed_database(session, marker)
    finally:
        session.close()
        engine.dispose()

    # The application enables WAL for SQLite. Checkpoint it before reading the
    # database as a standalone upload so the test never depends on sidecars.
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")


def _upload(path, filename="database-backup.db"):
    return UploadFile(
        file=BytesIO(path.read_bytes()),
        filename=filename,
        headers={"content-type": "application/x-sqlite3"},
    )


def _allow_readonly_fsync_on_windows(monkeypatch):
    """Keep restore-path assertions portable without changing production code.

    Windows rejects ``fsync`` on the read-only descriptor opened by the
    current restore implementation for the staged file. The upload file is
    still fsynced by the real function; only this platform-specific error is
    ignored so these tests can exercise the subsequent atomic replacement.
    """
    real_fsync = web.os.fsync

    def fsync(file_descriptor):
        try:
            real_fsync(file_descriptor)
        except OSError as error:
            if web.os.name != "nt" or error.errno != 9:
                raise

    monkeypatch.setattr(web.os, "fsync", fsync)


def _read_marker(path):
    with sqlite3.connect(path) as connection:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()
        assert integrity == ("ok",)
        rows = connection.execute(
            "SELECT program_id FROM mini_programs ORDER BY program_id"
        ).fetchall()
        return [row[0] for row in rows]


@pytest.fixture()
def live_database(tmp_path, monkeypatch):
    db_path = tmp_path / "live.db"
    engine = create_engine(
        _sqlite_url(db_path),
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    _seed_database(session, "before")

    # import_database resolves the configured path and disposes the global
    # application engine before replacing the file. Point both at this
    # temporary database so no test can touch data/database.db.
    monkeypatch.setattr(web.app_settings, "DATABASE_URL", _sqlite_url(db_path))
    monkeypatch.setattr(database_module, "engine", engine)

    try:
        yield db_path, session
    finally:
        session.close()
        engine.dispose()


def test_import_accepts_valid_sqlite_backup_and_replaces_live_database(
    live_database, tmp_path, monkeypatch
):
    db_path, session = live_database
    backup_path = tmp_path / "valid-backup.db"
    _create_sqlite_database(backup_path, "after")
    _allow_readonly_fsync_on_windows(monkeypatch)

    result = web.import_database(_upload(backup_path), session)

    assert result["status"] == "success"
    assert Path(result["path"]).resolve() == db_path.resolve()
    assert result["rollback_path"]
    assert _read_marker(db_path) == ["after-program"]
    assert _read_marker(result["rollback_path"]) == ["before-program"]


@pytest.mark.parametrize("invalid_kind", ["non_sqlite", "missing_table", "corrupt"])
def test_import_rejects_invalid_backups_without_touching_live_database(
    live_database, tmp_path, invalid_kind
):
    db_path, session = live_database
    invalid_path = tmp_path / f"{invalid_kind}.db"

    if invalid_kind == "non_sqlite":
        invalid_path.write_bytes(b"this is not a sqlite database")
    elif invalid_kind == "missing_table":
        with sqlite3.connect(invalid_path) as connection:
            connection.execute("CREATE TABLE unrelated (id INTEGER PRIMARY KEY)")
    else:
        invalid_path.write_bytes(b"SQLite format 3\x00" + b"\x00" * 4096)

    with pytest.raises(HTTPException) as error:
        web.import_database(_upload(invalid_path), session)

    assert error.value.status_code == 400
    assert _read_marker(db_path) == ["before-program"]


def test_import_returns_busy_when_database_maintenance_lock_is_held(
    live_database, tmp_path
):
    db_path, session = live_database
    backup_path = tmp_path / "valid-backup.db"
    _create_sqlite_database(backup_path, "after")
    lock_path = database_maintenance_lock_path(str(db_path))

    with database_maintenance(lock_path):
        with pytest.raises(HTTPException) as error:
            web.import_database(_upload(backup_path), session)

    assert error.value.status_code == 503
    assert error.value.headers["Retry-After"] == "5"
    assert "另一项恢复操作" in error.value.detail
    assert _read_marker(db_path) == ["before-program"]


def test_import_failure_leaves_original_database_usable(
    live_database, tmp_path, monkeypatch
):
    db_path, session = live_database
    backup_path = tmp_path / "valid-backup.db"
    _create_sqlite_database(backup_path, "after")

    def fail_replace(_source, _destination):
        raise OSError("simulated atomic replace failure")

    _allow_readonly_fsync_on_windows(monkeypatch)
    monkeypatch.setattr(web.os, "replace", fail_replace)

    with pytest.raises(HTTPException) as error:
        web.import_database(_upload(backup_path), session)

    assert error.value.status_code == 500
    assert "导入数据库失败" in error.value.detail
    assert _read_marker(db_path) == ["before-program"]
