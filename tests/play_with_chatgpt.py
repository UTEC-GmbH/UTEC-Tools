"""play with ChatGPT"""

# sourcery skip: avoid-global-variables
# pylint: disable=W0105,C0413
# ruff: noqa: E402, E501, RUF100

"""
I have a DataFrame in which I would like to 
set the value to "None" if the difference is 0. 
How can I do this in polars?
"""

import datetime as dt

import polars as pl

df = pl.DataFrame(
    {
        "↓ Index ↓": [
            dt.datetime(2022, 1, 1),
            dt.datetime(2022, 1, 2),
            dt.datetime(2022, 1, 3),
            dt.datetime(2022, 1, 4),
            dt.datetime(2022, 1, 5),
        ],
        "value": [1, 2, 2, 4, 5],
    }
)
df.with_columns(
    pl.when(pl.col(col).diff() == 0).then(None).otherwise(pl.col(col)).keep_name()
    for col in df.columns
)
