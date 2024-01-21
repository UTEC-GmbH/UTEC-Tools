"""Import und Download von Excel-Dateien"""

import datetime as dt
import re
from io import BytesIO
from typing import Any, Literal, NamedTuple

import polars as pl
import xlsx2csv
from loguru import logger

from modules import classes_constants as clc
from modules import classes_data as cld
from modules import constants as cont
from modules import general_functions as gf
from modules import setup_logger as slog

TEST_FILE = "example_files/Stromlastgang - 15min - 2 Jahre.xlsx"


def date_serial_number(serial_number: float) -> dt.datetime:
    """Convert an Excel serial number to a Python datetime object
    Excel stores dates as "number of days since 1900"
    """

    return dt.datetime(1899, 12, 30) + dt.timedelta(days=serial_number)


@gf.func_timer
def general_excel_import(
    file: BytesIO | str,
    worksheet: str = "Tabelle1",
    **kwargs,
) -> pl.DataFrame:
    """Import an Excel file

    Example:
    file= "example_map/Punkte_Längengrad_Breitengrad.xlsx"

    xlsx_options:
        sheetid - sheet no to convert (0 for all sheets)
        sheetname - sheet name to convert
        dateformat - override date/time format
        timeformat - override time format
        floatformat - override float format
        quoting - if and how to quote
        delimiter - csv columns delimiter symbol
        sheetdelimiter - sheets delimiter used when processing all sheets
        skip_empty_lines - skip empty lines
        skip_trailing_columns - skip trailing columns
        hyperlinks - include hyperlinks
        include_sheet_pattern - only include sheets named matching given pattern
        exclude_sheet_pattern - exclude sheets named matching given pattern
        exclude_hidden_sheets - exclude hidden sheets
        skip_hidden_rows - skip hidden rows

    csv_option:
        see "read_csv" function of polars
    """

    xlsx_options: dict[str, Any] = {
        "skip_empty_lines": kwargs.get("skip_empty_lines") or True,
        "skip_trailing_columns": kwargs.get("skip_trailing_columns") or False,
        "no_line_breaks": kwargs.get("no_line_breaks") or True,
        "merge_cells": kwargs.get("merge_cells") or True,
        # "dateformat": kwargs.get("dateformat") or "%d.%m.%Y %H:%M",
    }

    csv_options: dict[str, bool] = {
        "has_header": kwargs.get("has_header") or True,
        "try_parse_dates": kwargs.get("try_parse_dates") or False,
    }

    df: pl.DataFrame = pl.read_excel(
        source=file,
        sheet_name=worksheet,
        xlsx2csv_options=xlsx_options,
        read_csv_options=csv_options,
    )

    for col in ["Datum", cont.SpecialCols.index]:
        if col in df.columns and df.get_column(col).dtype != pl.Datetime:
            df = df.with_columns(
                pl.col(col).str.strptime(pl.Datetime, "%d.%m.%Y %H:%M")
            )

    df = remove_empty(df)
    logger.info(df.head())

    return df


@gf.func_timer
def import_prefab_excel(file: BytesIO | str = TEST_FILE) -> cld.MetaAndDfs:
    """Import and download Excel files.

    Args:
    - file (io.BytesIO | str): BytesIO object or string
        representing the Excel file to import.

    Returns:
    - MetaAndDfs: DataFrames and meta data extracted from the Excel file.

    Example files for testing:
    - file = "example_files/Stromlastgang - 15min - 1 Jahr.xlsx"
    - file = "example_files/Stromlastgang - 15min - 2 Jahre.xlsx"
    - file = "example_files/Wärmelastgang - 1h - 3 Jahre.xlsx"

    - file = "tests/problematic_files/Fehler Datum.xlsx"
    - file = "tests/problematic_files/nur teilweise zusammenfassung.xlsx"

    Example test run:
    mdf = import_prefab_excel()
    or
    mdf = import_prefab_excel(file)
    """

    mark_index: str = cont.ExcelMarkers.index
    mark_units: str = cont.ExcelMarkers.units

    df: pl.DataFrame = get_df_from_excel(file)

    # remove empty rows and columns and rename columns
    df = remove_empty(df)
    df = rename_columns(df, mark_index)

    # extract units
    meta: cld.MetaData = meta_units(df, mark_index, mark_units)

    # clean up DataFrame
    df = clean_up_df(df, mark_index)

    mdf: cld.MetaAndDfs = cld.MetaAndDfs(meta, df)
    # meta data if obis code in column title
    mdf = meta_from_obis(mdf)

    # Weitere Metadaten
    mdf = temporal_metadata(mdf, mark_index)
    mdf.meta = meta_number_format(mdf)

    # 15min und kWh
    mdf = convert_15min_kwh_to_kw(mdf)

    slog.log_df(mdf.df)

    logger.debug(gf.string_new_line_per_item(mdf.df.columns, "mdf.df.columns"))
    logger.debug(
        gf.string_new_line_per_item(list(mdf.meta.lines), "lines in mdf.meta.lines:")
    )
    logger.success("Excel-Datei importiert.")

    return mdf


