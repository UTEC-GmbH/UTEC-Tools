"""Sample Data for Tests"""

import json
from typing import Any, Literal

import pandas as pd
import plotly.graph_objects as go
import polars as pl

from modules import constants as cont


def sample_df(
    multi_year: Literal["single", "multi"] = "multi",
    index_resolution: Literal["15", "h", "m"] = "h",
) -> pl.DataFrame:
    """Create DataFrame with example data and datetime-index
    The DataFrames are read from parquet files which
    were created from the example files


    Years:
        - Multi-Year-DataFrame: 2017 - 2019
        - Single-Year-DataFrame: 2018

    Columns of the DataFrame:
        - Strombedarf [kWh]
        - BHKW Strom [kWh]
        - Strombezug (1-1:1.29.0) [kW]
        - Stromeinsp. (1-1:2.29.0) [kW]
        - Wärmebedarf [kWh]
        - Kessel [kWh]
        - BHKW Wärme [kWh]
        - Temperatur [°C]

    Args:
        - multi_year (Literal[single, multi], optional):
            Daten über ein einzelnes oder mehrere Jahre. Defaults to "multi".
        - index_resolution (Literal[15, h, m], optional):
            15-minutes, hourly or monthly resolution of the index. Defaults to "15min".

    Returns:
        pd.DataFrame
    """

    path: str = f"{cont.CWD}\\tests\\sample_data\\"
    df: pl.DataFrame = pl.read_parquet(
        f"{path}df_{multi_year}_{index_resolution}.parquet"
    )

    for col in df.columns:
        if any(neg in col for neg in cont.NEGATIVE_VALUES):
            df[col] = df[col] * -1

    return df


def sample_dic_meta(**kwargs) -> dict:
    """Create a dictionary with metadata for the sample DataFrames

    - kwargs: df (pd.DataFrame)

    Contents for each column:
    - orig_tit      (oritinal title)
    - tit           (title after rename)
    - unit     (unit of the original data)

    if an OBIS-code was found in the column title, also contains for that column:
    - code
    - messgr_c
    - messar_c
    - messgr_n
    - messar_n

    """
    with open("tests/sample_data/dic_meta.json") as json_file:
        meta: dict[str, dict[str, Any]] = json.load(json_file)

    meta["index"] = {"datetime": False, "years": []}

    df: pd.DataFrame = (
        kwargs["df"]
        if isinstance(kwargs.get("df"), pd.DataFrame)
        else sample_df("single", "h")
    )

    if isinstance(df.index, pd.DatetimeIndex):
        meta["index"]["datetime"] = True
        meta["index"]["td_mean"] = df.index.to_series().diff().mean().round("min")  # type: ignore
        if meta["index"]["td_mean"] == pd.Timedelta(minutes=15):
            meta["index"]["td_int"] = "15min"
        elif meta["index"]["td_mean"] == pd.Timedelta(hours=1):
            meta["index"]["td_int"] = "h"

        cut_off: int = 50
        meta["index"]["years"].extend(
            y
            for y in set(df.index.year)
            if len(df.loc[df.index.year == y, :]) > cut_off
        )

    return meta


def sample_fig(
    index_type: Literal["datetime", "int"] = "datetime",
    lines: list[str] | None = None,
    **kwargs,
) -> go.Figure:
    """Create a Plotly line graph from sample data

    Args:
        - df (pd.DataFrame, optional): Sample Data.
        - index_type (Literal[datetime, int], optional):
            Der Index des DataFrames kann entweder als datetime belassen oder in int umgewandelt werden. Defaults to "datetime".
        - lines (list[str] | None, optional): If set to None, all columns of the df are used. Defaults to None.

    Returns:
        go.Figure: Plotly Plot
    """

    df: pd.DataFrame = kwargs.get("df") or sample_df("single", "h")
    metadata: dict = sample_dic_meta(data_frame=df)

    if index_type == "int":
        df = df.reset_index(drop=True)

    fig: go.Figure = go.Figure()

    title: str = "Test Figure"
    fig = fig.update_layout(
        {"title": title, "meta": {"title": title, "units": ["kWh", "kW", "°C"]}}
    )

    used_lines: list[str] = lines or df.columns.to_list()

    for line in used_lines:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df[line],
                name=line,
                mode="lines",
                visible=True,
                meta={"unit": metadata[line]["unit"]},
            ),
        )

    return fig
