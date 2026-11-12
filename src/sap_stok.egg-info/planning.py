import numpy as np
import pandas as pd

from .config import DEFAULT_LEAD_TIME_DAYS, HOLDING_RATE, ORDER_COST, SERVICE_LEVEL_Z
from .stock import STOCK_COLUMNS


def eoq(annual_demand, order_cost, holding_cost):
    demand = np.asarray(annual_demand, dtype=float)
    holding = np.asarray(holding_cost, dtype=float)
    safe_holding = np.where(holding > 0, holding, np.nan)
    result = np.sqrt(2.0 * demand * order_cost / safe_holding)
    return np.nan_to_num(result, nan=0.0)


def safety_stock(std_daily, lead_time_days, z=SERVICE_LEVEL_Z):
    return z * np.asarray(std_daily, dtype=float) * np.sqrt(np.asarray(lead_time_days, dtype=float))


def reorder_point(avg_daily, lead_time_days, safety):
    return (
        np.asarray(avg_daily, dtype=float) * np.asarray(lead_time_days, dtype=float)
        + np.asarray(safety, dtype=float)
    )


def demand_stats(sales_docs: pd.DataFrame, sales_items: pd.DataFrame) -> pd.DataFrame:
    cols = ["material_number", "annual_demand", "avg_daily_demand", "std_daily_demand"]
    df = sales_items.merge(
        sales_docs[["sales_document_number", "document_date_in_document"]],
        on="sales_document_number",
        how="inner",
    ).dropna(subset=["document_date_in_document"])
    if df.empty:
        return pd.DataFrame(columns=cols)
    daily = df.pivot_table(
        index="document_date_in_document",
        columns="material_number",
        values="order_quantity",
        aggfunc="sum",
    )
    full_range = pd.date_range(daily.index.min(), daily.index.max(), freq="D")
    daily = daily.reindex(full_range).fillna(0.0)
    out = pd.DataFrame(
        {
            "avg_daily_demand": daily.mean(),
            "std_daily_demand": daily.std(ddof=1).fillna(0.0),
        }
    )
    out["annual_demand"] = out["avg_daily_demand"] * 365
    out.index.name = "material_number"
    return out.reset_index()[cols]


def lead_times(requisitions: pd.DataFrame, po_items: pd.DataFrame) -> pd.DataFrame:
    merged = requisitions.merge(
        po_items[["purchase_order_number", "purchase_order_item_number", "material_number"]],
        left_on=["purchase_document_number", "item_number_of_purchasing_document"],
        right_on=["purchase_order_number", "purchase_order_item_number"],
        how="inner",
    )
    return (
        merged.groupby("material_number", as_index=False)["planned_delivery_time"]
        .mean()
        .rename(columns={"planned_delivery_time": "lead_time_days"})
    )


def avg_prices(po_items: pd.DataFrame) -> pd.DataFrame:
    return (
        po_items.groupby("material_number", as_index=False)["net_price"]
        .mean()
        .rename(columns={"net_price": "avg_price"})
    )


def reorder_parameters(
    data: dict[str, pd.DataFrame],
    order_cost: float = ORDER_COST,
    holding_rate: float = HOLDING_RATE,
    z: float = SERVICE_LEVEL_Z,
    default_lead_time: float = DEFAULT_LEAD_TIME_DAYS,
) -> pd.DataFrame:
    materials = data["Materials"][["material_number", "material_type", "material_group"]]
    demand = demand_stats(data["SalesOrderDocuments"], data["SalesOrderItems"])
    lead = lead_times(data["PurchaseRequisitions"], data["PurchaseOrderItems"])
    prices = avg_prices(data["PurchaseOrderItems"])

    stocks = data["MaterialStocks"].copy()
    stocks["total_stock"] = stocks[STOCK_COLUMNS].sum(axis=1)
    stock = stocks.groupby("material_number", as_index=False)["total_stock"].sum()

    df = (
        materials.merge(demand, on="material_number", how="left")
        .merge(lead, on="material_number", how="left")
        .merge(prices, on="material_number", how="left")
        .merge(stock, on="material_number", how="left")
    )

    for col in ["annual_demand", "avg_daily_demand", "std_daily_demand", "total_stock"]:
        df[col] = df[col].fillna(0.0)
    df["lead_time_days"] = df["lead_time_days"].fillna(default_lead_time)
    fallback_price = df["avg_price"].mean()
    if pd.isna(fallback_price):
        fallback_price = 1.0
    df["avg_price"] = df["avg_price"].fillna(fallback_price)

    df["holding_cost"] = df["avg_price"] * holding_rate
    df["eoq"] = eoq(df["annual_demand"], order_cost, df["holding_cost"])
    df["safety_stock"] = safety_stock(df["std_daily_demand"], df["lead_time_days"], z)
    df["reorder_point"] = reorder_point(
        df["avg_daily_demand"], df["lead_time_days"], df["safety_stock"]
    )
    df["overstock_level"] = df["safety_stock"] + df["eoq"]

    conditions = [
        df["avg_daily_demand"] == 0,
        df["total_stock"] <= df["safety_stock"],
        df["total_stock"] <= df["reorder_point"],
        df["total_stock"] > df["overstock_level"],
    ]
    df["status"] = np.select(
        conditions, ["NO_DEMAND", "CRITICAL", "REORDER", "OVERSTOCK"], default="OK"
    )

    need = df["reorder_point"] + df["eoq"] - df["total_stock"]
    df["suggested_order_qty"] = np.where(
        df["status"].isin(["CRITICAL", "REORDER"]),
        np.ceil(np.clip(need, 0, None)),
        0.0,
    )
    return df.round(2)
