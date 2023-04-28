"""
Darstellung der Plots
"""

import os
from typing import Dict, List

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from geopy import distance

from modules import constants as cont
from modules import meteorolog as meteo
from modules.general_functions import func_timer, sort_list_by_occurance


@func_timer
def line_plot(df: pd.DataFrame, meta: Dict, **kwargs) -> go.Figure:
    """Liniengrafik für Daten eines einzelnen Jahres

    Args:
        - df (pd.DataFrame): Daten
        - meta (Dict): Metadaten

    Returns:
        - go.Figure: Linengrafik
    """
    cols: List[str] = [str(col) for col in df.columns]
    lines: List[str] = kwargs.get("lines") or [
        col for col in cols if "orgidx" not in col
    ]
    title: str = kwargs.get("title") or ""
    cusd_format: str = (
        "(%{customdata|%a %d. %b %Y %H:%M})"
        if "Monatswerte" not in title
        else "(%{customdata|%b %Y})"
    )
    all_units: List[str] = [
        meta[line].get("unit")
        for line in lines
        if all(ex not in line for ex in cont.EXCLUDE)
    ]

    fig: go.Figure = go.Figure()
    fig = fig.update_layout(
        {
            "meta": {
                "title": title,
                "var_name": kwargs.get("var_name"),
                "units": sort_list_by_occurance(all_units),
                "metadata": meta,
            }
        }
    )

    for line in [lin for lin in lines if "orgidx" not in lin]:
        manip: int = -1 if any(neg in line for neg in cont.NEGATIVE_VALUES) else 1
        cusd: pd.Series = (
            df[f"{line}_orgidx"] if f"{line}_orgidx" in df.columns else df["orgidx"]
        )
        trace_unit: str | None = meta[line].get("unit")
        hovtemp: str = f"{trace_unit} {cusd_format}"
        fig = fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df[line] * manip,
                customdata=cusd,
                name=meta[line].get("tit"),
                hovertemplate=(
                    np.select(
                        [abs(df[line]) < 10, abs(df[line]) < 100],
                        [
                            "%{y:,.2f}" + hovtemp,
                            "%{y:,.1f}" + hovtemp,
                        ],
                        "%{y:,.0f}" + hovtemp,
                    )
                ),
                mode="lines",
                visible=True,
                yaxis=meta[line]["y_axis"],
                meta={"unit": trace_unit, "negativ": manip < 0, "df_col": line},
            )
        )

    return fig


# Lastgang mehrerer Jahre übereinander darstellen
@func_timer
def line_plot_y_overlay(
    dic_df: Dict,
    meta: Dict,
    years: List,
    lines: List | None = None,
    title: str = "",
    var_name: str = "",
) -> go.Figure:
    """Liniengrafik mit mehreren Jahren übereinander
    (Jahreszahlen werden ausgetauscht)


    Args:
        - dic_df (Dict): Dictionary mit df für jedes Jahr
        - meta (Dict): Dictionary mit Metadaten für jedes Jahr
        - years (List): Liste der Jahre
        - lines (List | None, optional): Liste der Linien - wenn None, werden alle Linien der df verwendet. Defaults to None.
        - title (str, optional): Titel der Grafik. Defaults to "".
        - var_name (str, optional): Variablenname für Metadaten. Defaults to "".

    Returns:
        - go.Figure: Liniengrafik mit mehreren Jahren übereinander
    """

    if lines is None:
        lines = [
            str(col)
            for list in [dic_df[year].columns.to_list() for year in years]
            for col in list
            if all(ex not in col for ex in cont.EXCLUDE)
        ]
    all_units: List[str] = [
        meta[line].get("unit")
        for line in lines
        if all(excl not in line for excl in cont.EXCLUDE)
    ]

    cusd_format: str = (
        "(%{customdata|%a %d. %b %Y %H:%M})"
        if "Monatswerte" not in title
        else "(%{customdata|%b %Y})"
    )

    fig: go.Figure = go.Figure()
    fig = fig.update_layout(
        {
            "meta": {
                "title": title,
                "var_name": var_name,
                "multi_y": True,
                "units": sort_list_by_occurance(all_units),
                "metadata": meta,
            }
        }
    )

    for line in lines:
        manip: int = -1 if any(neg in line for neg in cont.NEGATIVE_VALUES) else 1
        trace_unit: str | None = meta[line].get("unit")
        hovtemp: str = f"{trace_unit} {cusd_format}"
        year: int = [year for year in years if str(year) in line][0]

        cusd: pd.Series = (
            dic_df[year][f"{line}_orgidx"]
            if f"{line}_orgidx" in list(dic_df[year].columns)
            else dic_df[year]["orgidx"]
        )
        fig = fig.add_trace(
            go.Scatter(
                x=dic_df[year].index,
                y=dic_df[year][line] * manip,
                customdata=cusd,
                legendgroup=year,
                legendgrouptitle_text=year,
                name=meta[line].get("tit"),
                mode="lines",
                hovertemplate=(
                    np.select(
                        [
                            abs(dic_df[year][line]) < 10,
                            abs(dic_df[year][line]) < 100,
                        ],
                        [
                            "%{y:,.2f}" + hovtemp,
                            "%{y:,.1f}" + hovtemp,
                        ],
                        "%{y:,.0f}" + hovtemp,
                    )
                ),
                visible=True,
                yaxis=meta[line].get("y_axis"),
                meta={
                    "unit": trace_unit,
                    "negativ": manip < 0,
                    "df_col": line,
                    "year": year,
                },
            )
        )

    return fig


