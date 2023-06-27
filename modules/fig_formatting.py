"""Formatting and configuration of plots

- add range slider
- formatting of axes, layout and traces
- plotly configuration
"""

import re
from datetime import datetime
from typing import Any

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from loguru import logger

from modules import constants as cont
from modules import fig_annotations as fa
from modules import fig_general_functions as fgf
from modules import general_functions as gf
from modules import streamlit_functions as sf

FORMAT_PRIMARY_Y: dict[str, Any] = {
    "tickformat": ",d",
    "side": "left",
    "anchor": "x",
    "separatethousands": True,
    "fixedrange": False,
    "visible": True,
}

FORMAT_SECONDARY_Y: dict[str, Any] = {
    "tickformat": ",d",
    "side": "right",
    "anchor": "free",
    "separatethousands": True,
    "fixedrange": False,
    "visible": False,
    "tickmode": "sync",
    "overlaying": "y",
    "autoshift": True,
    "shift": 10,
}


@gf.func_timer
def format_tickstops(fig: go.Figure) -> list[dict[str, Any]]:
    """Tickformat stops for axes

    Args:
        fig (go.Figure): figure to update

    Returns:
        list[dict[str, Any]]: formating parameters
    """

    multi_y: bool | None = fig.layout.meta.get("multi_y")  # type: ignore

    return [
        {
            "dtickrange": [None, cont.TIME_MS.half_day],
            "value": "%H:%M\n%e. %b" if multi_y else "%H:%M\n%a %e. %b",
        },
        {
            "dtickrange": [
                cont.TIME_MS.half_day + 1,
                cont.TIME_MS.week,
            ],
            "value": "%e. %b" if multi_y else "%a\n%e. %b",
        },
        {
            "dtickrange": [
                cont.TIME_MS.week + 1,
                cont.TIME_MS.month,
            ],
            "value": "%e.\n%b",
        },
        {
            "dtickrange": [cont.TIME_MS.month + 1, None],
            "value": "%b",
        },
    ]


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


@gf.func_timer
def standard_axes_and_layout(
    fig: go.Figure,
    x_tickformat: str = "%b",
) -> go.Figure:
    """Grundeinstellungen der Grafik


    Args:
        - fig (go.Figure): Grafik, die angepasst werden soll
        - x_tickformat (str, optional): Format der Daten auf der X-Achse.
            Standard: "%b" (Monat).

    Returns:
        - go.Figure: Bearbeitete Grafik
    """

    data: dict[str, dict[str, Any]] = fgf.fig_data_as_dic(fig)
    layout: dict[str, Any] = fgf.fig_layout_as_dic(fig)
    title: str = layout["title"]["text"]

    fig = standard_xaxis(fig, data, title, x_tickformat)
    fig = fig.update_yaxes(FORMAT_PRIMARY_Y)

    fig = standard_layout(fig, data)

    return fig


@gf.func_timer
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
    if isinstance(x_max, datetime | np.datetime64):
        x_max = gf.end_of_month(x_max)

    x_min: Any = min(min(p["x"]) for p in data.values())
    if isinstance(x_min, datetime | np.datetime64):
        x_min = gf.start_of_month(x_min)

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
        fixedrange=cont.FIG_TITLES.mon in title,
    )


@gf.func_timer
def standard_layout(fig: go.Figure, data: dict[str, dict[str, Any]]) -> go.Figure:
    """Standardlayout"""

    visible_traces: list[str] = [
        trace
        for trace, value in data.items()
        if value["visible"] and gf.check_if_not_exclude(trace)
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
            "y": 1.02 if lastgang else 0.98,
            "xanchor": "left" if lastgang else "right",
            "x": 1.02 if lastgang else 0.99,
        },
        showlegend=len(visible_traces) > 1,
        margin={"l": 5, "r": 5, "t": 40, "b": 10},
        hovermode="x",
    )


@gf.func_timer
def update_main(fig: go.Figure) -> go.Figure:
    """Darstellungseinstellungen aus dem Hauptfenster"""

    fig = show_traces(fig)
    data: dict[str, dict[str, Any]] = fgf.fig_data_as_dic(fig)

    visible_traces: list[dict] = [trace for trace in data.values() if trace["visible"]]
    visible_units: list[str] = gf.sort_list_by_occurance(
        [trace["meta"]["unit"] for trace in visible_traces]
    )

    debug_traces_units(fig, data, visible_traces, visible_units)

    fig = format_traces(fig, visible_traces, visible_units)
    fig = show_y_axes(fig, visible_units)
    fig = show_annos(fig, visible_traces)

    # Legende ausblenden, wenn nur eine Linie angezeigt wird
    fig = fig.update_layout({"showlegend": len(visible_traces) > 1})

    if sf.st_get("cb_multi_year"):
        fig = legend_groups_for_multi_year(fig)

    return fig


