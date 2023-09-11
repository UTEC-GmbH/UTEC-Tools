# sourcery skip: avoid-global-variables
"""Seite Meteorologische Daten"""

import streamlit as st

from modules import constants as cont
from modules import fig_formatting as fig_format
from modules import fig_plotly_plots as ploplo
from modules import general_functions as gf
from modules import meteo_menus as menu_m
from modules import setup_stuff as set_stuff
from modules import streamlit_functions as sf
from modules import user_authentication as uauth

# setup
gf.log_new_run()
set_stuff.page_header_setup(page=cont.ST_PAGES.meteo.short)


if uauth.authentication(sf.s_get("page")):
    # Auswahl Ort
    menu_m.sidebar_address_dates()
    if sf.s_get("but_addr_dates"):
        for session_state_entry in ["geo_location", "stations_distance", "params_list"]:
            sf.s_delete(key=session_state_entry)

    cols: list = st.columns([40, 60])
    with cols[0]:
        menu_m.parameter_selection()
        st.markdown("###")
        menu_m.download_as_excel()

    with cols[1]:
        plot_height = 750
        st.plotly_chart(
            ploplo.map_dwd_all(height=plot_height),
            use_container_width=True,
            theme=cont.ST_PLOTLY_THEME,
            config=fig_format.plotly_config(height=plot_height, title_edit=False),
        )
