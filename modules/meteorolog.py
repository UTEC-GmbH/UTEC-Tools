"""Meteorologische Daten"""
# ruff: noqa: E722, PD011, PERF203, BLE001
# pylint: disable=W0702,W0718
# sourcery skip: do-not-use-bare-except

import datetime as dt

import polars as pl
from loguru import logger

from modules import classes_data as cld
from modules import classes_errors as cle
from modules import constants as cont
from modules import df_manipulation as dfm
from modules import general_functions as gf
from modules import streamlit_functions as sf

ALL_PARAMETERS: dict[str, cld.DWDParam] = {
    par_name: cld.DWDParam(par_name) for par_name in cont.DWD_GOOD_PARAMS
}


def start_end_time(**kwargs) -> cld.TimeSpan:
    """Zeitraum für Daten-Download"""

    page: str = kwargs.get("page") or sf.s_get("page") or "test"
    mdf: cld.MetaAndDfs | None = kwargs.get("mdf") or sf.s_get("mdf")

    if page == "test":
        start_time = dt.datetime(2017, 1, 1, 0, 0)
        end_time = dt.datetime(2019, 12, 31, 23, 59)

    elif page == cont.ST_PAGES.meteo.short:
        di_start: dt.date | None = sf.s_get("di_start")
        di_end: dt.date | None = sf.s_get("di_end")
        ti_start: dt.time | None = sf.s_get("ti_start")
        ti_end: dt.time | None = sf.s_get("ti_end")
        if isinstance(di_start, dt.date) and isinstance(ti_start, dt.time):
            start_time = dt.datetime.combine(di_start, ti_start)
        else:
            raise TypeError
        if isinstance(di_end, dt.date) and isinstance(ti_end, dt.time):
            end_time = dt.datetime.combine(di_end, ti_end)
        else:
            raise TypeError

    elif mdf is not None:
        index: pl.Series = mdf.df.get_column(cont.SPECIAL_COLS.index).sort()
        start_time: dt.datetime = pl.first(index)
        end_time: dt.datetime = pl.last(index)

    else:
        raise ValueError

    return cld.TimeSpan(start=start_time, end=end_time)


# @gf.func_timer
# def geo_locate(address: str) -> cld.Location:
#     """Geographische daten (Längengrad, Breitengrad) aus eingegebener Adresse"""

#     user_agent_secret: str | None = os.environ.get(
#         "GEO_USER_AGENT", toml.load(".streamlit/secrets.toml").get("GEO_USER_AGENT")
#     )
#     if user_agent_secret is None:
#         raise cle.NotFoundError(entry="GEO_USER_AGENT", where="Secrets")

#     geolocator: Nominatim = Nominatim(user_agent=user_agent_secret)
#     geopy_loc: geopy.Location = geolocator.reverse(
#         geolocator.geocode(address, exactly_one=True, addressdetails=True).point,
#         exactly_one=True,
#         addressdetails=True,
#     )
#     addr: dict = geopy_loc.raw["address"]

#     loc: cld.Location = cld.Location(
#         latitude=geopy_loc.latitude,
#         longitude=geopy_loc.longitude,
#         altitude=None,
#         attr_size=None,
#         attr_colour=None,
#         name=addr.get("city", "unbekannt"),
#         address=geopy_loc.address,
#         street=addr.get("road", "unbekannt"),
#         house_number=int(addr.get("house_number")),
#         post_code=int(addr.get("postcode"))
#         if addr.get("postcode") is not None
#         else None,
#         city=addr.get("city", "unbekannt"),
#         suburb=addr.get("suburb", "unbekannt"),
#         country=addr.get("country", "unbekannt"),
#     )

# sf.s_set("geo_location", loc)

# logger.info(f"Koordinaten für '{address}' gefunden.")

# return loc


