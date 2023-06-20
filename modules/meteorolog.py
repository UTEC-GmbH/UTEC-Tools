"""Meteorologische Daten"""

import os
from datetime import datetime as dt
from typing import Any

import geopy
import pandas as pd
import plotly.graph_objects as go
import polars as pl
import streamlit as st
from geopy.geocoders import Nominatim
from loguru import logger
from wetterdienst import Settings
from wetterdienst.provider.dwd.observation import DwdObservationRequest

from modules import classes_data as cld
from modules import classes_errors as cle
from modules import constants as cont
from modules import general_functions as gf

# Grenze für Daten-Validität
# einen Wetterstation muss für den angegebenen Zeitraum
# mind. diesen Anteil an tatsächlich aufgezeichneten Daten haben
Settings(ts_skip_empty=True, ts_skip_threshold=0.90)


def list_all_parameters() -> list[str]:
    """List of all availabel DWD-parameters

    (including parameters that a specific station might not have data for)
    """

    pars: list[str] = []
    for val in DwdObservationRequest.discover().values():
        pars += list(val.keys())
    pars = list(set(pars))

    logger.info(f"Es stehen {len(pars)} Parameter zur Verfügung")

    return pars


def list_all_resolutions() -> list[str]:
    """List of all available temporal resolutions"""
    return list(DwdObservationRequest.discover().keys())


def start_end_time(**kwargs) -> cld.TimeSpan:
    """Zeitraum für Daten-Download"""

    page: str = str(kwargs.get("page")) or gf.st_get("page")
    mdf: cld.MetaAndDfs | None = kwargs.get("mdf") or gf.st_get("mdf")

    if page == "meteo":
        start_year: int = (
            min(
                gf.st_get("meteo_start_year"),
                gf.st_get("meteo_end_year"),
            )
            if gf.st_in(["meteo_start_year", "meteo_end_year"]) in st.session_state
            else 2020
        )

        end_year: int = (
            min(
                gf.st_get("meteo_start_year"),
                gf.st_get("meteo_end_year"),
            )
            if gf.st_in(["meteo_start_year", "meteo_end_year"]) in st.session_state
            else 2020
        )

        start_time = dt(start_year, 1, 1, 0, 0)  # , tzinfo=ZoneInfo("Europe/Berlin"))
        end_time = dt(end_year, 12, 31, 23, 59)  # , tzinfo=ZoneInfo("Europe/Berlin"))
        if end_time.year == dt.now().year:
            end_time = dt.now()

    elif mdf is not None:
        index: pl.Series = mdf.df.get_column(cont.SPECIAL_COLS.index)
        start_time: dt = index.min()
        end_time: dt = index.max()
    else:
        raise TypeError

    return cld.TimeSpan(start=start_time, end=end_time)


@gf.func_timer
def geo_locate(address: str = "Bremen") -> geopy.Location:
    """Geographische daten (Längengrad, Breitengrad) aus eingegebener Adresse"""

    user_agent_secret: str | None = os.environ.get("GEO_USER_AGENT") or "lasinludwig"
    if user_agent_secret is None:
        raise cle.SecretNotFoundError(entry="GEO_USER_AGENT")

    geolocator: Any = Nominatim(user_agent=user_agent_secret)
    location: geopy.Location = geolocator.geocode(address)

    gf.st_set("geo_location", location)

    return location


@gf.func_timer
def meteo_stations(
    address: str = "Bremen",
    parameter: str = "temperature_air_mean_200",
    resolution: str = "hourly",
) -> pl.DataFrame:
    """Verfügbare Wetterstationen
    in x Kilometer entfernung zur gegebenen Addresse
    mit Daten in gewünschter Auflösung und Zeitperiode

    Args:
        - address (str, optional): Adresse für Entfernung der Stationen.
            Defaults to "Bremen".
        - parameter (str, optional): Parameter, für den die Station Daten haben muss.
            Defaults to "temperature_air_mean_200".
        - resolution (str, optional): Gewünschte zeitliche Auflösung der Daten.
            Defaults to "hourly".

    Returns:
        - pl.DataFrame: DataFrame der Stationen mit folgenden Spalten:
            'station_id',
            'from_date',
            'to_date',
            'height',
            'latitude',
            'longitude',
            'name',
            'state',
            'distance'
    """
    if parameter not in list_all_parameters():
        logger.critical(f"Parameter '{parameter}' is not a valid DWD-Parameter!")
        raise ValueError

    time_span: cld.TimeSpan = start_end_time(page=gf.st_get("page"))
    location: geopy.Location = geo_locate(address)

    stations: pl.DataFrame = (
        DwdObservationRequest(
            parameter=parameter,
            resolution=resolution,
            start_date=time_span.start,
            end_date=time_span.end,
        )
        .filter_by_distance(
            latlon=(location.latitude, location.longitude),
            distance=cont.WEATHERSTATIONS_MAX_DISTANCE,
            unit="km",
        )
        .df
    )

    if stations.height == 0:
        logger.critical(
            "Für die Kombination aus \n"
            f"Parameter '{parameter}',\n"
            f"Auflösung '{resolution}' und \n"
            f"Zeit '{time_span.start}' bis '{time_span.end}' \n"
            "konnten keine Daten gefunden werden."
        )
        raise ValueError

    return stations


