"""Meteorologische Daten"""
# ruff: noqa: E722, PD011, PERF203
# pylint: disable=W0702
# sourcery skip: do-not-use-bare-except

import os
from datetime import datetime as dt

import geopy
import polars as pl
from geopy.geocoders import Nominatim
from loguru import logger
from wetterdienst import Settings
from wetterdienst.core.timeseries.result import ValuesResult
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
    ts_shape="long",
    ts_si_units=False,
    ts_skip_empty=True,
    ts_skip_threshold=0.90,
    ts_skip_criteria="min",
    ts_dropna=True,
    ignore_env=True,
)


@gf.func_timer
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

    elif page == cont.ST_PAGES.meteo.short:
        start_time = dt.combine(sf.s_get("di_start"), sf.s_get("ti_start"))
        end_time = dt.combine(sf.s_get("di_end"), sf.s_get("ti_end"))

    elif mdf is not None:
        index: pl.Series = mdf.df.get_column(cont.SPECIAL_COLS.index)
        start_time: dt = index.min()
        end_time: dt = index.max()
    else:
        raise ValueError

    return cld.TimeSpan(start=start_time, end=end_time)


@gf.func_timer
def geo_locate(address: str) -> geopy.Location:
    """Geographische daten (Längengrad, Breitengrad) aus eingegebener Adresse"""

    user_agent_secret: str | None = os.environ.get("GEO_USER_AGENT")
    if user_agent_secret is None:
        raise cle.NotFoundError(entry="GEO_USER_AGENT", where="Secrets")

    geolocator: Nominatim = Nominatim(user_agent=user_agent_secret)
    location: geopy.Location = geolocator.geocode(address)  # type: ignore

    sf.s_set("geo_location", location)

    logger.info(f"Koordinaten für '{address}' gefunden.")

    return location


def fill_parameter_with_data_from_query(
    parameter: cld.DWDParameter,
    query: ValuesResult,
    resolution: str,
    location: geopy.Location,
) -> cld.DWDParameter:
    """Gather data"""

    parameter.location_lat = location.latitude
    parameter.location_lon = location.longitude
    parameter.resolution = resolution
    parameter.resolution_de = next(
        res_de
        for res_de, res_en in cont.DWD_RESOLUTION_OPTIONS.items()
        if resolution == res_en
    )
    parameter.data_frame = query.df
    parameter.all_stations = query.stations.df
    station_id: str = query.df[0, "station_id"]
    parameter.station_info_from_station_df_and_id(station_id)

    return parameter


@gf.func_timer
def get_data_for_parameter_from_closest_station(
    parameter: cld.DWDParameter, requested_resolution: str
) -> cld.DWDParameter:
    """Check if a parameter name is valid and give out the best data resolution.

    If the parameter is available in the requested resolution,
    it returns the requested resolution as string, if not, returns the best available.
    """

    if parameter.name not in ALL_PARAMETERS:
        logger.critical(f"Parameter '{parameter.name}' is not a valid DWD-Parameter!")
        raise cle.NoDWDParameterError(parameter.name)

    # if requested resolution is given in german, translate to english
    if requested_resolution in cont.DWD_RESOLUTION_OPTIONS:
        logger.info(
            f"Translating requested_resolution ('{requested_resolution}') "
            f"to '{cont.DWD_RESOLUTION_OPTIONS[requested_resolution]}'"
        )
        requested_resolution = cont.DWD_RESOLUTION_OPTIONS[requested_resolution]

    # if requested resolution not availabe for parameter, find the best alternative
    if requested_resolution not in parameter.available_resolutions:
        logger.info(
            f"Requested resolution '{requested_resolution}' "
            f"not in available resolutions {parameter.available_resolutions}"
        )
        sorted_full: list[str] = gf.sort_from_selection_to_front_then_to_back(
            list(cont.DWD_RESOLUTION_OPTIONS.values()), requested_resolution
        )
        requested_resolution = next(
            res for res in sorted_full if res in parameter.available_resolutions
        )
        logger.info(f"Requested resolution changed to '{requested_resolution}'.")

    time_span: cld.TimeSpan = start_end_time(page=sf.s_get("page"))
    address: str = sf.s_get("ta_adr") or "Bremen"
    location: geopy.Location = sf.s_get("geo_location") or geo_locate(address)

    # check if data already in parameter
    if (
        parameter.location_lat == location.latitude
        and parameter.location_lon == location.longitude
        and parameter.data_frame is not None
    ):
        logger.info(f"Data for parameter '{parameter.name}' already collected.")
        return parameter

    # check if the parameter has data for the requested resolution
    try:
        logger.debug(
            gf.string_new_line_per_item(
                [
                    "Trying to find data for",
                    f"parameter '{parameter.name}'",
                    f"available resolutions: {parameter.available_resolutions}",
                    f"starting in resolution '{requested_resolution}'.",
                ],
                leading_empty_lines=1,
            )
        )
        query = next(
            DwdObservationRequest(
                parameter=parameter.name,
                resolution=requested_resolution,
                start_date=time_span.start,
                end_date=time_span.end,
                settings=WETTERDIENST_SETTINGS,
            )
            .filter_by_rank((location.latitude, location.longitude), 1)
            .values.query()
        )
    except:
        logger.debug(
            gf.string_new_line_per_item(
                [
                    "No values availabe for",
                    f"parameter '{parameter.name}'",
                    f"in resolution '{requested_resolution}'.",
                    "Checking other options...",
                ],
                leading_empty_lines=1,
            )
        )
        sorted_res: list[str] = gf.sort_from_selection_to_front_then_to_back(
            parameter.available_resolutions, requested_resolution
        )
        for res in sorted_res[1:]:
            logger.debug(
                gf.string_new_line_per_item(
                    [
                        "Trying to find data for",
                        f"parameter '{parameter.name}'",
                        f"in resolution '{res}'.",
                    ],
                    leading_empty_lines=1,
                )
            )
            try:
                query: ValuesResult = next(
                    DwdObservationRequest(
                        parameter=parameter.name,
                        resolution=res,
                        start_date=time_span.start,
                        end_date=time_span.end,
                        settings=WETTERDIENST_SETTINGS,
                    )
                    .filter_by_rank((location.latitude, location.longitude), 1)
                    .values.query()
                )
            except:
                logger.debug(
                    gf.string_new_line_per_item(
                        [
                            f"No values availabe for parameter '{parameter.name}'",
                            f"in resolution '{res}'.",
                            "Checking other options...",
                        ],
                        leading_empty_lines=1,
                    )
                )
            else:
                logger.success(
                    f"\nData found for Parameter '{parameter.name}' "
                    f"in resolution '{res}'\n"
                )
                return fill_parameter_with_data_from_query(
                    parameter, query, res, location
                )
    else:
        logger.success(
            f"\nData for Parameter '{parameter.name}' "
            f"available in requested resolution ('{requested_resolution}')\n"
        )
        return fill_parameter_with_data_from_query(
            parameter, query, requested_resolution, location
        )
    logger.critical(f"No values for parameter '{parameter.name}' could be found!!!")
    raise cle.NoValuesForParameterError(
        parameter=parameter,
        tested=parameter.available_resolutions,
        start=time_span.start,
        end=time_span.end,
    )


