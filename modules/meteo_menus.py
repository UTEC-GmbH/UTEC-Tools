"""Menus für die Meteorologie-Seite"""

import datetime as dt

import polars as pl
import streamlit as st

from modules import constants as cont


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

    with st.sidebar, st.form("meteo"):
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
        )

        cols: list = st.columns([2, 1])
        with cols[0]:
            st.date_input(
                label="Startdatum",
                format="DD.MM.YYYY",
                key="di_start",
            )
        with cols[1]:
            st.time_input(label="Zeit", value=dt.time(0, 0), key="ti_start")

        cols: list = st.columns([2, 1])
        with cols[0]:
            st.date_input(
                label="Enddatum",
                format="DD.MM.YYYY",
                key="di_end",
            )
        with cols[1]:
            st.time_input(label="Zeit", value=dt.time(23, 59), key="ti_end")

        st.selectbox(
            label="Datenauflösung",
            options=cont.DWD_RESOLUTION_OPTIONS.keys(),
            index=3,
            key="sb_resolution",
        )

        st.markdown("###")
        st.session_state["but_meteo_sidebar"] = st.form_submit_button("Knöpfle")
        st.markdown("###")


def parameter_selection() -> None:
    """DWD-Parameter data editor"""

    st.data_editor(data=cont.METEO_CODES.__dict__, key="de_parameter")
