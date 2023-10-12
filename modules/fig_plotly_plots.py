"""Darstellung der Plots"""

import os
from typing import Literal

import numpy as np
import plotly.graph_objects as go
import polars as pl
from loguru import logger

from modules import classes_data as cld
from modules import classes_errors as cle
from modules import constants as cont
from modules import general_functions as gf
from modules import meteorolog as met
from modules import streamlit_functions as sf


@gf.func_timer
def line_plot(
    mdf: cld.MetaAndDfs,
    data_frame: Literal["df", "df_h", "jdl", "mon"] = "df",
    **kwargs,
) -> go.Figure:
    """Liniengrafik für Daten eines einzelnen Jahres

    Args:
        - mdf (cl.MetaAndDfs): Data Frames und Metadaten
        - data_frame (Literal["df", "df_h", "jdl", "mon"], optional):
            Zu verwendender Data Frame. Defaults to "df".

    Returns:
        - go.Figure: Liniengrafik eines einzelnen Jahres
    """
    logger.info(f"Creating line plot from DataFrame 'mdf.{data_frame}'")

    df: pl.DataFrame = getattr(mdf, data_frame)
    lines: list[str] = kwargs.get("lines") or [
        col for col in df.columns if gf.check_if_not_exclude(col)
    ]
    title: str = kwargs.get("title") or ""

    fig: go.Figure = go.Figure()
    fig = fig.update_layout(
        {
            "meta": {
                "title": title,
                "var_name": kwargs.get("var_name"),
                "metadata": mdf.meta.as_dic(),
            }
        }
    )

    logger.debug(gf.string_new_line_per_item(lines, "lines in lines:"))

    for line in [lin for lin in lines if gf.check_if_not_exclude(lin)]:
        line_data: pl.Series = df.get_column(line)
        line_meta: cld.MetaLine = mdf.meta.lines[line]
        manip: int = -1 if any(neg in line for neg in cont.NEGATIVE_VALUES) else 1

        logger.info(f"Adding line '{line_meta.tit}' to Figure '{title.split('<')[0]}'.")
        logger.debug(f"original index column in line_meta: '{line_meta.name_orgidx}'")

        if line_meta.name_orgidx in df.columns:
            cusd: pl.Series = df.get_column(line_meta.name_orgidx)
            logger.debug("original index column found in df")
        else:
            cusd: pl.Series = df.get_column(cont.SPECIAL_COLS.original_index)
            logger.debug("original index column NOT found in df")

        trace_unit: str | None = (
            line_meta.unit if data_frame == "df" else line_meta.unit_h
        )

        fig = fig.add_trace(
            go.Scatter(
                x=df.get_column(cont.SPECIAL_COLS.index),
                y=line_data * manip,
                customdata=cusd,
                name=line_meta.tit,
                hovertemplate=hover_template(title, trace_unit, line_data),
                mode="lines",
                visible=True,
                # yaxis=line_meta.y_axis_h if df_h else line_meta.y_axis,
                meta={"unit": trace_unit, "negativ": manip < 0, "df_col": line},
            )
        )

    logger.info(
        f"Figure '{title.split('<')[0]}' has the following lines:\n"
        f"{gf.string_new_line_per_item([entry['name'] for entry in fig.data])}"
    )
    return fig


def hover_template(
    fig_title: str, trace_unit: str | None, line_data: pl.Series
) -> np.ndarray:
    """Generate the hover template for the given trace"""

    cusd_format: str = (
        "(%{customdata|%a %d. %b %Y %H:%M})"
        if "Monatswerte" not in fig_title
        else "(%{customdata|%b %Y})"
    )

    hovtemp: str = f"{trace_unit} {cusd_format}"

    return np.select(
        [np.abs(line_data) < 10, np.abs(line_data) < 100],  # noqa: PLR2004
        [
            "%{y:,.2f}" + hovtemp,
            "%{y:,.1f}" + hovtemp,
        ],
        "%{y:,.0f}" + hovtemp,
    )