def debug_traces_units(
    fig: go.Figure,
    data: dict[str, dict[str, Any]],
    visible_traces: list[dict],
    visible_units: list[str],
) -> None:
    """Log available traces in figure, as well as visible traces and units"""

    layout: dict[str, Any] = fgf.fig_layout_as_dic(fig)
    fig_title: str = layout["title"]["text"].split("<")[0]

    total_traces: list[dict] = list(data.values())
    logger.debug(
        f"Traces in figure '{fig_title}': \n"
        f"Available: {[trace['name'] for trace in total_traces]}  \n"
        f"Visible:   {[trace['name'] for trace in visible_traces]}"
    )
    logger.debug(f"Visible units in figure '{fig_title}': {visible_units}")


@gf.func_timer
def show_traces(fig: go.Figure) -> go.Figure:
    """Set the visibility of the traces in the figure.

    Args:
        - fig (go.Figure): Figure to edit
    """

    layout: dict[str, Any] = fgf.fig_layout_as_dic(fig)
    fig_type: str = "lastgang"
    for key, value in cont.FIG_TITLES.as_dic().items():
        if value in layout["meta"]["title"]:
            fig_type = key

    if fig_type == "lastgang":
        fig = fa.smooth(fig)
        layout: dict[str, Any] = fgf.fig_layout_as_dic(fig)

    data: dict[str, dict[str, Any]] = fgf.fig_data_as_dic(fig)

    for name, trace_data in data.items():
        if f"cp_{name}" not in st.session_state:
            new_name: str = (
                f"{name}{cont.SUFFIXES.col_arbeit}"
                if fig_type in ["mon"]
                else f"{name}{cont.SUFFIXES.col_leistung}"
            )
        else:
            new_name = name

        trace_visible: bool = False

        if fig_type in ["days"]:
            trace_visible = st.session_state[f'cb_vis_{trace_data["legendgroup"]}']
        if fig_type in ["mon", "jdl"]:
            trace_visible = trace_vis_jdl_mon(new_name)
        else:
            trace_visible = st.session_state[f"cb_vis_{new_name}"]

        fig = fig.update_traces({"visible": trace_visible}, {"name": new_name})
        if name != new_name:
            fig = fig.update_traces({"visible": trace_visible}, {"name": name})

    return fig


def trace_vis_jdl_mon(trace_name: str) -> bool:
    """Trace visibility for additional graphs Jahresdauerlinie und Monatswerte"""

    suffixes: list[str] = cont.ARBEIT_LEISTUNG.all_suffixes
    trace_stripped: str = trace_name
    for suffix in suffixes:
        trace_stripped = trace_stripped.replace(suffix, "")
    combos: list[str] = [trace_stripped] + [
        f"{trace_stripped}{suffix}" for suffix in suffixes
    ]

    return any(sf.st_get(f"cb_vis_{trace}") for trace in combos)


