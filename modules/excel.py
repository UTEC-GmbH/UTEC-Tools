"""Import und Download von Excel-Dateien"""

import re
from io import BytesIO
from typing import Any, Literal, NamedTuple

import pandas as pd
import pandas.io.formats.excel
import streamlit as st
from loguru import logger

from modules import constants as cont
from modules import meteorolog as meteo
from modules.classes import ExcelMarkers, MarkerPosition, MarkerType, ObisElectrical
from modules.df_manip import CleanUpDLS, clean_up_daylight_savings
from modules.general_functions import func_timer, sort_list_by_occurance
from modules.logger_setup import LogLevel

pandas.io.formats.excel.ExcelFormatter.header_style = None  # type: ignore


# ? return value (maybe dict) instead of putting everything in session_state???
# TODO: better docstring
@func_timer
def import_prefab_excel(file: Any) -> None:
    """Vordefinierte Datei (benannte Zelle für Index) importieren"""

    df_messy: pd.DataFrame = pd.read_excel(file, sheet_name="Daten")
    logger.debug("df_messy")
    logger.log(LogLevel.DATA_FRAME.name, df_messy.head(10))
    df: pd.DataFrame = edit_df_after_import(df_messy)
    logger.debug("clean df")
    logger.log(LogLevel.DATA_FRAME.name, df.head())

    # Metadaten
    units: dict[str, str] = units_from_messy_df(df_messy)
    meta_index: dict[str, Any] = meta_from_index(df)

    meta: cont.DicStrNest = meta_from_col_title(df, units)
    meta["index"] = meta_index

    # 15min und kWh
    df, meta = convert_15min_kwh_to_kw(df, meta)
    logger.debug(f"Metadaten nach 15min-Konvertierung: \n{meta}")
    units = {col: meta[col]["unit"] for col in meta if meta[col].get("unit")}

    # write stuff in session state
    st.session_state["metadata"] = meta
    st.session_state["all_units"] = list(units.values())
    st.session_state["metadata"]["units"] = {
        "all": list(units.values()),
        "set": sort_list_by_occurance(list(units.values())),
    }

    set_y_axis_for_lines()
    st.session_state["df"] = df
    if "years" not in st.session_state:
        st.session_state["years"] = meta["index"]["years"]

    logger.success("file imported and metadata extracted")
    logger.log(LogLevel.DATA_FRAME.name, df.head())


@func_timer
def units_from_messy_df(df_messy: pd.DataFrame) -> dict[str, str]:
    """Get the units of every column from the messy df right after import

    The function assumes that the DataFrame has a row with
    the string "↓ Index ↓" marking the start of the data
    and a row with the string "→ Einheit →" marking the units of each column.

    Args:
        - df (pd.DataFrame): messy df

    Returns:
        - dict[str, str]: keys = column names, values = units
    """

    p_in: MarkerPosition = ExcelMarkers(MarkerType.INDEX).get_marker_position(df_messy)
    p_un: MarkerPosition = ExcelMarkers(MarkerType.UNITS).get_marker_position(df_messy)

    column_names: list[str] = df_messy.iloc[p_in.row, p_in.col + 1 :].to_list()
    units: list[str] = [
        str(uni) for uni in df_messy.iloc[p_un.row, p_un.col + 1 :].to_list()
    ] or [" "] * len(column_names)

    # leerzeichen vor Einheit
    for ind, unit in enumerate(units):
        if not unit.startswith(" ") and unit not in ["", None]:
            units[ind] = f" {unit}"

    cols_units: dict[str, str] = dict(zip(column_names, units, strict=False))
    for key, value in cols_units.items():
        logger.info(f"{key}: '{value}'")

    return cols_units


@func_timer
def set_y_axis_for_lines() -> None:
    """Y-Achsen der Linien"""
    meta: cont.DicStrNest = st.session_state["metadata"]
    lines_with_units: list = [key for key, value in meta.items() if value.get("unit")]

    for line in lines_with_units:
        ind: int = meta["units"]["set"].index(meta[line]["unit"])
        meta[line]["y_axis"] = f"y{ind + 1}" if ind > 0 else "y"
        logger.info(f"{line}: Y-Achse {meta[line]['y_axis']}")
    st.session_state["metadata"] = meta