@gf.func_timer
def stations_sorted_by_distance(
    parameter: cld.DWDParameter | None = None,
    resolution: str = "hourly",
) -> pl.DataFrame:
    """Alle verfügbaren Wetterstationen
    in x Kilometer entfernung zur gegebenen Addresse
    mit Daten für den gewählten Parameter
    in gewünschter zeitlicher Auflösung und Zeitperiode

    (die Entfernung ist in der Konstante 'cont.WEATHERSTATIONS_MAX_DISTANCE' definiert)
    """

    param: cld.DWDParameter = parameter or cld.DWDParameter(
        name="temperature_air_mean_200",
        available_resolutions=[
            "minute_10",
            "hourly",
            "subdaily",
            "daily",
            "monthly",
            "annual",
        ],
        unit=" °C",
    )
    param = get_data_for_parameter_from_closest_station(param, resolution)

    if param.all_stations is None:
        logger.critical(f"Keine Daten für Parameter '{param.name}' gefunden!")
        raise ValueError

    sf.s_set("stations_distance", param.all_stations)

    return param.all_stations


@gf.func_timer
def collect_meteo_data_for_list_of_parameters(
    temporal_resolution: str | None = None,
) -> list[cld.DWDParameter]:
    """Meteorologische Daten für die ausgewählten Parameter"""

    selected_resolution: str = (
        temporal_resolution or sf.s_get("sb_resolution") or "hourly"
    )
    selection: list[str] = sf.s_get("selected_params") or ["temperature_air_mean_200"]

    previously_collected_params: list[cld.DWDParameter] | None = sf.s_get("params_list")

    selected_params: list[cld.DWDParameter] = []
    for sel in selection:
        if previously_collected_params is not None and sel in [
            par.name for par in previously_collected_params
        ]:
            selected_params.append(
                next(par for par in previously_collected_params if par.name == sel)
            )
        else:
            selected_params.append(ALL_PARAMETERS[sel])

    params: list[cld.DWDParameter] = [
        get_data_for_parameter_from_closest_station(par, selected_resolution)
        for par in selected_params
    ]
    sf.s_set("params_list", params)

    return params


@gf.func_timer
def df_from_param_list(param_list: list[cld.DWDParameter]) -> pl.DataFrame:
    """DataFrame from list[cld.DWDParameter] as returned from collect_meteo_data"""

    dic: dict[str, pl.DataFrame] = {
        par.name: par.data_frame.select(
            pl.col("date").dt.replace_time_zone(None).alias("Datum"),
            pl.col("value").alias(par.name),
        )
        for par in param_list
        if par.data_frame is not None
    }
    longest_param: str = next(
        par.name
        for par in param_list
        if dic[par.name].height == max(df.height for df in dic.values())
    )

    df: pl.DataFrame = dic[longest_param]
    other_dfs: list[pl.DataFrame] = [
        value for key, value in dic.items() if key != longest_param
    ]
    for df_add in other_dfs:
        df = df.join(df_add, on="Datum", how="outer")

    return df


def match_resolution(df_resolution: int) -> str:
    """Matches a temporal resolution of a data frame given as an integer
    to the resolution as string needed for the weather data.

    Args:
        - df_resolution (int): Temporal Resolution of Data Frame (mdf.meta.td_mnts)

    Returns:
        - str: resolution as string for the 'resolution' arg in DwdObservationRequest
    """
    res_options: dict[int, str] = {
        5: next(iter(cont.DWD_RESOLUTION_OPTIONS.values())),
        10: list(cont.DWD_RESOLUTION_OPTIONS.values())[1],
        60: list(cont.DWD_RESOLUTION_OPTIONS.values())[2],
        60 * 24: list(cont.DWD_RESOLUTION_OPTIONS.values())[3],
        60 * 24 * 28: list(cont.DWD_RESOLUTION_OPTIONS.values())[4],
    }

    return next(
        (
            resolution
            for threshold, resolution in res_options.items()
            if df_resolution < threshold
        ),
        list(cont.DWD_RESOLUTION_OPTIONS.values())[5],
    )


@gf.func_timer
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
    params: list[cld.DWDParameter] = collect_meteo_data_for_list_of_parameters(time_res)
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
