# sourcery skip: avoid-global-variables
"""test stuff with the excel import in an interactive window"""

import os

import pandas as pd
from typing import List, Dict

cwd: str = os.getcwd()

FILE_PATHS: Dict[str, str] = {
    "el_single": f"{cwd}/example_files/Auswertung Stromlastgang - einzelnes Jahr.xlsx",
    "el_multi": f"{cwd}/example_files/Stromlastgang - mehrere Jahre.xlsx",
    "heat_multi": f"{cwd}/example_files/Wärmelastgang - mehrere Jahre.xlsx",
}
# - "el_single": Strom, 15min, kWh, einzelnes Jahr
# - "el_multi": Strom+Temp, 15min, teileise in kW / kWh, mehrere Jahre
# - "heat_multi": Wärme+Temp, Stundenwerte, kWh, mehrere Jahre

# if "dic_exe_time" not in st.session_state:
#     st.session_state["dic_exe_time"] = {}

file: str = FILE_PATHS["el_single"]
df_messy: pd.DataFrame = pd.read_excel(file, sheet_name="Daten")


def units_from_messy_df(df_messy: pd.DataFrame) -> Dict[str, str]:
    """Get the units of every column from the messy df right after import

    Args:
        - df (pd.DataFrame): messy df

    Returns:
        - Dict[str, str]: keys = column names, values = units
    """

    # Zelle mit Index-Markierung
    ind_cell: pd.DataFrame = (
        df_messy[df_messy == "↓ Index ↓"].dropna(how="all").dropna(axis=1)
    )
    ind_row: int = df_messy.index.get_loc(ind_cell.index[0])
    ind_col: int = df_messy.columns.get_loc(ind_cell.columns[0])

    # Zelle mit Einheiten-Markierung
    unit_cell: pd.DataFrame = (
        df_messy[df_messy == "→ Einheit →"].dropna(how="all").dropna(axis=1)
    )
    unit_row: int = df_messy.index.get_loc(unit_cell.index[0])

    column_names: List[str] = df_messy.iloc[ind_row, ind_col + 1 :].to_list()
    units: List[str] = df_messy.iloc[unit_row, ind_col + 1 :].to_list()

    # leerzeichen vor Einheit
    for unit in units:
        if not unit.startswith(" ") and unit not in ["", None]:
            units[units.index(unit)] = f" {unit}"

    return dict(zip(column_names, units))


def edit_df_after_import(df_messy: pd.DataFrame) -> pd.DataFrame:
    """Get the units out of the imported (messy) df and clean up the df

    Args:
        - df (pd.DataFrame): messy df right after import

    Returns:
        - pd.DataFrame: clean df
    """

    # Zelle mit Index-Markierung
    ind: pd.DataFrame = (
        df_messy[df_messy == "↓ Index ↓"].dropna(how="all").dropna(axis=1)
    )
    ind_row: int = df_messy.index.get_loc(ind.index[0])
    ind_col: int = df_messy.columns.get_loc(ind.columns[0])

    df_messy.columns = df_messy.iloc[ind_row]

    # fix index and delete unneeded and empty cells
    df: pd.DataFrame = df_messy.iloc[ind_row + 1 :, ind_col:]
    df = df.set_index("↓ Index ↓")
    pd.to_datetime(df.index, dayfirst=True)
    df = df.infer_objects()
    df.dropna(how="all", inplace=True)
    df.dropna(axis="columns", how="all", inplace=True)

    # Index ohne Jahreszahl
    if not isinstance(df.index, pd.DatetimeIndex) and "01.01. " in str(df.index[0]):
        df.index = pd.to_datetime(
            [f"{x.split()[0]}2020 {x.split()[1]}" for x in df.index.values],
            dayfirst=True,
        )

    # delete duplicates in index (day light savings)
    # dls: Dict[str, pd.DataFrame] = clean_up_daylight_savings(df)
    # df = dls["df_clean"]
    # st.session_state["df_dls_deleted"] = (
    #     dls["df_deleted"] if len(dls["df_deleted"]) > 0 else None
    # )

    # copy index in separate column to preserve if index is changed (multi year)
    df["orgidx"] = df.index.copy()

    return df


df: pd.DataFrame = edit_df_after_import(df_messy)

# Metadaten
units: Dict[str, str] = units_from_messy_df(df_messy)
