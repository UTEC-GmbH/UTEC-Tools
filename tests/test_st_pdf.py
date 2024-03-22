"""Tests for the pdf editing section of the app"""

"""PDFs bearbeiten"""

from typing import Literal

import fitz as pymupdf
import streamlit as st
from loguru import logger

from modules import classes_data as cld
from modules import classes_figs as clf
from modules import constants as cont
from modules import df_manipulation as df_man
from modules import excel_import as ex_in
from modules import fig_annotations as fig_anno
from modules import fig_creation as fig_cr
from modules import fig_formatting as fig_format
from modules import general_functions as gf
from modules import graph_menus as menu_g
from modules import setup_stuff as set_stuff
from modules import streamlit_functions as sf
from modules import user_authentication as uauth

# setup stuff
gf.log_new_run()
MANUAL_DEBUG = True
set_stuff.page_header_setup(page=cont.ST_PAGES.graph.short)

EX_FILES: list[str] = [
    r"experiments/pdf_Deckblatt.pdf",
    r"experiments/pdf_Normale_Seite.pdf",
    r"experiments/pdf_Report.pdf",
]

"""
Jupyter

pdf = pymupdf.open(EX_FILES[0])
page = pdf[0]

"""


def remove_rexel_from_file(
    file: str = EX_FILES[0], save_type: Literal["overwrite", "new"] = "new"
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
