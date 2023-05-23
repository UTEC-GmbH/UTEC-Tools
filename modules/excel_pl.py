"""Import und Download von Excel-Dateien"""

import io
import re
from typing import NamedTuple

import polars as pl
from loguru import logger

import modules.classes as cl
import modules.general_functions as gf
import modules.logger_setup as los
from modules import constants as cont


@gf.func_timer
def import_prefab_excel(
    file: io.BytesIO | str,
) -> tuple[pl.DataFrame, cl.MetaData]:
    """Import and download Excel files.

    Args:
    - file (io.BytesIO | None): Optional BytesIO object representing
        the Excel file to import.
        If None, a default example file will be used (for testing).

    Returns:
    - tuple[pl.DataFrame, dict]: A tuple containing the imported DataFrame
        and a dictionary with metadata extracted from the Excel file.

    Example files for testing:
    - file = "example_files/Auswertung Stromlastgang - einzelnes Jahr.xlsx"
    - file = "example_files/Stromlastgang - mehrere Jahre.xlsx"
    - file = "example_files/Wärmelastgang - mehrere Jahre.xlsx"
    """

    mark_index: str = cl.ExcelMarkers(cl.MarkerType.INDEX).marker_string
    mark_units: str = cl.ExcelMarkers(cl.MarkerType.UNITS).marker_string

    df: pl.DataFrame = pl.read_excel(
        file,
        sheet_name="Daten",
        xlsx2csv_options={
            "skip_empty_lines": True,
            "skip_trailing_columns": True,
            "dateformat": "%d.%m.%Y %T",
        },
        read_csv_options={"has_header": False, "try_parse_dates": False},
    )  # type: ignore

    # remove empty rows and columns and rename columns
    df = remove_empty(df)
    df = rename_columns(df, mark_index)

    # extract units and set y-axis accordingly

    meta: cl.MetaData = meta_units(df, mark_index, mark_units)
    meta = set_y_axis_for_lines(meta)

    # clean up DataFrame
    df = clean_up_df(df, mark_index)
    df = clean_up_daylight_savings(df, mark_index).df_clean

    # copy index in separate column to preserve if index is changed (multi year)
    df = df.with_columns(pl.col(mark_index).alias("orgidx"))

    # meta Zeit
    meta = temporal_metadata(df, mark_index, meta)

    # meta data if obis code in column title
    meta = meta_from_obis(df, meta)

    for line in meta.lines:
        if line.name != line.tit:
            df = df.rename({line.name: line.tit})

    logger.info(meta)

    los.log_df(df)
    logger.success("Excel-Datei importiert.")

    return df, meta


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


def rename_columns(df: pl.DataFrame, mark_ind: str) -> pl.DataFrame:
    """Rename the columns of the DataFrame"""

    # find index marker
    ind_col: str = [str(col) for col in df.columns if mark_ind in df.get_column(col)][0]
    logger.info(f"Index-marker found in column '{ind_col}'")

    # rename columns
    cols: tuple = df.row(by_predicate=pl.col(ind_col) == mark_ind)
    df.columns = [str(col) for col in cols]

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
            cl.MetaLine(name=line, orig_tit=line, tit=line, unit=unit)
            for line, unit in units.items()
        ],
    )

    return meta


def set_y_axis_for_lines(meta: cl.MetaData) -> cl.MetaData:
    """Y-Achsen der Linien"""

    for line in meta.lines:
        if line.unit not in meta.units.set_units:
            continue
        index_unit: int = meta.units.set_units.index(line.unit)
        if index_unit > 0:
            meta.get_line(line.name).y_axis = f"y{index_unit + 1}"
        logger.info(f"{line.name}: Y-Achse '{meta.get_line(line.name).y_axis}'")

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
        - df (pd.DataFrame): DataFrame to edit

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
        logger.log(los.LogLevel.DATA_FRAME.name, df_deleted)
    else:
        logger.info("No data deleted due to daylight savings")

    return CleanUpDLS(df_clean=df_clean, df_deleted=df_deleted)


def temporal_metadata(
    df: pl.DataFrame, mark_index: str, meta: cl.MetaData
) -> cl.MetaData:
    """Get information about the time index."""

    if not df.get_column(mark_index).is_temporal():
        logger.error("Kein Zeitindex gefunden!!!")
        return meta

    viertel: int = 15
    std: int = 60

    meta.datetime = True
    meta.years = df.get_column(mark_index).dt.year().unique().sort().to_list()

    meta.td_mean = int(
        df.select(pl.col(mark_index).diff().dt.minutes().drop_nulls().mean()).item()
    )

    if meta.td_mean == viertel:
        meta.td_interval = "15min"
        logger.info("Index mit zeitlicher Auflösung von 15 Minuten erkannt.")
    elif meta.td_mean == std:
        meta.td_interval = "h"
        logger.info("Index mit zeitlicher Auflösung von 1 Stunde erkannt.")
    else:
        logger.debug(f"Mittlere zeitliche Auflösung des df: {meta.td_mean} Minuten")

    return meta


def meta_from_obis(df: pl.DataFrame, meta: cl.MetaData) -> cl.MetaData:
    """Update the meta data if there is an obis code in a column title.

    If there's an OBIS-code (e.g. 1-1:1.29.0), the following meta data is edited:
    - obis -> instance of ObisElecgtrical class
    - unit -> only if not given in Excel-File
    - tite -> "alternative name (code)"

    Args:
        - df (pl.DataFrame): DataFrame to inspect
        - meta (MetaData): MetaData dataclass

    Returns:
        - meta (MetaData): updated MetaData dataclass
    """

    for line in meta.lines:
        name: str = line.name

        # check if there is an OBIS-code in the column title
        if match := re.search(cont.OBIS_PATTERN_EL, name):
            line.obis = cl.ObisElectrical(match[0])
            line.unit = line.unit or line.obis.unit
            line.tit = line.obis.name

    return meta
