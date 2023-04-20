"""
General Functions for Figures
"""

from math import ceil
from typing import Any, Dict, List, Tuple

import plotly.graph_objects as go

from modules import constants as cont


def fig_data_as_dic(fig: go.Figure) -> Dict[str, Dict[str, Any]]:
    """Get the underlying data of a figure as Dictionaries for easy access

    Args:
        - fig (go.Figure): the figure to get the data from

    Returns:
        - data (Dict[str, Dict]): Dictionary with trace names as keys

    """

    return {entry["name"]: {key: entry[key] for key in entry} for entry in fig.data}


def fig_layout_as_dic(fig: go.Figure) -> Dict[str, Any]:
    """Get the underlying layout of a figure as Dictionaries for easy access

    Args:
        - fig (go.Figure): the figure to get the data from

    Returns:
        - layout (Dict[str, Any]): layout as Dictionary
    """

    return {item: fig.layout[item] for item in fig.layout}  # type: ignore


def get_colorway(fig: go.Figure, **kwargs) -> List[str]:
    """Get the available colors in the theme of the figure.
    If there are more lines in the figure than colors in the
    colorway, the colorway is elongated by copying.

    Args:
        - fig (go.Figure): Figure to examine

    Returns:
        - list[str]: List of available colors in the theme
    """
    data: Dict[str, Dict[str, Any]] = kwargs.get("data") or fig_data_as_dic(fig)
    layout: Dict[str, Any] = kwargs.get("layout") or fig_layout_as_dic(fig)
    colorway: List[str] = list(layout["template"]["layout"]["colorway"]) * 2
    if len(colorway) / 2 < len(list(data)):
        colorway *= ceil(len(data) / len(colorway)) + 2

    return colorway


def fig_type_by_title(fig: go.Figure, **kwargs) -> str:
    """Determine type of figure by comparing title to FIG_TITLES


    Args:
        - fig (go.Figure): Figure in question

    Returns:
        - str: Figure type as key in FIG_TITLES (e.g. 'lastgang', 'jdl', 'mon' etc.)

        (if type cannot be determined from the title, returns 'type unknown')
    """
    layout: Dict[str, Any] = kwargs.get("layout") or fig_layout_as_dic(fig)
    title: str = (
        layout["title"]["text"]
        if isinstance(layout.get("title"), Dict)
        else layout["meta"]["title"]
    )

    return next(
        (key for key, value in cont.FIG_TITLES.items() if value in title),
        "type unknown",
    )


def get_units_for_all_axes(fig: go.Figure, **kwargs) -> Dict[str, str]:
    """Get the units of all axes in a Figure from the metadata.


    Args:
        - fig (go.Figure): Figure in question

    Returns:
        - Dict[str, str]: Dictionary -> key = axis, value = unit
    """

    data: Dict[str, Dict[str, Any]] = kwargs.get("data") or fig_data_as_dic(fig)
    all_y_axes: List[str] = list(
        {f'yaxis{(val.get("yaxis") or "y").replace("y", "")}' for val in data.values()}
    )

    units_per_axis: Dict = {}
    for axis in all_y_axes:
        for trace in data.values():
            if trace.get("meta") and trace["yaxis"] == f'y{axis.replace("yaxis", "")}':
                units_per_axis[axis] = trace["meta"]["unit"]

    return units_per_axis


def fill_colour_with_opacity(sel_trans: str, line_colour: str) -> str:
    """Get an RGBA-string with the line colour and the selected transparency of the fill.
    Args:
        sel_trans (str): selected transparency (from the select box)
        line_colour (str): line colour (from colour picker)
    Returns:
        str: "rgba(r,g,b,a)"
    """
    fill_transp: int = (
        100
        if sel_trans == cont.TRANSPARENCY_OPTIONS[0]
        else (int(sel_trans.strip(cont.TRANSPARENCY_OPTIONS_SUFFIX)))
    )
    fill_col_rgba: Tuple[int | float] = tuple(
        int(line_colour.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4)
    ) + (1 - (fill_transp / 100),)

    return f"rgba{fill_col_rgba}"
