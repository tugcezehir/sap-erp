import pandas as pd

STOCK_COLUMNS = [
    "stock_in_quality_inspection",
    "stock_in_transfer",
    "stock_in_posting",
    "stock_of_material_provided_to_vendor",
    "blocked_stock",
    "returns_stock",
]


def stock_by_location(stocks: pd.DataFrame, materials: pd.DataFrame) -> pd.DataFrame:
    df = stocks.merge(
        materials[["material_number", "material_type", "material_group"]],
        on="material_number",
        how="left",
    )
    df["total_stock"] = df[STOCK_COLUMNS].sum(axis=1)
    return df.sort_values(["plant", "storage_location", "material_number"]).reset_index(drop=True)


def stock_by_material(stocks: pd.DataFrame) -> pd.DataFrame:
    out = stocks.groupby("material_number", as_index=False)[STOCK_COLUMNS].sum()
    out["total_stock"] = out[STOCK_COLUMNS].sum(axis=1)
    return out


def stock_by_plant(stocks: pd.DataFrame) -> pd.DataFrame:
    out = stocks.groupby("plant", as_index=False)[STOCK_COLUMNS].sum()
    out["total_stock"] = out[STOCK_COLUMNS].sum(axis=1)
    return out


def stock_value(stocks: pd.DataFrame, po_items: pd.DataFrame) -> pd.DataFrame:
    prices = po_items.groupby("material_number")["net_price"].mean()
    out = stock_by_material(stocks)
    out["avg_price"] = out["material_number"].map(prices)
    out["stock_value"] = out["total_stock"] * out["avg_price"]
    return out
