"""Menus für die Meteorologie-Seite"""

import datetime as dt
from typing import TYPE_CHECKING

import streamlit as st

from modules import classes_data as cld
from modules import constants as cont
from modules import excel_download as ex
from modules import general_functions as gf
from modules import meteorolog as met
from modules import streamlit_functions as sf

if TYPE_CHECKING:
    import polars as pl


def sidebar_reset() -> None:
    """Reset-Knöpfle für die Sidebar"""
    with st.sidebar:
        st.markdown("###")
        st.button(
            label="✨  Auswertung neu starten  ✨",
            key="but_complete_reset",
            use_container_width=True,
            help="Auswertung zurücksetzen um andere Datei hochladen zu können.",
        )
        st.markdown("---")


def sidebar_address_dates() -> None:
    """Adresse und Daten"""

    # sf.s_set(key="address_last_run", value=sf.s_get("ta_adr"))

    with st.sidebar, st.form("Standort und Daten"):
        st.text_area(
            label="Adresse",
            value="Cuxhavener Str. 10  \n20217 Bremen",
            help=(
                """
                Je genauer, desto besser, 
                aber es reicht auch nur eine Stadt.  \n
                _(Es wird eine Karte angezeigt, mit der kontrolliert werden kann, 
                ob die richtige Adresse gefunden wurde.)_
                """
            ),
            key="ta_adr",
            # on_change=sf.s_set(key="address_last_run", value=sf.s_get("ta_adr")),
        )

        # if sf.s_get(key="address_last_run") != sf.s_get("ta_adr"):
        #     sf.s_delete(key="geo_location")

        cols: list = st.columns([60, 40])
        with cols[0]:
            st.date_input(
                label="Startdatum",
                format="DD.MM.YYYY",
                value=dt.date(dt.datetime.now().year - 1, 1, 1),
                key="di_start",
            )
        with cols[1]:
            st.time_input(label="Zeit", value=dt.time(0, 0), key="ti_start")

        cols: list = st.columns([60, 40])
        with cols[0]:
            st.date_input(
                label="Enddatum",
                format="DD.MM.YYYY",
                value=dt.date(dt.datetime.now().year - 1, 12, 31),
                key="di_end",
            )
        with cols[1]:
            st.time_input(label="Zeit", value=dt.time(23, 59), key="ti_end")

        st.selectbox(
            label="Gewünschte Datenauflösung",
            options=[res.de for res in cont.TIME_RESOLUTIONS.values()],
            index=1,
            help=(
                """
                Es liegen nicht immer Daten in der gewünschten Auflösung direkt vor.  \n
                Falls nötig, werden Daten mit anderer Auflösung interpoliert, bzw.  \n
                per Mittelwert oder Summe auf die gewünschte Auflösung gebracht.  \n
                """
            ),
            key="sb_resolution",
        )

        st.markdown("###")
        st.session_state["but_addr_dates"] = st.form_submit_button(
            "Knöpfle", use_container_width=True
        )


@gf.func_timer
def parameter_selection() -> None:
    """DWD-Parameter data editor"""

    param_data: list[dict] = [
        {
            "Parameter": par.name_en,
            "Einheit": par.unit,
            "Auswahl": par.name_en in cont.DWD_DEFAULT_PARAMS,
        }
        for par in met.ALL_PARAMETERS.values()
    ]

    st.markdown("###")
    edited: list[dict] = st.data_editor(
        data=sorted(
            sorted(param_data, key=lambda s: s["Parameter"]),
            key=lambda sort: sort["Auswahl"],
            reverse=True,
        ),
        use_container_width=True,
        key="de_parameter",
    )

    selected: list[str] = [par["Parameter"] for par in edited if par["Auswahl"]]
    sf.s_set("selected_params", selected)

    res: str = sf.s_get("sb_resolution") or "Stundenwerte"
    params: list[cld.DWDParam] = met.collect_meteo_data_for_list_of_parameters(res)

    st.dataframe(
        data=[
            {
                "Parameter": param.name_de,
                "Auflösung": param.closest_available_res.name_de,
                "Wetterstation": param.closest_available_res.closest_station.name,
                "Entfernung": param.closest_available_res.closest_station.distance,
            }
            for param in params
            if param.closest_available_res is not None
        ],
        column_config={
            "Entfernung": st.column_config.NumberColumn(
                format="%.2f km", width="small"
            ),
        },
        use_container_width=True,
    )

    st.markdown(
        "_Falls der DWD keine Daten "
        "in der gewünschten Auflösung zur Verfügung stellt, "
        "werden Daten mit einer möglichst höheren Auflösung "
        "heruntergeladen und umgerechnet. Die Auflösung in der "
        "Tabelle (s.o.) ist die Auflösung der verwendeten DWD-Werte._"
    )


def download_as_excel() -> None:
    """Data as Excel-File"""

    cols: list = st.columns([1, 3, 1])

    if sf.s_get("but_collect_data") and sf.s_get("selected_params") is not None:
        # closest: dict = sf.s_get("closest_stations") or {}
        page: str = cont.ST_PAGES.meteo.short
        timespan: cld.TimeSpan = met.start_end_time()
        xl_file_name: str = (
            f"Wetterdaten {timespan.start.date()} - {timespan.end.date()}.xlsx"
        )
        dat: list[cld.DWDParameter] = met.collect_meteo_data_for_list_of_parameters()
        df_ex: pl.DataFrame = met.df_from_param_list(dat)
        meta: cld.MetaData = cld.MetaData(
            lines={
                par.name: cld.MetaLine(
                    name=par.name,
                    name_orgidx="Datum",
                    orig_tit=par.name,
                    tit=par.name,
                    unit=par.unit,
                    excel_number_format=par.num_format,
                )
                for par in dat
            }
        )

        with cols[1]:
            st.download_button(
                label="✨ Excel-Datei herunterladen ✨",
                data=ex.excel_download(df_ex, meta, page),
                file_name=xl_file_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="excel_download",
                use_container_width=True,
            )

            st.button(
                "abbrechen", key="cancel_excel_download", use_container_width=True
            )

        ani_height = 30
        with cols[0]:
            gf.show_lottie_animation(
                "animations/coin_i.json", height=ani_height, speed=0.75
            )
        with cols[2]:
            gf.show_lottie_animation(
                "animations/coin_i.json", height=ani_height, speed=0.75
            )

    else:
        with cols[1]:
            st.button(
                label="✨ Excel-Datei erzeugen ✨",
                help=(
                    """
                Daten für die gewählten Parameter zusammenstellen
                (im nächsten Schritt können sie heruntergeladen werden)    
                """
                ),
                key="but_collect_data",
                use_container_width=True,
            )
