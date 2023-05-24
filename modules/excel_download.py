"""Download the generated DataFrame as an Excel-File"""

import io
from typing import Any, NamedTuple

import polars as pl
import xlsxwriter

import modules.general_functions as gf


@gf.func_timer
def excel_download(df: pl.DataFrame, page: str = "graph") -> bytes:
    """Download data as an Excel file.

    Args:
        - df (pd.DataFrame): The data frame to download.
        - page (str, optional): The name of the page to use in the Excel file.
            Defaults to "graph".

    Returns:
        - bytes: The Excel file as a bytes object.
    """
    name_and_format: WsNameNumFormat = ws_name_num_format(df, page)
    ws_name: str = name_and_format.worksheet_name
    num_formats: dict[str, str] = name_and_format.number_formats

    column_offset: int = 2
    row_offset: int = 4

    # pylint: disable=abstract-class-instantiated
    with io.BytesIO() as output, xlsxwriter.Workbook(output) as wb:
        df.write_excel(
            wb,
            worksheet=ws_name,
            position=(row_offset, column_offset),
            has_header=True,
            hide_gridlines=True,
            autofit=True,
        )

        workbook: Any = wb.book
        worksheet: Any = wb.sheets[ws_name]

        format_worksheet(
            workbook,
            worksheet,
            df,
            num_formats,
            offset_col=column_offset,
            offset_row=row_offset,
        )

    return output.getvalue()


@func_timer
def format_worksheet(
    workbook: Any,
    worksheet: Any,
    df: pl.DataFrame,
    number_formats: dict[str, str],
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
    offset_col: int = kwargs.get("offset_col") or 2
    offset_row: int = kwargs.get("offset_row") or 4

    cols: list[str] = [str(col) for col in df.columns]

    # Formatierung
    worksheet.hide_gridlines(2)
    base_format: dict[str, Any] = {
        "bold": False,
        "font_name": "Arial",
        "font_size": 10,
        "align": "right",
        "border": 0,
    }

    # erste Spalte
    spec_format: dict[str, Any] = base_format.copy()
    spec_format["align"] = "left"
    cell_format: Any = workbook.add_format(spec_format)
    worksheet.set_column(offset_col, offset_col, 18, cell_format)

    # erste Zeile
    spec_format = base_format.copy()
    spec_format["bottom"] = 1
    cell_format = workbook.add_format(spec_format)
    worksheet.write(offset_row, offset_col, "Datum", cell_format)

    for col, header in enumerate(cols):
        worksheet.write(offset_row, col + 1 + offset_col, header, cell_format)

    for num_format in number_formats.values():
        spec_format = base_format.copy()
        spec_format["num_format"] = num_format
        col_format: Any = workbook.add_format(spec_format)

        for cnt, col in enumerate(cols):
            if number_formats[col] == num_format:
                worksheet.set_column(
                    cnt + offset_col + 1,
                    cnt + offset_col + 1,
                    len(col) + 1,
                    col_format,
                )


class WsNameNumFormat(NamedTuple):
    """Named tuple for the return value of the following function."""

    worksheet_name: str
    number_formats: dict[str, str]


def ws_name_num_format(df: pl.DataFrame, page: str) -> WsNameNumFormat:
    """Worksheet name and number fromat based on app page

    Args:
        - df (pd.DataFrame): main data frame
        - page (str): page of app (graph or meteo...)

    Returns:
        - tuple[str, dict]: ws_name, dic_num_formats = {column: number format}
    """

    page_mapping: dict[str, dict[str, Any]] = {
        "meteo": {
            "ws_name": "Wetterdaten",
            "num_formats": {par.tit_de: par.num_format for par in meteo.LIS_PARAMS},
        },
        "graph": {
            "ws_name": "Daten",
            "num_formats": {
                key: f'#,##0.0"{st.session_state["metadata"][key]["unit"]}"'
                for key in [str(col) for col in df.columns]
            },
        },
    }
    if page not in page_mapping:
        err_msg: str = f"Invalid page: {page}"
        raise ValueError(err_msg)
    mapping: dict[str, Any] = page_mapping[page]

    return WsNameNumFormat(
        worksheet_name=mapping["ws_name"], number_formats=mapping["num_formats"]
    )
