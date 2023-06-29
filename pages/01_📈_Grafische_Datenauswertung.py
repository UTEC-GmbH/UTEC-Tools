# sourcery skip: avoid-global-variables
"""Seite Grafische Datenauswertung"""

from typing import Any, Literal

import streamlit as st
from loguru import logger

from modules import classes_data as cld
from modules import classes_figs as clf
from modules import constants as cont
from modules import df_manipulation as df_man
from modules import excel_import as ex_in
from modules import fig_annotations as fig_anno
from modules import fig_creation_export as fig_create
from modules import fig_formatting as fig_format
from modules import general_functions as gf
from modules import graph_menus as menu_g
from modules import setup_stuff as set_stuff
from modules import streamlit_functions as sf
from modules import user_authentication as uauth

# setup stuff
gf.log_new_run()
MANUAL_DEBUG = True
set_stuff.page_header_setup(page="graph")


def debug_code_run(position: Literal["before", "after"]) -> None:
    """Infos zum Durchlauf des Programms mit st.write() für Debugging"""

    if MANUAL_DEBUG and sf.s_get("access_lvl") == "god":
        with st.expander(f"Debug {position}", expanded=False):
            st.plotly_chart(
                fig_create.ploplo.timings(sf.s_get("dic_exe_time")),
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
                        st.write(sf.s_get(show).to_dict())
                    else:
                        st.write(sf.s_get(show))
            st.markdown("---")
            st.write("Session State:")
            st.write(st.session_state)

        st.markdown("---")
        st.markdown("###")

    st.session_state["dic_exe_time"] = {}


def mdf_from_excel_or_st() -> cld.MetaAndDfs:
    """MDF aus Excel-Datei erzeugen oder aus session_state übernehmen"""

    if isinstance(sf.s_get("mdf"), cld.MetaAndDfs):
        mdf_i: cld.MetaAndDfs = sf.s_get("mdf")
        logger.info("Excel-Datei schon importiert - mdf aus session_state übernommen")
    else:
        mdf_i: cld.MetaAndDfs = ex_in.import_prefab_excel(sf.s_get("f_up"))

    return mdf_i


@gf.lottie_spinner
def gather_and_manipulate_data() -> cld.MetaAndDfs:
    """Import Excel file and do stuff with the data"""

    mdf_i: cld.MetaAndDfs = mdf_from_excel_or_st()

    # sidebar menus
    menu_g.base_settings(mdf_i)
    menu_g.select_graphs(mdf_i)
    menu_g.meteo_sidebar("graph")

    if any([sf.s_get("but_base_settings"), sf.s_get("but_meteo_sidebar")]):
        for df in ["df_h", "jdl", "mon", "df_multi", "df_h_multi", "mon_multi"]:
            setattr(mdf_i, df, None)
        logger.info(
            "Data Frames \n"
            '["df_h", "jdl", "mon", "df_multi", "df_h_multi", "mon_multi"]\n'
            "aus mdf entfernt."
        )

    if sf.s_get("but_meteo_sidebar"):
        if sf.s_get("cb_temp"):
            mdf_i = df_man.add_temperature_data(mdf_i)
        else:
            mdf_i.df.drop(cont.SPECIAL_COLS.temp)

    # split the base data frame into years if necessary
    if mdf_i.meta.multi_years and mdf_i.df_multi is None:
        mdf_i = df_man.split_multi_years(mdf_i, "df")

    # df mit Stundenwerten erzeugen
    if sf.s_get("cb_h"):
        mdf_i = df_man.df_h(mdf_i)

    # df für Tagesvergleich
    if sf.s_get("but_select_graphs") and sf.s_get("cb_days"):
        if sf.s_get("cb_h"):
            df_man.dic_days(mdf_i.df_h)
        else:
            df_man.dic_days(mdf_i.df)

    # df geordnete Jahresdauerlinie
    if sf.s_get("cb_jdl"):
        mdf_i = df_man.jdl(mdf_i)

    # df Monatswerte
    if sf.s_get("cb_mon"):
        mdf_i = df_man.mon(mdf_i)

    sf.s_set("mdf", mdf_i)
    return mdf_i


@gf.lottie_spinner
def make_graphs(mdf_g: cld.MetaAndDfs) -> clf.Figs:
    """Grafiken erzeugen"""

    figs_i: clf.Figs = sf.s_get("figs") or clf.Figs()

    if any([sf.s_get("but_base_settings"), sf.s_get("but_meteo_sidebar")]):
        for attr in figs_i.__dataclass_fields__:
            setattr(figs_i, attr, None)
        for key in cont.FIG_KEYS.list_all():
            sf.s_delete(key)

    # Grund-Grafik
    if figs_i.base is None:
        with st.spinner('Momentle bitte - Grafik "Lastgang" wird erzeugt...'):
            figs_i.base = clf.FigProp(
                fig=fig_create.cr_fig_base(mdf_g), st_key=cont.FIG_KEYS.lastgang
            )

    # Jahresdauerlinie
    if sf.s_get("cb_jdl") and (figs_i.jdl is None or sf.s_not_in("fig_jdl")):
        with st.spinner('Momentle bitte - Grafik "Jahresdauerlinie" wird erzeugt...'):
            figs_i.jdl = clf.FigProp(
                fig=fig_create.cr_fig_jdl(mdf_g), st_key=cont.FIG_KEYS.jdl
            )

    # Monatswerte
    if sf.s_get("cb_mon") and (figs_i.mon is None or sf.s_not_in("fig_mon")):
        with st.spinner('Momentle bitte - Grafik "Monatswerte" wird erzeugt...'):
            figs_i.mon = clf.FigProp(
                fig=fig_create.cr_fig_mon(mdf_g), st_key=cont.FIG_KEYS.mon
            )

    # Tagesvergleich
    if sf.s_get("cb_days") and (figs_i.days is None or sf.s_get("but_select_graphs")):
        with st.spinner('Momentle bitte - Grafik "Tagesvergleich" wird erzeugt...'):
            figs_i.days = clf.FigProp(
                fig=fig_create.cr_fig_days(mdf_g), st_key=cont.FIG_KEYS.days
            )

    figs_i.write_all_to_st()

    # horizontale / vertikale Linien
    menu_g.h_v_lines()
    if sf.s_get("but_h_v_lines"):
        fig_anno.h_v_lines()

    # Ausreißerbereinigung
    menu_g.clean_outliers()
    if sf.s_get("but_clean_outliers"):
        fig_anno.clean_outliers()

    sf.s_set("figs", figs_i)
    return figs_i


if uauth.authentication(sf.s_get("page")):
    debug_code_run(position="before")
    if sf.s_get("but_complete_reset"):
        sf.s_reset_graph()

    if sf.s_get("but_example_direct"):
        st.session_state["f_up"] = f"example_files/{sf.s_get('sb_example_file')}.xlsx"

    if all(sf.s_get(key) is None for key in ["f_up", "mdf"]):
        logger.warning("No file provided yet.")

        menu_g.sidebar_file_upload()

        st.warning("Bitte Datei hochladen oder Beispiel auswählen")

        st.markdown("###")
        st.markdown("---")
    else:
        logger.info(f"File to analyse: '{sf.s_get('f_up')}'")
        with st.sidebar:
            st.button(
                label="Auswertung neu starten",
                key="but_complete_reset",
                use_container_width=True,
            )
            st.write("---")

        # if any(sf.st_get(entry) is not None for entry in ("f_up", "mdf")):
        mdf: cld.MetaAndDfs = gather_and_manipulate_data()
        figs: clf.Figs = make_graphs(mdf)

        tab_grafik: Any
        tab_download: Any
        tab_grafik, tab_download = st.tabs(["Datenauswertung", "Downloads"])

        with tab_grafik:
            # --- Darstellungsoptionen ---
            with st.spinner("Momentle bitte - Optionen werden erzeugt..."):
                menu_g.display_options_main()
                menu_g.display_smooth_main()

                figs.update_all_figs()
                figs.write_all_to_st()

            with st.spinner("Momentle bitte - Grafiken werden angezeigt..."):
                fig_create.plot_figs(figs)

        sf.s_set("figs", figs)

        # --- Downloads ---
        with tab_download:
            menu_g.downloads()

    debug_code_run(position="after")
