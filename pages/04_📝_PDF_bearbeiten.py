# sourcery skip: avoid-global-variables
"""PDFs bearbeiten"""


import fitz as pymupdf
import streamlit as st
from loguru import logger
from streamlit.runtime.uploaded_file_manager import UploadedFile

from modules import constants as cont
from modules import general_functions as gf
from modules import pdf_edit, pdf_menus
from modules import setup_stuff as set_stuff
from modules import streamlit_functions as sf
from modules import user_authentication as uauth

# setup stuff
gf.log_new_run()
MANUAL_DEBUG = True
set_stuff.page_header_setup(page=cont.ST_PAGES.pdf.short)


if uauth.authentication(sf.s_get("page")):
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
        st.warning("Bitte Datei(en) hochladen")
        pdf_menus.file_upload()

    else:
        file_name: str = f_up.name
        logger.info(f"File '{file_name}' Uploaded")
        st.markdown("###")
        pdf_menus.de_text_to_delete()
        pdf_menus.to_delete_pvxpert_logo()

        st.markdown("###")

        if sf.s_get("but_edit_pdf"):
            pdf: pymupdf.Document = pdf_edit.open_file(f_up)

            if sf.s_get("de_text_to_delete"):
                pdf = pdf_edit.remove_text_from_file(pdf, sf.s_get("de_text_to_delete"))

            if sf.s_get("to_delete_pvXpert_logo"):
                pdf = pdf_edit.remove_drawing_by_color(pdf)

            new_file_name: str = file_name.replace(".pdf", "_bearbeitet_.pdf")
            pdf_menus.butt_download_pdf(pdf, new_file_name)

        else:
            pdf_menus.butt_edit_pdf()
