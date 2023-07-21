# sourcery skip: avoid-global-variables
"""Show stuff on a map"""


import plotly.graph_objects as go
import polars as pl
import streamlit as st

from modules import constants as cont
from modules import excel_import as ex_i
from modules import fig_formatting as fig_format
from modules import general_functions as gf
from modules import map as mp
from modules import setup_stuff as set_stuff
from modules import streamlit_functions as sf
from modules import user_authentication as uauth

# setup stuff
gf.log_new_run()
set_stuff.page_header_setup(page=cont.ST_PAGES.maps.short)

if uauth.authentication(sf.s_get("page")):
    graph_height: int = 750
    locations: pl.DataFrame = ex_i.general_excel_import(
        file="tests/sample_data/888 PV-Potenzial py.xlsx", worksheet="Leistungen"
    )
    # markers: list[fk.kml.Placemark] = mp.get_all_placemarkers_from_kmz_or_kml()
    # locations: list[cld.Location] = mp.list_or_df_of_locations_from_markers(markers)
    fig: go.Figure = mp.main_map(
        locations,
        zoom=13,
        title="PV-Potenzial Fischereihafen"
        '<i><span style="font-size: 12px;">'
        " (Punktgröße referenziert Leistungspotenzial)</span></i>",
        height=graph_height,
    )
    st.plotly_chart(
        fig,
        use_container_width=True,
        theme=cont.ST_PLOTLY_THEME,
        config=fig_format.plotly_config(height=graph_height, title_edit=False),
    )

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
