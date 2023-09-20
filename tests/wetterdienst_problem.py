"""Rumprobieren"""
# ruff: noqa: E722, PD011, PERF203
# pylint: disable=W0702,W0621
# sourcery skip: avoid-global-variables, do-not-use-bare-except, name-type-suffix


import time
from datetime import datetime as dt
from typing import Any

import polars as pl
from loguru import logger
from wetterdienst import Settings
from wetterdienst.core.timeseries.result import ValuesResult
from wetterdienst.provider.dwd.observation import DwdObservationRequest

from modules import classes_data as cld
from modules import classes_errors as cle
from modules import constants as cont
from modules import general_functions as gf

WETTERDIENST_SETTINGS = Settings(
    ts_shape="long",
    ts_si_units=False,
    ts_skip_empty=True,
    ts_skip_threshold=0.90,
    ts_skip_criteria="min",
    ts_dropna=True,
    ignore_env=True,
)

# selected_parameter: str = "radiation_global"
selected_parameter: str = "sunshine_duration"
selected_resolution: str = "hourly"
start: dt = dt(2022, 1, 1, 0, 0)
end: dt = dt(2022, 12, 31, 23, 59)
lat_lon: tuple[float, float] = 53.0980433, 8.7747248

request = DwdObservationRequest(
    parameter=selected_parameter,
    resolution=selected_resolution,
    start_date=start,
    end_date=end,
    settings=WETTERDIENST_SETTINGS,
)
filtered = request.filter_by_rank(latlon=lat_lon, rank=1)


def values_after_time(max_time: float) -> pl.DataFrame | str:
    """DataFrame - empty if nothing found after defined amount of time"""
    start_time: float = time.monotonic()
    station_id_sorted_by_distance: pl.Series = filtered.df.get_column("station_id")
    for station in station_id_sorted_by_distance:
        distance: float = pl.first(
            filtered.df.filter(pl.col("station_id") == station).get_column("distance")
        )
        exe_time: float = time.monotonic() - start_time
        if exe_time > max_time:
            return f"Nothing found after {max_time} seconds"
        values: pl.DataFrame = request.filter_by_station_id(station).values.all().df
        if not values.is_empty():
            return values

    return f"Nothing found after {exe_time:.0f} seconds"


# values = next(filtered.values.query())


time_span = cld.TimeSpan(start, end)
discover: dict = DwdObservationRequest.discover()
all_parameters: dict[str, dict[str, Any]] = {}
for res, params in discover.items():
    for param in params:
        if not all_parameters.get(param):
            all_parameters[param] = {
                "name": param,
                "available_resolutions": [res],
                "unit": f" {discover[res][param].get('origin')}",
            }
        else:
            all_parameters[param]["available_resolutions"].append(res)

dwd_params: list[cld.DWDParameter] = []
for res, params in discover.items():
    for param in params:
        if param not in [par.name for par in dwd_params]:
            dwd_params.append(
                cld.DWDParameter(
                    name=param,
                    available_resolutions=[res],
                    unit=f" {params[param].get('origin')}",
                )
            )
        else:
            par: cld.DWDParameter = next(par for par in dwd_params if par.name == param)
            par.available_resolutions.append(res)


parameter: cld.DWDParameter = next(
    par for par in dwd_params if par.name == selected_parameter
)


par_1: str = "temperature_air_mean_200"
par_2: str = "radiation_global"

res: str = "hourly"
start: dt = dt(2022, 1, 1, 0, 0)
end: dt = dt(2022, 12, 31, 23, 59)

latlon_bremen: tuple[float, float] = 53.0980433, 8.7747248

# request for temperature
request_1: DwdObservationRequest = DwdObservationRequest(
    parameter=par_1,
    resolution=res,
    start_date=start,
    end_date=end,
    settings=WETTERDIENST_SETTINGS,
)

# request for radiation
request_2: DwdObservationRequest = DwdObservationRequest(
    parameter=par_2,
    resolution=res,
    start_date=start,
    end_date=end,
    settings=WETTERDIENST_SETTINGS,
)