@gf.func_timer
def collect_meteo_data_for_list_of_parameters(
    temporal_resolution: str | None = None,
) -> list[cld.DWDParam]:
    """Meteorologische Daten für die ausgewählten Parameter"""
    time_span: cld.TimeSpan = start_end_time(page=sf.s_get("page"))
    address: str = sf.s_get("ta_adr") or "Bremen"
    location: cld.Location = (
        sf.s_get("geo_location") or cld.Location(address).fill_using_geopy()
    )
    sf.s_set("geo_location", location)

    selected_res: str = temporal_resolution or sf.s_get("sb_resolution") or "hourly"
    selected_res_en: str = cont.DWD_RESOLUTION_OPTIONS.get(selected_res, selected_res)
    logger.debug(f"selected resolution: '{selected_res_en}'")

    selection: list[str] = sf.s_get("selected_params") or cont.DWD_DEFAULT_PARAMS
    previously_collected_params: list[cld.DWDParam] = sf.s_get("params_list") or []
    selected_params: list[cld.DWDParam] = []

    for sel in selection:
        prev_par: cld.DWDParam | None = next(
            iter(par for par in previously_collected_params if par.name_en == sel),
            None,
        )
        if (
            prev_par is not None
            and prev_par.closest_available_res is not None
            and all(
                [
                    prev_par.location == location,
                    prev_par.time_span == time_span,
                    prev_par.requested_res_name_en == selected_res_en,
                    prev_par.closest_available_res.data.is_empty() is False,
                ]
            )
        ):
            logger.info(f"Parameter '{prev_par.name_en}' available from previous run.")
            selected_params.append(prev_par)
        else:
            selected_params.append(cld.DWDParam(sel, location, time_span))
            logger.info(f"Parameter '{sel}' added to list.")

    for par in selected_params:
        if (
            par.closest_available_res is None
            or par.closest_available_res.data.is_empty()
        ):
            par.requested_res_name_en = selected_res_en
            if selected_res_en in par.available_resolutions:
                logger.info(
                    f"Gathering data for Parameter '{par.name_en}' "
                    f"in requested resolution ({selected_res_en})."
                )
                par.fill_specific_resolution(selected_res_en)
                par.closest_available_res = getattr(par.resolutions, selected_res_en)
            else:
                closest_res: str = next(
                    res
                    for res in gf.sort_from_selection_to_front_then_to_back(
                        list(cont.DWD_RESOLUTION_OPTIONS.values()), selected_res_en
                    )
                    if res in par.available_resolutions
                )
                logger.info(
                    f"Requested resoltion ({selected_res_en}) not available...\n"
                    f"Gathering data for Parameter '{par.name_en}' "
                    f"in closest resolution ({closest_res})."
                )
                par.fill_specific_resolution(closest_res)
                par.closest_available_res = getattr(par.resolutions, closest_res)

    sf.s_set("params_list", selected_params)
    sf.s_set("stations_distance", all_available_stations(selected_params))

    return selected_params


@gf.func_timer
def all_available_stations(param_list: list[cld.DWDParam]) -> pl.DataFrame:
    """Combine the 'all_stations' attr of all Parameters in the given list"""

    first: cld.DWDParam = param_list[0]
    others: list[cld.DWDParam] = param_list[1:]
    if (
        first.closest_available_res is None
        or first.closest_available_res.all_stations is None
    ):
        raise ValueError
    df: pl.DataFrame = first.closest_available_res.all_stations
    for par in others:
        if (
            par.closest_available_res is None
            or par.closest_available_res.all_stations is None
        ):
            raise ValueError

        df = df.vstack(par.closest_available_res.all_stations)

    return df.unique(subset="station_id", keep="any").sort("distance")


@gf.func_timer
def df_from_param_list(param_list: list[cld.DWDParam]) -> pl.DataFrame:
    """DataFrame from list[cld.DWDParameter] as returned from collect_meteo_data"""

    dic: dict[str, pl.DataFrame] = {
        par.name_de: dfm.change_temporal_resolution(
            par.closest_available_res.data.select(
                pl.col("date").dt.replace_time_zone(None).alias("Datum"),
                pl.col("value").alias(par.name_de),
            ),
            {par.name_de: par.unit},
            next(
                res_lit
                for res_lit, res_cl in cont.TIME_RESOLUTIONS.items()
                if res_cl.dwd == par.requested_res_name_en
            ),  # type: ignore
        )
        for par in param_list
        if par.closest_available_res is not None
    }
    longest_param: str = next(
        par.name_de
        for par in param_list
        if dic[par.name_de].height == max(df.height for df in dic.values())
    )

    df: pl.DataFrame = dic[longest_param]
    other_dfs: list[pl.DataFrame] = [
        value for key, value in dic.items() if key != longest_param
    ]
    for df_add in other_dfs:
        df = df.join(df_add, on="Datum", how="outer")

    if sf.s_get("tog_polysun"):
        df = df.rename(
            {
                name_de: name_en
                for name_en, name_de in cont.DWD_PARAM_TRANSLATION.items()
                if name_de in df.columns
            }
        )

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
) -> list[cld.DWDParam]:
    """Get a DataFrame with date- and value-columns for each parameter"""

    mdf_intern: cld.MetaAndDfs | None = sf.s_get("mdf") or mdf
    if mdf_intern is None:
        raise cle.NotFoundError(entry="mdf", where="Session State")

    time_res: str = (
        match_resolution(mdf_intern.meta.td_mnts)
        if mdf_intern.meta.td_mnts and sf.s_get("page") != "meteo"
        else "hourly"
    )
    params: list[cld.DWDParam] = collect_meteo_data_for_list_of_parameters(time_res)
    for param in params:
        if (
            param.closest_available_res is None
            or param.closest_available_res.data is None
        ):
            raise ValueError

        param.closest_available_res.data = (
            param.closest_available_res.data.select(["value", "date"])
            .rename({"value": param.name_de, "date": cont.SPECIAL_COLS.index})
            .select(
                [
                    pl.col(param.name_de),
                    pl.col(cont.SPECIAL_COLS.index).dt.datetime.replace_time_zone(None),
                ]
            )
            .rename({param.name_de: param.name_de or param.name_de})
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