@func_timer
def edit_df_after_import(df_messy: pd.DataFrame) -> pd.DataFrame:
    """Clean up the df

    Args:
        - df (pd.DataFrame): messy df right after import

    Returns:
        - pd.DataFrame: clean df
    """

    # Zelle mit Index-Markierung
    p_in: MarkerPosition = ExcelMarkers(MarkerType.INDEX).get_marker_position(df_messy)
    df_messy.columns = df_messy.iloc[p_in.row]

    # fix index and delete unneeded and empty cells
    df: pd.DataFrame = df_messy.iloc[p_in.row + 1 :, p_in.col :]
    df = df.dropna(how="all")
    df = df.dropna(axis="columns", how="all")
    df = df.set_index("↓ Index ↓")
    df = df.infer_objects()

    # Index ohne Jahreszahl
    if not isinstance(df.index, pd.DatetimeIndex):
        if "01.01. " in str(df.index[0]):
            df.index = pd.to_datetime(
                [f"{x.split()[0]}2020 {x.split()[1]}" for x in df.index.to_numpy()],
                dayfirst=True,
            )
        else:
            df.index = pd.to_datetime(df.index, dayfirst=True)

    # delete duplicates in index (day light savings)
    dls: CleanUpDLS = clean_up_daylight_savings(df)
    df = dls.df_clean
    st.session_state["df_dls_deleted"] = (
        dls.df_deleted if len(dls.df_deleted) > 0 else None
    )

    # copy index in separate column to preserve if index is changed (multi year)
    df["orgidx"] = df.index.copy()

    return df


@func_timer
def meta_from_index(df: pd.DataFrame) -> dict[str, Any]:
    """Check if index is datetime and if so, get temporal resolution

    Args:
        - df (pd.DataFrame): pd.DataFrame

    Returns:
        - dict[str, Any]:
            - datetime: bool,
            - td_mean: average time difference (minutes),
            - td_int: "15min" or "h"
            - years: list of years in index
    """

    dic_index: dict[str, Any] = {
        "datetime": False,
        "years": [],
        "td_int": "unbekannt",
        "td_mean": "unbekannt",
    }
    if not isinstance(df.index, pd.DatetimeIndex):
        logger.error("Kein Zeitindex gefunden!!!")
    else:
        dic_index["datetime"] = True
        td_mean: pd.Timedelta = df.index.to_series().diff().mean().round("min")

        logger.debug(f"Zeitliche Auflösung des DataFrame: {td_mean}")

        dic_index["td_mean"] = td_mean
        if dic_index["td_mean"] == pd.Timedelta(minutes=15):
            dic_index["td_int"] = "15min"
            logger.info("Index mit zeitlicher Auflösung von 15 Minuten erkannt.")
        elif dic_index["td_mean"] == pd.Timedelta(hours=1):
            dic_index["td_int"] = "h"
            logger.info("Index mit zeitlicher Auflösung von 1 Stunde erkannt.")

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
        - cont.DicStrNest: dictionary with metadata (first key = column name)
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
            df = df.rename(columns={col: meta[col]["tit"]})

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
        - meta (cont.DicStrNest): dictionary mit Metadaten

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
            df, meta = insert_column_arbeit_leistung(original_data, df, meta, col)
            df, meta = rename_column_arbeit_leistung(original_data, df, meta, col)

            logger.success(f"Arbeit und Leistung für Spalte '{col}' aufgeteilt")

    return df, meta


def rename_column_arbeit_leistung(
    original_data: Literal["Arbeit", "Leistung"],
    df: pd.DataFrame,
    meta: cont.DicStrNest,
    col: str,
) -> tuple[pd.DataFrame, cont.DicStrNest]:
    """Wenn Daten als Arbeit oder Leistung in 15-Minuten-Auflösung
    vorliegen, wird die Originalspalte umbenannt (mit Suffix "Arbeit" oder "Leistung")
    und in den Metadaten ein Eintrag für den neuen Spaltennamen eingefügt.


    Args:
        - original_data (Literal['Arbeit', 'Leistung']):
            Sind die Daten "Arbeit" oder "Leistung"
        - df (pd.DataFrame): DataFrame für neue Spalte
        - meta (cont.DicStrNest): dictionar der Metadaten
        - col (str): Name der (Original-) Spalte
    """
    col_name: str = f'{col}{cont.ARBEIT_LEISTUNG["suffix"][original_data]}'
    df = df.rename(columns={col: col_name})
    meta[col_name] = meta[col].copy()
    meta[col_name]["tit"] = col_name

    logger.info(f"Spalte '{col}' umbenannt in '{col_name}'")

    return df, meta