@func_timer
def line_plot_day_overlay(
    dic_days: Dict, meta: Dict, title: str = "", var_name: str = ""
) -> go.Figure:
    """Liniengrafik für Tagesvergleich
    Jeder Tag bekommt eine Linie. Die Linien werden übereinander gelegt.


    Args:
        - dic_days (Dict): Dictionary mit Daten der Tage
        - meta (Dict): Dictionary mit Metadaten
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

    lis_units: List[str] = []
    for date in dic_days:
        for line in [lin for lin in dic_days[date].columns if "orgidx" not in lin]:
            lis_units.append(meta[line].get("unit"))
            manip: int = -1 if any(neg in line for neg in cont.NEGATIVE_VALUES) else 1
            cusd: pd.Series = (
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


@func_timer
def map_dwd_all() -> go.Figure:
    """Karte aller Wetterstationen"""

    hov_temp = "(lat: %{lat:,.2f}° | lon: %{lon:,.2f}°)<br>%{text}<extra></extra>"

    # alle Stationen
    all_sta = meteo.dwd_req().all().df
    all_lat = list(all_sta["latitude"])
    all_lon = list(all_sta["longitude"])
    all_nam = list(all_sta["name"])

    # alle Stationen
    fig = go.Figure(
        data=go.Scattermapbox(
            lat=all_lat,
            lon=all_lon,
            text=all_nam,
            mode="markers",
            marker={
                "size": 4,
                "color": "blue",
                # "colorscale": "Portland",  # Blackbody,Bluered,Blues,Cividis,Earth,Electric,Greens,Greys,Hot,Jet,Picnic,Portland,Rainbow,RdBu,Reds,Viridis,YlGnBu,YlOrRd
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

    fig = fig.update_layout(
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

    return fig


@func_timer
def map_weatherstations() -> go.Figure:
    """Karte der Wetterstationen (verwendete hervorgehoben)"""

    # alle Stationen ohne Duplikate
    all_sta = meteo.meteostat_stations()

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
                "colorscale": "Blues",  # Blackbody,Bluered,Blues,Cividis,Earth,Electric,Greens,Greys,Hot,Jet,Picnic,Portland,Rainbow,RdBu,Reds,Viridis,YlGnBu,YlOrRd
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
            hovertemplate="<b>%{text}</b> <i>(Entfernung: %{customdata:,.1f} km)</i><extra></extra>",
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
            hovertemplate="<b>%{text}</b> <i>(Entfernung: %{customdata:,.1f} km)</i><br>→ nächstgelgene Wetterstation<extra></extra>",
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
                        f'<i>(Entfernung: {used_sta.loc[ind, "distance"]:,.1f} km)</i><br>→ nächstgelgene Wetterstation für Parameter<br>{", ".join(used_sta.loc[ind, "params"])}'
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
def timings(dic: Dict) -> go.Figure:
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
