"""Seite Grafische Datenauswertung"""  # noqa: N999

from typing import Any, Literal

import polars as pl
import streamlit as st
import streamlit_lottie as stlot

from modules import classes as cl
from modules import df_manipulation as df_man
from modules import excel_import as ex_in
from modules import fig_annotations as fig_anno
from modules import fig_creation_export as fig_create
from modules import fig_formatting as fig_format
from modules import general_functions as gf
from modules import meteorolog as meteo
from modules import setup_stuff as set_stuff
from modules import streamlit_menus as sm
from modules import user_authentication as uauth

# setup
MANUAL_DEBUG = True
set_stuff.page_header_setup(page="graph")


def debug_code_run(position: Literal["before", "after"]) -> None:
    """Anzeige mit st.write() für Debugging"""

    if MANUAL_DEBUG and gf.st_get("access_lvl") == "god":
        with st.expander(f"Debug {position}", expanded=False):
            st.plotly_chart(
                fig_create.ploplo.timings(st.session_state["dic_exe_time"]),
                use_container_width=True,
                config=fig_format.plotly_config(),
            )

            se_st_show: list[str] = [
                "fig_base",
                "fig_jdl",
                "fig_mon",
                "metadata",
                "dic_days",
            ]

            for show in se_st_show:
                st.write(f"show: {show}")
                if show in st.session_state:
                    if "fig" in show:
                        st.write(st.session_state[show].to_dict())
                    else:
                        st.write(st.session_state[show])

            st.write(st.session_state)

        st.markdown("---")
        st.markdown("###")

    st.session_state["dic_exe_time"] = {}


def gather_data():
    """Import Excel file and do stuff with the data"""
    return


if uauth.authentication(st.session_state["page"]):
    debug_code_run(position="before")

    sm.sidebar_file_upload()

    if any(gf.st_get(entry) is not None for entry in ("f_up", "df")):
        with stlot.st_lottie_spinner(
            gf.load_lottie_file("animations/bored.json"), height=400
        ):
            if any(entry not in st.session_state for entry in ("df", "metadata")):
                with st.spinner("Momentle bitte - Datei wird importiert..."):
                    gf.st_new(
                        "mdf", ex_in.import_prefab_excel(st.session_state["f_up"])
                    )

            # Grundeinstellungen in der sidebar
            sm.base_settings()
            if gf.st_get("but_base_settings"):
                for entry in (
                    "fig_base",
                    "fig_jdl",
                    "fig_mon",
                    "df_h",
                    "df_jdl",
                    "df_mon",
                ):
                    gf.st_delete(entry)

            # anzuzeigende Grafiken
            sm.select_graphs()

            # Außentemperatur
            with st.sidebar, st.expander("Außentemperatur", expanded=False):
                sm.meteo_sidebar("graph")

            if gf.st_get("but_meteo_sidebar"):
                if gf.st_get("cb_temp"):
                    meteo.outside_temp_graph()
                else:
                    meteo.del_meteo()

            # df mit Stundenwerten erzeugen
            if gf.st_get("cb_h") and gf.st_get("mdf").df_h is None:
                with st.spinner("Momentle bitte - Stundenwerte werden erzeugt..."):
                    gf.st_get("mdf").df_h = df_man.df_h(gf.st_get("mdf"))

            # df für Tagesvergleich
            if gf.st_get("but_select_graphs") and gf.st_get("cb_days"):
                if gf.st_get("cb_h"):
                    df_man.dic_days(st.session_state["df_h"])
                else:
                    df_man.dic_days(st.session_state["df"])

            # einzelnes Jahr
            if (
                len(st.session_state["years"]) == 1
                or gf.st_get("cb_multi_year") is False
            ):
                # df geordnete Jahresdauerlinie
                if gf.st_get("cb_jdl") and "df_jdl" not in st.session_state:
                    with st.spinner(
                        "Momentle bitte - Jahresdauerlinie wird erzeugt..."
                    ):
                        df_man.jdl(st.session_state["df"])

                # df Monatswerte
                if gf.st_get("cb_mon") and "df_mon" not in st.session_state:
                    with st.spinner("Momentle bitte - Monatswerte werden erzeugt..."):
                        df_man.mon(st.session_state["df"], st.session_state["metadata"])

            # mehrere Jahre übereinander
            else:
                with st.spinner(
                    "Momentle bitte - Werte werden auf Jahre aufgeteilt..."
                ):
                    if "dic_df_multi" not in st.session_state:
                        df_man.df_multi_y(
                            st.session_state["df_h"]
                            if gf.st_get("cb_h")
                            else st.session_state["df"]
                        )

            # --- Grafiken erzeugen ---
            # Grund-Grafik
            st.session_state["lis_figs"] = ["fig_base"]
            if "fig_base" not in st.session_state:
                with st.spinner('Momentle bitte - Grafik "Lastgang" wird erzeugt...'):
                    st.session_state["fig_base"] = fig_create.cr_fig_base()

            # Jahresdauerlinie
            if gf.st_get("cb_jdl"):
                st.session_state["lis_figs"].append("fig_jdl")
                if "fig_jdl" not in st.session_state:
                    with st.spinner(
                        'Momentle bitte - Grafik "Jahresdauerlinie" wird erzeugt...'
                    ):
                        fig_create.cr_fig_jdl()

            # Monatswerte
            if gf.st_get("cb_mon"):
                st.session_state["lis_figs"].append("fig_mon")
                if "fig_mon" not in st.session_state:
                    with st.spinner(
                        'Momentle bitte - Grafik "Monatswerte" wird erzeugt...'
                    ):
                        fig_create.cr_fig_mon()

            # Tagesvergleich
            if gf.st_get("cb_days"):
                st.session_state["lis_figs"].append("fig_days")
                if gf.st_get("but_select_graphs"):
                    with st.spinner(
                        'Momentle bitte - Grafik "Tagesvergleich" wird erzeugt...'
                    ):
                        fig_create.cr_fig_days()

            # horizontale / vertikale Linien
            sm.h_v_lines()
            if gf.st_get("but_h_v_lines"):
                fig_anno.h_v_lines()

            # Ausreißerbereinigung
            sm.clean_outliers()
            if gf.st_get("but_clean_outliers"):
                fig_anno.clean_outliers()

            tab_grafik: Any
            tab_download: Any
            tab_grafik, tab_download = st.tabs(["Datenauswertung", "Downloads"])

            with tab_grafik:
                # --- Darstellungsoptionen ---
                with st.spinner("Momentle bitte - Optionen werden erzeugt..."):
                    sm.display_options_main()
                    sm.display_smooth_main()

                    for fig in st.session_state["lis_figs"]:
                        st.session_state[fig] = fig_format.update_main(
                            st.session_state[fig]
                        )

                with st.spinner("Momentle bitte - Grafiken werden angezeigt..."):
                    fig_create.plot_figs()

            # --- Downloads ---
            with tab_download:
                sm.downloads()

            debug_code_run(position="after")

            st.markdown("###")
            st.markdown("---")
