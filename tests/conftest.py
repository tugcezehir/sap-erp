import sqlite3

import numpy as np
import pandas as pd
import pytest

SCHEMA = """
CREATE TABLE Materials (
    material_number INTEGER PRIMARY KEY, material_type TEXT, industry_sector TEXT,
    material_group TEXT, valuation_class TEXT, gross_weight REAL, net_weight REAL,
    weight_unit TEXT, volume REAL, volume_unit TEXT, transport_group TEXT);
CREATE TABLE MaterialStocks (
    client TEXT, material_number INTEGER, plant TEXT, storage_location TEXT,
    stock_in_quality_inspection REAL, stock_in_transfer REAL, stock_in_posting REAL,
    stock_of_material_provided_to_vendor REAL, blocked_stock REAL, returns_stock REAL,
    PRIMARY KEY (material_number, plant, storage_location));
CREATE TABLE MaterialDocuments (
    client TEXT, material_document_number INTEGER, material_document_year INTEGER,
    line_item INTEGER, material_number INTEGER, plant TEXT, storage_location TEXT,
    vendors_account_number INTEGER, customer_number INTEGER, movement_type TEXT,
    receiving_plant TEXT, quantity REAL, posting_date_in_the_document DATE,
    PRIMARY KEY (material_document_number, material_document_year, line_item));
CREATE TABLE GoodsReceiptsAndIssues (
    client TEXT, purchase_document_number INTEGER, line_item_in_purchase_document INTEGER,
    sequential_number_of_account_assignment INTEGER, movement_type TEXT, fiscal_year INTEGER,
    document_number INTEGER, accounting_document_line INTEGER, material_number INTEGER,
    plant TEXT, reference_document_number INTEGER, document_date_in_document DATE,
    posting_date_in_the_document DATE, date_of_the_posting_in_the_document DATE,
    time_of_the_posting_in_the_document TEXT, quantity REAL);
CREATE TABLE OrderSuggestions (
    order_number INTEGER, order_position INTEGER, article_number INTEGER,
    order_quantity REAL, date DATE, order_date DATE, delivery_date DATE, plant TEXT,
    PRIMARY KEY (order_number, order_position));
CREATE TABLE PurchaseOrderDocuments (
    purchase_document_number INTEGER PRIMARY KEY, record_creation_date DATE,
    account_number_of_vendor INTEGER, purchase_order_date DATE,
    purchasing_document_category TEXT, purchasing_document_type TEXT,
    blocking_indicator BOOLEAN);
CREATE TABLE PurchaseOrderItems (
    purchase_order_number INTEGER, purchase_order_item_number INTEGER,
    material_number INTEGER, plant TEXT, quantity REAL, change_date DATE, net_price REAL,
    PRIMARY KEY (purchase_order_number, purchase_order_item_number));
CREATE TABLE PurchaseRequisitions (
    client TEXT, purchase_document_number INTEGER, item_number_of_purchasing_document INTEGER,
    purchase_requisition_number INTEGER PRIMARY KEY, purchase_requisition_item INTEGER,
    purchase_requisition_date DATE, document_type TEXT, purchasing_document_category TEXT,
    planned_delivery_time INTEGER, latest_possible_goods_receipt DATE, quantity REAL,
    unit_of_measure TEXT);
CREATE TABLE SalesDocumentFlows (
    client TEXT, sales_document INTEGER, sales_document_item INTEGER,
    subsequent_sales_document INTEGER, subsequent_sales_document_item INTEGER,
    document_category_of_subsequent_document TEXT,
    document_category_of_preceding_document TEXT, document_date DATE,
    PRIMARY KEY (sales_document, sales_document_item, subsequent_sales_document,
                 subsequent_sales_document_item));
CREATE TABLE SalesOrderDocuments (
    sales_document_number INTEGER PRIMARY KEY, document_creation_date DATE,
    customer_number INTEGER, document_date_in_document DATE, sales_document_type TEXT,
    order_type TEXT, order_reason TEXT);
CREATE TABLE SalesOrderItems (
    sales_document_number INTEGER, item_number INTEGER, material_number INTEGER,
    plant TEXT, order_quantity REAL, net_price REAL,
    PRIMARY KEY (sales_document_number, item_number));
"""

N_MATERIALS = 20


def _dates(rng, n, start="2024-01-01", days=180):
    base = pd.Timestamp(start)
    return [(base + pd.Timedelta(days=int(d))).strftime("%Y-%m-%d") for d in rng.integers(0, days, n)]