@gf.func_timer
def format_traces(
    fig: go.Figure, visible_traces: list[dict], visible_units: list[str]
) -> go.Figure:
    """Bearbeiten der Anzeige der Linien
    in Bezug auf die Auswahl im Anzeigen-Menu.
        - Linientyp
        - Linienfarbe
        - Füllfarbe und Transparenz

    Args:
        - fig (go.Figure): Figure in question
    """
    fig_type: str = fgf.fig_type_by_title(fig)
    switch: bool = fig_type == "fig_days"

    for trace in visible_traces:
        trace_name: str = trace["name"]
        index_unit: int = visible_units.index(trace["meta"]["unit"])
        trace_y: str = "y" if index_unit == 0 else f"y{index_unit + 1}"
        line_mode: str = "lines"
        if sf.st_get(f"cb_markers_{trace_name}") or fig_type == "mon":
            line_mode = "markers+lines"
        if sf.st_get(f"sb_line_dash_{trace_name}") == "keine":
            line_mode = "markers"

        if sf.st_not_in(f"cp_{trace_name}"):
            suff: str = "Arbeit" if fig_type in {"mon"} else "Leistung"
            trace_name = f"{trace_name}{cont.ARBEIT_LEISTUNG.get_suffix(suff)}"

        if sf.st_not_in(f"cp_{trace_name}"):
            trace_name = re.split(r"\b\d{4}\b", trace_name)[0]

        if not switch:
            line_colour: str = st.session_state[f"cp_{trace_name}"]
            line_transp: str = (
                cont.TRANSPARENCY_OPTIONS[0]
                if cont.SUFFIXES.col_smooth in trace_name
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
            line_dash: str = (
                cont.LINE_TYPES["gestrichelt lang"]
                if fig_type == "mon"
                else cont.LINE_TYPES[st.session_state[f"sb_line_dash_{trace_name}"]]
            )

            fig = fig.update_traces(
                {
                    "yaxis": trace_y,
                    "line_color": line_colour,
                    "line_dash": line_dash,
                    "mode": line_mode,
                    "marker_size": (
                        15
                        if fig_type == "mon"
                        else sf.st_get(f"ni_markers_{trace_name}")
                    ),
                    "fill": line_fill,
                    "fillcolor": fill_color,
                },
                {"name": trace["name"]},
            )

    return fig


@gf.func_timer
def show_y_axes(fig: go.Figure, visible_units: list[str]) -> go.Figure:
    """Y-Achsen ein- bzw. ausblenden.
    ...je nachdem, ob Linien in der Grafik angezeigt werden,
    die sich auf die Achse beziehen.


    Args:
        - fig (go.Figure): Figure in question
    """

    layout: dict[str, Any] = fgf.fig_layout_as_dic(fig)
    fig_type: str = fgf.fig_type_by_title(fig, layout=layout)

    fig = fig.update_yaxes({"visible": False})  # turn off all y-axes

    # show axis if a line is visible, that uses this axis
    # axes_to_show = ["yaxis", "yaxis2", etc.]
    axes_to_show: list[str] = ["yaxis"]
    if len(visible_units) > 1:
        axes_to_show += [
            f"yaxis{count+1}"
            for count in [visible_units.index(unit) for unit in visible_units][1:]
        ]

    logger.debug(
        f"Visible y-axes in figure "
        f"'{layout['title']['text'].split('<')[0]}': {axes_to_show}"
    )

    for count, axis in enumerate(axes_to_show):
        y_suffix: str = visible_units[count]
        if axis == "yaxis":
            if fig_type == "mon" and y_suffix == " kW":
                y_suffix = " kWh"
            fig = fig.update_layout(
                {"yaxis": {"ticksuffix": y_suffix, "visible": True}}
            )
        else:
            fig = fig.update_layout(
                {axis: FORMAT_SECONDARY_Y | {"visible": True, "ticksuffix": y_suffix}},
            )

    return fig


def show_annos(fig: go.Figure, visible_traces: list[dict]) -> go.Figure:
    """Annotations (Pfeile) ein-/ausblenden


    Args:
        - fig (go.Figure): Grafik, zum Anzeigen oder Ausblenden von Anmerkungen

    Returns:
        - go.Figure: Grafik mit bearbeiteter Anzeigt
    """
    visible_lines: list[str] = [trace["name"] for trace in visible_traces]
    layout: dict[str, Any] = fgf.fig_layout_as_dic(fig)
    fig_type: str = fgf.fig_type_by_title(fig)

    logger.debug(
        gf.string_new_line_per_item(
            [anno["name"] for anno in layout["annotations"]],
            f"Figure '{fig_type}': available annotations:",
        )
    )

    for anno in layout["annotations"]:
        an_name: str = anno["name"]
        if "hline" not in an_name:
            an_name_cust: str = an_name.split(": ")[0]
            visible: bool = all(
                [
                    sf.st_get(f"cb_anno_{an_name_cust}"),
                    any(line in an_name for line in visible_lines),
                ]
            )

            if all(
                [
                    fig_type == "jdl",
                    not visible,
                    cont.SUFFIXES.col_leistung not in an_name_cust,
                    sf.st_get(f"cb_anno_{an_name_cust}{cont.SUFFIXES.col_leistung}"),
                ]
            ):
                visible = True

            fig = fig.update_annotations(
                {"visible": visible},
                {"name": an_name},
            )

    return fig


def legend_groups_for_multi_year(fig: go.Figure) -> go.Figure:
    """Calculates legend groups for multi year plots."""

    data: dict[str, dict[str, Any]] = fgf.fig_data_as_dic(fig)
    layout: dict[str, Any] = fgf.fig_layout_as_dic(fig)
    legend_groups: list[str] = [
        str(year) for year in layout["meta"]["metadata"]["years"]
    ]
    for trace in data.values():
        if not trace.get("meta"):
            logger.critical(f"trace '{trace['name']}' has no meta data")
            raise ValueError

    number_of_traces_in_groups: dict = {
        group: len(
            [
                trace
                for trace in data.values()
                if (
                    str(trace["meta"].get("year")) == group
                    or group in trace.get("name")
                )
                and trace.get("visible")
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
                if group in str(trace["meta"].get("year")) or group in trace.get(
                    "name"
                ):
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
            "annotationTail": True,  # Enables changing length and direction of arrows.
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
