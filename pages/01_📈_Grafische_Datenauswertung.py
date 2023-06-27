# sourcery skip: avoid-global-variables
"""Seite Grafische Datenauswertung"""

from typing import Any, Literal

import streamlit as st

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

# setup
MANUAL_DEBUG = True
set_stuff.page_header_setup(page="graph")


def debug_code_run(position: Literal["before", "after"]) -> None:
    """Anzeige mit st.write() für Debugging"""

    if MANUAL_DEBUG and sf.st_get("access_lvl") == "god":
        with st.expander(f"Debug {position}", expanded=False):
            st.plotly_chart(
                fig_create.ploplo.timings(sf.st_get("dic_exe_time")),
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
                        st.write(sf.st_get(show).to_dict())
                    else:
                        st.write(sf.st_get(show))
            st.markdown("---")
            st.write("Session State:")
            st.write(st.session_state)

        st.markdown("---")
        st.markdown("###")

    st.session_state["dic_exe_time"] = {}


@gf.lottie_spinner
def gather_and_manipulate_data() -> cld.MetaAndDfs:
    """Import Excel file and do stuff with the data"""

    if isinstance(sf.st_get("mdf"), cld.MetaAndDfs):
        mdf_i: cld.MetaAndDfs = sf.st_get("mdf")
    else:
        mdf_i: cld.MetaAndDfs = ex_in.import_prefab_excel(sf.st_get("f_up"))

    # Grundeinstellungen in der sidebar
    menu_g.base_settings(mdf_i)

    if sf.st_get("but_base_settings") or sf.st_get("but_meteo_sidebar"):
        # delete all figs in session state
        for fig in cont.FIG_KEYS.as_dic().values():
            sf.st_delete(fig)

    # anzuzeigende Grafiken
    menu_g.select_graphs(mdf_i)

    # Außentemperatur
    menu_g.meteo_sidebar("graph")
    if sf.st_get("but_meteo_sidebar"):
        if sf.st_get("cb_temp"):
            mdf_i = df_man.add_air_temperature(mdf_i)
        else:
            mdf_i.df.drop(cont.SPECIAL_COLS.temp)

    # df mit Stundenwerten erzeugen
    if sf.st_get("cb_h"):
        mdf_i = df_man.df_h(mdf_i)

    # df für Tagesvergleich
    if sf.st_get("but_select_graphs") and sf.st_get("cb_days"):
        if sf.st_get("cb_h"):
            df_man.dic_days(mdf_i.df_h)
        else:
            df_man.dic_days(mdf_i.df)

    # df geordnete Jahresdauerlinie
    if sf.st_get("cb_jdl"):
        mdf_i = df_man.jdl(mdf_i)

    # df Monatswerte
    if sf.st_get("cb_mon"):
        mdf_i = df_man.mon(mdf_i)

    sf.st_set("mdf", mdf_i)
    return mdf_i


@gf.lottie_spinner
def make_graphs(mdf_g: cld.MetaAndDfs) -> clf.Figs:
    """Grafiken erzeugen"""

    figs_i: clf.Figs = sf.st_get("figs") or clf.Figs()

    if sf.st_get("but_base_settings") or sf.st_get("but_meteo_sidebar"):
        for attr in figs_i.__dataclass_fields__:
            setattr(figs_i, attr, None)

    # Grund-Grafik
    if figs_i.base is None:
        with st.spinner('Momentle bitte - Grafik "Lastgang" wird erzeugt...'):
            figs_i.base = clf.FigProp(
                fig=fig_create.cr_fig_base(mdf_g), st_key=cont.FIG_KEYS.lastgang
            )

    # Jahresdauerlinie
    if sf.st_get("cb_jdl") and (figs_i.jdl is None or sf.st_not_in("fig_jdl")):
        with st.spinner('Momentle bitte - Grafik "Jahresdauerlinie" wird erzeugt...'):
            figs_i.jdl = clf.FigProp(
                fig=fig_create.cr_fig_jdl(mdf_g), st_key=cont.FIG_KEYS.jdl
            )

    # Monatswerte
    if sf.st_get("cb_mon") and (figs_i.mon is None or sf.st_not_in("fig_mon")):
        with st.spinner('Momentle bitte - Grafik "Monatswerte" wird erzeugt...'):
            figs_i.mon = clf.FigProp(
                fig=fig_create.cr_fig_mon(mdf_g), st_key=cont.FIG_KEYS.mon
            )

    # Tagesvergleich
    if sf.st_get("cb_days") and (figs_i.days is None or sf.st_get("but_select_graphs")):
        with st.spinner('Momentle bitte - Grafik "Tagesvergleich" wird erzeugt...'):
            figs_i.days = clf.FigProp(
                fig=fig_create.cr_fig_days(mdf_g), st_key=cont.FIG_KEYS.days
            )

    figs_i.write_all_to_st()

    # horizontale / vertikale Linien
    menu_g.h_v_lines()
    if sf.st_get("but_h_v_lines"):
        fig_anno.h_v_lines()

    # Ausreißerbereinigung
    menu_g.clean_outliers()
    if sf.st_get("but_clean_outliers"):
        fig_anno.clean_outliers()

    sf.st_set("figs", figs_i)
    return figs_i


if uauth.authentication(st.session_state["page"]):
    debug_code_run(position="before")

    menu_g.sidebar_file_upload()

    if any(sf.st_get(entry) is not None for entry in ("f_up", "mdf")):
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

        sf.st_set("figs", figs)

        # --- Downloads ---
        with tab_download:
            menu_g.downloads()

    else:
        st.info("Bitte Datei hochladen oder Beispiel auswählen")

        st.markdown("###")
        st.markdown("---")

    debug_code_run(position="after")