def get_df_from_excel(file: BytesIO | str) -> pl.DataFrame:
    """Excel Import via csv-conversion

    xlsx2csv options:
       - sheetid - sheet no to convert (0 for all sheets)
       - sheetname - sheet name to convert
       - dateformat - override date/time format
       - timeformat - override time format
       - floatformat - override float format
       - quoting - if and how to quote
       - delimiter - csv columns delimiter symbol
       - sheetdelimiter - sheets delimiter used when processing all sheets
       - skip_empty_lines - skip empty lines
       - skip_trailing_columns - skip trailing columns
       - hyperlinks - include hyperlinks
       - include_sheet_pattern - only include sheets named matching given pattern
       - exclude_sheet_pattern - exclude sheets named matching given pattern
       - exclude_hidden_sheets - exclude hidden sheets
       - skip_hidden_rows - skip hidden rows
    """

    sheet: str = "Daten"
    xlsx_options: dict[str, str | bool | list[str]] = {"skip_empty_lines": True}
    csv_options: dict[str, bool] = {"has_header": False, "try_parse_dates": False}

    try:
        xl_options: dict[str, str | bool | list[str]] = xlsx_options | {
            "dateformat": "%d.%m.%Y %H:%M"
        }
        df: pl.DataFrame = pl.read_excel(
            source=file,
            sheet_name=sheet,
            xlsx2csv_options=xl_options,
            read_csv_options=csv_options,
        )
    except xlsx2csv.XlsxValueError as xle:
        logger.error(f"Problem with date format: \n{xle}")
        xl_options = xlsx_options | {"ignore_formats": ["date"]}
        df: pl.DataFrame = pl.read_excel(
            source=file,
            sheet_name=sheet,
            xlsx2csv_options=xl_options,
            read_csv_options=csv_options,
        )
        logger.success(
            "Import successful\n"
            "Date formats were ignored!\n"
            "Dates might have been imported as strings of excel serial numbers.\n"
            "(Excel stores dates as number of days since 1900 "
            "e.g. '42370' → 01.01.2016 00:00, '42370.041667' → 01.01.2016 00:15)"
        )

    return df


def remove_empty(df: pl.DataFrame, **kwargs) -> pl.DataFrame:
    """Remove empty rows and / or columns

    Args:
        - df (pl.DataFrame): DataFrame to edit
        - row (bool): Optional keyword argument.
            Set to False if empty rows should not be removed
        - col (bool): Optional keyword argument.
            Set to False if empty columns should not be removed

    Returns:
        - pl.DataFrame: DataFrame without empty rows / columns
    """

    row: bool = kwargs.get("row") or True
    col: bool = kwargs.get("col") or True

    # remove rows where all values are 'null'
    if row:
        df = df.filter(~pl.all_horizontal(pl.all().is_null()))

    # remove columns where all values are 'null'
    if col:
        df = df[[col.name for col in df if col.null_count() != df.height]]

    return df


def rename_columns(df: pl.DataFrame, mark_index: str) -> pl.DataFrame:
    """Rename the columns of the DataFrame"""

    # find index marker
    ind_col: str = next(col for col in df.columns if mark_index in df.get_column(col))
    logger.info(f"Index-marker found in column '{ind_col}'")

    # rename columns
    cols: tuple = df.row(by_predicate=pl.col(ind_col) == mark_index)
    df.columns = list(cols)

    return df


