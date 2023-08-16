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
                for x in glob("example_files/*.xlsx")
            ],
            help=(
                """
                Bitte eine der Beispieldateien (egal welche) herunterladen
                und mit den zu untersuchenden Daten füllen.
                """
            ),
            key="sb_example_file",
        )

        with open(f"example_files/{sb_example}.xlsx", "rb") as exfile:
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

    return sf.s_get("f_up")
