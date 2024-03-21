"""PDFs bearbeiten"""

from typing import Literal

import fitz as pymupdf

EX_FILES: list[str] = [r"experiments/Deckblatt.pdf", r"experiments/Normale_Seite.pdf"]

"""
Jupyter

pdf = pymupdf.open(EX_FILES[0])
page = pdf[0]

"""


def remove_rexel_from_file(
    file: str = EX_FILES[0], save_type: Literal["overwrite", "new"] = "new"
) -> None:
    """Remove Rexel and the pvXpert logo from a PDF file"""

    pdf = pymupdf.open(file)
    for page in pdf:

        # remove text
        for rect in sum(
            [
                page.search_for(text)
                for text in ["Rexel Germany GmbH & Co. KG", "www.rexel.de"]
            ],
            [],
        ):
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
