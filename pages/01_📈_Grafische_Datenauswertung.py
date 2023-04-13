"""
Seite Grafische Datenauswertung
"""

from typing import Any

import streamlit as st

from modules import df_manip as dfm
from modules import excel as ex
from modules import fig_annotations as fig_anno
from modules import fig_creation_export as fig_create
from modules import fig_formatting as fig_format
from modules import meteorolog as meteo
from modules import setup_stuff
from modules import streamlit_menus as sm
from modules import user_authentication as uauth
from modules.general_functions import del_session_state_entry

# setup
MANUAL_DEBUG: bool = True
setup_stuff.page_header_setup(page="graph")


def debug_code_run(before: bool) -> None:  # sourcery skip: flag-streamlit-show
    """Anzeige mit st.experimental_show() für Debugging"""

    if MANUAL_DEBUG and st.session_state.get("access_lvl") == "god":
        with st.expander(f"Debug {'before' if before else 'after'}", False):
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
                        st.experimental_show(st.session_state[show].to_dict())
                    else:
                        st.experimental_show(st.session_state[show])

            st.experimental_show(st.session_state)

        st.markdown("---")
        st.markdown("###")

    st.session_state["dic_exe_time"] = {}


if uauth.authentication(st.session_state["page"]):
    debug_code_run(before=True)

    sm.sidebar_file_upload()

    if any(st.session_state.get(entry) is not None for entry in ("f_up", "df")):
        if any(x not in st.session_state for x in ("df", "metadata")):
            with st.spinner("Momentle bitte - Datei wird gelesen..."):
                ex.import_prefab_excel(st.session_state["f_up"])

        # Grundeinstellungen in der sidebar
        sm.base_settings()
        if st.session_state.get("but_base_settings"):
            for entry in ("fig_base", "fig_jdl", "fig_mon", "df_h", "df_jdl", "df_mon"):
                del_session_state_entry(entry)

        # anzuzeigende Grafiken
        sm.select_graphs()

        # Außentemperatur
        with st.sidebar:
            with st.expander("Außentemperatur", False):
                sm.meteo_sidebar("graph")

        if st.session_state.get("but_meteo_sidebar"):
            if st.session_state.get("cb_temp"):
                meteo.outside_temp_graph()
            else:
                meteo.del_meteo()

        # df mit Stundenwerten erzeugen
        if st.session_state.get("cb_h") and "df_h" not in st.session_state:
            with st.spinner("Momentle bitte - Stundenwerte werden erzeugt..."):
                st.session_state["df_h"] = dfm.h_from_other(st.session_state["df"])

        # df für Tagesvergleich
        if st.session_state.get("but_select_graphs") and st.session_state.get(
            "cb_days"
        ):
            if st.session_state.get("cb_h"):
                dfm.dic_days(st.session_state["df_h"])
            else:
                dfm.dic_days(st.session_state["df"])

        # einzelnes Jahr
        if (
            len(st.session_state["years"]) == 1
            or st.session_state.get("cb_multi_year") is False
        ):
            # df geordnete Jahresdauerlinie
            if st.session_state.get("cb_jdl") and "df_jdl" not in st.session_state:
                with st.spinner("Momentle bitte - Jahresdauerlinie wird erzeugt..."):
                    dfm.jdl(st.session_state["df"])

            # df Monatswerte
            if st.session_state.get("cb_mon") and "df_mon" not in st.session_state:
                with st.spinner("Momentle bitte - Monatswerte werden erzeugt..."):
                    dfm.mon(st.session_state["df"], st.session_state["metadata"])

        # mehrere Jahre übereinander
        else:
            with st.spinner("Momentle bitte - Werte werden auf Jahre aufgeteilt..."):
                if "dic_df_multi" not in st.session_state:
                    dfm.df_multi_y(
                        st.session_state["df_h"]
                        if st.session_state.get("cb_h")
                        else st.session_state["df"]
                    )

        # --- Grafiken erzeugen ---
        # Grund-Grafik
        st.session_state["lis_figs"] = ["fig_base"]
        if "fig_base" not in st.session_state:
            with st.spinner('Momentle bitte - Grafik "Lastgang" wird erzeugt...'):
                st.session_state["fig_base"] = fig_create.cr_fig_base()

        # Jahresdauerlinie
        if st.session_state.get("cb_jdl"):
            st.session_state["lis_figs"].append("fig_jdl")
            if "fig_jdl" not in st.session_state:
                with st.spinner(
                    'Momentle bitte - Grafik "Jahresdauerlinie" wird erzeugt...'
                ):
                    fig_create.cr_fig_jdl()

        # Monatswerte
        if st.session_state.get("cb_mon"):
            st.session_state["lis_figs"].append("fig_mon")
            if "fig_mon" not in st.session_state:
                with st.spinner(
                    'Momentle bitte - Grafik "Monatswerte" wird erzeugt...'
                ):
                    fig_create.cr_fig_mon()

        # Tagesvergleich
        if st.session_state.get("cb_days"):
            st.session_state["lis_figs"].append("fig_days")
            if st.session_state.get("but_select_graphs"):
                with st.spinner(
                    'Momentle bitte - Grafik "Tagesvergleich" wird erzeugt...'
                ):
                    fig_create.cr_fig_days()

        # horizontale / vertikale Linien
        sm.h_v_lines()
        if st.session_state.get("but_h_v_lines"):
            fig_anno.h_v_lines()

        # Ausreißerbereinigung
        sm.clean_outliers()
        if st.session_state.get("but_clean_outliers"):
            fig_anno.clean_outliers()

        # glatte Linien
        # sm.smooth()
        # if st.session_state.get("but_smooth") and st.session_state.get("cb_smooth"):
        #     st.session_state["fig_base"] = fig_anno.smooth(st.session_state["fig_base"])
        # if (
        #     st.session_state.get("but_smooth")
        #     and st.session_state.get("cb_smooth") is not True
        # ):
        #     dfm.del_smooth()
        tab_grafik: Any
        tab_download: Any
        tab_grafik, tab_download = st.tabs(["Datenauswertung", "Downloads"])

        with tab_grafik:
            # --- Darstellungsoptionen ---
            with st.spinner("Momentle bitte - Optionen werden erzeugt..."):
                # but_upd_main: bool = sm.display_options_main()
                # but_smooth: bool = sm.display_smooth_main()

                sm.display_options_main()
                sm.display_smooth_main()

                for fig in st.session_state["lis_figs"]:
                    st.session_state[fig] = fig_format.update_main(
                        st.session_state[fig]
                    )

            #     if "first_run_display_options_main" not in st.session_state:
            #         for fig in st.session_state["lis_figs"]:
            #             fig_format.update_vis_main(st.session_state[fig])
            #         st.session_state["first_run_display_options_main"] = False

            # if but_upd_main or but_smooth:
            #     with st.spinner("Momentle bitte - Grafiken werden aktualisiert..."):
            #         for fig in st.session_state["lis_figs"]:
            #             fig_format.update_vis_main(st.session_state[fig])
            # --- Grafiken zeichnen ---
            # if not any([st.session_state.get("but_html"), st.session_state.get("but_h")]):
            with st.spinner("Momentle bitte - Grafiken werden angezeigt..."):
                fig_create.plot_figs()

        # --- Downloads ---
        # with st.sidebar:
        with tab_download:
            sm.downloads()

            #     # --- Monatswerte als Tabelle und Data Frame Report ---
            #     st.markdown('---')
            #     st.subheader('Monatswerte als Tabelle')
            #     but_tab_mon= st.button('Monatswerte als Tabelle erzeugen')

            #     # st.subheader('Pandas Profiling Report')
            #     # but_ppr= st.button('Report erzeugen')

            # if but_tab_mon:
            #     cont_tab= st.container()
            #     with cont_tab:
            #         # Monatswerte
            #         st.plotly_chart(
            #             tabs.tab_mon(st.session_state['fig_mon']),
            #             use_container_width= True,
            #         )

            # # if but_ppr:
            #     with st.expander('Pandas Profiling Report'):
            #         st_profile_report(df_rep)

        # debug
        debug_code_run(before=False)

        st.markdown("###")
        st.markdown("---")
