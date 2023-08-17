"""UI - Menus"""


from glob import glob
from typing import Any

import streamlit as st

from modules import streamlit_functions as sf


def sidebar_file_upload() -> Any:
    """Hochgeladene Excel-Datei"""

    with st.sidebar:
        sb_example: str | None = st.selectbox(
            "Beispieldateien",
            options=[
                x.replace("/", "\\").split("\\")[-1].replace(".xlsx", "")
                for x in glob("example_map/*.xlsx")
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
                label="Beispieldatei herunterladen",
                data=exfile,
                file_name=f"{sb_example}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
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
                    (z.B. 'kWp')"""
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
