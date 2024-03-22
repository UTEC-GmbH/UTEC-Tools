"""PDFs bearbeiten"""

from typing import Literal

import fitz as pymupdf
import streamlit as st
from loguru import logger

from modules import constants as cont
from modules import general_functions as gf
from modules import pdf_menus as menu_pdf
from modules import setup_stuff as set_stuff
from modules import streamlit_functions as sf
from modules import user_authentication as uauth

# setup stuff
gf.log_new_run()
MANUAL_DEBUG = True
set_stuff.page_header_setup(page=cont.ST_PAGES.pdf.short)


def remove_rexel_from_file(
    file: str, save_type: Literal["overwrite", "new"] = "new"
) -> None:
    """Remove Rexel and the pvXpert logo from a PDF file"""

    pdf: pymupdf.Document = pymupdf.open(file)
    for page in pdf:

        # remove text
        for rect in [
            rec
            for text in ["Rexel Germany GmbH & Co. KG", "www.rexel.de"]
            for rec in page.search_for(text)
        ]:
            page.add_redact_annot(rect, fill=(1, 1, 1))

        # remove logo
        for rect in [
            drawing.get("rect")
            for drawing in page.get_drawings()
            if drawing.get("fill") == (0.0, 0.26666998863220215, 0.549019992351532)
        ]:
            page.add_redact_annot(rect, fill=(1, 1, 1))

        page.apply_redactions()

    # save and close
    if save_type == "new":
        pdf.save(pdf.name.replace(".pdf", " - b.pdf"))
    else:
        pdf.save(pdf.name, incremental=True)

    pdf.close()


if uauth.authentication(sf.s_get("page")):
    if sf.s_get("but_complete_reset"):
        sf.s_reset_app()

    if sf.s_get("but_example_direct"):
        st.session_state["f_up"] = f"example_files/{sf.s_get('sb_example_file')}.xlsx"

    if all(sf.s_get(key) is None for key in ["f_up", "mdf"]):
        logger.warning("No file provided yet.")

        menu_pdf.sidebar_file_upload()

        st.warning("Bitte Datei hochladen oder Beispiel auswählen")

        st.markdown("###")
        st.markdown("---")
    else:
        with st.sidebar:
            reset_download_container = st.container()
        with reset_download_container:
            gf.reset_button()
