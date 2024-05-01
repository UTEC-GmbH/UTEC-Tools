"""Eine Dauerlinie oder ein Lastgang, 
der in großen Schritten gebeben ist, 
auf Stundenwerte umrechnen
"""

import polars as pl
from scipy import interpolate

from modules import excel_import as ex_in


def import_file(file: str = "experiments/JDL_Behringen_FL.xlsx") -> pl.DataFrame:
    """Datei importieren"""
    return ex_in.general_excel_import(file)


def interpolate_missing_data_akima(
    df: pl.DataFrame, index_column: str | None = None
) -> pl.DataFrame:
    """Interpolate missing data"""

    col_index: str = index_column or "Stunde"

    cols: list[str] = [
        col
        for col in df.columns
        if col_index not in col
        and any(df[col].is_null())
        and df[col].dtype.is_numeric()
    ]

    no_nulls: pl.DataFrame = df.drop_nulls()
    index: pl.Series = no_nulls[col_index]
    return df.sort(col_index).with_columns(
        pl.Series(
            col,
            interpolate.Akima1DInterpolator(x=index, y=no_nulls[col])(df[col_index]),
        )
        for col in cols
    )


def upsample_to_hourly(df: pl.DataFrame) -> pl.DataFrame:
    """Dauerlinie auf Stundenwerte umrechnen"""
    df_expanded: pl.DataFrame = pl.DataFrame(
        {"Stunde": pl.int_range(0, 8761, eager=True)}
    ).join(df, on="Stunde", how="outer_coalesce")

    return interpolate_missing_data_akima(df_expanded, "Stunde")


def excel_download(df: pl.DataFrame) -> None:
    """Download data as an Excel file.

    Args:
        - df_dic (dict[str, pl.DataFrame]): Dictionary of data frames to download.
            (every data frame gets its own worksheet)
        - meta (MetaData): meta data with number formats
        - page (str, optional): The name of the page to use in the Excel file.
            Defaults to "graph".

    Returns:
        - bytes: The Excel file as a bytes object.

    """

    column_offset: int = 2
    row_offset: int = 4

    worksh: str = "Stundenwerte"

    df.write_excel(
        workbook="C:\\Users\\fl\\Desktop\\JDL_Behringen_Stunden_FL.xlsx",
        worksheet=worksh,
        position=(row_offset, column_offset),
        hide_gridlines=True,
        autofit=True,
        include_header=True,
    )


def run_standard() -> None:
    """Run everything with default values"""

    df: pl.DataFrame = import_file()
    df = upsample_to_hourly(df)

    excel_download(df)
