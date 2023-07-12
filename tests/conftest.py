"""Configuration File for Tests"""

import pandas as pd
import plotly.graph_objects as go
import pytest

from tests import sample_data as sd


# ----------Meta Data-----------
@pytest.fixture(scope="session")
def dic_meta() -> dict:
    """Create a dictionary with meta data for the sample DataFrame"""

    return sd.sample_dic_meta()


# ----------DataFrames-----------
@pytest.fixture(scope="session")
def df_single_15() -> pd.DataFrame:
    """Create a sample DataFrame with 15-min-data for the year 2018"""

    return sd.sample_df(multi_year="single", index_resolution="15")


@pytest.fixture(scope="session")
def df_single_h() -> pd.DataFrame:
    """Create a sample DataFrame with hourly data for the year 2018"""

    return sd.sample_df(multi_year="single", index_resolution="h")


@pytest.fixture(scope="session")
def df_single_m() -> pd.DataFrame:
    """Create a sample DataFrame with monthly data for the year 2018"""

    return sd.sample_df(multi_year="single", index_resolution="m")


@pytest.fixture(scope="session")
def df_multi_15() -> pd.DataFrame:
    """Create a sample DataFrame with 15-min-data for the years 2017 - 2019"""

    return sd.sample_df(multi_year="multi", index_resolution="15")


@pytest.fixture(scope="session")
def df_multi_h() -> pd.DataFrame:
    """Create a sample DataFrame with hourly data for the years 2017 - 2019"""

    return sd.sample_df(multi_year="multi", index_resolution="h")


@pytest.fixture(scope="session")
def df_multi_m() -> pd.DataFrame:
    """Create a sample DataFrame with monthly data for the years 2017 - 2019"""

    return sd.sample_df(multi_year="multi", index_resolution="m")


# ----------Plotly Figures-----------
@pytest.fixture(scope="session")
def fig_single_15_datetime() -> go.Figure:
    """Create a sample Figure from hourly data of of the year 2018"""
    df: pd.DataFrame = sd.sample_df(multi_year="single", index_resolution="15")
    return sd.sample_fig(df)


@pytest.fixture(scope="session")
def fig_single_h_datetime() -> go.Figure:
    """Create a sample Figure from hourly data of of the year 2018"""
    df: pd.DataFrame = sd.sample_df(multi_year="single", index_resolution="h")
    return sd.sample_fig(df)


@pytest.fixture(scope="session")
def fig_single_m_datetime() -> go.Figure:
    """Create a sample Figure from hourly data of of the year 2018"""
    df: pd.DataFrame = sd.sample_df(multi_year="single", index_resolution="m")
    return sd.sample_fig(df)


@pytest.fixture(scope="session")
def fig_multi_15_datetime() -> go.Figure:
    """Create a sample Figure from hourly data of of the year 2018"""
    df: pd.DataFrame = sd.sample_df(multi_year="multi", index_resolution="15")
    return sd.sample_fig(df)


@pytest.fixture(scope="session")
def fig_multi_h_datetime() -> go.Figure:
    """Create a sample Figure from hourly data of of the year 2018"""
    df: pd.DataFrame = sd.sample_df(multi_year="multi", index_resolution="h")
    return sd.sample_fig(df)


@pytest.fixture(scope="session")
def fig_multi_m_datetime() -> go.Figure:
    """Create a sample Figure from hourly data of of the year 2018"""
    df: pd.DataFrame = sd.sample_df(multi_year="multi", index_resolution="m")
    return sd.sample_fig(df)
