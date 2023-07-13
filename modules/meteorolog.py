"""Meteorologische Daten"""

import os
from datetime import datetime as dt
from typing import Any

import geopy
import polars as pl
from geopy.geocoders import Nominatim
from loguru import logger
from wetterdienst import Settings
from wetterdienst.provider.dwd.observation import DwdObservationRequest

from modules import classes_data as cld
from modules import classes_errors as cle
from modules import constants as cont
from modules import general_functions as gf
from modules import streamlit_functions as sf

# Grenze für Daten-Validität
# einen Wetterstation muss für den angegebenen Zeitraum
# mind. diesen Anteil an tatsächlich aufgezeichneten Daten haben
WETTERDIENST_SETTINGS = Settings(
    ts_skip_empty=True, ts_skip_threshold=0.90, ts_si_units=False
)


def get_all_parameters() -> dict[str, cld.DWDParameter]:
    """Dictionary with all availabel DWD-parameters (key = parameter name).
    (including parameters that a specific station might not have data for)
    """

    discover: dict = DwdObservationRequest.discover()
    all_parameters: dict[str, cld.DWDParameter] = {}
    for res, params in discover.items():
        for param in params:
            if not all_parameters.get(param):
                all_parameters[param] = cld.DWDParameter(
                    name=param,
                    available_resolutions=[res],
                    unit=f" {discover[res][param].get('origin')}",
                    name_de=cont.DWD_TRANSLATION.get(param),
                )
            else:
                all_parameters[param].available_resolutions.append(res)

    return all_parameters


ALL_PARAMETERS: dict[str, cld.DWDParameter] = get_all_parameters()


def start_end_time(**kwargs) -> cld.TimeSpan:
    """Zeitraum für Daten-Download"""

    page: str = kwargs.get("page") or sf.s_get("page") or "test"
    mdf: cld.MetaAndDfs | None = kwargs.get("mdf") or sf.s_get("mdf")

    if page == "test":
        start_time = dt(2017, 1, 1, 0, 0)
        end_time = dt(2019, 12, 31, 23, 59)

    elif page == "meteo":
        st_first_year: Any | None = sf.s_get("meteo_start_year")
        st_second_year: Any | None = sf.s_get("meteo_end_year")
        first_year: int = st_first_year if isinstance(st_first_year, int) else 1981
        second_year: int = st_second_year if isinstance(st_second_year, int) else 1981
        start_year: int = min(first_year, second_year)
        end_year: int = max(first_year, second_year)

        start_time = dt(start_year, 1, 1, 0, 0)
        end_time = dt(end_year, 12, 31, 23, 59)
        if end_time.year == dt.now().year:
            end_time = dt.now()

    elif mdf is not None:
        index: pl.Series = mdf.df.get_column(cont.SPECIAL_COLS.index)
        start_time: dt = index.min()
        end_time: dt = index.max()
    else:
        raise ValueError

    return cld.TimeSpan(start=start_time, end=end_time)


@gf.func_timer
def geo_locate(address: str = "Bremen") -> geopy.Location:
    """Geographische daten (Längengrad, Breitengrad) aus eingegebener Adresse"""

    user_agent_secret: str | None = os.environ.get("GEO_USER_AGENT") or "lasinludwig"
    if user_agent_secret is None:
        raise cle.NotFoundError(entry="GEO_USER_AGENT", where="Secrets")

    geolocator: Nominatim = Nominatim(user_agent=user_agent_secret)
    location: geopy.Location = geolocator.geocode(address)  # type: ignore

    sf.s_set("geo_location", location)

    return location


def check_parameter_availability(parameter: str, requested_resolution: str) -> str:
    """Check if a parameter name is valid.

    If the parameter is available in the requested resolution,
    it returns the requested resolution, if not, returns the closest available.
    """

    if parameter not in ALL_PARAMETERS:
        logger.critical(f"Parameter '{parameter}' is not a valid DWD-Parameter!")
        raise cle.NoDWDParameterError(parameter)

    available_resolutions: list[str] = ALL_PARAMETERS[parameter].available_resolutions

    # check if the parameter has data for the requested resolution
    if requested_resolution in available_resolutions:
        return requested_resolution

    index_requested: int = cont.DWD_RESOLUTION_OPTIONS.index(requested_resolution)
    index_available: list[int] = [
        cont.DWD_RESOLUTION_OPTIONS.index(res) for res in available_resolutions
    ]

    # check if there is a higher resolution available
    for rank in reversed(range(index_requested - 1)):
        closest: int = index_requested - rank
        if closest in index_available:
            return cont.DWD_RESOLUTION_OPTIONS[closest]

    # if no higher resolution is available, return the highest available
    return available_resolutions[0]


