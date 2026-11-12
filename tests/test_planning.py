import pandas as pd
import pytest

from sap_stok.loaders import load_all
from sap_stok.planning import demand_stats, eoq, reorder_parameters, reorder_point, safety_stock


def test_eoq_formula():
    assert float(eoq(1800, 50, 2)) == pytest.approx(300.0)


def test_eoq_zero_holding_cost():
    assert float(eoq(1000, 50, 0)) == 0.0


def test_safety_stock_and_rop():
    ss = float(safety_stock(10, 4, 1.65))
    assert ss == pytest.approx(33.0)
    assert float(reorder_point(5, 4, ss)) == pytest.approx(53.0)


def test_demand_stats_handmade():
    docs = pd.DataFrame(
        {
            "sales_document_number": [1, 2],
            "document_date_in_document": pd.to_datetime(["2024-01-01", "2024-01-03"]),
        }
    )
    items = pd.DataFrame(
        {
            "sales_document_number": [1, 2],
            "item_number": [1, 1],
            "material_number": [7, 7],
            "plant": ["Plant1", "Plant1"],
            "order_quantity": [10.0, 20.0],
            "net_price": [1.0, 1.0],
        }
    )
    out = demand_stats(docs, items).iloc[0]
    assert out["avg_daily_demand"] == pytest.approx(10.0)
    assert out["std_daily_demand"] == pytest.approx(10.0)
    assert out["annual_demand"] == pytest.approx(3650.0)


def test_reorder_parameters(db_path):
    df = reorder_parameters(load_all(db_path))
    assert len(df) == 20
    assert set(df["status"]) <= {"CRITICAL", "REORDER", "OK", "OVERSTOCK", "NO_DEMAND"}
    assert not df[["eoq", "safety_stock", "reorder_point", "lead_time_days"]].isna().any().any()
    assert (df["suggested_order_qty"] >= 0).all()
