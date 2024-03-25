"""UI - Menus"""

from typing import TYPE_CHECKING

import fitz as pymupdf
import streamlit as st
from loguru import logger

from modules import constants as cont
from modules import streamlit_functions as sf

if TYPE_CHECKING:
    from streamlit.runtime.uploaded_file_manager import UploadedFile


def file_upload() -> None:
    """Hochgeladene PDF-Dateien"""

    files: UploadedFile | None = st.file_uploader(
        label="Datei hochladen",
        type=["pdf", "xps", "epub", "mobi", "fb2", "cbz", "svg", "txt"],
        accept_multiple_files=False,
        help=(
            """
            Zu bearbeitende Datei hochladen.
            """
        ),
    )
    sf.s_set("f_up", files)

    if files:
        st.rerun()


def de_text_to_delete() -> None:
    """Streamlit Data Editor for text to delete"""

    df: list[str] = st.data_editor(
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
        width=600,
    )
    sf.s_set("de_text_to_delete", df)

    logger.debug(f"de_text_to_delete: \n{sf.s_get('de_text_to_delete')}")


def to_delete_pvxpert_logo() -> None:
    """Toggle for deleting the pvXpert logo from the PDF"""
    st.toggle(label="pvXpert-Logo entfernen", value=True, key="to_delete_pvXpert_logo")


def butt_edit_pdf() -> None:
    """Button to save the modified PDF as a new file"""
    st.button(
        label="Datei bearbeiten",
        help="""
        Die Datei wird mit den oben ausgewählten Einstellngen bearbeitet.
        """,
        key="but_edit_pdf",
    )


def butt_download_pdf(pdf: pymupdf.Document, new_file_name: str) -> None:
    """Download the modified PDF"""

    st.download_button(
        label="PDF herunterladen",
        data=pdf.tobytes(),
        mime="application/pdf",
        file_name=new_file_name,
        key="but_download_pdf",
        type="primary",
    )
