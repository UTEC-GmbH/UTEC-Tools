"""play with ChatGPT"""

# sourcery skip: avoid-global-variables
# pylint: disable=W0105

"""
df_resolution is an integer
"""


def match_resolution(df_resolution: int) -> str:
    """Matches a temporal resolution of a data frame given as an integer
    to the resolution as string needed for the weather data.

    Args:
        - df_resolution (int): Temporal Resolution of Data Frame (mdf.meta.td_mnts)

    Returns:
        - str: resolution as string for the 'resolution' arg in DwdObservationRequest
    """
    res_options: list[str] = [
        "minute_1",
        "minute_5",
        "minute_10",
        "hourly",
        "daily",
        "monthly",
    ]

    res_10: int = 10
    if df_resolution < res_10:
        return res_options[0]
    res_h: int = 60
    if df_resolution < res_h:
        return res_options[1]
    res_d: int = 60 * 24
    if df_resolution < res_d:
        return res_options[2]

    res_m: int = 60 * 24 * 28
    return res_options[3] if df_resolution < res_m else res_options[4]
