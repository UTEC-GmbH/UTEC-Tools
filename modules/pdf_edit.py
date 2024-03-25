"""PDFs bearbeiten"""

import pathlib

import fitz as pymupdf
from loguru import logger
from streamlit.runtime.uploaded_file_manager import UploadedFile

from modules import general_functions as gf


def open_file(file: UploadedFile) -> pymupdf.Document:
    """Open a file with PyMuPDF"""

    pdf: pymupdf.Document = pymupdf.open(stream=file.getvalue())

    return pdf


def remove_text_from_file(
    pdf: pymupdf.Document, text_to_remove: list[str] | None = None
) -> pymupdf.Document:
    """Remove text from a PDF file

    Args:
        - pdf (pymupdf.Document): The PDF to edit
        - text_to_remove (list[str] | None, optional):
            A list of text to remove. Defaults to None.

    Returns:
        - pymupdf.Document: The modified PDF file

    """
    if text_to_remove is None:
        raise TypeError

    logger.info(f"Removing text from file: {pdf.name}")
    logger.info(
        gf.string_new_line_per_item(
            text_to_remove,
            title="Text-Elements to remove:",
            leading_empty_lines=1,
            trailing_empty_lines=1,
        )
    )

    for page in pdf:
        rects: list = [rec for text in text_to_remove for rec in page.search_for(text)]
        logger.info(
            f"{len(rects)} text elements to remove found on page {page.number}."
        )
        for rect in rects:
            page.add_redact_annot(rect, fill=(1, 1, 1))

        page.apply_redactions()

    return pdf


def remove_drawing_by_color(
    pdf: pymupdf.Document, color: tuple | None = None
) -> pymupdf.Document:
    """Remove every drawing with a certain color.

    Args:
        - pdf (pymupdf.Document): The PDF to edit
        - color (tuple | None, optional): Color to remove. Defaults to None.

    Returns:
        - pymupdf.Document: The modified PDF file

    """

    color = color or (0.0, 0.26666998863220215, 0.549019992351532)

    logger.info(f"Removing drawings from file: {pdf.name}")

    for page in pdf:
        rects: list = [
            drawing.get("rect")
            for drawing in page.get_drawings()
            if drawing.get("fill") == color
        ]
        logger.info(
            f"{len(rects)} drawing elements to remove found on page {page.number}."
        )
        for rect in rects:
            page.add_redact_annot(rect, fill=(1, 1, 1))

        page.apply_redactions()

    return pdf
