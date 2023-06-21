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


def list_all_parameters() -> list[cld.DWDParameter]:
    """List of all availabel DWD-parameters

    (including parameters that a specific station might not have data for)
    """
    all_resolutions: list[str] = list(DwdObservationRequest.discover().keys())
    all_parameters: list[cld.DWDParameter] = []
    for res in all_resolutions:
        for param in DwdObservationRequest.discover()[res]:
            if param not in [par.name for par in all_parameters]:
                all_parameters += [
                    cld.DWDParameter(
                        name=param,
                        available_resolutions=[res],
                        unit=DwdObservationRequest.discover()[res][param]["origin"],
                    )
                ]
            else:
                for par in all_parameters:
                    if par.name == param:
                        par.available_resolutions += [res]

    return all_parameters


def start_end_time(**kwargs) -> cld.TimeSpan:
    """Zeitraum für Daten-Download"""

    page: str = kwargs.get("page") or gf.st_get("page") or "test"
    mdf: cld.MetaAndDfs | None = kwargs.get("mdf") or gf.st_get("mdf")

    if page == "test":
        start_time = dt(2020, 1, 1)
        end_time = dt(2020, 12, 31)

    elif page == "meteo":
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


def check_parameter_availability(parameter: str, resolution: str) -> None:
    """Check if a parameter name is valid
    and if it's available in the requested resolution
    """

    if parameter not in [par.name for par in list_all_parameters()]:
        logger.critical(f"Parameter '{parameter}' is not a valid DWD-Parameter!")
        raise cle.NoDWDParameterError(parameter)

    available_resolutions: list[str] = gf.flatten_list_of_lists(
        [
            par.available_resolutions
            for par in list_all_parameters()
            if par.name == parameter
        ]
    )
    if resolution not in available_resolutions:
        logger.critical(
            f"Parameter '{parameter}' not available in '{resolution}' resolution! \n"
            f"Available resolutions are: {available_resolutions}"
        )
        raise cle.NotAvailableInResolutionError(
            parameter, resolution, available_resolutions
        )


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


@gf.func_timer
def collect_meteo_data() -> list[cld.DWDParameter]:
    """Meteorologische Daten für die ausgewählten Parameter"""

    time_res: str = gf.st_get("sb_meteo_resolution") or "hourly"
    address: str = gf.st_get("ti_address") or "Bremen"
    time_span: cld.TimeSpan = start_end_time()

    parameters: list[str] = gf.st_get("ms_meteo_params") or [
        "temperature_air_mean_200",
        "precipitation_height",
    ]
    for parameter in parameters:
        check_parameter_availability(parameter, time_res)

    params: list[cld.DWDParameter] = [
        par for par in list_all_parameters() if par.name in parameters
    ]

    for par in params:
        par.closest_station_id = str(
            pl.first(meteo_stations(address, par.name, time_res)["station_id"])
        )
        par.resolution = time_res
        par.data_frame = (
            DwdObservationRequest(  # noqa: PD011
                parameter=par.name,
                resolution=time_res,
                start_date=time_span.start,
                end_date=time_span.end,
            )
            .filter_by_station_id((par.closest_station_id,))
            .values.all()
            .df
        )

    return params


def meteo_df() -> pl.DataFrame:
    """Put all parameter date in one data frame"""
    params: list[cld.DWDParameter] = collect_meteo_data()

    df: pl.DataFrame = pl.DataFrame()
    for param in params:
        if param.data_frame is not None:
            df = df.with_columns(
                [
                    pl.Series(
                        name=param.name, values=param.data_frame.get_column("value")
                    ),
                    pl.Series(
                        name=f"{param.name} - date",
                        values=param.data_frame.get_column("date").dt.replace_time_zone(
                            None
                        ),
                    ),
                ]
            )

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
