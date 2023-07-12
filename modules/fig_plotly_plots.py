"""Darstellung der Plots"""

import os
from typing import Literal

import numpy as np
import plotly.graph_objects as go
import polars as pl
import streamlit as st
from geopy import distance, Location
from loguru import logger

from modules import classes_data as cld
from modules import classes_errors as cle
from modules import constants as cont
from modules import general_functions as gf
from modules import meteorolog as meteo
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
        year: int = [year for year in mdf.meta.years if str(year) in line][0]
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

    return fig


@gf.func_timer
def map_dwd_all() -> go.Figure:
    """Karte aller Wetterstationen"""

    hov_temp = "(lat: %{lat:,.2f}° | lon: %{lon:,.2f}°)<br>%{text}<extra></extra>"

    # alle Stationen
    all_sta: pl.DataFrame = meteo.meteo_stations()
    all_lat = list(all_sta["latitude"])
    all_lon = list(all_sta["longitude"])
    all_nam = list(all_sta["name"])

    # alle Stationen
    fig: go.Figure = go.Figure(
        data=go.Scattermapbox(
            lat=all_lat,
            lon=all_lon,
            text=all_nam,
            mode="markers",
            marker={
                "size": 4,
                "color": "blue",
                # "colorscale": "Portland",  # Blackbody,Bluered,Blues,Cividis,Earth,
                #   Electric,Greens,Greys,Hot,Jet,Picnic,Portland,Rainbow,RdBu,Reds,Viridis,YlGnBu,YlOrRd
                # "colorbar": {
                #     "title": "Entfernung<br>DWD-Station<br>Adresse<br> ----- ",
                #     "bgcolor": "rgba(255,255,255,0.5)",
                #     "ticksuffix": " km",
                #     "x": 0,
                # },
                # "opacity": 0.5,
                # "reversescale": True,
                # "cmax": 400,
                # "cmin": 0,
            },
            hovertemplate=hov_temp,
        )
    )

    # eingegebene Adresse
    loc: Location | None = sf.s_get("geo_location")
    if isinstance(loc, Location):
        address: str = loc.address
        fig = fig.add_trace(
            go.Scattermapbox(
                lat=loc.latitude,
                lon=loc.longitude,
                text=address.replace("Germany", "").title(),
                hovertemplate="<b>%{text}</b><br>→ eingegebener Standort<extra></extra>",
                mode="markers",
                marker={
                    "size": 12,
                    "color": "limegreen",
                },
            )
        )

    return fig.update_layout(
        title="Wetterstationen des DWD",
        autosize=True,
        showlegend=False,
        font_family="Arial",
        separators=",.",
        margin={"l": 5, "r": 5, "t": 30, "b": 5},
        mapbox={
            "accesstoken": os.getenv("MAPBOX_TOKEN"),
            "zoom": 4.5,
            "center": {
                "lat": 51.5,
                "lon": 9.5,
            },
        },
    )


