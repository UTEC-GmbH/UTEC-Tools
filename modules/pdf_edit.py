"""PDFs bearbeiten"""

import pathlib
import tempfile

import fitz as pymupdf
from loguru import logger
from streamlit.runtime.uploaded_file_manager import UploadedFile

from modules import general_functions as gf


def temporary_files(files: list[UploadedFile]) -> list[pathlib.WindowsPath]:
    """Create temporary files"""

    temp_dir: str = tempfile.mkdtemp()
    for file in files:
        path: str = pathlib.Path(temp_dir) / file.name
        with open(path, "wb") as f:
            f.write(file.getvalue())

    file_paths: list[pathlib.WindowsPath] = [
        pathlib.Path(temp_dir) / file.name for file in files
    ]

    logger.info(
        gf.string_new_line_per_item(
            [str(path) for path in file_paths], "Temporäre Dateien:"
        )
    )

    return file_paths


def open_file(file: str) -> pymupdf.Document:
    """Open a file with PyMuPDF"""

    pdf: pymupdf.Document = pymupdf.open(file)
    logger.success(f"Successfully opened file: {pdf.name}")

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


def save_and_close(pdf: pymupdf.Document) -> None:
    """Save the PDF either as
    a new file (with an extension in the file name) in the same folder or
    overwrite the original file.
    """
    save_path: pathlib.Path = pathlib.Path.home() / "Desktop/bearbeitet"
    save_path.mkdir(parents=True, exist_ok=True)
    file_name: str = pathlib.Path(pdf.name).name
    file_save: pathlib.Path = save_path / file_name
    pdf.save(file_save)
    logger.info(f"PDF saved as {file_save}")

    pdf.close()