# get a DataFrame with all stations that have data with the given constraints
# (here: 502 stations for "temperature" and 42 stations for "radiation")
stations_with_data_1: pl.DataFrame = request_1.filter_by_distance(latlon_bremen, 500).df
stations_with_data_2: pl.DataFrame = request_2.filter_by_distance(latlon_bremen, 500).df

# get the station-id of the closest station that has data (here: "00691" for both)
closest_station_id_1: str = stations_with_data_1.row(0, named=True)["station_id"]
closest_station_id_2: str = stations_with_data_2.row(0, named=True)["station_id"]


@gf.func_timer
def trying_out_stuff(version: int) -> pl.DataFrame:
    # get the actual weather data from the closest station
    # -> "temperature" works as expected, "radiation" raises TypeError:
    # TypeError: argument 'length': 'Expr' object cannot be interpreted as an integer

    if version == 1:
        request: DwdObservationRequest = request_1
        closest_station: str = closest_station_id_1
    else:
        request: DwdObservationRequest = request_2
        closest_station: str = closest_station_id_2

    return request.filter_by_station_id(closest_station).values.all().df


@gf.func_timer
def fill_parameter_with_data_from_query(
    parameter: cld.DWDParameter, query: ValuesResult, resolution: str
) -> cld.DWDParameter:
    """Gather data"""
    parameter.resolution = resolution
    parameter.data_frame = query.df
    parameter.all_stations = query.stations.df
    station_id: str = query.df[0, "station_id"]
    parameter.station_info_from_station_df_and_id(station_id)

    return parameter


@gf.func_timer
def get_data_for_parameter_from_closest_station(
    parameter: cld.DWDParameter, requested_resolution: str
) -> cld.DWDParameter:
    # sourcery skip: do-not-use-bare-except
    """Check if a parameter name is valid and give out the best data resolution.

    If the parameter is available in the requested resolution,
    it returns the requested resolution as string, if not, returns the best available.
    """

    # if requested resolution not availabe for parameter, find the best alternative
    if requested_resolution not in parameter.available_resolutions:
        sorted_full: list[str] = gf.sort_from_selection_to_front_then_to_back(
            list(cont.DWD_RESOLUTION_OPTIONS.values()), requested_resolution
        )
        requested_resolution = next(
            res for res in sorted_full if res in parameter.available_resolutions
        )

    # check if the parameter has data for the requested resolution
    try:
        logger.debug(
            f"\nTrying to find data for \n"
            f"parameter '{parameter.name}' \n"
            f"available resolutions: {parameter.available_resolutions} \n"
            f"starting in resolution '{requested_resolution}'. \n"
        )
        query = next(
            DwdObservationRequest(
                parameter=parameter.name,
                resolution=requested_resolution,
                start_date=time_span.start,
                end_date=time_span.end,
                settings=WETTERDIENST_SETTINGS,
            )
            .filter_by_rank(lat_lon, 1)
            .values.query()
        )
    except:
        logger.debug(
            f"\nNo values availabe for \n"
            f"parameter '{parameter.name}' \n"
            f"in resolution '{requested_resolution}'. \n"
            "Checking other options...\n"
        )
        sorted_res: list[str] = gf.sort_from_selection_to_front_then_to_back(
            parameter.available_resolutions, requested_resolution
        )
        for res in sorted_res[1:]:
            logger.debug(
                f"\nTrying to find data for \n"
                f"parameter '{parameter.name}' \n"
                f"in resolution '{res}'.\n"
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
                    .filter_by_rank(lat_lon, 1)
                    .values.query()
                )
            except:
                logger.debug(
                    f"\nNo values availabe for parameter '{parameter.name}' "
                    f"in resolution '{res}'. \n"
                    "Checking other options...\n"
                )
            else:
                logger.success(
                    f"\nData found for Parameter '{parameter.name}' "
                    f"in resolution '{res}'\n"
                )
                return fill_parameter_with_data_from_query(parameter, query, res)
    else:
        logger.success(
            f"\nData for Parameter '{parameter.name}' "
            f"found in requested resolution ('{requested_resolution}')\n"
        )
        return fill_parameter_with_data_from_query(
            parameter, query, requested_resolution
        )
    logger.critical(f"No values for parameter '{parameter.name}' could be found!!!")
    raise cle.NoValuesForParameterError(
        parameter=parameter,
        tested=parameter.available_resolutions,
        start=time_span.start,
        end=time_span.end,
    )