def meta_units(df: pl.DataFrame, mark_index: str, mark_units: str) -> cld.MetaData:
    """Get units for dataclass"""

    units: dict[str, str] = (
        df.filter(pl.col(mark_index) == mark_units)
        .select([col for col in df.columns if col != mark_index])
        .row(0, named=True)
    )

    # leerzeichen vor Einheit
    units = {line: f" {unit.strip()}" for line, unit in units.items()}

    meta: cld.MetaData = cld.MetaData(
        lines={
            line: cld.MetaLine(
                name=line,
                name_orgidx=(
                    f"{line}{cont.Suffixes.col_original_index}"
                    if cont.Suffixes.col_original_index not in line
                    else line
                ),
                orig_tit=line,
                tit=line,
                unit=unit,
                unit_h=unit.strip("h"),
            )
            for line, unit in units.items()
        },
    )
    logger.info(
        gf.string_new_line_per_item(
            [f"{line}:{unit}" for line, unit in units.items()],
            "Folgende Einheiten wurden gefunden:",
            trailing_empty_lines=1,
        )
    )
    return meta


def meta_number_format(mdf: cld.MetaAndDfs) -> cld.MetaData:
    """Define Number Formats for Excel-Export"""

    # cut-off for decimal places
    decimal_0: int = 1000
    decimal_1: int = 100
    decimal_2: int = 10

    quantiles: pl.DataFrame = mdf.df.quantile(0.95)

    for line in mdf.meta.lines.values():
        if line.name in mdf.df.columns:
            line_quant: float = quantiles.get_column(line.name).item()
            unit: str = line.unit or ""
            line.excel_number_format = f"#,##0.0{unit}"
            if line_quant and abs(line_quant) >= decimal_2:
                line.excel_number_format = f'#,##0.00"{unit}"'
            if line_quant and abs(line_quant) >= decimal_1:
                line.excel_number_format = f'#,##0.0"{unit}"'
            if line_quant and abs(line_quant) >= decimal_0:
                line.excel_number_format = f'#,##0"{unit}"'

    return mdf.meta


def clean_up_df(df: pl.DataFrame, mark_index: str) -> pl.DataFrame:
    """Clean up the DataFrame and adjust the data types

    First removes everythin above the header row.
    If the date column is strings, the dates are probably excel serial numbers.
    (Excel stores dates as number of days since 1900)
    """

    ind_row: int = (
        df.with_row_count().filter(pl.col(mark_index) == mark_index).row(0)[0]
    )
    df = df.slice(ind_row + 1)

    # Convert strings (Excel serial dates or "DD.MM.YYYY hh:mm") to datetime
    try:
        df = df.select(
            [pl.col(mark_index).str.strptime(pl.Datetime, "%d.%m.%Y %H:%M")]
            + [col.cast(pl.Float32) for col in df.select(pl.exclude(mark_index))]
        ).sort(mark_index)

    except pl.ComputeError:
        df = (
            df.cast(
                {mark_index: pl.Float64}
                | {col: pl.Float32 for col in df.select(pl.exclude(mark_index)).columns}  # type: ignore
            )
            .with_columns(
                (pl.col(mark_index) * cont.TimeMicrosecondsIn.day).cast(pl.Duration)
                + pl.datetime(1899, 12, 30)
            )
            .sort(mark_index)
        )

        if df.get_column(mark_index).is_temporal():
            logger.success(
                "Date column was converted "
                "from excel serial numbers to datetime values."
            )

    if all(
        [
            df.get_column(mark_index).is_temporal(),
            *[col.is_float() for col in df.select(pl.exclude(mark_index))],
        ]
    ):
        logger.success("Data types set → index: datetime, all others: float.")

    df = clean_up_daylight_savings(df, mark_index).df_clean

    # copy index in separate column to preserve if index is changed (multi year)
    return df.with_columns(pl.col(mark_index).alias(cont.SpecialCols.original_index))


class CleanUpDLS(NamedTuple):
    """Named Tuple for return value of following function"""

    df_clean: pl.DataFrame
    df_deleted: pl.DataFrame


