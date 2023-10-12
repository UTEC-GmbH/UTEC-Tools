"""Download the generated DataFrame as an Excel-File"""

import io

import polars as pl
import xlsxwriter
from plotly import graph_objects as go

from modules import classes_data as cld
from modules import constants as cont
from modules import fig_formatting as fig_format
from modules import fig_general_functions as fgf
from modules import general_functions as gf
from modules import streamlit_functions as sf


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

    buffer = io.BytesIO()

    with xlsxwriter.Workbook(buffer) as wb:
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

    return buffer.getvalue()


def html_graph() -> str:
    """Return a string to create a html-file"""

    if sf.s_get("cb_jdl"):
        graph_styles = (
            "#las{width: 100%; margin-left:auto; margin-right:auto; }"
            "#jdl{width: 45%; float: left; margin-right: 5%; } "
            "#mon{width: 45%; float: right; margin-left: 5%; } "
        )
    else:
        graph_styles = (
            "#las{width: 100%; margin-left:auto; margin-right:auto; }"
            "#mon{width: 45%; float: left; margin-right: 5%; } "
        )

    all_figs: str = ""

    for fig in [
        cont.FIG_KEYS.lastgang,
        *[
            fig
            for fig in cont.FIG_KEYS.list_all()
            if sf.s_get(f"cb_{fig.split('_')[1]}")
        ],
    ]:
        figure: go.Figure | None = sf.s_get(fig)
        if figure is not None:
            fig_type: str = fgf.fig_type_by_title(figure)
            if "las" in fig_type:
                all_figs = f'{all_figs} <div id="las">'
            elif "jdl" in fig_type:
                all_figs = f'{all_figs} <div id="jdl">'
            elif "mon" in fig_type:
                all_figs = f'{all_figs} <div id="mon">'

            all_figs = (
                f"{all_figs}"
                f"{figure.to_html(full_html=False, config=fig_format.plotly_config())}"
                "<br /><br /><hr><br /><br /><br /></div>"
            )

    return (
        "<!DOCTYPE html>"
        "<title>Interaktive Grafische Datenauswertung</title>"
        "<head><style>"
        "h1{text-align: left; font-family: sans-serif;}"
        "body{width: 85%; margin-left:auto; margin-right:auto}"
        "</style></head>"
        '<body><h1><a href="https://www.utec-bremen.de/">'
        f"{sf.s_get('UTEC_logo') or gf.render_svg()}"
        "</a><br /><br />"
        "Interaktive Grafische Datenauswertung"
        "</h1><br /><hr><br /><br />"
        "<style>"
        f"{graph_styles}"
        "</style>"
        f"{all_figs}"
        "</body></html>"
    )


def html_map(fig: go.Figure) -> str:
    """Return a string to create a html-file"""

    fig_html = fig.to_html(
        full_html=False,
        config=fig_format.plotly_config(height=1600, title_edit=False),
    )

    return (
        "<!DOCTYPE html>"
        "<title>Kartografische Datenauswertung</title>"
        "<head><style>"
        "h1{text-align: left; font-family: sans-serif;}"
        "body{width: 85%; margin-left:auto; margin-right:auto}"
        "</style></head>"
        '<body><h1><a href="https://www.utec-bremen.de/">'
        f"{sf.s_get('UTEC_logo') or gf.render_svg()}"
        "</a><br /><br />"
        "Kartografische Datenauswertung"
        "</h1><br /><hr><br /><br />"
        "<style>"
        "#map{width: 100%; margin-left:auto; margin-right:auto; }"
        "</style>"
        '<div id="map">'
        f"{fig_html}"
        "<br /><br /><hr><br /><br /><br /></div>"
        "</body></html>"
    )