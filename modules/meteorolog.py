"""Meteorologische Daten"""

import os
from dataclasses import dataclass, field
from datetime import datetime as dt
from zoneinfo import ZoneInfo

import geopy
import meteostat as met
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from geopy import distance

from modules import general_functions as gf

SKIP = True

if not SKIP:
    # Grenze für Daten-Validität
    # einen Wetterstation muss für den angegebenen Zeitraum
    # mind. diesen Anteil an tatsächlich aufgezeichneten Daten haben
    DATA_THRESH = 0.85

    # nur für Testzwecke im interaktiven Fenster
    PAR_TEST = "temperature_air_mean_200"
    STATION_ID_TEST = "05822"

    # Umkreis für Meteostat-Stationen
    WEATHERSTATIONS_MAX_DISTANCE = 700

    @gf.func_timer
    def start_end_time(**kwargs) -> tuple[dt | None, dt | None]:
        """Zeitraum für Daten-Download"""

        page: str = str(kwargs.get("page")) or gf.st_get("page")

        if page == "meteo":
            start_year: int = (
                min(
                    st.session_state["meteo_start_year"],
                    st.session_state["meteo_end_year"],
                )
                if "meteo_start_year" in st.session_state
                else 2020
            )

            if "meteo_end_year" in st.session_state:
                end_year: int = max(
                    st.session_state["meteo_start_year"],
                    st.session_state["meteo_end_year"],
                )
            else:
                end_year = 2020

            start_time = dt(start_year, 1, 1, 0, 0, tzinfo=ZoneInfo("Europe/Berlin"))
            end_time = dt(end_year, 12, 31, 23, 59, tzinfo=ZoneInfo("Europe/Berlin"))
            if end_time.year == dt.now().year:
                end_time = dt.now()
        elif "df" not in st.session_state:
            start_time = end_time = None
        else:
            ind_0 = min(
                st.session_state["df"].index[0], st.session_state["df"].index[-1]
            )
            ind_1 = max(
                st.session_state["df"].index[0], st.session_state["df"].index[-1]
            )
            start_time = dt(
                ind_0.year,
                1,
                1,
                0,
                0,
                tzinfo=ZoneInfo("Europe/Berlin"),
            )
            end_time = dt(
                ind_1.year,
                12,
                31,
                23,
                59,
                tzinfo=ZoneInfo("Europe/Berlin"),
            )

        return start_time, end_time

    if "page" in st.session_state:
        start, end = start_end_time(page=gf.st_get("page"))

    @gf.func_timer
    def geo(address: str) -> dict:
        """Geographische daten (Längengrad, Breitengrad) aus eingegebener Adresse"""
        geolocator = geopy.geocoders.Nominatim(user_agent=os.getenv("GEO_USER_AGENT"))
        location = geolocator.geocode(address)
        dic_geo = {
            "lat": location.latitude,
            "lon": location.longitude,
            "alt": location.altitude,
        }
        st.session_state["dic_geo"] = dic_geo

        return dic_geo

    @gf.func_timer
    def all_stations() -> pd.DataFrame:
        """DataFrame aller Stationen"""
        df_met = meteostat_stations()
        df_all = df_met.sort_values(["distance"]).reset_index(drop=True)

        st.session_state["df_all_stations"] = df_all
        return df_all

    @gf.func_timer
    def all_stations_without_dups() -> pd.DataFrame:
        """alle Stationen ohne Duplikate"""
        df = (
            st.session_state["df_all_stations"]
            if "df_all_stations" in st.session_state
            else all_stations()
        ).copy()

        st.session_state["all_stations_without_dups"] = df
        return df

    @gf.func_timer
    def meteostat_stations(
        lat: float | None = None,
        lon: float | None = None,
        distance_sta: float = WEATHERSTATIONS_MAX_DISTANCE,
    ) -> pd.DataFrame:
        """
        verfügbare Wetterstationen von meteostat
        in x Meter entfernung zur gegebenen Addresse
        mit stündlichen Daten in der erforderlichen Zeitperiode
        """
        if "start" not in locals():
            start_time, end_time = start_end_time(gf.st_get("page"))

        if lat is None or lon is None:
            adr = gf.st_get("ti_adr")  # or "Bremen"
            lat = geo(adr)["lat"]
            lon = geo(adr)["lon"]

        # alle Wetterstationen im gewählten Umkreis um den Standort
        df_meteostat_stations = (
            met.Stations()
            .nearby(lat, lon, distance_sta * 1_000)
            .inventory(
                "hourly",
                (start_time.replace(tzinfo=None), end_time.replace(tzinfo=None)),
            )
        ).fetch()

        if distance_sta == WEATHERSTATIONS_MAX_DISTANCE:
            df_meteostat_stations = meteostat_stations_df_edit(df_meteostat_stations)
            st.session_state["df_meteostat_stations"] = df_meteostat_stations

        return df_meteostat_stations

    @gf.func_timer
    def meteostat_stations_df_edit(df: pd.DataFrame) -> pd.DataFrame:
        """Anpassung auf Format der Meteostat-Stationen"""
        df["station_id"] = df.index
        df = df.reset_index(drop=True)
        df["provider"] = "Meteostat"

        drop_cols = [
            "wmo",
            "icao",
            "daily_start",
            "daily_end",
            "monthly_start",
            "monthly_end",
        ]
        df = df.drop(columns=drop_cols)

        # Distanz zum gewählten Standort in km umrechnen (wird in m ausgegeben)
        df["distance"] = df["distance"] / 1000

        return df

    @gf.func_timer
    def meteostat_data_by_stationid(station_id: str) -> pd.DataFrame:
        """Meteostat-Daten eine einzelnen Station"""
        if "start" not in locals():
            start_time, end_time = start_end_time(gf.st_get("page"))

        meteostat_data_hourly = met.Hourly(
            station_id,
            start_time.replace(tzinfo=None),
            end_time.replace(tzinfo=None),
        )
        meteostat_codes = [
            par.code for par in LIS_PARAMS if "Meteostat" in par.provider
        ]
        meteostat_data_norm = meteostat_data_hourly.normalize()
        meteostat_data_inter = meteostat_data_norm.interpolate()
        df_meteostat_data = meteostat_data_inter.fetch()

        # only columns where at least x% of entries are valid data
        df_meteostat_data = df_meteostat_data.dropna(
            axis="columns", thresh=df_meteostat_data.shape[0] * DATA_THRESH
        )

        df_meteostat_data = df_meteostat_data.drop(
            columns=[
                col
                for col in df_meteostat_data.columns
                if col.upper() not in meteostat_codes
            ]
        )

        return df_meteostat_data

    @gf.func_timer
    def closest_station_with_data(param: str) -> tuple[str | float]:
        """nächstgelegene Station, die Daten zum gewählten Parameter hat"""

        df_met_st = (
            gf.st_get("df_meteostat_stations")
            if "df_meteostat_stations" in st.session_state
            else meteostat_stations()
        )
        idx_0 = df_met_st.index[0]
        station_id = f'Meteostat_{df_met_st.loc[idx_0, "station_id"]}'
        distance_sta: float = df_met_st.loc[idx_0, "distance"]
        df_station_data = meteostat_data_by_stationid(station_id.split("_")[-1])
        if param.code.lower() not in df_station_data.columns:
            for rank in range(1, df_met_st.shape[0]):
                idx = df_met_st.index[rank]
                station_id = f'Meteostat_{df_met_st.loc[idx, "station_id"]}'
                distance_sta: float = df_met_st.loc[idx, "distance"]
                df_station_data = meteostat_data_by_stationid(station_id.split("_")[-1])
                if param.code.lower() in df_station_data.columns:
                    break

        return station_id, distance_sta

    @gf.func_timer
    def selected_params(page: str = "meteo") -> list:
        """ausgewählte Parameter"""

        if "graph" in page:
            lis_sel_params = gf.st_get("lis_sel_params")
        else:
            lis_sel_params = [
                par for par in LIS_PARAMS if gf.st_get(f"cb_{par.tit_de}")
            ] or [par for par in LIS_PARAMS if par.tit_de in LIS_DEFAULT_PARAMS]

        df_met_st = (
            gf.st_get("df_meteostat_stations")
            if "df_meteostat_stations" in st.session_state
            else meteostat_stations()
        )

        for par in lis_sel_params:
            par.closest_station_id, par.distance = closest_station_with_data(par)

        for par in lis_sel_params:
            lis_dup = [param for param in lis_sel_params if param.tit_de in par.tit_de]
            if len(lis_dup) > 1:
                station_ids = [lis_dup[pos].closest_station_id for pos in range(2)]
                stations = [
                    df_met_st[df_met_st["station_id"] == s_id.split("_")[-1]]
                    for s_id in station_ids
                ]
                positions = [
                    (
                        station.loc[station.index[0], "latitude"],
                        station.loc[station.index[0], "longitude"],
                    )
                    for station in stations
                ]

                lis_sel_params.remove(
                    lis_dup[0]
                    if lis_dup[0].distance > lis_dup[1].distance
                    else lis_dup[1]
                )

        st.session_state["lis_sel_params"] = lis_sel_params
        return lis_sel_params

    @gf.func_timer
    def used_stations() -> pd.DataFrame:
        """nur verwendete Stationen"""
        lis_sel_params = (
            st.session_state["lis_sel_params"]
            if "lis_sel_params" in st.session_state
            else selected_params()
        )

        df_all = (
            st.session_state["df_all_stations"]
            if "df_all_stations" in st.session_state
            else all_stations()
        )

        set_used_stations = {par.closest_station_id for par in lis_sel_params}
        df_used_stations = pd.concat(
            [
                df_all[
                    (df_all["station_id"] == st.split("_")[1])
                    & (df_all["provider"] == st.split("_")[0])
                ]
                for st in set_used_stations
            ]
        )
        df_used_stations["params"] = [
            [
                par.tit_de
                for par in lis_sel_params
                if par.closest_station_id.split("_")[1]
                in df_used_stations.loc[idx, "station_id"]
            ]
            for idx in df_used_stations.index
        ]

        st.session_state["df_used_stations"] = df_used_stations
        return df_used_stations

    @gf.func_timer
    def used_stations_show() -> pd.DataFrame:
        """df mit verwendeten Stationen für die Darstellung in der app"""
        df = (
            st.session_state["df_used_stations"]
            if "df_used_stations" in st.session_state
            else used_stations()
        )

        st.session_state["df_used_stations_show"] = df
        return df

    @gf.func_timer
    def df_used_show_edit() -> pd.DataFrame:
        """Anpassen und formatieren des df der benutzten Wetterstationen"""
        df = (
            st.session_state["df_used_stations_show"]
            if "df_used_stations_show" in st.session_state
            else used_stations_show()
        )

        li_drp = [
            "hourly_start",
            "hourly_end",
            "timezone",
            "provider",
            "station_id",
        ]
        df = df.drop(li_drp, axis="columns")
        df.index = df["name"]

        # rename everything
        ren = {
            "distance": "Entfernung",
            "region": "Region",
            "country": "Land",
            "elevation": "Höhe über NN",
            "latitude": "Breitengrad",
            "longitude": "Längengrad",
            "params": "Parameter",
        }
        df = df.rename(ren, axis="columns")
        df = df[ren.values()]
        df = df.sort_values(["Entfernung"])

        df = df.style.format(
            {
                "Höhe über NN": "{:,.1f} m",
                "Breitengrad": "{:,.2f}°",
                "Längengrad": "{:,.2f}°",
                "Entfernung": "{:,.1f} km",
            },
            decimal=",",
            thousands=".",
        )

        return df

    @gf.func_timer
    def meteo_data() -> pd.DataFrame:
        """
        Meteorologische Daten für die ausgewählten Parameter
        """
        page = gf.st_get("page")
        if "start" not in locals():
            start_time, end_time = start_end_time(gf.st_get("page"))

        # alte Grafiken löschen
        for key, value in st.session_state.items():
            if isinstance(value, go.Figure):
                gf.st_delete(key)

        lis_sel_params = (
            gf.st_get("lis_sel_params")
            if "lis_sel_params" in st.session_state
            else selected_params()
        )

        if "graph" in page:
            lis_sel_params = selected_params("graph")

        set_used_stations = {par.closest_station_id for par in lis_sel_params}

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
            df["Temperatur"] = df["Temperatur"].interpolate(
                method="akima", axis="index"
            )

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

    # --------------------------------------------------------------------------

    # Parameter
    @dataclass
    class ClassParam:
        """Parameter der Wetterstationen"""

        code: str
        tit_en: str | None = field(default=None)
        tit_de: str | None = field(default=None)
        cat_utec: str | None = field(default=None)
        cat_en: str | None = field(default=None)
        cat_de: str | None = field(default=None)
        default: bool | None = field(default=False)
        unit: str | None = field(default=None)
        pandas_styler: str | None = field(default=None)
        num_format: str | None = field(default=None)
        provider: str | None = field(default="Meteostat")
        closest_station_id: str | None = None
        distance: float | None = None

        def __post_init__(self) -> None:
            """Eigenschaften nach Erzeugung der Felder ausfüllen"""
            if self.code in DIC_METEOSTAT_CODES:
                self.provider = "Meteostat"

            # meteostat Parameter
            if "Meteostat" in self.provider:
                self.tit_en = DIC_METEOSTAT_CODES[self.code].get("orig_name")
                self.tit_de = DIC_METEOSTAT_CODES[self.code].get("tit")
                self.unit = DIC_METEOSTAT_CODES[self.code].get("unit")
                self.cat_utec = DIC_METEOSTAT_CODES[self.code].get("cat_utec")

            self.num_format = f'#,##0.0" {self.unit}"'
            self.pandas_styler = "{:,.1f} " + self.unit
            self.default = self.tit_de in LIS_DEFAULT_PARAMS

    # Parameter, die standardmäßig für den Download ausgewählt sind
    LIS_DEFAULT_PARAMS: list = [
        "Lufttemperatur in 2 m Höhe",
        "Globalstrahlung",
        "Windgeschwindigkeit",
        "Windrichtung",
    ]

    # Parameter von Meteostat
    DIC_METEOSTAT_CODES: dict = {
        "TEMP": {
            "orig_name": "Air Temperature",
            "tit": "Lufttemperatur in 2 m Höhe",
            "unit": "°C",
            "cat_utec": "Temperaturen",
        },
        "DWPT": {
            "orig_name": "Dew Point",
            "tit": "Taupunkt",
            "unit": "°C",
            "cat_utec": "Temperaturen",
        },
        "PRCP": {
            "orig_name": "Total Precipitation",
            "tit": "Niederschlag",
            "unit": "mm",
            "cat_utec": "Feuchte, Luftdruck, Niederschlag",
        },
        "WDIR": {
            "orig_name": "Wind (From) Direction",
            "tit": "Windrichtung",
            "unit": "°",
            "cat_utec": "Sonne und Wind",
        },
        "WSPD": {
            "orig_name": "Average Wind Speed",
            "tit": "Windgeschwindigkeit",
            "unit": "km/h",
            "cat_utec": "Sonne und Wind",
        },
        "WPGT": {
            "orig_name": "Wind Peak Gust",
            "tit": "max. Windböe",
            "unit": "km/h",
            "cat_utec": "Sonne und Wind",
        },
        "RHUM": {
            "orig_name": "Relative Humidity",
            "tit": "rel. Luftfeuchtigkeit",
            "unit": "%",
            "cat_utec": "Feuchte, Luftdruck, Niederschlag",
        },
        "PRES": {
            "orig_name": "Sea-Level Air Pressure",
            "tit": "Luftdruck (Meereshöhe)",
            "unit": "hPa",
            "cat_utec": "Feuchte, Luftdruck, Niederschlag",
        },
        "SNOW": {
            "orig_name": "Snow Depth",
            "tit": "Schneehöhe",
            "unit": "m",
            "cat_utec": "Feuchte, Luftdruck, Niederschlag",
        },
        "TSUN": {
            "orig_name": "Total Sunshine Duration",
            "tit": "Sonnenstunden",
            "unit": "min",
            "cat_utec": "Sonne und Wind",
        },
    }

    # Eigene Kategorien
    LIS_CAT_UTEC: list = [
        "Temperaturen",
        "Sonne und Wind",
        "Feuchte, Luftdruck, Niederschlag",
        "Bewölkung und Sichtweite",
    ]

    # alle Parameter
    LIS_PARAMS: list = [
        ClassParam(key)
        for key in list(DIC_METEOSTAT_CODES.keys())
        if ClassParam(key).cat_utec
    ]

    DIC_PARAMS: dict = {
        key: ClassParam(key)
        for key in list(DIC_METEOSTAT_CODES.keys())
        if ClassParam(key).cat_utec
    }
