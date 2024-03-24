"""UI - Menus"""

import streamlit as st
from loguru import logger

from modules import constants as cont
from modules import streamlit_functions as sf
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from streamlit.runtime.uploaded_file_manager import UploadedFile


def file_upload() -> None:  # sourcery skip: use-named-expression
    """Hochgeladene PDF-Dateien werden in temporärem ordner abgespeichert.
    Die Dateipfade werden im Session State unter "f_up" gespeichert.
    """

    files: list[UploadedFile] | None = st.file_uploader(
        label="Datei hochladen",
        type=["pdf", "xps", "epub", "mobi", "fb2", "cbz", "svg", "txt"],
        accept_multiple_files=True,
        help=(
            """
            Zu bearbeitende Datei(en) hochladen.
            """
        ),
        # key="f_up",
    )
    sf.s_set("f_up", files)

    if files:
        st.rerun()


def de_text_to_delete() -> None:
    """Streamlit Data Editor for text to delete"""

    df = st.data_editor(
        cont.REXEL_TEXT_BLOCKS,
        column_config={
            "value": st.column_config.TextColumn(
                label="Text-Elemente, die gelöscht werden sollen",
                required=True,
                help="""
                Jeder Textbaustein wird in der pdf-Datei gesucht und gelöscht.
                """,
            )
        },
        num_rows="dynamic",
        hide_index=True,
        # key="de_text_to_delete",
    )
    sf.s_set("de_text_to_delete", df)

    logger.debug(f"de_text_to_delete: \n{sf.s_get('de_text_to_delete')}")


def to_delete_pvxpert_logo() -> None:
    """Toggle for deleting the pvXpert logo from the PDF"""
    st.toggle(label="pvXpert-Logo entfernen", value=True, key="to_delete_pvXpert_logo")


def butt_edit_and_save() -> None:
    """Button to save the modified PDF as a new file"""
    st.button(
        label="Datei(en) bearbeiten und auf dem Desktop speichern",
        help="""
        Die Dateien werden mit den oben ausgewählten Einstellngen bearbeitet und
        auf dem Desktop im Ordner "bearbeitet" abgespeichert.
        """,
        key="but_edit_and_save",
    )
