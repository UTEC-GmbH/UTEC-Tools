"""UI - Menus"""


import pathlib
from typing import Any

import streamlit as st

from modules import constants as cont
from modules import streamlit_functions as sf


def sidebar_file_upload() -> Any:
    """Hochgeladene Excel-Datei"""

    with st.sidebar:
        sb_example: str | None = st.selectbox(
            "Beispieldateien",
            options=[
                phil.stem for phil in pathlib.Path.cwd().glob("example_map/*.xlsx")
            ],
            help=(
                """
                Bitte eine der Beispieldateien (egal welche) herunterladen
                und mit den zu untersuchenden Daten füllen.
                """
            ),
            key="sb_example_file",
        )

        with open(f"example_map/{sb_example}.xlsx", "rb") as exfile:
            st.download_button(
                **cont.Buttons.download_example.func_args(),
                data=exfile,
                file_name=f"{sb_example}.xlsx",
            )

        # benutze ausgewählte Beispieldatei direkt für debugging
        if sf.s_get("access_lvl") == "god":
            st.button("Beispieldatei direkt verwenden", "but_example_direct")

        st.markdown("---")
        st.file_uploader(
            label="Datei hochladen",
            type=["xlsx", "xlsm"],
            accept_multiple_files=False,
            help=(
                """
                Das Arbeitsblatt "Daten" in der Datei muss
                wie eine der Beispieldateien aufgebaut sein.
                """
            ),
            key="f_up",
        )
        st.markdown("---")

    return sf.s_get("f_up")


def sidebar_text() -> None:
    """Menu to define the graph title etc."""

    with st.sidebar:
        st.text_input(
            label="Titel der Grafik",
            help="Titel wird über der Grafik angezeigt",
            key="ti_title",
        )
        st.text_input(
            label="Titel - Zusatz",
            help="Wird kleiner und in Klammern hinter dem Titel angezeigt",
            key="ti_title_add",
        )

        cols: list = st.columns([2, 1])
        with cols[0]:
            st.text_input(
                label="Punktgröße",
                help=(
                    """
                    Name der Eigenschaft, die die Punktgröße bestimmt 
                    (z.B. 'Leistung')
                    """
                ),
                key="ti_ref_size",
            )
        with cols[1]:
            st.text_input(
                label="Einheit",
                help=(
                    """
                    Einheit der Eigenschaft, die die Punktgröße bestimmt 
                    (z.B. 'kWp')
                    """
                ),
                key="ti_ref_size_unit",
            )

        cols: list = st.columns([2, 1])
        with cols[0]:
            st.text_input(
                label="Punktfarbe",
                help=(
                    """
                    Name der Eigenschaft, die die Punktfarbe bestimmt 
                    (z.B. 'spezifische Leistung')
                    """
                ),
                key="ti_ref_col",
            )
        with cols[1]:
            st.text_input(
                label="Einheit",
                help=(
                    """
                    Einheit der Eigenschaft, die die Punktfarbe bestimmt 
                    (z.B. 'kWh/kWp')
                    """
                ),
                key="ti_ref_col_unit",
            )


def sidebar_slider_size() -> None:
    """Slider für Punktgröße"""
    with st.sidebar:
        st.markdown("###")
        st.slider(
            label="Punktgröße",
            min_value=1,
            max_value=100,
            value=50,
            help=(
                """
                Falls die Punktegrößen mit eingegebenen Werten berechnet werden, 
                bleiben die Größenverhältnisse so weit wie möglich bestehen.
                (Bei sehr kleinen Werten funktioniert das nicht immer.)
                """
            ),
            key="sl_marker_size",
        )


def sidebar_slider_colour() -> None:
    """Slider für Punktgröße"""
    with st.sidebar:
        st.markdown("###")
        st.slider(
            label="Punktfarbe",
            min_value=1,
            max_value=100,
            value=50,
            help=(
                """
                Falls die Punktfarbe mit Werte bestimmt wird 
                und sich auf eine Farbskala bezieht, 
                hat diese Einstellung keine Auswirkung auf die Grafik.
                """
            ),
            key="sl_marker_colour",
        )


def sidebar_colour_scale() -> None:
    """Selector for Colour Scale"""
    with st.sidebar:
        st.selectbox(
            label="Farbskala",
            options=[
                "Blackbody",
                "Bluered",
                "Blues",
                "Cividis",
                "Earth",
                "Electric",
                "Greens",
                "Greys",
                "Hot",
                "Jet",
                "Picnic",
                "Portland",
                "Rainbow",
                "RdBu",
                "Reds",
                "Viridis",
                "YlGnBu",
                "YlOrRd",
            ],
            index=11,
            key="sb_col_scale",
        )
