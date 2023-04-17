"""
Formatting and configuration of plots

- add range slider
- formatting of axes, layout and traces
- plotly configuration
"""

from datetime import datetime
from typing import Any

import plotly.graph_objects as go
import streamlit as st
from loguru import logger

from modules import constants as cont
from modules import fig_general_functions as fgf
from modules.fig_annotations import smooth
from modules.general_functions import (
    func_timer,
    last_day_of_month,
    sort_list_by_occurance,
)


@func_timer
def format_tickstops(fig: go.Figure) -> list[dict[str, Any]]:
    """tickformat stops for axes

    Args:
        fig (go.Figure): figure to update

    Returns:
        list[dict[str, Any]]: formating parameters
    """

    multi_y: bool | None = fig.layout.meta.get("multi_y")  # type: ignore

    return [
        {
            "dtickrange": [None, cont.DURATIONS_IN_MS["half_day"]],
            "value": "%H:%M\n%e. %b" if multi_y else "%H:%M\n%a %e. %b",
        },
        {
            "dtickrange": [
                cont.DURATIONS_IN_MS["half_day"] + 1,
                cont.DURATIONS_IN_MS["week"],
            ],
            "value": "%e. %b" if multi_y else "%a\n%e. %b",
        },
        {
            "dtickrange": [
                cont.DURATIONS_IN_MS["week"] + 1,
                cont.DURATIONS_IN_MS["month"],
            ],
            "value": "%e.\n%b",
        },
        {"dtickrange": [cont.DURATIONS_IN_MS["month"] + 1, None], "value": "%b"},
    ]


def format_primary_y_axis(y_suffix: str) -> dict[str, Any]:
    """Format Parameters for the Primary Y-Axis


    Args:
        - y_suffix (str): suffix for ticks (usually the unit)

    Returns:
        - dict[str, Any]: dictionary of parameters
    """
    return {
        "ticksuffix": y_suffix,
        "tickformat": ",d",
        "side": "left",
        "anchor": "x",
        "separatethousands": True,
        "fixedrange": False,
        "visible": True,
    }


def format_secondary_y_axis(y_suffix: str, overlaying: str) -> dict[str, Any]:
    """Format Parameters for the Secondary Y-Axes

    Args:
        - y_suffix (str): siffix for ticks (usually the unit)
        - overlaying (str): name of primary y-axis (e.g. "y", "y2", ...)

    Returns:
        - dict[str, Any]: dictionary of parameters
    """
    return format_primary_y_axis(y_suffix) | {
        "tickmode": "sync",
        "anchor": "free",
        "side": "right",
        "overlaying": overlaying,
        "autoshift": True,
        "shift": 10,
    }


def add_range_slider(fig: go.Figure) -> go.Figure:
    """Range Slider und Range Selector in Grafik einfügen

    Args:
        fig (go.Figure): Grafik, die den Range Slider bekommen soll

    Returns:
        go.Figure: Grafik mit Range Slider
    """

    return fig.update_xaxes(
        {
            "rangeslider": {
                "visible": True,
            },
            "rangeselector": {
                "buttons": [
                    {"count": 1, "label": "Tag", "step": "day", "stepmode": "backward"},
                    {
                        "count": 7,
                        "label": "Woche",
                        "step": "day",
                        "stepmode": "backward",
                    },
                    {
                        "count": 1,
                        "label": "Monat",
                        "step": "month",
                        "stepmode": "backward",
                    },
                    {"step": "all", "label": "alle"},
                ],
                "xanchor": "center",
                "x": 0.5,
                "yanchor": "bottom",
                "y": 1.15,
            },
        }
    )


@func_timer
def standard_axes_and_layout(
    fig: go.Figure,
    x_tickformat: str = "%b",
) -> go.Figure:
    """Grundeinstellungen der Grafik


    Args:
        - fig (go.Figure): Grafik, die angepasst werden soll
        - x_tickformat (str, optional): Format der Daten auf der X-Achse. Standard: "%b" (Monat).

    Returns:
        - go.Figure: Bearbeitete Grafik
    """

    data: dict[str, dict[str, Any]] = fgf.fig_data_as_dic(fig)
    layout: dict[str, Any] = fgf.fig_layout_as_dic(fig)
    title: str = layout["title"]["text"]

    fig = standard_xaxis(fig, data, title, x_tickformat)
    fig = standard_yaxis(fig, data, layout, title)

    fig = standard_layout(fig, data)

    return fig


