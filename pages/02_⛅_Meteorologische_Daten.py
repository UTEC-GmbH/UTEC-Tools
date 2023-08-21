"""Seite Meteorologische Daten"""  # noqa: N999

import streamlit as st

from modules import constants as cont
from modules import fig_formatting as fig_format
from modules import fig_plotly_plots as ploplo
from modules import meteo_menus as menu_m
from modules import meteorolog as meteo
from modules import setup_stuff as set_stuff
from modules import streamlit_functions as sf
from modules import user_authentication as uauth

# setup
set_stuff.page_header_setup(page=cont.ST_PAGES.meteo.short)


if uauth.authentication(sf.s_get("page")):
    
    # Auswahl Ort
    with st.sidebar:
        menu_m.sidebar_reset()
        menu_m.sidebar_address_dates()

    # st.write(sf.s_get("but_meteo_main"))

    if any(
        sf.s_get(key)
        for key in (
            "but_meteo_sidebar",
            "excel_download",
            "cancel_excel_download",
        )
    ):
        if sf.s_get("but_meteo_sidebar"):
            for entry in (
                "dic_geo",
                "meteo_fig",
                "meteo_data",
                "df_all_stations",
                "all_stations_without_dups",
                "df_dwd_stations",
                "df_meteostat_stations",
                "df_used_stations",
                "df_used_stations_show",
                "lis_sel_params",
            ):
                sf.s_delete(entry)

       

        with st.spinner("Momentle bitte - Daten werden vorbereitet..."):
            meteo.del_meteo()
            gv.df_used_stations = meteo.df_used_show_edit()
            gv.df_data = (
                sf.s_get("meteo_data")
                if "meteo_data" in st.session_state
                else meteo.meteo_data()
            )
            gv.fig = (
                sf.s_get("meteo_fig")
                if "meteo_fig" in st.session_state
                else ploplo.map_weatherstations()
            )

            tab_info, tab_down = st.tabs(["Information", "Excel-Download"])
            with tab_info:
                st.markdown("###")
                st.subheader("verwendete Wetterstationen")
                st.dataframe(gv.df_used_stations)
                st.markdown("###")
                st.subheader(
                    f"Wetterstationen im Radius von {meteo.WEATHERSTATIONS_MAX_DISTANCE} km um den Standort"
                )
                st.plotly_chart(
                    gv.fig,
                    use_container_width=True,
                    config=fuan.plotly_config(height=450, title_edit=False),
                )
                st.markdown("###")
                menu_m.meteo_params_main()

            with tab_down:
                menu_m.downloads(sf.s_get("page"))

    else:
        col1, col2 = st.columns([4, 3], gap="medium")
        with col1:
            st.markdown("###")
            st.plotly_chart(
                ploplo.map_dwd_all(),
                use_container_width=True,
                config=fuan.plotly_config(),
            )
        with col2:
            st.markdown("###")
            st.markdown("###")
            st.markdown(
                "Folgende Daten werden standardmäßig bereitgestellt:"  
                "_(Auswahl kann zukünftig unten geändert werden)_"
            )
            for param in meteo.METEO_DEFAULT_PARAMETER:
                st.markdown(f"- {param}")

        st.markdown("###")
        menu_m.meteo_params_main()
"""
