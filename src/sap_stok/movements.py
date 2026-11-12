import pandas as pd

from .sap_mapping import MOVEMENT_TYPES, movement_code, movement_sign

DATE_COL = "posting_date_in_the_document"


def movement_list(
    matdocs: pd.DataFrame,
    material: int | None = None,
    plant: str | None = None,
    start: str | None = None,
    end: str | None = None,
) -> pd.DataFrame:
    df = matdocs.copy()
    df["sap_movement"] = df["movement_type"].map(movement_code)
    df["signed_quantity"] = df["quantity"] * df["movement_type"].map(movement_sign)
    if material is not None:
        df = df[df["material_number"] == material]
    if plant is not None:
        df = df[df["plant"] == plant]
    if start is not None:
        df = df[df[DATE_COL] >= pd.Timestamp(start)]
    if end is not None:
        df = df[df[DATE_COL] <= pd.Timestamp(end)]
    return df.sort_values(DATE_COL).reset_index(drop=True)


def monthly_summary(matdocs: pd.DataFrame) -> pd.DataFrame:
    df = matdocs.dropna(subset=[DATE_COL]).copy()
    df["month"] = df[DATE_COL].dt.strftime("%Y-%m")
    return df.pivot_table(
        index="month",
        columns="movement_type",
        values="quantity",
        aggfunc="sum",
        fill_value=0,
    ).reset_index()


def net_movement_by_material(matdocs: pd.DataFrame) -> pd.DataFrame:
    df = movement_list(matdocs)
    return (
        df.groupby("material_number", as_index=False)["signed_quantity"]
        .sum()
        .rename(columns={"signed_quantity": "net_movement"})
    )


def unknown_movement_types(matdocs: pd.DataFrame) -> list[str]:
    found = set(matdocs["movement_type"].dropna().unique())
    return sorted(found - set(MOVEMENT_TYPES))
