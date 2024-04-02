"""PDFs bearbeiten"""

import pypdf
from loguru import logger
from streamlit.runtime.uploaded_file_manager import UploadedFile

from modules import general_functions as gf


def remove_text_from_file(
    pdf_file: UploadedFile, text_bits_to_remove: list[str] | None = None
) -> pypdf.PdfWriter:
    """Remove text from a PDF file"""
    if text_bits_to_remove is None:
        raise TypeError

    logger.info(f"Removing text from file: {pdf_file.name}")
    logger.info(
        gf.string_new_line_per_item(
            text_bits_to_remove,
            title="Text-Elements to remove:",
            leading_empty_lines=1,
            trailing_empty_lines=1,
        )
    )

    with open(pdf_file, "rb") as file:
        pdf_in = pypdf.PdfReader(file)
        pdf_out = pypdf.PdfWriter()
        for page in pdf_in.pages:
            modified_text: str = page.extract_text()
            for text_to_remove in text_bits_to_remove:
                if text_to_remove in modified_text:
                    logger.info(
                        f"'{text_to_remove}' found on page {page.page_number}."
                    )
                    modified_text: str = text_on_page.replace(text_to_remove, "")
            
            pdf_out.add_page(page.extract_text()manipulated_text)
                
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