@func_timer
def standard_xaxis(
    fig: go.Figure,
    data: dict[str, dict[str, Any]],
    title: str,
    x_tickformat: str,
) -> go.Figure:
    """Grundeinstelungen der X-Achse


    Args:
        - fig (go.Figure): Grafik, die bearbeitet werden soll
        - data (dict[str, dict[str, Any]]): Daten der Grafik (für Range der Achse)
        - title (str): Titel der Grafik (nicht der Achse)
        - x_tickformat (str): Format der Daten auf der X-Achse. Standard: "%b" (Monat).

    Returns:
        - go.Figure: Bearbeitete Grafik
    """

    x_max: Any = max(max(p["x"]) for p in data.values())
    if isinstance(x_max, datetime):
        x_max = last_day_of_month(x_max)

    x_min: Any = min(min(p["x"]) for p in data.values())
    if isinstance(x_min, datetime):
        x_min = x_min.replace(day=1)

    return fig.update_xaxes(
        nticks=13,
        tickformat=x_tickformat,
        ticklabelmode="period",
        ticksuffix=None,
        range=[x_min, x_max],
        separatethousands=True,
        tickformatstops=format_tickstops(fig) if x_tickformat == "%b" else None,
        showspikes=True,
        spikemode="across",
        spikecolor="black",
        spikesnap="cursor",
        spikethickness=1,
        fixedrange=cont.FIG_TITLES["mon"] in title,
    )


@func_timer
def standard_yaxis(
    fig: go.Figure,
    data: dict[str, dict[str, Any]],
    layout: dict[str, Any],
    title: str,
) -> go.Figure:
    """standard formatting of the y-axis"""

    all_y_axes: list[str] = list(
        {f'yaxis{(val.get("yaxis") or "y").replace("y", "")}' for val in data.values()}
    )
    units_per_axis: dict[str, str] = fgf.get_units_for_all_axes(
        fig, data=data, layout=layout
    )

    y_suffix: str = units_per_axis[all_y_axes[0]]
    if cont.FIG_TITLES["mon"] in title and y_suffix == " kW":
        y_suffix = " kWh"

    fig = fig.update_layout({all_y_axes[0]: format_primary_y_axis(y_suffix)})

    if len(all_y_axes) > 1:
        for axis in all_y_axes[1:]:
            y_suffix = units_per_axis[axis]
            fig = fig.update_layout(
                {
                    axis: format_secondary_y_axis(
                        y_suffix, all_y_axes[0].replace("axis", "")
                    )
                }
            )

    return fig


@func_timer
def standard_layout(fig: go.Figure, data: dict[str, dict[str, Any]]) -> go.Figure:
    """Standardlayout"""

    visible_traces: list[str] = [
        trace
        for trace, value in data.items()
        if value["visible"] and all(excl not in trace for excl in cont.EXCLUDE)
    ]
    lastgang: bool = fgf.fig_type_by_title(fig) == "lastgang"

    return fig.update_layout(
        separators=",.",
        font_family="Arial",
        title={
            "xref": "container",
            "x": 0,
            "yanchor": "bottom",
            "yref": "paper",
            "y": 1,
            "pad_b": 15,
        },
        legend={
            "groupclick": "toggleitem",
            "orientation": "v",
            "yanchor": "top",
            "y": 1 if lastgang else 0.98,
            "xanchor": "left" if lastgang else "right",
            "x": 1.02 if lastgang else 0.99,
        },
        showlegend=len(visible_traces) > 1,
        margin={"l": 5, "r": 5, "t": 40, "b": 10},
        hovermode="x",
    )


@func_timer
def update_main(fig: go.Figure) -> go.Figure:
    """Darstellungseinstellungen aus dem Hauptfenster"""

    fig = show_traces(fig)
    fig = format_traces(fig)
    visible_traces: list[str] = [
        tr.name
        for tr in fig.data
        if tr.visible and all(ex not in tr.name for ex in cont.EXCLUDE)
    ]
    number_of_visible_traces: int = len(visible_traces)

    fig = show_y_axes(fig)

    fig = show_annos(fig, visible_traces)

    # Legende ausblenden, wenn nur eine Linie angezeigt wird
    fig = fig.update_layout({"showlegend": number_of_visible_traces > 1})

    if st.session_state.get("cb_multi_year"):
        fig = legend_groups_for_multi_year(fig)

    return fig