# Lastgang mehrerer Jahre übereinander darstellen
@gf.func_timer
def line_plot_y_overlay(
    mdf: cld.MetaAndDfs,
    data_frame: Literal["df_multi", "df_h_multi", "mon_multi"] = "df_multi",
    **kwargs,
) -> go.Figure:
    """Liniengrafik mit mehreren Jahren übereinander
    (Jahreszahlen werden ausgetauscht)

    Args:
        - mdf (cl.MetaAndDfs): Data Frames und Metadaten
        - data_frame (Literal["df_multi", "df_h_multi", "mon_multi"], optional):
            Zu verwendender Data Frame. Defaults to "df_multi".

    Returns:
        - go.Figure: Liniengrafik mit mehreren Jahren übereinander
    """
    if mdf.meta.years is None:
        raise cle.NotFoundError(entry="list of years", where="mdf.meta.years")

    logger.debug(f"Creating line plot from DataFrame '{data_frame}'")

    dic_df: dict[int, pl.DataFrame] = getattr(mdf, data_frame)
    lines: list[str] = kwargs.get("lines") or mdf.get_lines_in_multi_df(data_frame)

    cusd_format: str = (
        "(%{customdata|%a %d. %b %Y %H:%M})"
        if "Monatswerte" not in (kwargs.get("title") or "")
        else "(%{customdata|%b %Y})"
    )

    fig: go.Figure = go.Figure()
    fig = fig.update_layout(
        {
            "meta": {
                "title": (kwargs.get("title") or ""),
                "var_name": kwargs.get("var_name"),
                "multi_y": True,
                "metadata": mdf.meta.as_dic(),
            }
        }
    )
    logger.debug("The following lines will be added to the graph:")
    for line in lines:
        logger.debug(gf.string_new_line_per_item(mdf.meta.lines[line].as_dic()))

    for line in lines:
        year: int = next(year for year in mdf.meta.years if str(year) in line)
        line_data: pl.Series = dic_df[year].get_column(line)
        line_meta: cld.MetaLine = mdf.meta.lines[line]
        manip: int = -1 if any(neg in line for neg in cont.NEGATIVE_VALUES) else 1
        trace_unit: str | None = (
            line_meta.unit if data_frame == "df_multi" else line_meta.unit_h
        )
        hovtemp: str = f"{trace_unit} {cusd_format}"

        cusd: pl.Series = (
            dic_df[year].get_column(line_meta.name_orgidx)
            if line_meta.name_orgidx in list(dic_df[year].columns)
            else dic_df[year].get_column(cont.SPECIAL_COLS.original_index)
        )
        fig = fig.add_trace(
            go.Scatter(
                x=dic_df[year].get_column(cont.SPECIAL_COLS.index),
                y=line_data * manip,
                customdata=cusd,
                legendgroup=year,
                legendgrouptitle_text=year,
                name=line_meta.tit,
                mode="lines",
                hovertemplate=(
                    np.select(
                        [abs(line_data) < 10, abs(line_data) < 100],
                        ["%{y:,.2f}" + hovtemp, "%{y:,.1f}" + hovtemp],
                        "%{y:,.0f}" + hovtemp,
                    )
                ),
                visible=True,
                # yaxis=line_meta.y_axis_h if df_h else line_meta.y_axis,
                meta={
                    "unit": trace_unit,
                    "negativ": manip < 0,
                    "df_col": line,
                    "year": year,
                },
            )
        )

    return fig


@gf.func_timer
def line_plot_day_overlay(
    dic_days: dict, meta: dict, title: str = "", var_name: str = ""
) -> go.Figure:
    """Liniengrafik für Tagesvergleich
    Jeder Tag bekommt eine Linie. Die Linien werden übereinander gelegt.


    Args:
        - dic_days (dict): dictionary mit Daten der Tage
        - meta (dict): dictionary mit Metadaten
        - title (str, optional): Titel der Grafik. Defaults to "".
        - var_name (str, optional): Variablenname für Metadaten. Defaults to "".

    Returns:
        - go.Figure: _description_
    """

    fig: go.Figure = go.Figure()
    fig = fig.update_layout(
        {
            "meta": {
                "title": title,
                "var_name": var_name,
                "metadata": meta,
            }
        }
    )
    cusd_format: str = "(%{customdata|%a %e. %b %Y %H:%M})"

    lis_units: list[str] = []
    for date in dic_days:
        for line in [lin for lin in dic_days[date].columns if "orgidx" not in lin]:
            lis_units.append(meta[line].get("unit"))
            manip: int = -1 if any(neg in line for neg in cont.NEGATIVE_VALUES) else 1
            cusd: pl.Series = (
                dic_days[f"{line}_orgidx"]
                if f"{line}_orgidx" in dic_days[date].columns
                else dic_days[date]["orgidx"]
            )

            trace_unit: str | None = meta[line].get("unit")
            hovtemp: str = f"{trace_unit} {cusd_format} <extra>{line}</extra>"

            fig = fig.add_trace(
                go.Scatter(
                    x=dic_days[date].index,
                    y=dic_days[date][line] * manip,
                    customdata=cusd,
                    name=date,
                    mode="lines",
                    hovertemplate=(
                        np.select(
                            [
                                abs(dic_days[date][line]) < 10,
                                abs(dic_days[date][line]) < 100,
                            ],
                            [
                                "%{y:,.2f}" + hovtemp,
                                "%{y:,.1f}" + hovtemp,
                            ],
                            "%{y:,.0f}" + hovtemp,
                        )
                    ),
                    legendgroup=line,
                    legendgrouptitle_text=line,
                    visible=True,
                    yaxis=meta[line]["y_axis"],
                    meta={"unit": trace_unit, "negativ": manip < 0, "df_col": line},
                )
            )
    ♾️🪄🧮
    return fig


