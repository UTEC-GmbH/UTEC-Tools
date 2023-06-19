"""Download the generated DataFrame as an Excel-File"""

import io
from typing import Any

import polars as pl
import xlsxwriter

from modules import classes_constants as clc
from modules import classes_data as cl
from modules import constants as cont
from modules import general_functions as gf


@gf.func_timer
def excel_download(
    df: pl.DataFrame, meta: cl.MetaData, page_short: str = "graph"
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

    with io.BytesIO() as output, xlsxwriter.Workbook(output) as workbook:
        worksheet: Any = workbook.add_worksheet(ws_name)

        df.write_excel(
            workbook,
            worksheet=ws_name,
            position=(row_offset, column_offset),
            has_header=True,
            hide_gridlines=True,
            autofit=True,
            dtype_formats={pl.Datetime: "TT.MM.JJJJ hh:mm", pl.Date: "TT.MM.JJJJ"},
        )

        format_worksheet(
            workbook,
            worksheet,
            df,
            meta,
            offset_col=column_offset,
            offset_row=row_offset,
        )

        return output.getvalue()


def format_worksheet(
    workbook: Any,
    worksheet: Any,
    df: pl.DataFrame,
    meta: cl.MetaData,
    **kwargs: Any,
) -> None:
    """Edit the formatting of the worksheet in the output excel-file

    Args:
        - wkb (Any): Workbook
        - wks (Any): Worksheet
        - df (pd.DataFrame): main pd.DataFrame
        - dic_num_formats (dict): dictionary {col: number format}
    KWArgs:
        - offset_col (int): Spalte, in der die Daten eingefügt weren
        - offset_row (int): Reihe, in der die Daten eingefügt weren
    """

    offset: dict[str, int] = {
        "col": kwargs.get("offset_col") or 2,
        "row": kwargs.get("offset_row") or 4,
    }

    cols: list[str] = [
        col
        for col in df.columns
        if all(
            col not in idx
            for idx in [cont.SPECIAL_COLS.index, cont.SPECIAL_COLS.original_index]
        )
    ]

    # Formatierung
    worksheet.hide_gridlines(2)
    base_format: dict[str, Any] = {
        "bold": False,
        "font_name": "Arial",
        "font_size": 10,
        "align": "right",
        "border": 0,
    }

    # Formatierung der ersten Spalte
    spec_format: dict[str, Any] = base_format.copy()
    spec_format["align"] = "left"
    cell_format: Any = workbook.add_format(spec_format)
    worksheet.set_column(offset["col"], offset["col"], 18, cell_format)

    # Formatierung der ersten Zeile
    spec_format = base_format.copy()
    spec_format["bottom"] = 1
    cell_format = workbook.add_format(spec_format)
    worksheet.write(offset["row"], offset["col"], "Datum", cell_format)

    for col, header in enumerate(cols):
        worksheet.write(offset["row"], col + 1 + offset["col"], header, cell_format)

    for num_format in meta.get_all_num_formats():
        spec_format = base_format.copy()
        spec_format["num_format"] = num_format
        col_format: Any = workbook.add_format(spec_format)

        for cnt, col in enumerate(cols):
            if meta.get_line_by_name(col).excel_number_format == num_format:
                worksheet.set_column(
                    cnt + offset["col"] + 1,
                    cnt + offset["col"] + 1,
                    len(col) + 1,
                    col_format,
                )
