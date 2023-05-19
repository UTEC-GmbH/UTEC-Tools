"""Import und Download von Excel-Dateien"""

import io
import random
from pathlib import Path
from typing import NamedTuple

import polars as pl
from loguru import logger

import modules.classes as cl
import modules.general_functions as gf
import modules.logger_setup as los


@gf.func_timer
def import_prefab_excel(
    file: io.BytesIO | None = None,
) -> tuple[pl.DataFrame, dict]:
    """Import and download Excel files.

    Args:
    - file (io.BytesIO | None): Optional BytesIO object representing
        the Excel file to import.
        If None, a default example file will be used (for testing).

    Returns:
    - tuple[pl.DataFrame, dict]: A tuple containing the imported DataFrame
        and a dictionary with metadata extracted from the Excel file.
    """

    example_files: list[Path] = list(Path(f"{Path.cwd()}/example_files").glob("*.xlsx"))

    phil: io.BytesIO | Path = file or random.choice(example_files)  # noqa: S311

    mark_index: str = cl.ExcelMarkers(cl.MarkerType.INDEX).marker_string
    mark_units: str = cl.ExcelMarkers(cl.MarkerType.UNITS).marker_string

    df: pl.DataFrame = pl.read_excel(
        phil,
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
    meta: dict = get_units(df, mark_index, mark_units)
    meta = set_y_axis_for_lines(meta)
    logger.info(meta)

    # clean up DataFrame
    df = clean_up_df(df, mark_index)
    df = clean_up_daylight_savings(df, mark_index).df_clean

    # copy index in separate column to preserve if index is changed (multi year)
    df = df.with_columns(pl.col(mark_index).alias("orgidx"))

    # meta Zeit
    meta = temporal_metadata(df, mark_index, meta)

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
        df = df.filter(~pl.all(pl.all().is_null()))

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


def get_units(df: pl.DataFrame, mark_index: str, mark_units: str) -> dict:
    """Get units from imported Excel-file"""

    units: dict[str, str] = (
        df.filter(pl.col(mark_index) == mark_units)
        .select([col for col in df.columns if col != mark_index])
        .row(0, named=True)
    )

    # leerzeichen vor Einheit
    units = {line: f" {unit.strip()}" for line, unit in units.items()}

    meta: dict = {
        "units": {
            "all": list(units.values()),
            "set": gf.sort_list_by_occurance(list(units.values())),
        }
    }
    for line, unit in units.items():
        meta[line] = {"unit": unit}
        logger.info(f"{line}: Einheit '{meta[line]['unit']}'")

    return meta


def set_y_axis_for_lines(meta: dict) -> dict:
    """Y-Achsen der Linien"""

    lines_with_units: dict[str, str] = {
        line: meta[line].get("unit") for line in meta if "unit" in meta[line]
    }

    for line, unit in lines_with_units.items():
        ind: int = meta["units"]["set"].index(unit)
        meta[line]["y_axis"] = f"y{ind + 1}" if ind > 0 else "y"
        logger.info(f"{line}: Y-Achse '{meta[line]['y_axis']}'")

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


def temporal_metadata(df: pl.DataFrame, mark_index: str, meta: dict) -> dict:
    """Get information about the time index."""

    if not df.get_column(mark_index).is_temporal():
        logger.error("Kein Zeitindex gefunden!!!")
        return meta

    viertel: int = 15
    std: int = 60
    meta["datetime"] = True
    meta["years"] = df.get_column(mark_index).dt.year().unique().sort().to_list()

    td_mean: int = int(
        df.select(pl.col(mark_index).diff().dt.minutes().drop_nulls().mean()).item()
    )

    meta["td_mean"] = td_mean
    if meta["td_mean"] == viertel:
        meta["td_int"] = "15min"
        logger.info("Index mit zeitlicher Auflösung von 15 Minuten erkannt.")
    elif meta["td_mean"] == std:
        meta["td_int"] = "h"
        logger.info("Index mit zeitlicher Auflösung von 1 Stunde erkannt.")
    else:
        logger.debug(f"Mittlere zeitliche Auflösung des DataFrame: {td_mean} Minuten")

    return meta
