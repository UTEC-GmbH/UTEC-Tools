"""Einstellungen und Anmerkungen für plots"""


import datetime as dt
from typing import Any, Literal, TypeVar

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from loguru import logger
from scipy import signal

from modules import constants as cont
from modules import fig_general_functions as fgf
from modules import general_functions as gf
from modules import streamlit_functions as sf

DATE_OR_FLOAT = TypeVar("DATE_OR_FLOAT", dt.datetime, float, np.datetime64)


@gf.func_timer
def middle_xaxis(fig_data: dict[str, dict[str, Any]]) -> dt.datetime | float:
    """Mitte der x-Achse finden

    Args:
        - fig (go.Figure): Grafik, die untersucht werden soll

    Returns:
        - dt.datetime | float: je nach Index entweder die Zeit
            oder die Zahl in der Mitte der x-Achse
    """

    data_x: list = [val["x"] for val in fig_data.values()]
    x_max = max(max(dat) for dat in data_x if len(dat) > 0)
    x_min = min(min(dat) for dat in data_x if len(dat) > 0)

    middle: dt.datetime | float = x_min + (x_max - x_min) / 2

    logger.info(f"middle of x-axis: {middle}")

    return middle


def add_arrow(
    fig: go.Figure,
    fig_data: dict[str, dict[str, Any]],
    fig_layout: dict[str, Any],
    x_val: dt.datetime | float | int,
    y_or_line: float | int | str,
    **kwargs,
) -> go.Figure:
    """Beschriftungspfeil einfügen

    Args:
        - fig (go.Figure): Grafik
        - x_val (dt.datetime, float, int): Wert auf der x-Achse
        - y_or_line (float, int, str): Wert auf der y-Achse (float) oder
            Name der Linie (str), die beschriftet werden soll

    optional kwargs:
        - text (str): Beschriftungstext
        - hovertxt (str): Text bei Maus-Über
        - yaxis(str): die y-Achse, auf die sich der y-Wert bezieht
        - anchor (Literal["right", "left"]): Ausrichtung der Beschriftung
        - x_vers (int): Abstand zwischen Pfeilspitze und Beschriftung
            in X-Richtung in px; default = 20
        - y_vers (int): Abstand zwischen Pfeilspitze und Beschriftung
            in Y-Richtung in px; default = 10
        - middle_xaxis (dt.datetime | float):
            die Mitte der x-Achse (für die Ausrichtung)

    Returns:
        - go.Figure: Grafik mit Pfeilen
    """

    # find the y-value for the given x-value, if no y-value is given
    if isinstance(y_or_line, str):
        line_data: dict[str, Any] | None = fig_data[y_or_line]
        y_val: float = line_data["x"][np.where(line_data["y"] == x_val)[0][0]]
    else:
        line_data = None
        y_val = float(y_or_line)

    # Beschriftungstext
    text: str = kwargs.get("text") or f"{x_val!s} kW"

    # Text bei mouse-hover - default: x-Wert (Datum, an dem der y-Wert auftritt)
    hovertext: str = kwargs.get("hovertext") or hovertext_from_x_val(
        fig_layout["meta"]["title"], x_val, line_data
    )

    # Textausrichtung
    mid: dt.datetime | np.datetime64 | int = kwargs.get("middle_xaxis") or middle_xaxis(
        fig_data
    )
    anc: bool = x_val > mid
    anchor: Literal["right", "left"] = (
        kwargs.get("anchor") or "right" if anc else "left"
    )

    dic_arrow: dict[str, Any] = {
        "x": x_val,
        "y": y_val,
        "yref": kwargs.get("yaxis") or "y1",
        "name": text,
        "text": text,
        "hovertext": hovertext,
        "xanchor": anchor,
        "ax": kwargs.get("x_vers") or -20 if anchor == "right" else 20,
        "ay": kwargs.get("y_vers") or (10 * y_val / (abs(y_val))) if y_val > 0 else 10,
        "showarrow": True,
        "arrowhead": 3,
        "bgcolor": "rgba(" + cont.FARBEN["weiß"] + cont.ALPHA["bg"],
        "visible": False,
    }

    if fig_layout.get("annotations") and text in [
        an["name"] for an in fig_layout["annotations"]
    ]:
        fig = fig.update_annotations(dic_arrow, {"name": text})
    else:
        fig = fig.add_annotation(dic_arrow)

    return fig


