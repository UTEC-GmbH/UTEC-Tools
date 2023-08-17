"""Seite Meteorologische Daten"""  # noqa: N999

import streamlit as st

from modules import constants as cont
from modules import fig_formatting as fig_format
from modules import fig_plotly_plots as ploplo
from modules import graph_menus as menu_g
from modules import meteorolog as meteo
from modules import user_authentication as uauth
from modules.setup_stuff import page_header_setup

# setup
PAGE = st.session_state["page"] = "meteo"
page_header_setup(PAGE)


if uauth.authentication(PAGE):
    st.warning("temporär außer Betrieb")
"""
    # Auswahl Ort
    with st.sidebar:
        menu_g.meteo_sidebar(PAGE)
        st.markdown("###")
        st.markdown("###")

    # st.write(gf.st_get("but_meteo_main"))

    if any(
        gf.st_get(key)
        for key in (
            "but_meteo_sidebar",
            "but_meteo_main",
            "excel_download",
            "cancel_excel_download",
        )
    ):
        if gf.st_get("but_meteo_sidebar"):
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
                dics.del_session_state_entry(entry)

        # if gf.st_get("but_meteo_main"):
        #     for entry in (
        #         "meteo_fig",
        #         "meteo_data",
        #         "df_used_stations",
        #         "df_used_stations_show",
        #         "lis_sel_params",
        #     ):
        #         dics.del_session_state_entry(entry)

        with st.spinner("Momentle bitte - Daten werden vorbereitet..."):
            meteo.del_meteo()
            gv.df_used_stations = meteo.df_used_show_edit()
            gv.df_data = (
                gf.st_get("meteo_data")
                if "meteo_data" in st.session_state
                else meteo.meteo_data()
            )
            gv.fig = (
                gf.st_get("meteo_fig")
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
                menu_g.meteo_params_main()

            with tab_down:
                menu_g.downloads(PAGE)

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
        menu_g.meteo_params_main()
"""
