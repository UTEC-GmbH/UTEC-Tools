"""Menus für die Meteorologie-Seite"""

import datetime as dt

import polars as pl
import streamlit as st

from modules import constants as cont
from modules import meteorolog as met
from modules import streamlit_functions as sf


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

        st.markdown("###")
        st.session_state["but_addr_dates"] = st.form_submit_button(
            "Knöpfle", use_container_width=True
        )


def parameter_selection() -> None:
    """DWD-Parameter data editor"""

    st.selectbox(
        label="Gewünschte Datenauflösung",
        options=cont.DWD_RESOLUTION_OPTIONS.keys(),
        index=3,
        help=(
            """
            In der Tabelle wird die Auflösung angezeigt,  \n
            die der gewünschten Auflösung an nähesten liegt,  \n
            falls es keine Daten in der gewünschten Auflösung gibt.
            """
        ),
        key="sb_resolution",
    )

    res: str = sf.s_get("sb_resolution") or "Stundenwerte"

    param_data: list[dict] = [
        {
            "Parameter": par.name,
            # "Einheit": par.unit,
            "Auflösung": next(
                res_de
                for res_de, res_en in cont.DWD_RESOLUTION_OPTIONS.items()
                if met.check_parameter_availability(par.name, res) in res_en
            ),
            "Auswahl": par.name in cont.DWD_DEFAULT_PARAMS,
        }
        for par in met.ALL_PARAMETERS.values()
    ]

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

    closest: dict = met.closest_station_per_parameter()
    st.dataframe(
        data=[
            {
                "Parameter": param,
                "Wetterstation": dic["name"],
                "Entfernung": dic["distance"],
            }
            for param, dic in closest.items()
        ],
        column_config={
            "Entfernung": st.column_config.NumberColumn(
                format="%.2f km", width="small"
            ),
        },
        use_container_width=True,
    )


def closest_stations() -> None:
    """Map of closest Weather Stations"""