@gf.func_timer
def add_arrows_min_max(fig: go.Figure, **kwargs) -> go.Figure:
    """Pfeile an Maximum und Minimum aller Linien in der Grafik


    Args:
        - fig (go.Figure): Grafik, die Pfeile erhalten soll
    """

    fig_data: dict[str, dict[str, Any]] = kwargs.get("data") or fgf.fig_data_as_dic(fig)
    fig_layout: dict[str, Any] = kwargs.get("layout") or fgf.fig_layout_as_dic(fig)
    middle_x: dt.datetime | float = middle_xaxis(fig_data)

    # alle Linien in Grafik
    for line in fig_data.values():
        if gf.check_if_not_exclude(line):
            y_val: float = (
                np.nanmin(line["y"])
                if line["meta"]["negativ"]
                else np.nanmax(line["y"])
            )

            if not isinstance(y_val, float | np.floating):
                logger.debug(
                    f"Annotation for {line['name']} SKIPPED "
                    f"because y_val is type '{type(y_val)}'."
                )
                continue

            x_val: dt.datetime | float = line["x"][np.where(line["y"] == y_val)[0][0]]
            unit: str = line["meta"]["unit"]
            tit: str = line["name"]

            fig = add_arrow(
                fig,
                fig_data,
                fig_layout,
                x_val,
                y_or_line=y_val,
                text=f"max {tit}: {gf.number_as_string(abs(y_val))}{unit}",
                yaxis=line["yaxis"],
                middle_xaxis=middle_x,
            )
            logger.info(
                f"Pfeil hinzugefügt in '{fig.layout.meta['title'].split('<')[0]}': "
                f"'max {tit}: {gf.number_as_string(abs(y_val))}{unit}'"
            )

    logger.success("Max / Min arrows added to figure")

    return fig


def hovertext_from_x_val(
    title: str, x_val: dt.datetime | float, line_data: dict[str, Any] | None
) -> str:
    """Falls kein Hovertext gegeben wird, erstellt diese Funktion einen aus dem x-Wert

    Args:
        jdl (bool): handelt es sich bei der Grafik um eine Jahresdauerlinie
        x_val (dt.datetime | float): x-Wert, der bezeichnet wird
        line_data (dict[str, Any] | None): line_data für zu beschriftende Linie

    Returns:
        str: Hovertext
    """
    jdl: bool = cont.FIG_TITLES.jdl in title
    if jdl and line_data:
        hov_date: dt.datetime | str = line_data["customdata"][
            np.where(line_data["x"] == x_val)
        ][0][0]

    elif isinstance(x_val, dt.datetime):
        hov_date = x_val

    else:
        hov_date = str(x_val)

    hovertext: str = (
        f"{hov_date:%d.%m.%Y %H:%M}" if isinstance(hov_date, dt.datetime) else hov_date
    )

    return hovertext


# @st.experimental_memo(suppress_st_warning=True, show_spinner=False)
@gf.func_timer
def vline(fig: go.Figure, x_val: float or dt.datetime, txt: str, pos: str) -> None:
    """Vertikale Linie einfügen"""

    fig.add_vline(
        x=x_val,
        line_dash="dot",
        line_width=1,
        annotation_text=txt,
        annotation_position=pos,
        annotation_textangle=-90,
        annotation_bgcolor="rgba(" + cont.FARBEN["weiß"] + cont.ALPHA["bg"],
    )

    logger.success(f"created vertical line at x-val: {x_val}")