def insert_column_arbeit_leistung(
    original_data: Literal["Arbeit", "Leistung"],
    df: pd.DataFrame,
    meta: cont.DicStrNest,
    col: str,
) -> tuple[pd.DataFrame, cont.DicStrNest]:
    """Wenn Daten als Arbeit oder Leistung in 15-Minuten-Auflösung
    vorliegen, wird eine neue Spalte mit dem jeweils andern Typ eingefügt.


    Args:
        - original_data (Literal['Arbeit', 'Leistung']):
            Sind die Daten "Arbeit" oder "Leistung"
        - df (pd.DataFrame): DataFrame für neue Spalte
        - meta (cont.DicStrNest): dictionar der Metadaten
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

    logger.info(f"Spalte '{col_name}' mit Einheit '{meta[col_name]['unit']}' eingefügt")

    return df, meta


@func_timer
def excel_download(df: pd.DataFrame, page: str = "graph") -> bytes:
    """Download data as an Excel file.

    Args:
        - df (pd.DataFrame): The data frame to download.
        - page (str, optional): The name of the page to use in the Excel file.
            Defaults to "graph".

    Returns:
        - bytes: The Excel file as a bytes object.
    """
    name_and_format: WsNameNumFormat = ws_name_num_format(df, page)
    ws_name: str = name_and_format.worksheet_name
    num_formats: dict[str, str] = name_and_format.number_formats

    column_offset: int = 2
    row_offset: int = 4

    # pylint: disable=abstract-class-instantiated
    with BytesIO() as output, pd.ExcelWriter(
        output,
        engine="xlsxwriter",
        datetime_format="dd.mm.yyyy hh:mm",
        date_format="dd.mm.yyyy",
    ) as writer:
        df.to_excel(
            writer,
            sheet_name=ws_name,
            startrow=row_offset,
            startcol=column_offset,
            engine="xlsxwriter",
        )

        workbook: Any = writer.book
        worksheet: Any = writer.sheets[ws_name]

        format_worksheet(
            workbook, worksheet, df, num_formats, column_offset, row_offset
        )

    return output.getvalue()


@func_timer
def format_worksheet(
    workbook: Any,
    worksheet: Any,
    df: pd.DataFrame,
    number_formats: dict[str, str],
    offset_col: int = 2,
    offset_row: int = 4,
) -> None:
    """Edit the formatting of the worksheet in the output excel-file

    Args:
        - wkb (Any): Workbook
        - wks (Any): Worksheet
        - df (pd.DataFrame): main pd.DataFrame
        - dic_num_formats (dict): dictionary {col: number format}
    """

    cols: list[str] = [str(col) for col in df.columns]

    # Formatierung
    worksheet.hide_gridlines(2)
    base_format: dict[str, Any] = {
        "bold": False,
        "font_name": "Arial",
        "font_size": 10,
        "align": "right",
        "border": 0,
    }

    # erste Spalte
    spec_format: dict[str, Any] = base_format.copy()
    spec_format["align"] = "left"
    cell_format: Any = workbook.add_format(spec_format)
    worksheet.set_column(offset_col, offset_col, 18, cell_format)

    # erste Zeile
    spec_format = base_format.copy()
    spec_format["bottom"] = 1
    cell_format = workbook.add_format(spec_format)
    worksheet.write(offset_row, offset_col, "Datum", cell_format)

    for col, header in enumerate(cols):
        worksheet.write(offset_row, col + 1 + offset_col, header, cell_format)

    for num_format in number_formats.values():
        spec_format = base_format.copy()
        spec_format["num_format"] = num_format
        col_format: Any = workbook.add_format(spec_format)

        for cnt, col in enumerate(cols):
            if number_formats[col] == num_format:
                worksheet.set_column(
                    cnt + offset_col + 1,
                    cnt + offset_col + 1,
                    len(col) + 1,
                    col_format,
                )


class WsNameNumFormat(NamedTuple):
    """Named tuple for the return value of the following function."""

    worksheet_name: str
    number_formats: dict[str, str]


@func_timer
def ws_name_num_format(df: pd.DataFrame, page: str) -> WsNameNumFormat:
    """Worksheet name and number fromat based on app page

    Args:
        - df (pd.DataFrame): main data frame
        - page (str): page of app (graph or meteo...)

    Returns:
        - tuple[str, dict]: ws_name, dic_num_formats = {column: number format}
    """

    page_mapping: dict[str, dict[str, Any]] = {
        "meteo": {
            "ws_name": "Wetterdaten",
            "num_formats": {par.tit_de: par.num_format for par in meteo.LIS_PARAMS},
        },
        "graph": {
            "ws_name": "Daten",
            "num_formats": {
                key: f'#,##0.0"{st.session_state["metadata"][key]["unit"]}"'
                for key in [str(col) for col in df.columns]
            },
        },
    }
    if page not in page_mapping:
        err_msg: str = f"Invalid page: {page}"
        raise ValueError(err_msg)
    mapping: dict[str, Any] = page_mapping[page]

    return WsNameNumFormat(
        worksheet_name=mapping["ws_name"], number_formats=mapping["num_formats"]
    )