@gf.func_timer
def map_weatherstations() -> go.Figure:
    """Karte der Wetterstationen (verwendete hervorgehoben)"""

    # alle Stationen ohne Duplikate
    all_sta = meteo.meteo_stations()

    # nächstgelegene Station
    clo_sta = all_sta[all_sta.index == all_sta.index[0]].copy()

    # verwendete Stationen
    used_sta = (
        st.session_state["df_used_stations_show"]
        if "df_used_stations_show" in st.session_state
        else meteo.used_stations_show()
    )

    # verwendete und nächstgelegene Stationen löschen
    for ind in used_sta.index:
        lat = used_sta.loc[ind, "latitude"]
        lon = used_sta.loc[ind, "longitude"]
        met_sta = meteo.same_station_in_meteostat(lat, lon)

        if met_sta is not None:
            ind = all_sta[all_sta["station_id"] == met_sta].index[0]
            all_sta = all_sta.drop(ind, axis="index")
    if clo_sta.index[0] in used_sta.index:
        used_sta = used_sta.drop(clo_sta.index[0], axis="index")

    # delete station if closer than max_dist_wetter
    clo_pos = (
        clo_sta.loc[clo_sta.index[0], "latitude"],
        clo_sta.loc[clo_sta.index[0], "longitude"],
    )
    for ind in used_sta.index:
        sta_pos = (used_sta.loc[ind, "latitude"], used_sta.loc[ind, "longitude"])
        if distance.distance(clo_pos, sta_pos).km < meteo.MIN_DIST_DWD_STAT:
            used_sta = used_sta.drop(ind, axis="index")

    if clo_sta.index[0] in all_sta.index:
        all_sta = all_sta.drop(clo_sta.index[0], axis="index")

    # alle Stationen
    fig = go.Figure(
        data=go.Scattermapbox(
            lat=list(all_sta["latitude"]),
            lon=list(all_sta["longitude"]),
            text=list(all_sta["name"]),
            customdata=list(all_sta["distance"]),
            mode="markers",
            marker={
                "size": list(all_sta["distance"])[::-1],
                "sizeref": float(meteo.WEATHERSTATIONS_MAX_DISTANCE / 7),
                "sizemin": 2,
                "allowoverlap": True,
                "color": list(all_sta["distance"]),
                "colorscale": "Blues",  # Blackbody,Bluered,Blues,Cividis,Earth,
                # Electric,Greens,Greys,Hot,Jet,Picnic,
                # Portland,Rainbow,RdBu,Reds,Viridis,YlGnBu,YlOrRd
                "colorbar": {
                    "title": "Entfernung<br> ----- ",
                    "bgcolor": "rgba(255,255,255,0.5)",
                    "ticksuffix": " km",
                    "x": 0,
                },
                "opacity": 0.5,
                "reversescale": True,
                "cmax": meteo.WEATHERSTATIONS_MAX_DISTANCE,
                "cmin": 0,
            },
            hovertemplate=(
                "<b>%{text}</b> <i>(Entfernung: "
                "%{customdata:,.1f} km)</i><extra></extra>"
            ),
        )
    )

    # eingegebene Adresse
    fig.add_trace(
        go.Scattermapbox(
            lat=[st.session_state["dic_geo"]["lat"]],
            lon=[st.session_state["dic_geo"]["lon"]],
            text=[st.session_state["ti_adr"].title()],
            hovertemplate="<b>%{text}</b><br>→ eingegebener Standort<extra></extra>",
            mode="markers",
            marker={
                "size": 12,
                "color": "limegreen",
            },
        )
    )

    # closest station
    fig.add_trace(
        go.Scattermapbox(
            lat=[clo_sta.loc[clo_sta.index[0], "latitude"]],
            lon=[clo_sta.loc[clo_sta.index[0], "longitude"]],
            customdata=[clo_sta.loc[clo_sta.index[0], "distance"]],
            text=[f"{clo_sta.loc[clo_sta.index[0], 'name']}"],
            hovertemplate=(
                "<b>%{text}</b> <i>(Entfernung: %{customdata:,.1f} km)"
                "</i><br>→ nächstgelgene Wetterstation<extra></extra>"
            ),
            mode="markers",
            marker={
                "size": 12,
                "color": "crimson",
            },
        )
    )

    # Wetterstationen für Zusatzparameter
    if used_sta.shape[0] > 0:
        for ind in used_sta.index:
            fig.add_trace(
                go.Scattermapbox(
                    lat=[used_sta.loc[ind, "latitude"]],
                    lon=[used_sta.loc[ind, "longitude"]],
                    customdata=[
                        (
                            f'<i>(Entfernung: {used_sta.loc[ind, "distance"]:,.1f} km)'
                            f"</i><br>→ nächstgelgene Wetterstation für Parameter<br>"
                            f'{", ".join(used_sta.loc[ind, "params"])}'
                        )
                    ],
                    text=[used_sta.loc[ind, "name"]],
                    hovertemplate="<b>%{text}</b> %{customdata}<extra></extra>",
                    mode="markers",
                    marker={
                        "size": 12,
                        "color": "gold",
                    },
                )
            )

    fig = fig.update_layout(
        # title=f"Wetterstationen im Radius von {meteo.weatherstations_max_distance} km um den Standort",
        autosize=False,
        height=800,
        showlegend=False,
        font_family="Arial",
        separators=",.",
        margin={"l": 5, "r": 5, "t": 30, "b": 5},
        mapbox={
            "accesstoken": os.getenv("MAPBOX_TOKEN"),
            "zoom": 6,
            "center": {
                "lat": st.session_state["dic_geo"]["lat"],
                "lon": st.session_state["dic_geo"]["lon"],
            },
        },
    )
    st.session_state["meteo_fig"] = fig
    return fig


# @st.experimental_memo(suppress_st_warning=True, show_spinner=False)
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