@gf.func_timer
def map_dwd_all(**kwargs) -> go.Figure:
    """Karte aller Wetterstationen"""

    # hov_temp = "%{text}<br>(lat: %{lat:,.2f}° | lon: %{lon:,.2f}°)<extra></extra>"
    hov_temp: str = (
        "%{text}<br><i>(Distanz: %{marker.color:,.1f} km)</i><extra></extra>"
    )

    # alle Stationen
    all_sta: pl.DataFrame | None = sf.s_get("stations_distance")
    if all_sta is None:
        met.collect_meteo_data_for_list_of_parameters(cont.DWD_DEFAULT_PARAMS)
        all_sta = sf.s_get("stations_distance")

    if all_sta is None:
        raise ValueError

    all_lat = list(all_sta["latitude"])
    all_lon = list(all_sta["longitude"])
    all_nam = list(all_sta["name"])
    all_dis = list(all_sta["distance"])

    # alle Stationen
    fig: go.Figure = go.Figure(
        data=go.Scattermapbox(
            lat=all_lat,
            lon=all_lon,
            text=all_nam,
            mode="markers",
            marker={
                "size": 7,
                "color": all_dis,
                "colorscale": "Reds",  # Blackbody,Bluered,Blues,Cividis,Earth,
                #   Electric,Greens,Greys,Hot,Jet,Picnic,Portland,
                #   Rainbow,RdBu,Reds,Viridis,YlGnBu,YlOrRd
                # "colorbar": {
                #     "title": "Entfernung<br>DWD-Station<br>Adresse<br> ----- ",
                #     "bgcolor": "rgba(255,255,255,0.5)",
                #     "ticksuffix": " km",
                #     "x": 0,
                # },
                # "opacity": 0.5,
                "reversescale": True,
                # "cmax": 400,
                # "cmin": 0,
            },
            hovertemplate=hov_temp,
        )
    )

    # eingegebene Adresse
    loc = sf.s_get("geo_location")
    if not isinstance(loc, cld.Location):
        raise cle.NotFoundError(entry="location", where="Session State")

    address: str = f"{loc.street}, {loc.city}"
    hov_temp: str = (
        f"{address}<br><i>(Standort aus gegebener Addresse)</i><extra></extra>"
    )
    fig = fig.add_trace(
        go.Scattermapbox(
            lat=[loc.latitude],
            lon=[loc.longitude],
            text=address,
            hovertemplate=hov_temp,
            mode="markers",
            marker={
                "size": 15,
                "color": "limegreen",
            },
        )
    )

    return fig.update_layout(
        # title="Wetterstationen des DWD",
        height=kwargs.get("height") or 500,
        autosize=True,
        showlegend=False,
        font_family="Arial",
        separators=",.",
        margin={"l": 5, "r": 5, "t": 30, "b": 5},
        mapbox={
            "accesstoken": os.getenv("MAPBOX_TOKEN"),
            "zoom": 6,
            "center": {
                "lat": loc.latitude,
                "lon": loc.longitude,
            },
        },
    )


def timings(dic: dict) -> go.Figure:
    """Grafik mit Ausführungszeiten für debug"""
    fig_tim = go.Figure(
        [
            go.Bar(
                x=list(dic.keys()),
                y=list(dic.values()),
            )
        ]
    )

    fig_tim.update_layout(
        {
            "title": {
                "text": "execution times of the latest run",
            },
            "yaxis": {
                "ticksuffix": " s",
            },
        }
    )

    return fig_tim
