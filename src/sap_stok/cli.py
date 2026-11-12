import argparse

import pandas as pd

from . import inspect_schema
from .loaders import load_all
from .movements import (
    monthly_summary,
    movement_list,
    net_movement_by_material,
    unknown_movement_types,
)
from .planning import reorder_parameters
from .reports import save_csv, save_excel
from .stock import stock_by_location, stock_by_material, stock_by_plant, stock_value

STATUS_ORDER = ["CRITICAL", "REORDER", "OK", "OVERSTOCK", "NO_DEMAND"]


def _show(df: pd.DataFrame, limit: int = 30) -> None:
    print(df.head(limit).to_string(index=False))
    if len(df) > limit:
        print(f"... toplam {len(df)} satır")


def _planning_table(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    df = reorder_parameters(data)
    df["status"] = pd.Categorical(df["status"], categories=STATUS_ORDER, ordered=True)
    df = df.sort_values(["status", "material_number"]).reset_index(drop=True)
    df["status"] = df["status"].astype(str)
    return df


def cmd_stock(data, args) -> None:
    print("\n-- Fabrika bazında stok --")
    _show(stock_by_plant(data["MaterialStocks"]))
    print("\n-- Depo bazında stok (ilk satırlar) --")
    _show(stock_by_location(data["MaterialStocks"], data["Materials"]), args.limit)
    print("\n-- Stok değeri (ilk satırlar) --")
    _show(stock_value(data["MaterialStocks"], data["PurchaseOrderItems"]), args.limit)


def cmd_movements(data, args) -> None:
    matdocs = data["MaterialDocuments"]
    unknown = unknown_movement_types(matdocs)
    if unknown:
        print(f"Uyarı: eşlemesi olmayan hareket tipleri: {unknown}")
    print("\n-- Hareket listesi --")
    _show(
        movement_list(matdocs, args.material, args.plant, args.start, args.end),
        args.limit,
    )
    print("\n-- Aylık özet --")
    _show(monthly_summary(matdocs), args.limit)


def cmd_planning(data, args) -> None:
    df = _planning_table(data)
    print(df["status"].value_counts().to_string())
    print()
    cols = [
        "material_number", "total_stock", "avg_daily_demand", "lead_time_days",
        "safety_stock", "reorder_point", "eoq", "status", "suggested_order_qty",
    ]
    _show(df[cols], args.limit)


def cmd_report(data, args) -> None:
    planning = _planning_table(data)
    sheets = {
        "Stok_Depo": stock_by_location(data["MaterialStocks"], data["Materials"]),
        "Stok_Malzeme": stock_by_material(data["MaterialStocks"]),
        "Stok_Deger": stock_value(data["MaterialStocks"], data["PurchaseOrderItems"]),
        "Hareketler": movement_list(data["MaterialDocuments"]),
        "Aylik_Ozet": monthly_summary(data["MaterialDocuments"]),
        "Net_Hareket": net_movement_by_material(data["MaterialDocuments"]),
        "Planlama": planning,
    }
    print(save_excel(sheets))
    print(save_csv(planning, "planlama.csv"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sap-stok")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("schema")

    p_stock = sub.add_parser("stock")
    p_stock.add_argument("--limit", type=int, default=30)

    p_mov = sub.add_parser("movements")
    p_mov.add_argument("--material", type=int)
    p_mov.add_argument("--plant")
    p_mov.add_argument("--start")
    p_mov.add_argument("--end")
    p_mov.add_argument("--limit", type=int, default=30)

    p_plan = sub.add_parser("planning")
    p_plan.add_argument("--limit", type=int, default=30)

    sub.add_parser("report")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    if args.command == "schema":
        inspect_schema.main()
        return
    data = load_all()
    handlers = {
        "stock": cmd_stock,
        "movements": cmd_movements,
        "planning": cmd_planning,
        "report": cmd_report,
    }
    handlers[args.command](data, args)
