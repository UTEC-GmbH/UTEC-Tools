# sourcery skip: avoid-global-variables
"""Show stuff on a map"""


from io import BytesIO

import plotly.graph_objects as go
import polars as pl
import streamlit as st
from loguru import logger

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


def plot_map(uploaded_file: BytesIO | str, **kwargs) -> go.Figure:
    """Plot map"""
    graph_height: int = 750
    locations: pl.DataFrame = ex_i.general_excel_import(file=uploaded_file)
    # markers: list[fk.kml.Placemark] = mp.get_all_placemarkers_from_kmz_or_kml()
    # locations: list[cld.Location] = mp.list_or_df_of_locations_from_markers(markers)
    fig: go.Figure = mp.main_map_scatter(
        locations,
        title="PV-Potenzial Fischereihafen"
        '<i><span style="font-size: 12px;">'
        " (Punktgröße referenziert Leistungspotenzial)</span></i>",
        height=graph_height,
        ref_size=kwargs.get("ref_size") or "Leistung",
        ref_size_unit="kWp",
        ref_col="spezifische Leistung",
        ref_col_unit="kWh/kWp",
    )
    st.plotly_chart(
        fig,
        use_container_width=True,
        theme=cont.ST_PLOTLY_THEME,
        config=fig_format.plotly_config(height=graph_height, title_edit=False),
    )
    return fig


def export_to_html(fig: go.Figure) -> None:
    """Export to html"""

    st.markdown("---")

    ani_height = 30
    if sf.s_get("butt_html_map"):
        mp.html_exp(fig)
        f_pn = "export\\Kartografische_Datenauswertung.html"
        cols: list = st.columns(3)
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


if uauth.authentication(sf.s_get("page")):
    if sf.s_get("but_example_direct"):
        st.session_state["f_up"] = f"example_map/{sf.s_get('sb_example_file')}.xlsx"

    if sf.s_get("f_up") is None:
        logger.warning("No file provided yet.")

        menu_m.sidebar_file_upload()

        st.warning("Bitte Datei hochladen oder Beispiel auswählen")

        st.markdown("###")
        st.markdown("---")
    else:
        logger.info(f"File to analyse: '{sf.s_get('f_up')}'")
        with st.sidebar:
            st.markdown("###")
            st.button(
                label="✨  Auswertung neu starten  ✨",
                key="but_complete_reset",
                use_container_width=True,
                help="Auswertung zurücksetzen um andere Datei hochladen zu können.",
            )
            st.write("---")

        fig: go.Figure = plot_map(sf.s_get("f_up"))
        export_to_html(fig)
