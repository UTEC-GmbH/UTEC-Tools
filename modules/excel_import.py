"""Import und Download von Excel-Dateien"""

import io
import re
from typing import Any, Literal, NamedTuple

import polars as pl
from loguru import logger

from modules import classes_constants as clc
from modules import classes_data as cl
from modules import constants as cont
from modules import df_manipulation as df_man
from modules import general_functions as gf
from modules import setup_logger as slog

TEST_FILE = "example_files/Stromlastgang - mehrere Jahre.xlsx"


@gf.func_timer
def import_prefab_excel(file: io.BytesIO | str = TEST_FILE) -> cl.MetaAndDfs:
    """Import and download Excel files.

    Args:
    - file (io.BytesIO | str): BytesIO object or string
        representing the Excel file to import.

    Returns:
    - MetaAndDfs: DataFrames and meta data extracted from the Excel file.

    Example files for testing:
    - file = "example_files/Auswertung Stromlastgang - einzelnes Jahr.xlsx"
    - file = "example_files/Stromlastgang - mehrere Jahre.xlsx"
    - file = "example_files/Wärmelastgang - mehrere Jahre.xlsx"

    Example test run:
    mdf = import_prefab_excel()
    """

    mark_index: str = cont.EXCEL_MARKERS.index
    mark_units: str = cont.EXCEL_MARKERS.units

    df: pl.DataFrame = get_df_from_excel(file)

    # remove empty rows and columns and rename columns
    df = remove_empty(df)
    df = rename_columns(df, mark_index)

    # extract units
    meta: cl.MetaData = meta_units(df, mark_index, mark_units)

    # clean up DataFrame
    df = clean_up_df(df, mark_index)

    mdf: cl.MetaAndDfs = cl.MetaAndDfs(meta, df)
    # meta data if obis code in column title
    mdf = meta_from_obis(mdf)

    # Weitere Metadaten
    mdf = temporal_metadata(mdf, mark_index)
    mdf.meta = set_y_axis_for_lines(mdf.meta)
    mdf.meta = meta_number_format(mdf)

    # 15min und kWh
    mdf = convert_15min_kwh_to_kw(mdf)

    slog.log_df(mdf.df)

    if mdf.meta.multi_years:
        mdf.df_multi = df_man.split_multi_years(mdf, "df")

    logger.success("Excel-Datei importiert.")
    logger.info(f"Imported lines: \n{mdf.meta.get_all_line_names()}")

    return mdf


def get_df_from_excel(file: io.BytesIO | str) -> pl.DataFrame:
    """Excel Import via csv-conversion"""

    sheet: str = "Daten"
    xlsx_options: dict[str, str | bool] = {
        "skip_empty_lines": True,
        "skip_trailing_columns": True,
        "dateformat": "%d.%m.%Y %T",
    }
    csv_options: dict[str, bool] = {"has_header": False, "try_parse_dates": False}

    return pl.read_excel(
        file,
        sheet_name=sheet,
        xlsx2csv_options=xlsx_options,
        read_csv_options=csv_options,
    )


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
        df = df.filter(~pl.all(pl.all().is_null()))  # pylint: disable=E1130

    # remove columns where all values are 'null'
    if col:
        df = df[[col.name for col in df if col.null_count() != df.height]]

    return df


def rename_columns(df: pl.DataFrame, mark_index: str) -> pl.DataFrame:
    """Rename the columns of the DataFrame"""

    # find index marker
    ind_col: str = [col for col in df.columns if mark_index in df.get_column(col)][0]
    logger.info(f"Index-marker found in column '{ind_col}'")

    # rename columns
    cols: tuple = df.row(by_predicate=pl.col(ind_col) == mark_index)
    df.columns = list(cols)

    return df