def clean_up_daylight_savings(df: pl.DataFrame, mark_index: str) -> CleanUpDLS:
    """Zeitumstellung

    Bei der Zeitumstellung auf Sommerzeit wird die Uhr eine Stunde vor gestellt,
    sodass in der Zeitreihe eine Stunde fehlt. Falls das DataFrame diese Stunde
    enthält (z.B. mit nullen in der Stunde), werden diese Zeilen gelöscht.

    Bei der Zeitumstellung auf Winterzeit wird die Uhr eine Sunde zurück gestellt.
    Dadurch gibt es die Stunde doppelt in der Zeitreihe. Das erste Auftreten der
    doppelten Stunde wird gelöscht.

    Args:
        - df (DataFrame): DataFrame to edit
        - mark_index (str): Date column

    Returns:
        - CleanUpDLS:
            - df_clean (DataFrame): edited DataFrame
            - df_deleted (DateFrame): deleted data
    """

    # Sommerzeitumstellung: letzter Sonntag im Maerz - von 2h auf 3h
    month: int = 3  # Monat = 3 -> März
    day: int = 31 - 7  # letzte Woche (Tag > 31-7)
    weekday: int = 6  # Wochentag = 6 -> Sonntag
    hour: int = 2  # Stunde 2 wird ausgelassen

    date_col: pl.Series = df.get_column(mark_index)
    summer: pl.Series = df.filter(
        (date_col.dt.month() == month)
        & (date_col.dt.day() > day)
        & (date_col.dt.weekday() == weekday)
        & (date_col.dt.hour() == hour)
    ).get_column(mark_index)

    # Winterzeitumstellung: doppelte Stunde -> Duplikate löschen
    df_clean: pl.DataFrame = df.filter(~pl.col(mark_index).is_in(summer)).unique(
        subset=mark_index, keep="first", maintain_order=True
    )
    df_deleted: pl.DataFrame = df.filter(
        pl.col(mark_index).is_in(summer) | pl.col(mark_index).is_duplicated()
    ).unique(subset=mark_index, keep="last", maintain_order=True)

    if df_deleted.height > 0:
        logger.warning("Data deleted due to daylight savings.")
        logger.log(slog.LVLS.data_frame.name, df_deleted)
    else:
        logger.info("No data deleted due to daylight savings")

    return CleanUpDLS(df_clean=df_clean, df_deleted=df_deleted)


def temporal_metadata(mdf: cld.MetaAndDfs, mark_index: str) -> cld.MetaAndDfs:
    """Get information about the time index."""

    if not mdf.df.get_column(mark_index).is_temporal():
        logger.error("Kein Zeitindex gefunden!!!")
        return mdf

    mdf.meta.datetime = True
    mdf.meta.years = mdf.df.get_column(mark_index).dt.year().unique().sort().to_list()
    mdf.meta.multi_years = len(mdf.meta.years) > 1

    mdf.meta.td_mnts = int(
        mdf.df.select(pl.col(mark_index).diff().dt.minutes().drop_nulls().mean()).item()
    )

    if mdf.meta.td_mnts == cont.TimeMinutesIn.quarter_hour:
        mdf.meta.td_interval = "15min"
        logger.info("Index mit zeitlicher Auflösung von 15 Minuten erkannt.")
    elif mdf.meta.td_mnts == cont.TimeMinutesIn.hour:
        mdf.meta.td_interval = "h"
        mdf.df_h = mdf.df
        logger.info("Index mit zeitlicher Auflösung von 1 Stunde erkannt.")
    else:
        logger.debug(f"Mittlere zeitliche Auflösung des df: {mdf.meta.td_mnts} Minuten")

    return mdf


def meta_from_obis(mdf: cld.MetaAndDfs) -> cld.MetaAndDfs:
    # sourcery skip: extract-method
    """Update meta data and column name if there is an obis code in a column title.

    If there's an OBIS-code (e.g. 1-1:1.29.0), the following meta data is edited:
    - obis -> instance of ObisElecgtrical class
    - unit -> only if not given in Excel-File
    - tite -> "alternative name (code)"

    Args:
        - mdf (MetaAndDfs): Metadaten und DataFrames

    Returns:
        - mdf (MetaAndDfs): Metadaten und DataFrames
    """
    names_to_change: dict[str, str] = {}
    for line in mdf.meta.lines.values():
        name: str = line.name

        # check if there is an OBIS-code in the column title
        if match := re.search(clc.ObisElectrical.pattern, name):
            line.obis = clc.ObisElectrical(match[0])
            line.name = line.obis.name
            line.name_orgidx = (
                f"{line.obis.name}{cont.Suffixes.col_original_index}"
                if cont.Suffixes.col_original_index not in line.obis.name
                else line.obis.name
            )
            line.tit = line.obis.name
            line.unit = line.unit or line.obis.unit
            line.unit_h = line.unit.strip("h")

            mdf.df = mdf.df.rename({name: line.obis.name})
            names_to_change[name] = line.obis.name

    for old, new in names_to_change.items():
        mdf.meta.lines[new] = mdf.meta.lines.pop(old)

    return mdf


