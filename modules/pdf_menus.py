"""UI - Menus"""

import datetime as dt
import pathlib
from typing import TYPE_CHECKING, Any

import plotly.graph_objects as go
import streamlit as st

from modules import classes_data as cld
from modules import classes_errors as cle
from modules import constants as cont
from modules import export as ex
from modules import fig_creation as fig_cr
from modules import fig_general_functions as fgf
from modules import general_functions as gf
from modules import streamlit_functions as sf


def sidebar_file_upload() -> Any:
    """Hochgeladene PDF-Datei"""

    with st.sidebar:

        # benutze ausgewählte Beispieldatei direkt für debugging
        if sf.s_get("access_lvl") == "god":
            st.button("Beispieldatei direkt verwenden", "but_example_direct")

        st.markdown("---")
        st.file_uploader(
            label="Datei hochladen",
            type=["pdf", "xps", "epub", "mobi", "fb2", "cbz", "svg", "txt"],
            accept_multiple_files=False,
            help=(
                """
                Zu bearbeitende Datei hochladen.
                """
            ),
            key="f_up",
        )

    return sf.s_get("f_up")
