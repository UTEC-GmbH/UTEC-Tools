"""Meteorologische Daten"""

import os
from datetime import datetime as dt

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
                    unit=discover[res][param].get("origin"),
                )
            else:
                all_parameters[param].available_resolutions.append(res)

    return all_parameters


def start_end_time(**kwargs) -> cld.TimeSpan:
    """Zeitraum für Daten-Download"""

    page: str = kwargs.get("page") or gf.st_get("page") or "test"
    mdf: cld.MetaAndDfs | None = kwargs.get("mdf") or gf.st_get("mdf")

    if page == "test":
        start_time = dt(2020, 1, 1, 0, 0)
        end_time = dt(2020, 12, 31, 23, 59)

    elif page == "meteo":
        start_year: int = (
            min(
                gf.st_get("meteo_start_year"),
                gf.st_get("meteo_end_year"),
            )
            or 2020
        )
        end_year: int = (
            max(
                gf.st_get("meteo_start_year"),
                gf.st_get("meteo_end_year"),
            )
            or 2020
        )

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
        raise cle.SecretNotFoundError(entry="GEO_USER_AGENT")

    geolocator: Nominatim = Nominatim(user_agent=user_agent_secret)
    location: geopy.Location = geolocator.geocode(address)  # type: ignore

    gf.st_set("geo_location", location)

    return location


def check_parameter_availability(parameter: str, resolution: str) -> None:
    """Check if a parameter name is valid
    and if it's available in the requested resolution
    """
    all_params: dict[str, cld.DWDParameter] = get_all_parameters()
    if all_params.get(parameter) is None:
        logger.critical(f"Parameter '{parameter}' is not a valid DWD-Parameter!")
        raise cle.NoDWDParameterError(parameter)

    res_available: list[str] = all_params[parameter].available_resolutions
    if resolution not in res_available:
        logger.critical(
            f"Parameter '{parameter}' not available in '{resolution}' resolution! \n"
            f"Available resolutions are: {res_available}"
        )
        raise cle.NotAvailableInResolutionError(parameter, resolution, res_available)


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

    time_span: cld.TimeSpan = start_end_time(page=gf.st_get("page"))
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

    time_res: str = temporal_resolution or gf.st_get("sb_meteo_resolution") or "hourly"
    address: str = gf.st_get("ti_address") or "Bremen"
    time_span: cld.TimeSpan = start_end_time()

    parameters: list[str] = gf.st_get("ms_meteo_params") or ["temperature_air_mean_200"]
    for parameter in parameters:
        check_parameter_availability(parameter, time_res)

    params: list[cld.DWDParameter] = [get_all_parameters()[par] for par in parameters]

    for par in params:
        par.closest_station_id = str(
            pl.first(meteo_stations(address, par.name, time_res)["station_id"])
        )
        par.resolution = time_res
        par.data_frame = next(
            DwdObservationRequest(  # noqa: PD011
                parameter=par.name,
                resolution=time_res,
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
        5: "minute_1",
        10: "minute_5",
        60: "minute_10",
        60 * 24: "hourly",
        60 * 24 * 28: "daily",
    }

    return next(
        (
            resolution
            for threshold, resolution in res_options.items()
            if df_resolution < threshold
        ),
        "monthly",
    )


def meteo_df(df_resolution: int | None = None) -> pl.DataFrame:
    """Put all parameter date in one data frame"""

    time_res: str = match_resolution(df_resolution) if df_resolution else "hourly"
    params: list[cld.DWDParameter] = collect_meteo_data(time_res)

    return pl.concat(
        [
            param.data_frame.select(["value", "date"])
            .rename({"value": param.name, "date": f"{param.name} - date"})
            .select(
                [
                    pl.col(param.name),
                    pl.col(f"{param.name} - date").dt.replace_time_zone(None),
                ]
            )
            for param in params
            if param.data_frame is not None
        ],
        how="horizontal",
    )


# ---------------------------------------------------------------------------


# @gf.func_timer
# def outside_temp_graph() -> None:
#     """
#     Außentemperatur in df für Grafiken eintragen
#     """
#     page = gf.st_get("page")
#     if "graph" not in page:
#         return

#     st.session_state["lis_sel_params"] = [ClassParam("temperature_air_mean_200")]
#     if "meteo_data" not in st.session_state:
#         meteo_data()
#     st.session_state["meteo_data"].rename(
#         columns={"Lufttemperatur in 2 m Höhe": "temp"}, inplace=True
#     )

#     st.session_state["df_temp"] = st.session_state["meteo_data"]["temp"]

#     st.session_state["metadata"]["Temperatur"] = {
#         "tit": "Temperatur",
#         "orig_tit": "temp",
#         "unit": " °C",
#         "unit": " °C",
#     }
#     if "Temperatur" in st.session_state["df"].columns:
#         st.session_state["df"].drop(columns=["Temperatur"], inplace=True)

#     df = pd.concat(
#         [
#             st.session_state["df"],
#             st.session_state["df_temp"].reindex(st.session_state["df"].index),
#         ],
#         axis=1,
#     )
#     df.rename(columns={"temp": "Temperatur"}, inplace=True)
#     units()

#     if gf.st_get("cb_h") is False:
#         df["Temperatur"] = df["Temperatur"].interpolate(method="akima", axis="index")

#     st.session_state["df"] = df


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