def convert_15min_kwh_to_kw(mdf: cld.MetaAndDfs) -> cld.MetaAndDfs:
    """Falls die Daten als 15-Minuten-Daten vorliegen,
    wird geprüft ob es sich um Verbrauchsdaten handelt.
    Falls dem so ist, werden sie mit 4 multipliziert um
    Leistungsdaten zu erhalten.

    Die Leistungsdaten werden in neue Spalten im
    DataFrame geschrieben.

    Args:
        - mdf (MetaAndDfs): Metadaten und DataFrames
    """

    if mdf.meta.td_interval not in ["15min"]:
        logger.debug("Skipped 'convert_15min_kwh_to_kw'")
        return mdf

    suffixes: list[str] = cont.ARBEIT_LEISTUNG.all_suffixes

    arbeit_leistung_split: dict[str, Literal["Arbeit", "Leistung"]] = {}
    for col in mdf.meta.lines:
        unit: str = (mdf.meta.lines[col].unit or "").strip()
        suffix_not_in_col_name: bool = all(suffix not in col for suffix in suffixes)
        unit_is_leistung_or_arbeit: bool = unit in [
            *cont.ARBEIT_LEISTUNG.arbeit.possible_units,
            *cont.ARBEIT_LEISTUNG.leistung.possible_units,
        ]
        if suffix_not_in_col_name and unit_is_leistung_or_arbeit:
            original_type: Literal["Arbeit", "Leistung"] = (
                "Arbeit"
                if unit in cont.ARBEIT_LEISTUNG.arbeit.possible_units
                else "Leistung"
            )
            arbeit_leistung_split[col] = original_type

    for col, org_type in arbeit_leistung_split.items():
        mdf = insert_column_arbeit_leistung(org_type, mdf, col)
        mdf = rename_column_arbeit_leistung(org_type, mdf, col)

    return mdf


def rename_column_arbeit_leistung(
    original_data_type: Literal["Arbeit", "Leistung"],
    mdf: cld.MetaAndDfs,
    col: str,
) -> cld.MetaAndDfs:
    """Wenn Daten als Arbeit oder Leistung in 15-Minuten-Auflösung
    vorliegen, wird die Originalspalte umbenannt (mit Suffix "Arbeit" oder "Leistung")
    und in den Metadaten ein Eintrag für den neuen Spaltennamen eingefügt.


    Args:
        - original_data_type (Literal['Arbeit', 'Leistung']):
            Sind die Daten "Arbeit" oder "Leistung"
        - mdf (MetaAndDfs): Metadaten und DataFrames
        - col (str): Name der (Original-) Spalte
    """
    new_name: str = f"{col}{cont.ARBEIT_LEISTUNG.get_suffix(original_data_type)}"
    mdf.df = mdf.df.rename({col: new_name})
    mdf.meta.lines[new_name] = mdf.meta.copy_line(col, new_name)

    logger.info(f"Spalte '{col}' umbenannt in '{new_name}'")

    return mdf


def insert_column_arbeit_leistung(
    original_data: Literal["Arbeit", "Leistung"],
    mdf: cld.MetaAndDfs,
    col: str,
) -> cld.MetaAndDfs:
    """Wenn Daten als Arbeit oder Leistung in 15-Minuten-Auflösung
    vorliegen, wird eine neue Spalte mit dem jeweils andern Typ eingefügt.


    Args:
        - original_data (Literal['Arbeit', 'Leistung']):
            Sind die Daten "Arbeit" oder "Leistung"
        - mdf (MetaAndDfs): Metadaten und DataFrames
        - col (str): Name der (Original-) Spalte
    """

    new_type: str = "Arbeit" if original_data == "Leistung" else "Leistung"
    new_name: str = f"{col}{cont.ARBEIT_LEISTUNG.get_suffix(new_type)}"

    if original_data == "Arbeit":
        mdf.df = mdf.df.with_columns((pl.col(col) * 4).alias(new_name))
        old_unit: str = mdf.meta.lines[col].unit or " kWh"
        new_unit: str = old_unit[:-1]
    else:
        mdf.df = mdf.df.with_columns((pl.col(col) / 4).alias(new_name))
        old_unit = mdf.meta.lines[col].unit or " kW"
        new_unit: str = f"{old_unit}h"

    mdf.meta.lines[new_name] = mdf.meta.copy_line(col, new_name)
    mdf.meta.lines[new_name].unit = new_unit

    logger.info(f"Spalte '{new_name}' mit Einheit '{new_unit}' eingefügt.")

    return mdf