def meta_units(df: pl.DataFrame, mark_index: str, mark_units: str) -> cl.MetaData:
    """Get units for dataclass"""

    units: dict[str, str] = (
        df.filter(pl.col(mark_index) == mark_units)
        .select([col for col in df.columns if col != mark_index])
        .row(0, named=True)
    )

    # leerzeichen vor Einheit
    units = {line: f" {unit.strip()}" for line, unit in units.items()}

    meta: cl.MetaData = cl.MetaData(
        units=cl.MetaUnits(
            all_units=list(units.values()),
            set_units=gf.sort_list_by_occurance(list(units.values())),
        ),
        lines=[
            cl.MetaLine(
                name=line,
                name_orgidx=f"{line}{cont.SUFFIXES.col_original_index}"
                if cont.SUFFIXES.col_original_index not in line
                else line,
                orig_tit=line,
                tit=line,
                unit=unit,
            )
            for line, unit in units.items()
        ],
    )

    return meta


def meta_number_format(mdf: cl.MetaAndDfs) -> cl.MetaData:
    """Define Number Formats for Excel-Export"""

    # cut-off for decimal places
    decimal_0: int = 1000
    decimal_1: int = 100
    decimal_2: int = 10

    quantiles: pl.DataFrame = mdf.df.quantile(0.95)

    for line in mdf.meta.lines:
        if line.name in mdf.df.columns:
            line_quant: Any = quantiles.get_column(line.name).item()
            if any(isinstance(line_quant, number) for number in [int, float]):
                if abs(line_quant) >= decimal_0:
                    line.excel_number_format = f'#.##0"{line.unit}"'
                if abs(line_quant) >= decimal_1:
                    line.excel_number_format = f'#.##0,0"{line.unit}"'
                if abs(line_quant) >= decimal_2:
                    line.excel_number_format = f'#.##0,00"{line.unit}"'
                else:
                    line.excel_number_format = f'#.##0,000"{line.unit}"'

    return mdf.meta


def meta_units_update(meta: cl.MetaData) -> cl.MetaData:
    """Update units with all units from metadata"""

    all_units: list[str] = [str(line.unit) for line in meta.lines]
    meta.units.all_units = all_units
    meta.units.set_units = gf.sort_list_by_occurance(all_units)

    return meta


def set_y_axis_for_lines(meta: cl.MetaData) -> cl.MetaData:
    """Y-Achsen der Linien"""

    for line in meta.lines:
        if line.unit not in meta.units.set_units:
            continue
        index_unit: int = meta.units.set_units.index(line.unit)
        if index_unit > 0:
            meta.get_line_by_name(line.name).y_axis = f"y{index_unit + 1}"
        logger.info(f"{line.name}: Y-Achse '{meta.get_line_by_name(line.name).y_axis}'")

    return meta


def clean_up_df(df: pl.DataFrame, mark_index: str) -> pl.DataFrame:
    """Clean up the DataFrame and adjust the data types"""

    ind_row: int = (
        df.with_row_count().filter(pl.col(mark_index) == mark_index).row(0)[0]
    )
    df = df.slice(ind_row + 1)
    df = df.select(
        [pl.col(mark_index).str.strptime(pl.Datetime, "%d.%m.%Y %T")]
        + [pl.col(col).cast(pl.Float32) for col in df.columns if col != mark_index]
    )

    df = clean_up_daylight_savings(df, mark_index).df_clean

    # copy index in separate column to preserve if index is changed (multi year)
    df = df.with_columns(pl.col(mark_index).alias(cont.SPECIAL_COLS.original_index))

    return df


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

    Returns:
        - dict[str, pd.DataFrame]:
            - "df_clean": edited DataFrame
            - "df_deleted": deleted data
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


def temporal_metadata(mdf: cl.MetaAndDfs, mark_index: str) -> cl.MetaAndDfs:
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

    if mdf.meta.td_mnts == cont.TIME_MIN.quarter_hour:
        mdf.meta.td_interval = "15min"
        logger.info("Index mit zeitlicher Auflösung von 15 Minuten erkannt.")
    elif mdf.meta.td_mnts == cont.TIME_MIN.hour:
        mdf.meta.td_interval = "h"
        mdf.df_h = mdf.df
        logger.info("Index mit zeitlicher Auflösung von 1 Stunde erkannt.")
    else:
        logger.debug(f"Mittlere zeitliche Auflösung des df: {mdf.meta.td_mnts} Minuten")

    return mdf


