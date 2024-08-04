"""PDFs bearbeiten"""

from typing import TYPE_CHECKING

import streamlit as st
import streamlit_lottie as stlot
from loguru import logger
from streamlit.runtime.uploaded_file_manager import UploadedFile

from modules import constants as cont
from modules import general_functions as gf
from modules import pdf_edit as pe
from modules import pdf_menus as pm
from modules import setup_stuff as set_stuff
from modules import streamlit_functions as sf
from modules import user_authentication as uauth

if TYPE_CHECKING:
    import fitz as pymupdf

# setup stuff
gf.log_new_run()
MANUAL_DEBUG = True
set_stuff.page_header_setup(page=cont.ST_PAGES.pdf.short)


@gf.func_timer
def display_login_page() -> None:
    """Login-Page with two columns
    - login with username and password
    - lottie-animation
    """
    columns: list = st.columns([1, 1])

    with columns[0]:
        edit_section()
    with columns[1]:
        stlot.st_lottie(
            gf.load_lottie_file("animations/pdf.json"), height=300, key="lottie_pdf"
        )


def edit_section() -> None:
    """Edit section"""
    if sf.s_get("but_complete_reset"):
        sf.s_reset_app()
    with st.sidebar:
        gf.reset_button()

    f_up: UploadedFile | None = sf.s_get("f_up")

    if f_up is None:

        st.info(
            """Hier können Texte aus pdfs entfernt werden.
            \nAußerdem kann das pvXpert Logo aus pdf-Berichten entfernt werden."""
        )
        st.write("---")
        logger.warning(f"No file provided yet. (f_up = {f_up})")
        pm.file_upload()

    else:
        edit_file(f_up)


def edit_file(f_up: UploadedFile) -> None:
    """Edit file"""

    st.markdown("###")
    pm.de_text_to_delete()
    pm.to_delete_pvxpert_logo()

    st.markdown("###")

    if sf.s_get("but_edit_pdf"):
        pdf: pymupdf.Document = pe.open_file(f_up)
        pdf = pe.remove_text_and_logo(pdf)

        new_file_name: str = f_up.name.replace(".pdf", "_UTEC_.pdf")
        pm.butt_download_pdf(pdf, new_file_name)

    else:
        pm.butt_edit_pdf()


if uauth.authentication(sf.s_get("page", default="unknown")):
    display_login_page()
