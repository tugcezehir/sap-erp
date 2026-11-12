SAP_TABLES = {
    "Materials": "MARA",
    "MaterialStocks": "MARD",
    "PurchaseRequisitions": "EBAN",
    "PurchaseOrderDocuments": "EKKO",
    "PurchaseOrderItems": "EKPO",
    "GoodsReceiptsAndIssues": "EKBE",
    "MaterialDocuments": "MKPF/MSEG (MATDOC)",
    "SalesOrderDocuments": "VBAK",
    "SalesOrderItems": "VBAP",
    "SalesDocumentFlows": "VBFA",
    "OrderSuggestions": "PLAF",
}

MOVEMENT_TYPES = {
    "Goods Receipt": {"sap": "101", "sign": 1},
    "Goods Issue": {"sap": "201", "sign": -1},
}


def movement_sign(name) -> int:
    return MOVEMENT_TYPES.get(name, {}).get("sign", 0)


def movement_code(name) -> str:
    return MOVEMENT_TYPES.get(name, {}).get("sap", "")
