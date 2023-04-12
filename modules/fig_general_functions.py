"""
General Functions for Figures
"""

from math import ceil
from typing import Any

import plotly.graph_objects as go

from modules import constants as cont


def fig_data_as_dic(fig: go.Figure) -> dict[str, dict[str, Any]]:
    """Get the underlying data of a figure as dictionaries for easy access

    Args:
        - fig (go.Figure): the figure to get the data from

    Returns:
        - data (dict[str, dict]): dictionary with trace names as keys

    """

    return {entry["name"]: {key: entry[key] for key in entry} for entry in fig.data}


def fig_layout_as_dic(fig: go.Figure) -> dict[str, Any]:
    """Get the underlying layout of a figure as dictionaries for easy access

    Args:
        - fig (go.Figure): the figure to get the data from

    Returns:
        - layout (dict[str, Any]): layout as dictionary
    """

    return {item: fig.layout[item] for item in fig.layout}  # type: ignore


def get_colorway(fig: go.Figure, **kwargs) -> list[str]:
    """Get the available colors in the theme of the figure.
    If there are more lines in the figure than colors in the
    colorway, the colorway is elongated by copying.

    Args:
        - fig (go.Figure): Figure to examine

    Returns:
        - list[str]: List of available colors in the theme
    """
    data: dict[str, dict[str, Any]] = kwargs.get("data") or fig_data_as_dic(fig)
    layout: dict[str, Any] = kwargs.get("layout") or fig_layout_as_dic(fig)
    colorway: list[str] = list(layout["template"]["layout"]["colorway"])
    if len(colorway) < len(list(data)):
        colorway *= ceil(len(data) / len(colorway))

    return colorway


def fig_type_by_title(fig: go.Figure, **kwargs) -> str:
    """Determine type of figure by comparing title to FIG_TITLES


    Args:
        - fig (go.Figure): Figure in question

    Returns:
        - str: Figure type as key in FIG_TITLES (e.g. 'lastgang', 'jdl', 'mon' etc.)

        (if type cannot be determined from the title, returns 'type unknown')
    """
    layout: dict[str, Any] = kwargs.get("layout") or fig_layout_as_dic(fig)
    title: str = (
        layout["title"]["text"]
        if isinstance(layout.get("title"), dict)
        else layout["meta"]["title"]
    )

    return next(
        (key for key, value in cont.FIG_TITLES.items() if value in title),
        "type unknown",
    )


def get_units_for_all_axes(fig: go.Figure, **kwargs) -> dict[str, str]:
    """Get the units of all axes in a Figure from the metadata.


    Args:
        - fig (go.Figure): Figure in question

    Returns:
        - dict[str, str]: Dictionary -> key = axis, value = unit
    """

    data: dict[str, dict[str, Any]] = kwargs.get("data") or fig_data_as_dic(fig)
    all_y_axes: list[str] = list(
        {f'yaxis{(val.get("yaxis") or "y").replace("y", "")}' for val in data.values()}
    )

    units_per_axis: dict = {}
    for axis in all_y_axes:
        for trace in data.values():
            if trace.get("meta") and trace["yaxis"] == f'y{axis.replace("yaxis", "")}':
                units_per_axis[axis] = trace["meta"]["unit"]

    return units_per_axis
