"""
Import und Download von Excel-Dateien
"""
import re
from io import BytesIO
from typing import Any, Literal

import pandas as pd
import pandas.io.formats.excel
import streamlit as st
from loguru import logger

from modules import constants as cont
from modules import meteorolog as meteo
from modules.classes import ObisElectrical
from modules.df_manip import clean_up_daylight_savings
from modules.general_functions import func_timer, sort_list_by_occurance

pandas.io.formats.excel.ExcelFormatter.header_style = None  # type: ignore


# ? return value (maybe dict) instead of putting everything in session_state???
# TODO: better docstring
@func_timer
@st.cache_data(show_spinner=False)
def import_prefab_excel(file: Any) -> None:
    """vordefinierte Datei (benannte Zelle für Indes) importieren"""

    df_messy: pd.DataFrame = pd.read_excel(file, sheet_name="Daten")
    df: pd.DataFrame = edit_df_after_import(df_messy)

    # Metadaten
    units: dict[str, str] = units_from_messy_df(df_messy)
    meta_index: dict[str, Any] = meta_from_index(df)

    meta: cont.DicStrNest = meta_from_col_title(df, units)
    meta["index"] = meta_index

    # 15min und kWh
    df, meta = convert_15min_kwh_to_kw(df, meta)
    units = {col: meta[col]["unit"] for col in meta if meta[col].get("unit")}

    # write stuff in session state
    st.session_state["metadata"] = meta
    st.session_state["all_units"] = list(units.values())
    st.session_state["metadata"]["units"] = {
        "all": list(units.values()),
        "set": sort_list_by_occurance(list(units.values())),
    }
    # st.experimental_show(st.session_state["metadata"])
    set_y_axis_for_lines()
    st.session_state["df"] = df
    if "years" not in st.session_state:
        st.session_state["years"] = meta["index"]["years"]

    logger.success("file imported as DataFrame")
    logger.info(f"{df.info(verbose=True)}")