# @st.experimental_memo(suppress_st_warning=True, show_spinner=False)
@gf.func_timer
def hide_hlines(fig: go.Figure) -> None:
    """Horizontale Linien ausblenden (ohne sie zu löschen)"""

    fig_data: dict[str, dict[str, Any]] = fgf.fig_data_as_dic(fig)
    fig_layout: dict[str, Any] = fgf.fig_layout_as_dic(fig)

    for dat in fig_data:
        if "hline" in dat:
            fig_data[dat]["visible"] = False

    for shape_or_anno in ["shapes", "annotations"]:
        if shape_or_anno in fig_layout:
            for item in fig_layout[shape_or_anno]:
                if "hline" in item["name"]:
                    item["visible"] = False

    logger.success("set the visibility of all horizontal lines to False")


# @st.experimental_memo(suppress_st_warning=True, show_spinner=False)
@gf.func_timer
def hline_line(
    fig: go.Figure,
    value: float,
    ti_hor_init: str | None = None,
) -> None:
    """Horizontale Linie einfügen"""

    ti_hor: str | None = None if ti_hor_init in {"", "new text"} else ti_hor_init
    cb_hor_dash: bool = sf.s_get("cb_hor_dash") or True
    y_axis: str = sf.s_get("sb_h_line_y") or "y"
    y_axis = "y" if y_axis not in fgf.get_set_of_visible_y_axes(fig) else y_axis
    if any("hline" in x for x in [s.name for s in fig.layout.shapes]):
        for shape in fig.layout.shapes:
            if "hline" in shape.name:
                shape.y0 = shape.y1 = value
                shape.visible = True
                shape.line.dash = "dot" if cb_hor_dash else "solid"
                shape.yref = y_axis

        for annot in fig.layout.annotations:
            if "hline" in annot.name:
                annot.y = value
                annot.visible = bool(ti_hor)
                annot.text = ti_hor
                annot.yref = y_axis

        logger.info(f"existing horizontal line moved to y = {value}")

    else:
        fig.add_hline(
            y=value,
            yref=y_axis,
            name="hline",
            line_dash="dot" if cb_hor_dash else "solid",
            line_width=1,
            annotation_text=ti_hor,
            annotation_name="hline",
            annotation_visible=bool(ti_hor),
            annotation_position="top left",
            annotation_bgcolor="rgba(" + cont.FARBEN["weiß"] + cont.ALPHA["bg"],
            visible=True,
        )

        logger.success(f"horizontal line create at y = {value}")


# @st.experimental_memo(suppress_st_warning=True, show_spinner=False)
@gf.func_timer
def hline_fill(fig: go.Figure, value: float, ms_hor: list) -> go.Figure:
    """Ausfüllen zwischen horizontaler Linie und Linien"""
    dic_fill = {}
    traces = [tr for tr in fig.data if tr.name in ms_hor]

    for trace in traces:
        if value > 0:
            dic_fill[trace.name] = np.where(trace.y < value, trace.y, value)
        else:
            dic_fill[trace.name] = np.where(trace.y > value, trace.y, value)

    # hline-Füllungen, die es schon gibt
    for key in dic_fill:
        if "hline " + key in [tr.name for tr in fig.data]:
            trace = [tr for tr in fig.data if tr.name == "hline " + key][0]
            trace.y = dic_fill[trace.name.replace("hline ", "")]
            trace.showlegend = False
            trace.visible = True

        else:
            trace = [tr for tr in fig.data if tr.name == key][0]
            fig.add_trace(
                go.Scatter(
                    x=trace.x,
                    y=dic_fill[trace.name],
                    legendgroup=trace.legendgroup,
                    name="hline " + trace.name,
                    fill="tozeroy",
                    fillcolor="rgba(" + cont.FARBEN["schwarz"] + cont.ALPHA["fill"],
                    mode="none",
                    showlegend=False,
                    visible=True,
                    hoverinfo="skip",
                )
            )

    return fig


# horizontale / vertikale Linien
@gf.func_timer
def h_v_lines() -> None:
    """Horizontale und vertikale Linien"""

    # horizontale Linie
    lis_figs_hor: list[str] = ["fig_base"]
    if sf.s_get("cb_jdl"):
        lis_figs_hor.append("fig_jdl")

    for fig in lis_figs_hor:
        hide_hlines(st.session_state[fig])
        if st.session_state["ni_hor"] != 0:
            hline_line(
                st.session_state[fig],
                st.session_state["ni_hor"],
                st.session_state["ti_hor"],
            )