@func_timer
def show_traces(fig: go.Figure) -> go.Figure:
    """Set the visibility of the traces in the figure.

    Args:
        - fig (go.Figure): Figure to edit
    """

    layout: dict[str, Any] = fgf.fig_layout_as_dic(fig)
    fig_type: str = "lastgang"
    for key, value in cont.FIG_TITLES.items():
        if value in layout["meta"]["title"]:
            fig_type = key

    if fig_type == "lastgang":
        fig = smooth(fig)
        layout: dict[str, Any] = fgf.fig_layout_as_dic(fig)

    data: dict[str, dict[str, Any]] = fgf.fig_data_as_dic(fig)

    switch: bool = layout["meta"]["title"] == "fig_days"

    for name, trace_data in data.items():
        if f"cp_{name}" not in st.session_state:
            suff: str = "Arbeit" if fig_type in ["mon"] else "Leistung"
            name = f"{name}{cont.ARBEIT_LEISTUNG['suffix'][suff]}"

        trace_visible: bool = False
        if switch:
            trace_visible = st.session_state[f'cb_vis_{trace_data["legendgroup"]}']
        if fig_type in ["mon", "jdl"] and any(
            suff in name for suff in cont.ARBEIT_LEISTUNG["suffix"].values()
        ):
            suffixes: list[str] = list(cont.ARBEIT_LEISTUNG["suffix"].values())
            trace_stripped: str = name
            for suffix in suffixes:
                trace_stripped = trace_stripped.replace(suffix, "")
            combos: list[str] = [f"{trace_stripped}{suffix}" for suffix in suffixes]
            trace_visible = any(
                st.session_state[f"cb_vis_{trace_suff}"] for trace_suff in combos
            )
        else:
            trace_visible = st.session_state[f"cb_vis_{name}"]

        fig = fig.update_traces({"visible": trace_visible}, {"name": name})

    return fig


@func_timer
def format_traces(fig: go.Figure) -> go.Figure:
    """Bearbeiten der Anzeige der Linien
    in Bezug auf die Auswahl im Anzeigen-Menu.
        - Linientyp
        - Linienfarbe
        - Füllfarbe und Transparenz

    Args:
        - fig (go.Figure): Figure in question
    """
    data: dict[str, dict[str, Any]] = fgf.fig_data_as_dic(fig)
    fig_type: str = fgf.fig_type_by_title(fig)
    switch: bool = fig_type == "fig_days"

    visible_traces: list[dict] = [trace for trace in data.values() if trace["visible"]]

    for trace in visible_traces:
        trace_name: str = trace["name"]

        if f"cp_{trace_name}" not in st.session_state:
            suff: str = "Arbeit" if fig_type in {"mon"} else "Leistung"
            trace_name = f"{trace_name}{cont.ARBEIT_LEISTUNG['suffix'][suff]}"

        if not switch:
            line_colour: str = st.session_state[f"cp_{trace_name}"]
            line_transp: str = (
                cont.TRANSPARENCY_OPTIONS[0]
                if cont.SMOOTH_SUFFIX in trace_name
                else st.session_state[
                    f"sb_fill_{trace['legendgroup'] if switch else trace_name}"
                ]
            )
            line_fill: str | None = (
                "tozeroy" if line_transp != cont.TRANSPARENCY_OPTIONS[0] else None
            )
            fill_color: str | None = (
                fgf.fill_colour_with_opacity(line_transp, line_colour)
                if line_fill
                else None
            )
            fig = fig.update_traces(
                {
                    "line_color": line_colour,
                    "line_dash": cont.LINE_TYPES[
                        st.session_state[f"sb_line_dash_{trace_name}"]
                    ],
                    "fill": line_fill,
                    "fillcolor": fill_color,
                },
                {"name": trace["name"]},
            )

    return fig


@func_timer
def show_y_axes(fig: go.Figure) -> go.Figure:
    """Y-Achsen ein- bzw. ausblenden.
    ...je nachdem, ob Linien in der Grafik angezeigt werden,
    die sich auf die Achse beziehen.


    Args:
        - fig (go.Figure): Figure in question
    """
    data: dict[str, dict[str, Any]] = fgf.fig_data_as_dic(fig)
    layout: dict[str, Any] = fgf.fig_layout_as_dic(fig)

    fig_type: str = fgf.fig_type_by_title(fig, layout=layout)

    fig = fig.update_yaxes({"visible": False})  # turn off all y-axes

    # show axis if a line is visible, that uses this axis
    axes_to_show: list[str] = [
        f'yaxis{(val.get("yaxis") or "y").replace("y", "")}'
        for val in data.values()
        if val.get("visible")
    ]
    axes_to_show = sort_list_by_occurance(axes_to_show)
    units_per_axes: dict[str, str] = fgf.get_units_for_all_axes(fig, data=data)

    y_suffix: str = units_per_axes[axes_to_show[0]]
    if fig_type == "mon" and y_suffix == " kW":
        y_suffix = " kWh"
    fig = fig.update_layout(
        {axes_to_show[0]: format_primary_y_axis(y_suffix)}, overwrite=True
    )

    if len(axes_to_show) > 1:
        for axis in axes_to_show[1:]:
            y_suffix = units_per_axes[axis]
            fig = fig.update_layout(
                {
                    axis: format_secondary_y_axis(
                        y_suffix, axes_to_show[0].replace("axis", "")
                    )
                    | {"visible": True}
                },
                overwrite=True,
            )

    return fig


