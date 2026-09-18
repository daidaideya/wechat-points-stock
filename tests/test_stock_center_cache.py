from datetime import datetime

import pytest
from fastapi import Request, Response
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.database import Base
from app.routers import stock


def make_request(if_none_match=None):
    headers = []
    if if_none_match:
        headers.append((b"if-none-match", if_none_match.encode("ascii")))
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/stock/center",
            "headers": headers,
            "query_string": b"",
            "scheme": "http",
            "server": ("testserver", 80),
            "client": ("testclient", 1234),
        }
    )


@pytest.fixture()
def stock_center_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    db = session_factory()

    program = models.MiniProgram(
        program_id="program-cache",
        program_name="缓存测试小程序",
        tags='["热门"]',
    )
    account = models.WechatAccount(wechat_id="wechat-cache", nickname="缓存测试账号")
    db.add_all([program, account])
    db.flush()
    db.add(models.PointsHistory(
        program_id=program.program_id,
        wechat_id=account.wechat_id,
        points=100,
        cash=5,
        report_time=datetime(2025, 1, 1),
    ))
    db.add(models.Product(
        program_id=program.program_id,
        product_id="cache-product",
        product_name="缓存商品",
        points=50,
        cash=0,
        stock=10,
        is_hidden=0,
        is_unlisted=0,
    ))
    db.commit()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def call_center(db, *, request=None):
    response = Response()
    result = stock.get_stock_center(
        page=1,
        size=20,
        q=None,
        tag=None,
        status="all",
        price_mode="all",
        cash_max=None,
        db=db,
        request=request,
        response=response,
    )
    return result, response


def test_stock_center_sets_etag_and_returns_304(stock_center_db):
    payload, first_response = call_center(stock_center_db)

    assert set(payload) == {
        "page",
        "size",
        "total",
        "items",
        "summary",
        "available_tags",
        "hidden_total",
        "off_shelf_total",
    }
    etag = first_response.headers["etag"]
    assert etag.startswith('"stock-center-revision-')
    assert first_response.headers["cache-control"] == "private, max-age=0, must-revalidate"

    not_modified, cached_response = call_center(
        stock_center_db,
        request=make_request(etag),
    )

    assert isinstance(not_modified, Response)
    assert not_modified.status_code == 304
    assert not_modified.headers["etag"] == etag
    assert not_modified.headers["cache-control"] == "private, max-age=0, must-revalidate"
    assert "etag" not in cached_response.headers


def test_stock_center_etag_changes_for_source_data_mutations(stock_center_db):
    _payload, response = call_center(stock_center_db)
    previous_etag = response.headers["etag"]

    product = stock_center_db.query(models.Product).one()
    product.stock = 3
    stock_center_db.commit()
    _payload, response = call_center(stock_center_db)
    assert response.headers["etag"] != previous_etag
    previous_etag = response.headers["etag"]

    point_history = stock_center_db.query(models.PointsHistory).one()
    point_history.points = 10
    stock_center_db.commit()
    _payload, response = call_center(stock_center_db)
    assert response.headers["etag"] != previous_etag
    previous_etag = response.headers["etag"]

    stock_center_db.add(models.StockHistory(
        program_id=product.program_id,
        product_id=product.product_id,
        old_stock=10,
        new_stock=3,
        change_time=datetime(2025, 1, 2),
    ))
    stock_center_db.commit()
    _payload, response = call_center(stock_center_db)
    assert response.headers["etag"] != previous_etag
    previous_etag = response.headers["etag"]

    program = stock_center_db.query(models.MiniProgram).one()
    program.tags = '["更新后的标签"]'
    stock_center_db.commit()
    _payload, response = call_center(stock_center_db)
    assert response.headers["etag"] != previous_etag
    previous_etag = response.headers["etag"]

    product.is_hidden = 1
    product.hidden_at = datetime(2025, 1, 2)
    stock_center_db.commit()
    _payload, response = call_center(stock_center_db)
    assert response.headers["etag"] != previous_etag
    previous_etag = response.headers["etag"]

    product.is_hidden = 0
    product.hidden_at = None
    product.is_unlisted = 1
    product.unlisted_at = datetime(2025, 1, 3)
    stock_center_db.commit()
    _payload, response = call_center(stock_center_db)
    assert response.headers["etag"] != previous_etag
    previous_etag = response.headers["etag"]

    product.is_unlisted = 0
    product.unlisted_at = None
    product.product_name = "改名后的缓存商品"
    stock_center_db.commit()
    _payload, response = call_center(stock_center_db)
    assert response.headers["etag"] != previous_etag
    previous_etag = response.headers["etag"]

    stock_center_db.add(models.Product(
        program_id=product.program_id,
        product_id="new-cache-product",
        product_name="新增缓存商品",
        points=20,
        cash=0,
        stock=1,
        is_hidden=0,
        is_unlisted=0,
    ))
    stock_center_db.commit()
    _payload, response = call_center(stock_center_db)
    assert response.headers["etag"] != previous_etag
    previous_etag = response.headers["etag"]

    stock_center_db.delete(product)
    stock_center_db.commit()
    _payload, response = call_center(stock_center_db)
    assert response.headers["etag"] != previous_etag


def test_stock_center_filter_parameters_are_isolated(stock_center_db):
    _payload, all_response = call_center(stock_center_db)
    all_etag = all_response.headers["etag"]

    filtered_response = Response()
    filtered_payload = stock.get_stock_center(
        page=1,
        size=20,
        q="不存在的商品",
        tag=None,
        status="all",
        price_mode="all",
        cash_max=None,
        db=stock_center_db,
        request=make_request(all_etag),
        response=filtered_response,
    )

    assert not isinstance(filtered_payload, Response)
    assert filtered_payload["total"] == 0
    assert filtered_response.status_code == 200
    assert filtered_response.headers["etag"] != all_etag


def test_stock_center_wildcard_and_weak_etag_match(stock_center_db):
    _payload, response = call_center(stock_center_db)
    etag = response.headers["etag"]

    weak_304, _ = call_center(
        stock_center_db,
        request=make_request(f"W/{etag}"),
    )
    wildcard_304, _ = call_center(
        stock_center_db,
        request=make_request("*"),
    )

    assert isinstance(weak_304, Response)
    assert weak_304.status_code == 304
    assert isinstance(wildcard_304, Response)
    assert wildcard_304.status_code == 304
