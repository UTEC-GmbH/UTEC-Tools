"""Tests for Plotly Figrues"""

from datetime import datetime
from typing import Any

import numpy as np
import plotly.graph_objects as go

from modules import fig_annotations as anno
from modules import fig_general_functions as fgf
from tests import sample_data as sd


def test_middle_x_axis_int() -> None:
    """Test if finding the middle of the X-Axis works"""

    fig: go.Figure = sd.sample_fig(index_type="int")
    # dictionary for fig.data with trace names as keys
    fig_data: dict[str, dict[str, Any]] = fgf.fig_data_as_dic(fig)
    data_x: list[np.ndarray] = [fig_data[line]["x"] for line in fig_data]
    x_max: datetime = max(max(dat) for dat in data_x if len(dat) > 0)
    x_min: datetime = min(min(dat) for dat in data_x if len(dat) > 0)

    middle: datetime | float | int = anno.middle_xaxis(fig)

    assert isinstance(middle, (float, int))
    assert x_min < middle < x_max


def test_middle_x_axis_datetime() -> None:
    """Test if finding the middle of the X-Axis works"""

    fig: go.Figure = sd.sample_fig(
        df=sd.sample_df(multi_year="single", index_resolution="h"),
        index_type="datetime",
    )
    # dictionary for fig.data with trace names as keys
    fig_data: dict[str, dict[str, Any]] = fgf.fig_data_as_dic(fig)
    data_x: list[np.ndarray] = [fig_data[line]["x"] for line in fig_data]
    x_max: datetime = max(max(dat) for dat in data_x if len(dat) > 0)
    x_min: datetime = min(min(dat) for dat in data_x if len(dat) > 0)

    middle: datetime | float | int = anno.middle_xaxis(fig)

    assert isinstance(middle, datetime)
    assert x_min < middle < x_max


def test_add_arrow(fig_single_h_datetime: go.Figure) -> None:
    """Test if adding an arrow works"""
    fig: go.Figure = fig_single_h_datetime
    fig_data: dict[str, dict[str, Any]] = fgf.fig_data_as_dic(fig)
    fig_layout: dict[str, Any] = fgf.fig_layout_as_dic(fig)
    fig = anno.add_arrow(
        fig, fig_data, fig_layout, datetime(2021, 5, 5), 40, text="Test Arrow"
    )

    # dictionary for fig.layout
    fig_layout: dict[str, Any] = fgf.fig_layout_as_dic(fig)
    assert "Test Arrow" in [anno["name"] for anno in fig_layout]