def meta_from_obis(mdf: cl.MetaAndDfs) -> cl.MetaAndDfs:
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

    for line in mdf.meta.lines:
        name: str = line.name

        # check if there is an OBIS-code in the column title
        if match := re.search(clc.ObisElectrical.pattern, name):
            line.obis = clc.ObisElectrical(match[0])
            line.name = line.obis.name
            line.name_orgidx = (
                f"{line.obis.name}{cont.SUFFIXES.col_original_index}"
                if cont.SUFFIXES.col_original_index not in line.obis.name
                else line.obis.name
            )
            line.tit = line.obis.name
            line.unit = line.unit or line.obis.unit

            mdf.df = mdf.df.rename({name: line.obis.name})

    mdf.meta = meta_units_update(mdf.meta)

    return mdf


def convert_15min_kwh_to_kw(mdf: cl.MetaAndDfs) -> cl.MetaAndDfs:
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

    for col in mdf.meta.get_all_line_names():
        unit: str = (mdf.meta.get_line_by_name(col).unit or "").strip()
        suffix_not_in_col_name: bool = all(suffix not in col for suffix in suffixes)
        unit_is_leistung_or_arbeit: bool = unit in (
            cont.ARBEIT_LEISTUNG.arbeit.possible_units
            + cont.ARBEIT_LEISTUNG.leistung.possible_units
        )
        if suffix_not_in_col_name and unit_is_leistung_or_arbeit:
            originla_type: Literal["Arbeit", "Leistung"] = (
                "Arbeit"
                if unit in cont.ARBEIT_LEISTUNG.arbeit.possible_units
                else "Leistung"
            )
            mdf = insert_column_arbeit_leistung(originla_type, mdf, col)
            mdf = rename_column_arbeit_leistung(originla_type, mdf, col)

            logger.success(f"Arbeit und Leistung für Spalte '{col}' aufgeteilt")

    mdf.meta = meta_units_update(mdf.meta)

    return mdf


def rename_column_arbeit_leistung(
    original_data_type: Literal["Arbeit", "Leistung"],
    mdf: cl.MetaAndDfs,
    col: str,
) -> cl.MetaAndDfs:
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
    # mdf = copy_line_meta_with_new_name(mdf, col, new_name)
    mdf.meta.copy_line_meta_with_new_name(col, new_name)

    logger.info(f"Spalte '{col}' umbenannt in '{new_name}'")

    return mdf


def insert_column_arbeit_leistung(
    original_data: Literal["Arbeit", "Leistung"],
    mdf: cl.MetaAndDfs,
    col: str,
) -> cl.MetaAndDfs:
    """Wenn Daten als Arbeit oder Leistung in 15-Minuten-Auflösung
    vorliegen, wird eine neue Spalte mit dem jeweils andern Typ eingefügt.


    Args:
        - original_data (Literal['Arbeit', 'Leistung']):
            Sind die Daten "Arbeit" oder "Leistung"
        - mdf (MetaAndDfs): Metadaten und DataFrames
        - col (str): Name der (Original-) Spalte
    """
    new_col_type: str = "Arbeit" if original_data == "Leistung" else "Leistung"
    new_col_name: str = f"{col}{cont.ARBEIT_LEISTUNG.get_suffix(new_col_type)}"
    # mdf = copy_line_meta_with_new_name(mdf, col, new_col_name)
    mdf.meta.copy_line_meta_with_new_name(col, new_col_name)

    if original_data == "Arbeit":
        mdf.df = mdf.df.with_columns((pl.col(col) * 4).alias(new_col_name))
        old_unit: str = mdf.meta.get_line_attribute(col, "unit") or " kWh"
        new_unit: str = old_unit[:-1]
    else:
        mdf.df = mdf.df.with_columns((pl.col(col) / 4).alias(new_col_name))
        old_unit = mdf.meta.get_line_attribute(col, "unit") or " kW"
        new_unit: str = f"{old_unit}h"

    mdf.meta.change_line_attribute(new_col_name, "unit", new_unit)
    logger.info(f"Spalte '{new_col_name}' mit Einheit '{new_unit}' eingefügt")

    return mdf