@func_timer
def units_from_messy_df(df_messy: pd.DataFrame) -> dict[str, str]:
    """Get the units of every column from the messy df right after import

    Args:
        - df (pd.DataFrame): messy df

    Returns:
        - dict[str, str]: keys = column names, values = units
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

    column_names: list[str] = df_messy.iloc[ind_row, ind_col + 1 :].to_list()
    units: list[str] = df_messy.iloc[unit_row, ind_col + 1 :].to_list()

    # leerzeichen vor Einheit
    for unit in units:
        if not unit.startswith(" ") and unit not in ["", None]:
            units[units.index(unit)] = f" {unit}"

    return dict(zip(column_names, units))


# Einheiten
@func_timer
def set_y_axis_for_lines() -> None:
    """Y-Achsen der Linien"""

    for k_1 in [
        k_2
        for k_2 in st.session_state["metadata"]
        if st.session_state["metadata"][k_2].get("unit")
    ]:
        ind: int = st.session_state["metadata"]["units"]["set"].index(
            st.session_state["metadata"][k_1].get("unit")
        )

        st.session_state["metadata"][k_1]["y_axis"] = (
            f"y{str(ind + 1)}" if ind > 0 else "y"
        )


@func_timer
@st.cache_data(show_spinner=False)
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
    dls: dict[str, pd.DataFrame] = clean_up_daylight_savings(df)
    df = dls["df_clean"]
    st.session_state["df_dls_deleted"] = (
        dls["df_deleted"] if len(dls["df_deleted"]) > 0 else None
    )

    # copy index in separate column to preserve if index is changed (multi year)
    df["orgidx"] = df.index.copy()

    return df


@func_timer
@st.cache_data(show_spinner=False)
def meta_from_index(df: pd.DataFrame) -> dict[str, Any]:
    """check if index is datetime and if so, get temporal resolution

    Args:
        - df (pd.DataFrame): pd.DataFrame

    Returns:
        - dict[str, Any]:
            - datetime: bool,
            - td_mean: average time difference (minutes),
            - td_int: "15min" or "h"
            - years: list of years in index
    """

    dic_index: dict[str, Any] = {"datetime": False, "years": []}

    if isinstance(df.index, pd.DatetimeIndex):
        dic_index["datetime"] = True
        dic_index["td_mean"] = df.index.to_series().diff().mean().round("min")  # type: ignore
        if dic_index["td_mean"] == pd.Timedelta(minutes=15):
            dic_index["td_int"] = "15min"
        elif dic_index["td_mean"] == pd.Timedelta(hours=1):
            dic_index["td_int"] = "h"

        cut_off: int = 50
        dic_index["years"].extend(
            y
            for y in set(df.index.year)
            if len(df.loc[df.index.year == y, :]) > cut_off
        )

    return dic_index


@func_timer
def meta_from_col_title(df: pd.DataFrame, units: dict[str, str]) -> cont.DicStrNest:
    """Get metadata from the column title and obis code (if available)

    Args:
        - df (pd.DataFrame): pd.DataFrame

    Returns:
        - cont.DicStrNest: Dictionary with metadata (first key = column name)
            - for every column:
                - "orig_tit": Original Title of the column
                - "tit": renamed title if OBIS code in title, else same as orig_tit
                - "unit": unit given in Excel-file or ""
            - if column has OBIS-code:
                - "obis_code" (z.B. "1-1:29.0")
                - "messgroesse" (z.B. "Bezug", "Lieferung", "Spannung", etc.)
                - "messart" (z.B. "min", "max", "Mittel", etc.)
                - "unit" (from OBIS-code if not given in Excel-file)
    """

    meta: cont.DicStrNest = {}
    for col in [str(col) for col in df.columns]:
        meta[col] = {"orig_tit": col, "tit": col, "unit": units.get(col) or ""}

        # check if there is an OBIS-code in the column title
        if match := re.search(cont.OBIS_PATTERN_EL, col):
            obis_code = ObisElectrical(match[0])
            meta[col].update(
                {
                    "unit": units.get(col) or obis_code.unit,
                    "obis_code": obis_code.code,
                    "messgroesse": obis_code.messgroesse,
                    "messart": obis_code.messart,
                    "tit": obis_code.name,
                }
            )
            meta[meta[col]["tit"]] = meta[col]
            df.rename(columns={col: meta[col]["tit"]}, inplace=True)

    return meta


@func_timer
def convert_15min_kwh_to_kw(
    df: pd.DataFrame, meta: cont.DicStrNest
) -> tuple[pd.DataFrame, cont.DicStrNest]:
    """Falls die Daten als 15-Minuten-Daten vorliegen,
    wird geprüft ob es sich um Verbrauchsdaten handelt.
    Falls dem so ist, werden sie mit 4 multipliziert um
    Leistungsdaten zu erhalten.

    Die Leistungsdaten werden in neue Spalten im
    DataFrame geschrieben.


    Args:
        - df (pd.DataFrame): Der zu untersuchende DataFrame
        - meta (cont.DicStrNest): Dictionary mit Metadaten

    Returns:
        - tuple[pd.DataFrame, cont.DicStrNest]: Aktualisierte df und Metadaten
    """

    if meta["index"]["td_int"] not in ["15min"]:
        return df, meta

    suffixes: list[str] = list(cont.ARBEIT_LEISTUNG["suffix"].values())

    for col in [str(column) for column in df.columns]:
        suffix_not_in_col_name: bool = all(suffix not in col for suffix in suffixes)
        unit_is_leistung_or_arbeit: bool = meta[col]["unit"].strip() in (
            cont.ARBEIT_LEISTUNG["units"]["Arbeit"]
            + cont.ARBEIT_LEISTUNG["units"]["Leistung"]
        )
        if suffix_not_in_col_name and unit_is_leistung_or_arbeit:
            original_data: Literal["Arbeit", "Leistung"] = (
                "Arbeit"
                if meta[col]["unit"].strip() in cont.ARBEIT_LEISTUNG["units"]["Arbeit"]
                else "Leistung"
            )
            insert_column_arbeit_leistung(original_data, df, meta, col)
            rename_column_arbeit_leistung(original_data, df, meta, col)

            logger.success("Arbeit und Leistung aufgeteilt")

    return df, meta


def rename_column_arbeit_leistung(
    original_data: Literal["Arbeit", "Leistung"],
    df: pd.DataFrame,
    meta: cont.DicStrNest,
    col: str,
) -> None:
    """Wenn Daten als Arbeit oder Leistung in 15-Minuten-Auflösung
    vorliegen, wird die Originalspalte umbenannt (mit Suffix "Arbeit" oder "Leistung")
    und in den Metadaten ein Eintrag für den neuen Spaltennamen eingefügt.


    Args:
        - original_data (Literal['Arbeit', 'Leistung']): Sind die Daten "Arbeit" oder "Leistung"
        - df (pd.DataFrame): DataFrame für neue Spalte
        - meta (cont.DicStrNest): Dictionar der Metadaten
        - col (str): Name der (Original-) Spalte
    """
    col_name: str = f'{col}{cont.ARBEIT_LEISTUNG["suffix"][original_data]}'
    df.rename(columns={col: col_name}, inplace=True)
    meta[col_name] = meta[col].copy()
    meta[col_name]["tit"] = col_name


def insert_column_arbeit_leistung(
    original_data: Literal["Arbeit", "Leistung"],
    df: pd.DataFrame,
    meta: cont.DicStrNest,
    col: str,
) -> None:
    """Wenn Daten als Arbeit oder Leistung in 15-Minuten-Auflösung
    vorliegen, wird eine neue Spalte mit dem jeweils andern Typ eingefügt.


    Args:
        - original_data (Literal['Arbeit', 'Leistung']): Sind die Daten "Arbeit" oder "Leistung"
        - df (pd.DataFrame): DataFrame für neue Spalte
        - meta (cont.DicStrNest): Dictionar der Metadaten
        - col (str): Name der (Original-) Spalte
    """
    new_col: str = "Arbeit" if original_data == "Leistung" else "Leistung"
    col_name: str = f'{col}{cont.ARBEIT_LEISTUNG["suffix"][new_col]}'
    meta[col_name] = meta[col].copy()
    meta[col_name]["tit"] = col_name

    df[col_name] = (
        df[col].copy() * 4 if original_data == "Arbeit" else df[col].copy() / 4
    )
    meta[col_name]["unit"] = (
        meta[col]["unit"][:-1] if original_data == "Arbeit" else f'{meta[col]["unit"]}h'
    )


def meta_from_obis_code(obis_code: str) -> dict[str, str]:
    """Get metadata from an OBIS-code

    Args:
        - code (str): OBIS-Code (from column title)

    Returns:
        - dict[str, str]: Dictionary with the following:
            - "obis_code" (z.B. "1-1:29.0")
            - "messgroesse" (z.B. "Bezug", "Lieferung", "Spannung", etc.)
            - "messart" (z.B. "min", "max", "Mittel", etc.)
            - "unit" (z.B. " kW", " kWh", etc.)
    """
    messgr_code: str = obis_code.split(":")[1].split(".")[0]
    messar_code: str = obis_code.split(":")[1].split(".")[1]

    return {
        "obis_code": obis_code,
        "messgroesse": cont.OBIS_ELECTRICAL["messgroesse"][messgr_code]["alt_bez"],
        "messart": cont.OBIS_ELECTRICAL["messart"][messar_code]["alt_bez"],
        "unit": f' {cont.OBIS_ELECTRICAL["messgroesse"][messgr_code]["unit"]}',
    }


# TODO: rewrite, refactor, docstring
@func_timer
def excel_download(df: pd.DataFrame, page: str = "graph") -> Any:
    """Daten als Excel-Datei herunterladen"""

    ws_name: str = ws_name_num_format(df, page)[0]
    dic_num_formats: dict[str, str] = ws_name_num_format(df, page)[1]

    offset_col: int = 2
    offset_row: int = 4

    output: BytesIO = BytesIO()
    # pylint: disable=abstract-class-instantiated
    writer: pd.ExcelWriter = pd.ExcelWriter(
        output,
        engine="xlsxwriter",
        datetime_format="dd.mm.yyyy hh:mm",
        date_format="dd.mm.yyyy",
    )
    # pylint: enable=abstract-class-instantiated
    df.to_excel(
        writer,
        sheet_name=ws_name,
        startrow=offset_row,
        startcol=offset_col,
    )

    wkb: Any = writer.book
    wks: Any = writer.sheets[ws_name]

    # Formatierung

    edit_ws_format(wkb, wks, df, dic_num_formats)

    wkb.close()

    return output.getvalue()


def edit_ws_format(
    wkb: Any,
    wks: Any,
    df: pd.DataFrame,
    dic_num_formats: dict[str, str],
) -> None:
    """Edit the formatting of the worksheet in the output excel-file

    Args:
        - wkb (Any): Workbook
        - wks (Any): Worksheet
        - df (pd.DataFrame): main pd.DataFrame
        - dic_num_formats (dict): dictionary {col: number format}
    """

    cols: list[str] = [str(col) for col in df.columns]
    offset_col: int = 2
    offset_row: int = 4

    # Formatierung
    wks.hide_gridlines(2)
    dic_format_base: dict[str, Any] = {
        "bold": False,
        "font_name": "Arial",
        "font_size": 10,
        "align": "right",
        "border": 0,
    }

    # erste Spalte
    dic_format: dict[str, Any] = dic_format_base.copy()
    dic_format["align"] = "left"
    cell_format = wkb.add_format(dic_format)
    wks.set_column(offset_col, offset_col, 18, cell_format)

    # erste Zeile
    dic_format = dic_format_base.copy()
    dic_format["bottom"] = 1
    cell_format = wkb.add_format(dic_format)
    wks.write(offset_row, offset_col, "Datum", cell_format)

    for col, header in enumerate(cols):
        wks.write(offset_row, col + 1 + offset_col, header, cell_format)

    for num_format in dic_num_formats.values():
        dic_format = dic_format_base.copy()
        dic_format["num_format"] = num_format
        col_format = wkb.add_format(dic_format)

        for cnt, col in enumerate(cols):
            if dic_num_formats[col] == num_format:
                wks.set_column(
                    cnt + offset_col + 1,
                    cnt + offset_col + 1,
                    len(col) + 1,
                    col_format,
                )


def ws_name_num_format(df: pd.DataFrame, page: str) -> tuple[str, dict]:
    """Worksheet name and number fromat based on app page

    Args:
        - df (pd.DataFrame): main data frame
        - page (str): page of app (graph or meteo...)

    Returns:
        - tuple[str, dict]: ws_name, dic_num_formats = {column: number format}
    """

    ws_name: str = "Tabelle1"
    dic_num_formats: dict[str, str] = {}

    if page in ("meteo"):
        ws_name = "Wetterdaten"
        dic_num_formats = {par.tit_de: par.num_format for par in meteo.LIS_PARAMS}

    if page in ("graph"):
        ws_name = "Daten"
        dic_num_formats = {
            key: f'#,##0.0"{st.session_state["metadata"][key]["unit"]}"'
            for key in [str(col) for col in df.columns]
        }

    return ws_name, dic_num_formats
