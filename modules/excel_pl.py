"""Import und Download von Excel-Dateien"""

import io

import polars as pl
from loguru import logger

import modules.general_functions as gf


@gf.func_timer
def import_prefab_excel(file: io.BytesIO | None = None) -> pl.DataFrame:
    """Vordefinierte Excel-Datei importieren"""
    phil: io.BytesIO | str = (
        file or "example_files/Auswertung Stromlastgang - einzelnes Jahr.xlsx"
    )
    df_messy: pl.DataFrame = pl.read_excel(
        phil,
        sheet_name="Daten",
        xlsx2csv_options={"skip_empty_lines": True, "skip_trailing_columns": True},
        read_csv_options={"has_header": False},
    )  # type: ignore
    logger.info(df_messy.head())

    return df_messy
