"""Rumprobieren"""
# ruff: noqa: E722, PD011, PERF203
# pylint: disable=W0702,W0621
# sourcery skip: avoid-global-variables, do-not-use-bare-except, name-type-suffix


from datetime import datetime as dt
from typing import Any

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