def show_annos(fig: go.Figure, visible_traces: list[str]) -> go.Figure:
    """Annotations (Pfeile) ein-/ausblenden


    Args:
        - fig (go.Figure): Grafik, bei der Anmerkungen angezeigt oder ausgeblendet werden sollen

    Returns:
        - go.Figure: Grafik mit bearbeiteter Anzeigt
    """

    layout: dict[str, Any] = fgf.fig_layout_as_dic(fig)

    for anno in layout["annotations"]:
        an_name: str = anno["name"]
        if "hline" not in an_name:
            # find_year: re.Match[str] | None = re.search(r"\d{4}", an_name)
            # an_name_strip: str = (
            #     an_name.replace(find_year.group(), "") if find_year else an_name
            # )
            an_name_cust: str = an_name
            for suff in cont.ARBEIT_LEISTUNG["suffix"].values():
                if suff in an_name:
                    an_name_cust: str = an_name.split(suff)[0]
            an_name_cust = an_name_cust.split(": ")[0]

            visible: bool = all(
                [
                    st.session_state.get(f"cb_anno_{an_name_cust}"),
                    any(trace in an_name for trace in visible_traces),
                ]
            )

            fig = fig.update_annotations(
                {"visible": visible},
                {"name": an_name},
            )

    return fig


# TODO: docstring
def legend_groups_for_multi_year(fig: go.Figure) -> go.Figure:
    """change"""

    data: dict[str, dict[str, Any]] = fgf.fig_data_as_dic(fig)
    legend_groups: list[str] = [str(year) for year in st.session_state["years"]]

    number_of_traces_in_groups: dict = {
        group: len(
            [
                trace
                for trace in data.values()
                if str(trace["meta"]["year"]) == group and trace.get("visible")
            ]
        )
        for group in legend_groups
    }

    logger.debug(f"number of traces in groups: {number_of_traces_in_groups}")

    for group, amount in number_of_traces_in_groups.items():
        if amount < 2:
            fig = fig.update_traces({"legendgroup": None}, {"legendgroup": group})
            fig = fig.update_traces(
                {"legendgrouptitle": None}, {"legendgrouptitle": {"text": group}}
            )
        else:
            for trace in data.values():
                if group in str(trace["meta"]["year"]):
                    fig = fig.update_traces(
                        {"legendgroup": group, "legendgrouptitle": {"text": group}},
                        {"name": trace["name"]},
                    )

    return fig


def plotly_config(height: int = 420, title_edit: bool = True) -> dict[str, Any]:
    """Anzeigeeinstellungen für Plotly-Grafiken"""

    return {
        "scrollZoom": True,
        "locale": "de_DE",
        "displaylogo": False,
        "modeBarButtonsToAdd": [
            "lasso2d",
            "select2d",
            "drawline",
            "drawopenpath",
            "drawclosedpath",
            "drawcircle",
            "drawrect",
            "eraseshape",
        ],
        "modeBarButtonsToRemove": [
            "zoomIn",
            "zoomOut",
        ],
        "toImageButtonOptions": {
            "format": "svg",  # one of png, svg, jpeg, webp
            "filename": "grafische Datenauswertung",
            "height": height,
            "width": 640,  # 640 passt auf eine A4-Seite (ist in Word knapp 17 cm breit)
            # 'scale': 1 # Multiply title/legend/axis/canvas sizes by this factor
        },
        "edits": {
            "annotationTail": True,  # Enables changing the length and direction of the arrow.
            "annotationPosition": True,
            "annotationText": True,
            "axisTitleText": False,
            "colorbarPosition": True,
            "colorbarTitleText": True,
            "legendPosition": True,
            "legendText": True,
            "shapePosition": True,
            "titleText": title_edit,
        },
    }
