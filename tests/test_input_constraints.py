import math

import pytest
from pydantic import ValidationError

from app.schemas import (
    MAX_POINTS_ROWS_PER_REPORT,
    MAX_PROGRAMS_PER_ACCOUNT,
    MAX_PRODUCTS_PER_STOCK_REPORT,
    MAX_WECHAT_ACCOUNTS_PER_REPORT,
    PointsReportRequest,
    ProductData,
    StockReportRequest,
)
from app.schemas_stock import ProductCreateUpdate


def valid_points_payload(**overrides):
    payload = {
        "script_id": "legacy-script",
        "data": {
            "wechat_accounts": [
                {
                    "wechat_id": "wxid_001",
                    "points_data": [
                        {
                            "program_id": "program_001",
                            "current_points": 100,
                        }
                    ],
                }
            ]
        },
    }
    payload.update(overrides)
    return payload


def test_legacy_points_only_and_stock_points_only_payloads_remain_valid():
    points = PointsReportRequest.model_validate(valid_points_payload())
    assert points.data.wechat_accounts[0].points_data[0].current_points == 100
    assert points.data.wechat_accounts[0].points_data[0].current_cash is None

    stock = StockReportRequest.model_validate(
        {
            "program_id": "program_001",
            "products": [{"product_name": "纯积分商品", "points": "300", "stock": "5"}],
        }
    )
    assert stock.products[0].product_id is None
    assert stock.products[0].points == 300
    assert stock.products[0].stock == 5


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("current_points", -1),
        ("current_cash", -0.01),
        ("current_points", math.inf),
        ("current_cash", "nan"),
    ],
)
def test_point_balances_reject_negative_and_non_finite_values(field, value):
    payload = valid_points_payload()
    payload["data"]["wechat_accounts"][0]["points_data"][0][field] = value
    with pytest.raises(ValidationError):
        PointsReportRequest.model_validate(payload)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("stock", -1),
        ("points", -1),
        ("cash", -0.01),
        ("cash", math.inf),
        ("cash", "-inf"),
        ("points", float("nan")),
        ("stock", True),
        ("cash", False),
    ],
)
def test_stock_report_rejects_negative_and_non_finite_values(field, value):
    payload = {"program_id": "program_001", "products": [{"product_name": "商品"}]}
    payload["products"][0][field] = value
    with pytest.raises(ValidationError):
        StockReportRequest.model_validate(payload)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("stock", -1),
        ("points", -1),
        ("cash", -0.01),
        ("cash", math.inf),
        ("stock", True),
        ("points", True),
        ("cash", False),
    ],
)
def test_ui_product_schema_rejects_invalid_numeric_values(field, value):
    with pytest.raises(ValidationError):
        ProductCreateUpdate(program_id="program", product_name="商品", **{field: value})


def test_optional_blank_product_id_keeps_legacy_fallback_semantics():
    report = StockReportRequest.model_validate(
        {
            "program_id": " program_001 ",
            "products": [{"product_id": "  ", "product_name": " 商品 ", "cash": ""}],
        }
    )
    assert report.program_id == "program_001"
    assert report.products[0].product_id is None
    assert report.products[0].product_name == "商品"
    assert report.products[0].cash == 0


@pytest.mark.parametrize(
    "payload",
    [
        valid_points_payload(script_id="   "),
        {
            "script_id": "script",
            "data": {
                "wechat_accounts": [
                    {"wechat_id": "  ", "points_data": [{"program_id": "p", "current_points": 1}]}
                ]
            },
        },
        {
            "script_id": "script",
            "data": {
                "wechat_accounts": [
                    {"wechat_id": "wx", "points_data": [{"program_id": "  ", "current_points": 1}]}
                ]
            },
        },
        {"program_id": "program", "products": [{"product_name": "  "}]},
    ],
)
def test_required_identifiers_and_names_cannot_be_blank(payload):
    model = PointsReportRequest if "data" in payload else StockReportRequest
    with pytest.raises(ValidationError):
        model.model_validate(payload)


def test_string_lengths_follow_persistence_contract():
    too_long_program_id = valid_points_payload()
    too_long_program_id["data"]["wechat_accounts"][0]["points_data"][0]["program_id"] = "p" * 101
    with pytest.raises(ValidationError):
        PointsReportRequest.model_validate(too_long_program_id)

    too_long_name = {
        "program_id": "program",
        "products": [{"product_name": "x" * 201}],
    }
    with pytest.raises(ValidationError):
        StockReportRequest.model_validate(too_long_name)

    with pytest.raises(ValidationError):
        ProductCreateUpdate(
            program_id="program",
            product_name="商品",
            product_id="p" * 101,
        )


def test_report_batch_limits_are_enforced_without_rejecting_empty_snapshots():
    too_many_accounts = valid_points_payload()
    too_many_accounts["data"]["wechat_accounts"] = [
        {"wechat_id": f"wx_{index}", "points_data": []}
        for index in range(MAX_WECHAT_ACCOUNTS_PER_REPORT + 1)
    ]
    with pytest.raises(ValidationError):
        PointsReportRequest.model_validate(too_many_accounts)

    too_many_programs = valid_points_payload()
    too_many_programs["data"]["wechat_accounts"][0]["points_data"] = [
        {"program_id": f"program_{index}", "current_points": 1}
        for index in range(MAX_PROGRAMS_PER_ACCOUNT + 1)
    ]
    with pytest.raises(ValidationError):
        PointsReportRequest.model_validate(too_many_programs)

    too_many_rows = valid_points_payload()
    # Stay below both per-list limits while exceeding the request-level total.
    accounts_needed = MAX_POINTS_ROWS_PER_REPORT // MAX_PROGRAMS_PER_ACCOUNT + 1
    too_many_rows["data"]["wechat_accounts"] = [
        {
            "wechat_id": f"wx_{account_index}",
            "points_data": [
                {
                    "program_id": f"program_{account_index}_{program_index}",
                    "current_points": 1,
                }
                for program_index in range(MAX_PROGRAMS_PER_ACCOUNT)
            ],
        }
        for account_index in range(accounts_needed)
    ]
    with pytest.raises(ValidationError):
        PointsReportRequest.model_validate(too_many_rows)

    empty_stock = StockReportRequest.model_validate({"program_id": "program", "products": []})
    assert empty_stock.products == []

    too_many_products = {
        "program_id": "program",
        "products": [
            {"product_name": f"product_{index}"}
            for index in range(MAX_PRODUCTS_PER_STOCK_REPORT + 1)
        ],
    }
    with pytest.raises(ValidationError):
        StockReportRequest.model_validate(too_many_products)
