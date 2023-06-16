"""Seite Grafische Datenauswertung"""  # noqa: N999

from typing import Any, Literal

import streamlit as st

from modules import classes_data as cl
from modules import classes_figs as clf
from modules import constants as cont
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
                fig_create.ploplo.timings(gf.st_get("dic_exe_time")),
                use_container_width=True,
                config=fig_format.plotly_config(),
            )

            se_st_show: list[str] = [
                "fig_base",
            ]

            for show in se_st_show:
                if show in st.session_state:
                    st.write(f"st.session_state['{show}']:")
                    if "fig" in show:
                        st.write(gf.st_get(show).to_dict())
                    else:
                        st.write(gf.st_get(show))
            st.markdown("---")
            st.write("Session State:")
            st.write(st.session_state)

        st.markdown("---")
        st.markdown("###")

    st.session_state["dic_exe_time"] = {}


@gf.lottie_spinner
def gather_and_manipulate_data() -> cl.MetaAndDfs:
    """Import Excel file and do stuff with the data"""

    if isinstance(gf.st_get("mdf"), cl.MetaAndDfs):
        mdf: cl.MetaAndDfs = gf.st_get("mdf")
    else:
        mdf: cl.MetaAndDfs = ex_in.import_prefab_excel(gf.st_get("f_up"))

    # Grundeinstellungen in der sidebar
    sm.base_settings(mdf)

    if gf.st_get("but_base_settings"):
        gf.st_delete("fig_base")
        gf.st_delete("fig_jdl")
        gf.st_delete("fig_mon")

    # anzuzeigende Grafiken
    sm.select_graphs(mdf)

    # Außentemperatur
    sm.meteo_sidebar("graph")

    if gf.st_get("but_meteo_sidebar"):
        if gf.st_get("cb_temp"):
            meteo.outside_temp_graph()
        else:
            meteo.del_meteo()

    # df mit Stundenwerten erzeugen
    if gf.st_get("cb_h"):
        mdf = df_man.df_h(mdf)

    # df für Tagesvergleich
    if gf.st_get("but_select_graphs") and gf.st_get("cb_days"):
        if gf.st_get("cb_h"):
            df_man.dic_days(mdf.df_h)
        else:
            df_man.dic_days(mdf.df)

    # df geordnete Jahresdauerlinie
    if gf.st_get("cb_jdl"):
        mdf = df_man.jdl(mdf)

    # df Monatswerte
    if gf.st_get("cb_mon"):
        mdf = df_man.mon(mdf)

    gf.st_set("mdf", mdf)
    return mdf


@gf.lottie_spinner
def make_graphs(mdf: cl.MetaAndDfs) -> clf.Figs:
    """Grafiken erzeugen"""

    figs: clf.Figs = gf.st_get("figs") or clf.Figs()

    if gf.st_get("but_base_settings"):
        figs.base = None
        figs.jdl = None
        figs.mon = None
        figs.days = None

    # Grund-Grafik
    if figs.base is None:
        with st.spinner('Momentle bitte - Grafik "Lastgang" wird erzeugt...'):
            figs.base = clf.FigProp(
                fig=fig_create.cr_fig_base(mdf), st_key=cont.FIG_KEYS.lastgang
            )

    # Jahresdauerlinie
    if figs.jdl is None and gf.st_not_in("fig_jdl") and gf.st_get("cb_jdl"):
        with st.spinner('Momentle bitte - Grafik "Jahresdauerlinie" wird erzeugt...'):
            figs.jdl = clf.FigProp(
                fig=fig_create.cr_fig_jdl(mdf), st_key=cont.FIG_KEYS.jdl
            )

    # Monatswerte
    if figs.mon is None and gf.st_not_in("fig_mon") and gf.st_get("cb_mon"):
        with st.spinner('Momentle bitte - Grafik "Monatswerte" wird erzeugt...'):
            figs.mon = clf.FigProp(
                fig=fig_create.cr_fig_mon(mdf), st_key=cont.FIG_KEYS.mon
            )

    # Tagesvergleich
    if figs.days is None and gf.st_get("but_select_graphs") and gf.st_get("cb_days"):
        with st.spinner('Momentle bitte - Grafik "Tagesvergleich" wird erzeugt...'):
            figs.days = clf.FigProp(
                fig=fig_create.cr_fig_days(mdf), st_key=cont.FIG_KEYS.days
            )

    figs.write_all_to_st()

    # horizontale / vertikale Linien
    sm.h_v_lines()
    if gf.st_get("but_h_v_lines"):
        fig_anno.h_v_lines()

    # Ausreißerbereinigung
    sm.clean_outliers()
    if gf.st_get("but_clean_outliers"):
        fig_anno.clean_outliers()

    gf.st_set("figs", figs)
    return figs


if uauth.authentication(st.session_state["page"]):
    debug_code_run(position="before")

    sm.sidebar_file_upload()

    if any(gf.st_get(entry) is not None for entry in ("f_up", "mdf")):
        mdf: cl.MetaAndDfs = gather_and_manipulate_data()
        figs: clf.Figs = make_graphs(mdf)

        tab_grafik: Any
        tab_download: Any
        tab_grafik, tab_download = st.tabs(["Datenauswertung", "Downloads"])

        with tab_grafik:
            # --- Darstellungsoptionen ---
            with st.spinner("Momentle bitte - Optionen werden erzeugt..."):
                sm.display_options_main()
                sm.display_smooth_main()

                figs.update_all_figs()
                figs.write_all_to_st()

            with st.spinner("Momentle bitte - Grafiken werden angezeigt..."):
                fig_create.plot_figs(figs)

        gf.st_set("figs", figs)

        # --- Downloads ---
        with tab_download:
            sm.downloads()

    else:
        st.info("Bitte Datei hochladen oder Beispiel auswählen")

        st.markdown("###")
        st.markdown("---")

    debug_code_run(position="after")
