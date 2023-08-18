# sourcery skip: avoid-global-variables
"""Show stuff on a map"""


from io import BytesIO
from typing import Any

import plotly.graph_objects as go
import polars as pl
import streamlit as st
from loguru import logger

from modules import classes_data as cld
from modules import constants as cont
from modules import excel_import as ex_i
from modules import fig_formatting as fig_format
from modules import general_functions as gf
from modules import map as mp
from modules import map_menus as menu_m
from modules import setup_stuff as set_stuff
from modules import streamlit_functions as sf
from modules import user_authentication as uauth

# setup stuff
gf.log_new_run()
set_stuff.page_header_setup(page=cont.ST_PAGES.maps.short)


def plot_map() -> go.Figure:
    """Plot map"""
    graph_height: int = 750

    phil: Any = sf.s_get("f_up")
    if isinstance(phil, str):
        logger.info(f"File to analyse: '{phil}'")
    if isinstance(phil, BytesIO):
        logger.info("File uploaded and available as bytes")

    st_map_df: Any = sf.s_get("map_df")
    if isinstance(st_map_df, pl.DataFrame):
        logger.info("DataFrame of locations available in SessionState")
        df = st_map_df
    elif isinstance(phil, BytesIO | str):
        logger.info("DataFrame will be created from uploaded file.")
        df: pl.DataFrame = df_from_file(phil)
    else:
        raise TypeError

    tit: str | None = sf.s_get("ti_title")
    if sf.s_get("ti_title_add") and sf.s_get("ti_title"):
        tit = (
            f"{tit}"
            '<i><span style="font-size: 12px;"> '
            f"({sf.s_get('ti_title_add')})</span></i>"
        )

    st_locs: Any = sf.s_get("map_locations")
    if isinstance(st_locs, list) and all(
        isinstance(loc, cld.Location) for loc in st_locs
    ):
        locations: list[cld.Location] = st_locs
    else:
        locations = mp.create_list_of_locations_from_df(df)
        sf.s_set("map_locations", locations)

    # markers: list[fk.kml.Placemark] = mp.get_all_placemarkers_from_kmz_or_kml()
    fig_map: go.Figure = mp.main_map_scatter(
        locations,
        title=tit,
        height=graph_height,
    )
    st.plotly_chart(
        fig_map,
        use_container_width=True,
        theme=cont.ST_PLOTLY_THEME,
        config=fig_format.plotly_config(height=graph_height),
    )
    return fig_map


def export_to_html(fig_to_convert: go.Figure) -> None:
    """Export to html"""

    st.markdown("---")

    if sf.s_get("butt_html_map"):
        mp.html_exp(fig_to_convert)
        f_pn = "export\\Kartografische_Datenauswertung.html"
        cols: list = st.columns(3)
        ani_height = 30
        with cols[0]:
            gf.show_lottie_animation(
                "animations/coin_i.json", height=ani_height, speed=0.75
            )
        with cols[1], open(f_pn, "rb") as exfile:
            st.download_button(
                label="✨ html-Datei herunterladen ✨",
                data=exfile,
                file_name=f_pn.rsplit("/", maxsplit=1)[-1],
                mime="application/xhtml+xml",
                use_container_width=True,
            )
        with cols[2]:
            gf.show_lottie_animation(
                "animations/coin_i.json", height=ani_height, speed=0.75
            )
    else:
        st.button(label="html-Export", key="butt_html_map")


def df_from_file(uploaded_file: BytesIO | str) -> pl.DataFrame:
    """Import Excel-File as Polars DataFrame"""

    st_entry: Any = sf.s_get("map_df")

    df: pl.DataFrame = (
        st_entry
        if isinstance(st_entry, pl.DataFrame)
        else ex_i.general_excel_import(uploaded_file)
    )
    sf.s_add_once("map_df", df)

    return df


if uauth.authentication(sf.s_get("page")):
    if sf.s_get("but_complete_reset"):
        sf.s_reset_app()

    if sf.s_get("but_example_direct"):
        sf.s_set("f_up", f"example_map/{sf.s_get('sb_example_file')}.xlsx")

    if all(sf.s_get(key) is None for key in ["f_up", "map_df"]):
        menu_m.sidebar_file_upload()
        menu_m.sidebar_text()
        st.warning("Bitte Datei hochladen oder Beispiel auswählen")

        st.markdown("###")
        st.markdown("---")

        logger.warning("No file provided yet.")
    else:
        menu_m.sidebar_reset()
        menu_m.sidebar_text()
        menu_m.sidebar_slider_size()
        menu_m.sidebar_slider_colour()

        fig: go.Figure = plot_map()
        export_to_html(fig)
