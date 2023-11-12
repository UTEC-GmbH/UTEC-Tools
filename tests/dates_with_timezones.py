"""Mit Zeitzonen rumspielen"""

import datetime as dt

import polars as pl


def create_df() -> pl.DataFrame:
    """Create a df for testing"""

    dates: list[dt.datetime] = [
        dt.datetime(2021, 10, 31, 1, 0),
        dt.datetime(2021, 10, 31, 1, 15),
        dt.datetime(2021, 10, 31, 1, 30),
        dt.datetime(2021, 10, 31, 1, 45),
        dt.datetime(2021, 10, 31, 2, 0),
        dt.datetime(2021, 10, 31, 2, 15),
        dt.datetime(2021, 10, 31, 2, 30),
        dt.datetime(2021, 10, 31, 2, 45),
        dt.datetime(2021, 10, 31, 2, 0),
        dt.datetime(2021, 10, 31, 2, 15),
        dt.datetime(2021, 10, 31, 2, 30),
        dt.datetime(2021, 10, 31, 2, 45),
        dt.datetime(2021, 10, 31, 3, 0),
        dt.datetime(2021, 10, 31, 3, 15),
        dt.datetime(2021, 10, 31, 3, 30),
        dt.datetime(2021, 10, 31, 3, 45),
    ]

    return pl.DataFrame({"Date": dates, "Value": list(range(len(dates)))})
