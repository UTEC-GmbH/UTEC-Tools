"""Import und Download von Excel-Dateien"""

import io

import polars as pl
from loguru import logger

import modules.classes as cl
import modules.general_functions as gf


@gf.func_timer
def import_prefab_excel(
    file: io.BytesIO | None = None,
) -> tuple[pl.DataFrame, dict[str, str]]:
    """Import and download Excel files.

    Args:
    - file (io.BytesIO | None): Optional BytesIO object representing
        the Excel file to import.
        If None, a default example file will be used (for testing).

    Returns:
    - tuple[pl.DataFrame, dict[str, str]]: A tuple containing the imported DataFrame
        and a dictionary mapping column names to units extracted from the Excel file.
    """

    phil: io.BytesIO | str = (
        file or "example_files/Auswertung Stromlastgang - einzelnes Jahr.xlsx"
    )

    mark_ind: str = cl.ExcelMarkers(cl.MarkerType.INDEX).marker_string

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

    # remove empty rows and columns
    df = remove_empty(df)

    # rename columns
    df = rename_columns(df, mark_ind)

    # extract units
    units: dict[str, str] = df.select(
        [col for col in df.columns if col != mark_ind]
    ).row(0, named=True)

    # clean up DataFrame
    df = clean_up_df(df, mark_ind)
    logger.info(df.head())

    return df, units


def clean_up_df(df: pl.DataFrame, mark_ind: str) -> pl.DataFrame:
    """Clean up the DataFrame and adjust the data types"""
    df = df.slice(2)
    df = df.select(
        [pl.col(mark_ind).str.strptime(pl.Datetime, "%d.%m.%Y %T")]
        + [pl.col(col).cast(pl.Float32) for col in df.columns if col != mark_ind]
    )
    return df


def rename_columns(df: pl.DataFrame, mark_ind: str) -> pl.DataFrame:
    """Rename the columns of the DataFrame"""

    # find index marker
    ind_col: str = [str(col) for col in df.columns if mark_ind in df.get_column(col)][0]
    logger.info(f"Index-marker found in column '{ind_col}'")

    # rename columns
    cols: tuple = df.row(by_predicate=pl.col(ind_col) == "↓ Index ↓")
    df.columns = [str(col) for col in cols]

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
        df = df.filter(~pl.all(pl.all().is_null()))

    # remove columns where all values are 'null'
    if col:
        df = df[[col.name for col in df if col.null_count() != df.height]]

    return df
