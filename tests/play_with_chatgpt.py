"""play with ChatGPT"""

# sourcery skip: avoid-global-variables

"""
How can I replace multiple strings in a list of strings?
"""


years: list[int] = [2018, 2019]

cols: list[str] = [
    "Bedarf 2018 - Arbeit",
    "Lieferung 2018 - Leistung",
    "Bedarf 2019 - Leistung",
    "Lieferung 2019",
]

for col in cols:
    for year in years:
        col = col.replace(year, "")
