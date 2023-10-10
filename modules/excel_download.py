"""Download the generated DataFrame as an Excel-File"""

import io

import polars as pl
import xlsxwriter

from modules import classes_data as cld
from modules import constants as cont
from modules import general_functions as gf


@gf.func_timer
def excel_download(df: dict[str, pl.DataFrame], meta: cld.MetaData) -> bytes:
    """Download data as an Excel file.

    Args:
        - df (DataFrame): The data frame to download.
        - meta (MetaData): meta data with number formats
        - page (str, optional): The name of the page to use in the Excel file.
            Defaults to "graph".

    Returns:
        - bytes: The Excel file as a bytes object.
    """

    column_offset: int = 2
    row_offset: int = 4

    output = io.BytesIO()

    with xlsxwriter.Workbook(output) as wb:
        for worksh, data in df.items():
            wb.add_worksheet(worksh)
            data.write_excel(
                workbook=wb,
                worksheet=worksh,
                position=(row_offset, column_offset),
                hide_gridlines=True,
                autofit=True,
                has_header=True,
                header_format={"align": "right", "bottom": 1},
                column_formats={
                    name: line.excel_number_format or "#,##0.0"
                    for name, line in meta.lines.items()
                },
                column_widths={
                    "Datum": 120,
                    cont.SPECIAL_COLS.index: 120,
                    cont.SPECIAL_COLS.original_index: 120,
                },
                dtype_formats={
                    pl.Datetime: "DD.MM.YYYY hh:mm",
                    pl.Date: "DD.MM.YYYY",
                },
            )

    return output.getvalue()