@pytest.fixture(scope="session")
def db_path(tmp_path_factory):
    path = tmp_path_factory.mktemp("db") / "inventory_management.db"
    rng = np.random.default_rng(42)
    con = sqlite3.connect(path)
    con.executescript(SCHEMA)

    mats = np.arange(1, N_MATERIALS + 1)
    pd.DataFrame(
        {
            "material_number": mats,
            "material_type": rng.choice(["RAW", "SEMIFINISHED", "FINISHED"], N_MATERIALS),
            "industry_sector": "Electronics",
            "material_group": rng.choice(["GroupA", "GroupB", "GroupC"], N_MATERIALS),
            "valuation_class": "ValClass1",
            "gross_weight": 1.0,
            "net_weight": 1.0,
            "weight_unit": "kg",
            "volume": 1.0,
            "volume_unit": "m3",
            "transport_group": "TG1",
        }
    ).to_sql("Materials", con, if_exists="append", index=False)

    stock_cols = [
        "stock_in_quality_inspection", "stock_in_transfer", "stock_in_posting",
        "stock_of_material_provided_to_vendor", "blocked_stock", "returns_stock",
    ]
    stocks = pd.DataFrame(
        {"client": "Client1", "material_number": mats, "plant": "Plant1", "storage_location": "Storage1"}
    )
    for col in stock_cols:
        stocks[col] = rng.uniform(0, 100, N_MATERIALS).round(2)
    stocks.to_sql("MaterialStocks", con, if_exists="append", index=False)

    n_docs = 60
    pd.DataFrame(
        {
            "sales_document_number": np.arange(1, n_docs + 1),
            "document_creation_date": _dates(rng, n_docs),
            "customer_number": rng.integers(1, 20, n_docs),
            "document_date_in_document": _dates(rng, n_docs),
            "sales_document_type": "TypeA",
            "order_type": "Standard",
            "order_reason": "Promotion",
        }
    ).to_sql("SalesOrderDocuments", con, if_exists="append", index=False)

    items = pd.DataFrame(
        [(d, i, int(rng.choice(mats)), "Plant1", float(rng.integers(5, 100)), 100.0)
         for d in range(1, n_docs + 1) for i in (1, 2, 3)],
        columns=["sales_document_number", "item_number", "material_number", "plant",
                 "order_quantity", "net_price"],
    )
    items.to_sql("SalesOrderItems", con, if_exists="append", index=False)

    n_po = 30
    pd.DataFrame(
        {
            "purchase_document_number": np.arange(1, n_po + 1),
            "record_creation_date": _dates(rng, n_po),
            "account_number_of_vendor": rng.integers(1, 10, n_po),
            "purchase_order_date": _dates(rng, n_po),
            "purchasing_document_category": "Standard",
            "purchasing_document_type": "POTypeA",
            "blocking_indicator": 0,
        }
    ).to_sql("PurchaseOrderDocuments", con, if_exists="append", index=False)

    po_items = pd.DataFrame(
        [(p, i, int(rng.choice(mats)), "Plant1", float(rng.integers(10, 200)),
          "2024-02-01", round(float(rng.uniform(50, 500)), 2))
         for p in range(1, n_po + 1) for i in (1, 2)],
        columns=["purchase_order_number", "purchase_order_item_number", "material_number",
                 "plant", "quantity", "change_date", "net_price"],
    )
    po_items.to_sql("PurchaseOrderItems", con, if_exists="append", index=False)

    pd.DataFrame(
        {
            "client": "Client1",
            "purchase_document_number": po_items["purchase_order_number"],
            "item_number_of_purchasing_document": po_items["purchase_order_item_number"],
            "purchase_requisition_number": np.arange(1, len(po_items) + 1),
            "purchase_requisition_item": 1,
            "purchase_requisition_date": "2024-01-15",
            "document_type": "TypeA",
            "purchasing_document_category": "Standard",
            "planned_delivery_time": rng.integers(5, 30, len(po_items)),
            "latest_possible_goods_receipt": "2024-02-15",
            "quantity": 10.0,
            "unit_of_measure": "PCS",
        }
    ).to_sql("PurchaseRequisitions", con, if_exists="append", index=False)

    n_md = 80
    pd.DataFrame(
        {
            "client": "Client1",
            "material_document_number": 1000 + np.arange(n_md),
            "material_document_year": 2024,
            "line_item": 1,
            "material_number": rng.choice(mats, n_md),
            "plant": rng.choice(["Plant1", "Plant2"], n_md),
            "storage_location": "Storage1",
            "vendors_account_number": 1,
            "customer_number": 1,
            "movement_type": rng.choice(["Goods Receipt", "Goods Issue"], n_md),
            "receiving_plant": "Plant1",
            "quantity": rng.integers(1, 80, n_md).astype(float),
            "posting_date_in_the_document": _dates(rng, n_md),
        }
    ).to_sql("MaterialDocuments", con, if_exists="append", index=False)

    con.commit()
    con.close()
    return path