def calculate_smooth_values(trace: dict[str, Any]) -> np.ndarray:
    """Y-Werte für geglättete Linie berechnen


    Args:
        - trace (dict[str, Any]): Linie, die geglättet werden soll

    Returns:
        - np.ndarray: geglättete Y-Werte
    """

    logger.info(f"Geglättete y-Werte für '{trace['name']}' werden neu berechnet.")

    return signal.savgol_filter(
        x=pd.Series(trace["y"]).interpolate("akima"),
        mode="mirror",
        window_length=int(sf.s_get("gl_win") or sf.s_get("smooth_start_val")),
        polyorder=int(sf.s_get("gl_deg") or 3),
    )


@gf.func_timer
def smooth(fig: go.Figure, **kwargs) -> go.Figure:
    """geglättete Linien"""

    fig_data: dict[str, dict[str, Any]] = kwargs.get("data") or fgf.fig_data_as_dic(fig)

    traces: list[dict] = kwargs.get("traces") or [
        trace for trace in fig_data.values() if gf.check_if_not_exclude(trace["name"])
    ]
    gl_win: int = sf.s_get("gl_win")
    gl_deg: int = sf.s_get("gl_deg") or 3

    for trace in traces:
        smooth_name: str = f"{trace['name']}{cont.Suffixes.col_smooth}"
        smooth_visible: bool = bool(sf.s_get(f"cb_vis_{smooth_name}"))

        if smooth_visible:
            meta_trace: dict[str, Any] = trace["meta"]
            logger.debug(f"meta data for '{trace['name']}': {meta_trace}")
            if smooth_name not in fig_data:
                meta_trace |= {"gl_win": gl_win, "gl_deg": gl_deg}
                logger.debug(
                    f"meta data for '{trace['name']}' after update: {meta_trace}"
                )
                smooth_legendgroup: str = trace.get("legendgroup") or "geglättet"
                fig = fig.add_trace(
                    go.Scatter(
                        x=trace["x"],
                        y=calculate_smooth_values(trace),
                        mode="lines",
                        line_dash="0.75%",
                        name=smooth_name,
                        legendgroup=smooth_legendgroup,
                        legendgrouptitle_text=smooth_legendgroup,
                        hoverinfo="skip",
                        visible=True,
                        yaxis=trace["yaxis"],
                        meta=meta_trace,
                    )
                )
                fgf.debug_check_for_missing_meta_data(fig)

            elif any(
                [
                    meta_trace.get("gl_win") != gl_win,
                    meta_trace.get("gl_deg") != gl_deg,
                ]
            ):
                meta_trace |= {"gl_win": gl_win, "gl_deg": gl_deg}
                fig = fig.update_traces(
                    {"y": calculate_smooth_values(trace), "meta": meta_trace},
                    {"name": smooth_name},
                )

        elif smooth_name in fig_data:
            fig = fig.update_traces({"visible": False}, {"name": smooth_name})

    fgf.debug_check_for_missing_meta_data(fig)

    return fig


# Ausreißer entfernen
# @st.experimental_memo(suppress_st_warning=True, show_spinner=False)
@gf.func_timer
def remove_outl(fig: go.Figure, cut_off: float) -> go.Figure:
    """Ausreißerbereinigung"""
    for trace in fig.data:
        trace["y"] = pd.Series(
            np.where(trace["y"] > cut_off, np.nan, trace["y"])
        ).interpolate("akima")

    for annot in fig.layout.annotations:
        if annot["y"] > cut_off:
            y_old = annot["y"]
            annot["y"] = cut_off
            annot["text"] = annot["text"].replace(str(y_old), str(cut_off))

    return fig


# Ausreißerbereinigung
@gf.func_timer
def clean_outliers() -> None:
    """Ausreißerbereinigung"""

    if st.session_state["ni_outl"] < st.session_state["abs_max"]:
        for fig in st.session_state["lis_figs"]:
            if fig != "fig_mon":
                st.session_state[fig] = remove_outl(
                    st.session_state[fig], st.session_state["ni_outl"]
                )
