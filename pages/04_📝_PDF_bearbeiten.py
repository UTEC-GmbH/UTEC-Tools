# sourcery skip: avoid-global-variables
"""PDFs bearbeiten"""


import pathlib

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


st.info(
    """Hier können Texte aus pdfs entfernt werden.
      \nAußerdem kann das pvXpert Logo aus pdf-Berichten entfernt werden."""
)
st.write("---")
if uauth.authentication(sf.s_get("page")):
    if sf.s_get("but_complete_reset"):
        sf.s_reset_app()
    with st.sidebar:
        gf.reset_button()

    f_up: list[UploadedFile] | None = sf.s_get("f_up")

    if f_up is None or (isinstance(f_up, list) and len(f_up) == 0):
        logger.warning(f"No file provided yet. (f_up = {f_up})")
        st.warning("Bitte Datei(en) hochladen")
        pdf_menus.file_upload()

    else:
        logger.info(
            gf.string_new_line_per_item(
                [file.name for file in f_up], f"{len(f_up)} file(s) Uploaded:"
            )
        )
        st.markdown("###")
        pdf_menus.de_text_to_delete()
        pdf_menus.to_delete_pvxpert_logo()

        st.markdown("###")
        pdf_menus.butt_edit_and_save()

        if sf.s_get("but_edit_and_save"):
            files: list[pathlib.WindowsPath] = pdf_edit.temporary_files(f_up)
            for file in files:
                pdf: pymupdf.Document = pdf_edit.open_file(str(file))

                if sf.s_get("de_text_to_delete"):
                    pdf = pdf_edit.remove_text_from_file(
                        pdf, sf.s_get("de_text_to_delete")
                    )

                if sf.s_get("to_delete_pvXpert_logo"):
                    pdf = pdf_edit.remove_drawing_by_color(pdf)

                pdf_edit.save_and_close(pdf)
