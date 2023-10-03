"""Download the generated DataFrame as an Excel-File"""

import io

import polars as pl

from modules import classes_constants as clc
from modules import classes_data as cld
from modules import constants as cont
from modules import general_functions as gf


@gf.func_timer
def excel_download(
    df: pl.DataFrame, meta: cld.MetaData, page_short: str = "graph"
) -> bytes:
    """Download data as an Excel file.

    Args:
        - df (DataFrame): The data frame to download.
        - meta (MetaData): meta data with number formats
        - page (str, optional): The name of the page to use in the Excel file.
            Defaults to "graph".

    Returns:
        - bytes: The Excel file as a bytes object.
    """

    page: clc.StPageProps = getattr(cont.ST_PAGES, page_short)
    ws_name: str = page.excel_ws_name or "Tabelle1"

    column_offset: int = 2
    row_offset: int = 4

    with io.BytesIO() as output:
        df.write_excel(
            output,
            worksheet=ws_name,
            position=(row_offset, column_offset),
            hide_gridlines=True,
            autofit=True,
            has_header=True,
            # header_format={"halign": "right"},
            column_formats={
                name: line.excel_number_format or "#,##0.0"
                for name, line in meta.lines.items()
            },
            column_widths={"Datum": 120},
            dtype_formats={pl.Datetime: "DD.MM.YYYY hh:mm", pl.Date: "DD.MM.YYYY"},
        )

        return output.getvalue()