@gf.func_timer
def meteo_stations(
    address: str = "Bremen",
    parameter: str = "temperature_air_mean_200",
    resolution: str = "hourly",
) -> pl.DataFrame:
    """Alle verfügbaren Wetterstationen
    in x Kilometer entfernung zur gegebenen Addresse
    mit Daten für den gewählten Parameter
    in gewünschter zeitlicher Auflösung und Zeitperiode

    (die Entfernung ist in der Konstante 'cont.WEATHERSTATIONS_MAX_DISTANCE' definiert)

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

    time_span: cld.TimeSpan = start_end_time(page=sf.s_get("page"))
    location: geopy.Location = geo_locate(address)

    stations: pl.DataFrame = (
        DwdObservationRequest(
            parameter=parameter,
            resolution=resolution,
            start_date=time_span.start,
            end_date=time_span.end,
            settings=WETTERDIENST_SETTINGS,
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
def collect_meteo_data(
    temporal_resolution: str | None = None,
) -> list[cld.DWDParameter]:
    """Meteorologische Daten für die ausgewählten Parameter"""

    time_res: str = temporal_resolution or sf.s_get("sb_meteo_resolution") or "hourly"
    address: str = sf.s_get("ti_address") or "Bremen"
    location: geopy.Location = sf.s_get("geo_location") or geo_locate(address)
    time_span: cld.TimeSpan = start_end_time()

    parameters: list[str] = sf.s_get("ms_meteo_params") or ["temperature_air_mean_200"]
    params: list[cld.DWDParameter] = [ALL_PARAMETERS[par] for par in parameters]

    for par in params:
        par.resolution = check_parameter_availability(par.name, time_res)
        par.location_lat = location.latitude
        par.location_lon = location.longitude
        par.closest_station_id = str(
            pl.first(meteo_stations(address, par.name, par.resolution)["station_id"])
        )
        par.data_frame = next(
            DwdObservationRequest(  # noqa: PD011
                parameter=par.name,
                resolution=par.resolution,
                start_date=time_span.start,
                end_date=time_span.end,
                settings=WETTERDIENST_SETTINGS,
            )
            .filter_by_station_id((par.closest_station_id,))
            .values.query()
        ).df

    return params


def match_resolution(df_resolution: int) -> str:
    """Matches a temporal resolution of a data frame given as an integer
    to the resolution as string needed for the weather data.

    Args:
        - df_resolution (int): Temporal Resolution of Data Frame (mdf.meta.td_mnts)

    Returns:
        - str: resolution as string for the 'resolution' arg in DwdObservationRequest
    """
    res_options: dict[int, str] = {
        5: cont.DWD_RESOLUTION_OPTIONS[0],
        10: cont.DWD_RESOLUTION_OPTIONS[1],
        60: cont.DWD_RESOLUTION_OPTIONS[2],
        60 * 24: cont.DWD_RESOLUTION_OPTIONS[3],
        60 * 24 * 28: cont.DWD_RESOLUTION_OPTIONS[4],
    }

    return next(
        (
            resolution
            for threshold, resolution in res_options.items()
            if df_resolution < threshold
        ),
        cont.DWD_RESOLUTION_OPTIONS[5],
    )


def meteo_df(
    mdf: cld.MetaAndDfs | None = None,
) -> list[cld.DWDParameter]:
    """Get a DataFrame with date- and value-columns for each parameter"""

    mdf_intern: cld.MetaAndDfs | None = sf.s_get("mdf") or mdf
    if mdf_intern is None:
        raise cle.NotFoundError(entry="mdf", where="Session State")

    time_res: str = (
        match_resolution(mdf_intern.meta.td_mnts)
        if mdf_intern.meta.td_mnts and sf.s_get("page") != "meteo"
        else "hourly"
    )
    params: list[cld.DWDParameter] = collect_meteo_data(time_res)
    for param in params:
        if param.data_frame is None:
            raise ValueError
        param.data_frame = (
            param.data_frame.select(["value", "date"])
            .rename({"value": param.name, "date": cont.SPECIAL_COLS.index})
            .select(
                [
                    pl.col(param.name),
                    pl.col(cont.SPECIAL_COLS.index).dt.replace_time_zone(None),
                ]
            )
            .rename({param.name: param.name_de or param.name})
        )
    return params


# ---------------------------------------------------------------------------


# @gf.func_timer
# def del_meteo() -> None:
#     """vorhandene meteorologische Daten löschen"""
#     # Spalten in dfs löschen
#     for key in st.session_state:
#         if isinstance(st.session_state[key], pd.DataFrame):
#             for col in st.session_state[key].columns:
#                 for meteo in [
#                     str(DIC_METEOSTAT_CODES[code]["tit"])
#                     for code in DIC_METEOSTAT_CODES
#                 ]:
#                     if meteo in col:
#                         st.session_state[key].drop(columns=[str(col)], inplace=True)

#     # Metadaten löschen
#     if gf.st_get("metadata"):
#         if "Temperatur" in st.session_state["metadata"].keys():
#             del st.session_state["metadata"]["Temperatur"]
#         if (
#             " °C"
#             not in [
#                 st.session_state["metadata"][key].get("unit")
#                 for key in st.session_state["metadata"].keys()
#             ]
#             and " °C" in st.session_state["metadata"]["units"]["set"]
#         ):
#             st.session_state["metadata"]["units"]["set"].remove(" °C")

#     # Linien löschen
#     for key in st.session_state:
#         if isinstance(st.session_state[key], go.Figure):
#             gf.st_delete(key)
