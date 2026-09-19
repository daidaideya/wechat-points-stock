import pytest
from pydantic import ValidationError

from app.money import normalize_cash_amount
from app.schemas import PointsReportRequest, ProductData
from app.schemas_stock import ProductCreateUpdate


def points_payload(cash):
    return {
        "script_id": "money-test",
        "data": {
            "wechat_accounts": [
                {
                    "wechat_id": "wx-money",
                    "points_data": [
                        {
                            "program_id": "program-money",
                            "current_cash": cash,
                        }
                    ],
                }
            ]
        },
    }


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("1.005", 1.01),
        ("2.675", 2.68),
        (0.1, 0.1),
        (None, None),
    ],
)
def test_cash_normalization_uses_decimal_half_up_and_optional_defaults(value, expected):
    assert normalize_cash_amount(value) == expected
    assert normalize_cash_amount(value, default=0.0) == (0.0 if value is None else expected)


@pytest.mark.parametrize("value", [True, "", "not-a-number", "NaN", -0.01])
def test_cash_normalization_rejects_invalid_values(value):
    if value == "":
        assert normalize_cash_amount(value, default=0.0) == 0.0
        return
    with pytest.raises(ValueError):
        normalize_cash_amount(value)


def test_cash_schema_boundaries_share_two_decimal_rule():
    points = PointsReportRequest.model_validate(points_payload("1.005"))
    assert points.data.wechat_accounts[0].points_data[0].current_cash == 1.01

    product = ProductData.model_validate({"product_name": "库存商品", "cash": "2.675"})
    assert product.cash == 2.68

    ui_product = ProductCreateUpdate(
        program_id="program-money",
        product_name="库存商品",
        cash="3.335",
    )
    assert ui_product.cash == 3.34

    with pytest.raises(ValidationError):
        PointsReportRequest.model_validate(points_payload("-0.001"))