@gf.func_timer
def get_data_for_parameter_from_closest_station_mod_1(
    parameter: cld.DWDParameter, requested_resolution: str
) -> cld.DWDParameter:
    # sourcery skip: do-not-use-bare-except
    """Check if a parameter name is valid and give out the best data resolution.

    If the parameter is available in the requested resolution,
    it returns the requested resolution as string, if not, returns the best available.
    """

    # if requested resolution not availabe for parameter, find the best alternative
    if requested_resolution not in parameter.available_resolutions:
        sorted_full: list[str] = gf.sort_from_selection_to_front_then_to_back(
            list(cont.DWD_RESOLUTION_OPTIONS.values()), requested_resolution
        )
        requested_resolution = next(
            res for res in sorted_full if res in parameter.available_resolutions
        )

    # check if the parameter has data for the requested resolution
    try:
        logger.debug(
            f"\nTrying to find data for \n"
            f"parameter '{parameter.name}' \n"
            f"starting in resolution '{requested_resolution}'. \n"
            f"available resolutions: {parameter.available_resolutions} \n"
        )
        query = next(
            DwdObservationRequest(
                parameter=parameter.name,
                resolution=requested_resolution,
                start_date=time_span.start,
                end_date=time_span.end,
                settings=WETTERDIENST_SETTINGS,
            )
            .filter_by_rank(lat_lon, 1)
            .values.query()
        )
    except:
        logger.debug(
            f"\nNo values availabe for \n"
            f"parameter '{parameter.name}' \n"
            f"in resolution '{requested_resolution}'. \n"
            "Checking other options...\n"
        )
        sorted_res: list[str] = gf.sort_from_selection_to_front_then_to_back(
            parameter.available_resolutions, requested_resolution
        )
        for res in sorted_res[1:]:
            logger.debug(
                f"\nTrying to find data for \n"
                f"parameter '{parameter.name}' \n"
                f"in resolution '{res}'.\n"
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
                    .filter_by_rank(lat_lon, 1)
                    .values.query()
                )
            except:
                logger.debug(
                    f"\nNo values availabe for parameter '{parameter.name}' "
                    f"in resolution '{res}'. \n"
                    "Checking other options...\n"
                )
            else:
                logger.success(
                    f"\nData found for Parameter '{parameter.name}' "
                    f"in resolution '{res}'\n"
                )
                return fill_parameter_with_data_from_query(parameter, query, res)
    else:
        logger.success(
            f"\nData for Parameter '{parameter.name}' "
            f"found in requested resolution ('{requested_resolution}')\n"
        )
        return fill_parameter_with_data_from_query(
            parameter, query, requested_resolution
        )
    logger.critical(f"No values for parameter '{parameter.name}' could be found!!!")
    raise cle.NoValuesForParameterError(
        parameter=parameter,
        tested=parameter.available_resolutions,
        start=time_span.start,
        end=time_span.end,
    )


# query = next(
#     DwdObservationRequest(
#         parameter=selected_parameter,
#         resolution=selected_res,
#         start_date=start,
#         end_date=end,
#         settings=WETTERDIENST_SETTINGS,
#     )
#     .filter_by_rank(lat_lon, 1)
#     .values.query()
# )

# for param, par_dic in all_parameters.items():
#     res_options: list[str] = par_dic["available_resolutions"]
#     for res in res_options:
#         try:
#             query: ValuesResult = next(
#                 DwdObservationRequest(
#                     parameter=param,
#                     resolution=res,
#                     start_date=start,
#                     end_date=end,
#                     settings=WETTERDIENST_SETTINGS,
#                 )
#                 .filter_by_rank(lat_lon, 1)
#                 .values.query()
#             )
#         except:
#             print(f"No values found for '{res}' resolution")
#             res_options.remove(res)