def closest_station_per_param(
    resolution: str, address: str, parameters: list[str]
) -> dict[str, list[str]]:
    """Returns a dictionary of the closest station for each parameter.

    key: station id
    value: list of parameters the station has data for
    """
    stations: dict[str, list[str]] = {}
    for parameter in parameters:
        closest_station_id: str = meteo_stations(address, parameter, resolution)[0][
            "station_id"
        ]
        if closest_station_id in stations:
            stations[closest_station_id] += [parameter]
        else:
            stations[closest_station_id] = [parameter]

    return stations


@gf.func_timer
def meteo_data() -> pd.DataFrame:
    """Meteorologische Daten für die ausgewählten Parameter"""

    parameters: list[str] = gf.st_get("ms_meteo_params") or ["temperature_air_mean_200"]
    resolution: str = gf.st_get("sb_meteo_resolution") or "hourly"
    address: str = gf.st_get("ti_address") or "Bremen"

    stations_parameters: dict[str, list[str]] = closest_station_per_param(
        resolution=resolution, address=address, parameters=parameters
    )

    met_data = {}
    for station in set_used_stations:
        station_provider = station.split("_")[0]
        station_id = station.split("_")[1]
        ren = {}

        met_data[station_id] = meteostat_data_by_stationid(station_id)

        for col in met_data[station_id]:
            ren[col] = DIC_METEOSTAT_CODES[col.upper()]["tit"]
        met_data[station_id].rename(columns=ren, inplace=True)

    df = pd.DataFrame()
    for par in lis_sel_params:
        station_id = par.closest_station_id.split("_")[1]
        for col in met_data[station_id]:
            if col in [param.tit_de for param in lis_sel_params]:
                df[col] = met_data[station_id][col]

    df = df[df.index >= start_time.replace(tzinfo=None)]
    df = df[df.index <= end_time.replace(tzinfo=None)]

    # df = dls(df)[0]
    st.session_state["meteo_data"] = df

    return df


# ---------------------------------------------------------------------------


@gf.func_timer
def outside_temp_graph() -> None:
    """
    Außentemperatur in df für Grafiken eintragen
    """
    page = gf.st_get("page")
    if "graph" not in page:
        return

    st.session_state["lis_sel_params"] = [ClassParam("temperature_air_mean_200")]
    if "meteo_data" not in st.session_state:
        meteo_data()
    st.session_state["meteo_data"].rename(
        columns={"Lufttemperatur in 2 m Höhe": "temp"}, inplace=True
    )

    st.session_state["df_temp"] = st.session_state["meteo_data"]["temp"]

    st.session_state["metadata"]["Temperatur"] = {
        "tit": "Temperatur",
        "orig_tit": "temp",
        "unit": " °C",
        "unit": " °C",
    }
    if "Temperatur" in st.session_state["df"].columns:
        st.session_state["df"].drop(columns=["Temperatur"], inplace=True)

    df = pd.concat(
        [
            st.session_state["df"],
            st.session_state["df_temp"].reindex(st.session_state["df"].index),
        ],
        axis=1,
    )
    df.rename(columns={"temp": "Temperatur"}, inplace=True)
    units()

    if gf.st_get("cb_h") is False:
        df["Temperatur"] = df["Temperatur"].interpolate(method="akima", axis="index")

    st.session_state["df"] = df


@gf.func_timer
def del_meteo() -> None:
    """vorhandene meteorologische Daten löschen"""
    # Spalten in dfs löschen
    for key in st.session_state:
        if isinstance(st.session_state[key], pd.DataFrame):
            for col in st.session_state[key].columns:
                for meteo in [
                    str(DIC_METEOSTAT_CODES[code]["tit"])
                    for code in DIC_METEOSTAT_CODES
                ]:
                    if meteo in col:
                        st.session_state[key].drop(columns=[str(col)], inplace=True)

    # Metadaten löschen
    if gf.st_get("metadata"):
        if "Temperatur" in st.session_state["metadata"].keys():
            del st.session_state["metadata"]["Temperatur"]
        if (
            " °C"
            not in [
                st.session_state["metadata"][key].get("unit")
                for key in st.session_state["metadata"].keys()
            ]
            and " °C" in st.session_state["metadata"]["units"]["set"]
        ):
            st.session_state["metadata"]["units"]["set"].remove(" °C")

    # Linien löschen
    for key in st.session_state:
        if isinstance(st.session_state[key], go.Figure):
            gf.st_delete(key)
