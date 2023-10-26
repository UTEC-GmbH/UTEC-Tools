"""Classes for meteorological data"""

import time
from dataclasses import dataclass, field
from typing import Self

import polars as pl
from loguru import logger
from wetterdienst.provider.dwd.observation import DwdObservationRequest

from modules import constants as cont
from modules import df_manipulation as dfm
from modules import general_functions as gf
from modules.classes_data import Location, TimeSpan


@dataclass
class DWDStation:
    """Properties of DWD Station"""

    station_id: str = "unbekannt"
    name: str = "unbekannt"
    state: str = "unbekannt"
    height: float = 0
    latitude: float = 0
    longitude: float = 0
    distance: float = 0


@dataclass
class DWDResData:
    """Data for given parameter and location"""

    name_en: str
    name_de: str
    all_stations: pl.DataFrame | None = None
    closest_station: DWDStation = field(init=False)
    data: pl.DataFrame = field(init=False)
    no_data: str | None = "No Data Available"

    def __post_init__(self) -> None:
        """Fill in fields"""
        self.closest_station = DWDStation()
        self.data = pl.DataFrame()


@dataclass
class DWDResolutions:
    """Temporal resolutions"""

    minute_1: DWDResData = field(init=False)
    minute_5: DWDResData = field(init=False)
    minute_10: DWDResData = field(init=False)
    hourly: DWDResData = field(init=False)
    six_hour: DWDResData = field(init=False)
    subdaily: DWDResData = field(init=False)
    daily: DWDResData = field(init=False)
    monthly: DWDResData = field(init=False)
    annual: DWDResData = field(init=False)

    def __post_init__(self) -> None:
        """Fill in fields"""
        self.minute_1 = DWDResData("minute_1", "Minutenwerte")
        self.minute_5 = DWDResData("minute_5", "5-Minutenwerte")
        self.minute_10 = DWDResData("minute_10", "10-Minutenwerte")
        self.hourly = DWDResData("hourly", "Stundenwerte")
        self.six_hour = DWDResData("6_hour", "6-Stundenwerte")
        self.subdaily = DWDResData("subdaily", "mehrmals täglich")
        self.daily = DWDResData("daily", "Tageswerte")
        self.monthly = DWDResData("monthly", "Monateswerte")
        self.annual = DWDResData("annual", "Jahreswerte")

    def list_all_res_names_en(self) -> list[str]:
        """List of all resolution names"""
        return [getattr(self, key).name_en for key in self.__dataclass_fields__]

    def res_with_data(self) -> list[DWDResData]:
        """Get all resolutions that have data"""
        return [
            getattr(self, res)
            for res in self.__dataclass_fields__
            if getattr(self, res).no_data is None
        ]

    def res_without_data(self) -> list[DWDResData]:
        """Get all resolutions that don't have data"""
        return [
            getattr(self, res)
            for res in self.__dataclass_fields__
            if isinstance(getattr(self, res).no_data, str)
        ]


@dataclass
class DWDParam:
    """DWD Parameter

    Test:
        import datetime as dt
        loc = Location("Bremen", 53.0758196, 8.8071646)
        tim = TimeSpan(dt.datetime(2017, 1, 1, 0, 0), dt.datetime(2019, 12, 31, 23, 59))
        par = DWDParam("temperature_air_mean_200", loc, tim)
        par.fill_all_resolutions()

    pars for Polysun weather data (hourly resolution):
        par = DWDParam("radiation_global", loc, tim)
        par = DWDParam("radiation_sky_short_wave_diffuse", loc, tim)
        par = DWDParam("radiation_sky_long_wave", loc, tim)
        par = DWDParam("temperature_air_mean_200", loc, tim)
        par = DWDParam("wind_speed", loc, tim)
        par = DWDParam("humidity", loc, tim)

        par.fill_specific_resolution("hourly")
    """

    name_en: str
    location: Location | None = None
    time_span: TimeSpan | None = None

    unit: str = field(init=False)
    name_de: str = field(init=False)
    available_resolutions: set[str] = field(init=False)

    resolutions: DWDResolutions = field(init=False)

    requested_res_name_en: str | None = None
    closest_available_res: DWDResData | None = None

    num_format: str = field(init=False)
    pandas_styler: str = field(init=False)

    def __post_init__(self) -> None:
        """Fill in fields"""
        self.resolutions = DWDResolutions()

        self.available_resolutions = {
            res for res, dic in cont.DWD_DISCOVER.items() if self.name_en in dic
        }
        self.unit: str = " " + next(
            dic[self.name_en]["origin"]
            for dic in cont.DWD_DISCOVER.values()
            if self.name_en in dic
        )
        self.name_de = cont.DWD_PARAM_TRANSLATION.get(self.name_en, self.name_en)

        self.num_format = f'#,##0.0" {self.unit.strip()}"'
        self.pandas_styler = "{:,.1f} " + self.unit

    def fill_all_resolutions(self) -> Self:
        """Get data for available resolutions"""

        for res in self.resolutions.list_all_res_names_en():
            if res in self.available_resolutions:
                att_dic: dict = self.get_data(res)
                for key, value in att_dic.items():
                    setattr(getattr(self.resolutions, res), key, value)

        return self

    def fill_specific_resolution(self, resolution: str) -> Self:
        """Get data for a chosen resolution"""
        res: str = cont.DWD_RESOLUTION_OPTIONS.get(resolution) or resolution
        if res not in self.available_resolutions:
            return self

        att_dic: dict = self.get_data(res)
        for key, value in att_dic.items():
            setattr(getattr(self.resolutions, res), key, value)

        return self

    def get_data(self, resolution: str) -> dict:
        """Get the values in a specified resolution
        from the closest station that has data.

        (Checks in every station if a higher resolution is available
        if the requested has no data)
        """
        if (
            self.location is None
            or self.time_span is None
            or self.location.latitude is None
            or self.location.longitude is None
        ):
            raise ValueError

        logger.info(
            gf.string_new_line_per_item(
                [
                    "Searching data for",
                    f"Parameter: '{self.name_en}'",
                    f"Resolution: '{resolution}'",
                ],
                leading_empty_lines=2,
                trailing_empty_lines=2,
            )
        )
        request = DwdObservationRequest(
            parameter=self.name_en,
            resolution=resolution,
            start_date=self.time_span.start,
            end_date=self.time_span.end,
            settings=cont.WETTERDIENST_SETTINGS,
        )

        all_stations: pl.DataFrame = request.filter_by_distance(
            latlon=(self.location.latitude, self.location.longitude),
            distance=cont.WEATHERSTATIONS_MAX_DISTANCE,
        ).df

        closest_station: DWDStation = DWDStation()
        data_frame: pl.DataFrame = pl.DataFrame()
        no_data: str | None = None

        start_time: float = time.monotonic()

        for station_id in all_stations.get_column("station_id"):
            no_data = self.check_time_distance(station_id, all_stations, start_time)
            if no_data:
                break

            values: pl.DataFrame = (
                request.filter_by_station_id(station_id).values.all().df  # noqa: PD011
            )

            # Falls keine Daten gefunden wurdengefunden,
            # wird nachgeschaut, ob die Station Daten in höherer Auflösung hat
            if values.is_empty():
                values = self.look_for_higher_resolution(resolution, station_id)

            if not values.is_empty():
                data_frame = values
                closest_station_df: pl.DataFrame = all_stations.filter(
                    pl.col("station_id") == station_id
                )

                for key in DWDStation.__dataclass_fields__:
                    value: str | float = (
                        station_id
                        if key == "station_id"
                        else closest_station_df.get_column(key)[0]
                    )
                    setattr(closest_station, key, value)

                logger.success(
                    gf.string_new_line_per_item(
                        [
                            f"'{resolution}'-data for '{self.name_en}' found!",
                            f"Station ID: '{closest_station.station_id}'",
                            f"Station: '{closest_station.name}'",
                            f"Distance: '{closest_station.distance}' km",
                        ],
                        leading_empty_lines=1,
                        trailing_empty_lines=2,
                    )
                )
                break

        return {
            "all_stations": all_stations,
            "closest_station": closest_station,
            "data": data_frame,
            "no_data": no_data,
        }

    def look_for_higher_resolution(
        self, resolution: str, station_id: str
    ) -> pl.DataFrame:
        """Check if there is data available in higher resolution"""

        if self.location is None or self.time_span is None:
            raise ValueError

        res_op = list(cont.DWD_RESOLUTION_OPTIONS.values())
        higher_resolutions: list[str] = [
            res_op[ind]
            for ind in range(res_op.index(resolution), -1, -1)
            if res_op[ind] in self.available_resolutions
        ]
        values = pl.DataFrame()
        for res in higher_resolutions:
            logger.debug(f"checking '{res}'")
            request_higher = DwdObservationRequest(
                parameter=self.name_en,
                resolution=res,
                start_date=self.time_span.start,
                end_date=self.time_span.end,
                settings=cont.WETTERDIENST_SETTINGS,
            )

            values_higher: pl.DataFrame = (
                request_higher.filter_by_station_id(station_id)  # noqa: PD011
                .values.all()
                .df
            )
            if not values_higher.is_empty():
                values_change = dfm.change_temporal_resolution(
                    values_higher.select([pl.col("date"), pl.col("value")]),
                    {"value": self.unit},
                    next(
                        res.polars
                        for res in cont.TIME_RESOLUTIONS.values()
                        if res.dwd == resolution
                    ),
                )
                values = values.with_columns(
                    [
                        values_change["date"].alias("date"),
                        values_change["value"].alias("value"),
                    ]
                )
                break
        return values

    def check_time_distance(
        self, station_id: str, all_stations: pl.DataFrame, start_time: float
    ) -> str | None:
        """Check if a station has data

        Returns:
            - None if below time and distance threshold
            - str if threshold reached
        """

        logger.info(f"checking station id '{station_id}'")
        no_data: str | None = None
        distance: float = all_stations.filter(
            pl.col("station_id") == station_id
        ).get_column("distance")[0]

        if distance > cont.DWD_QUERY_DISTANCE_LIMIT:
            no_data = (
                "In einem Umkreis von "
                f"{cont.DWD_QUERY_DISTANCE_LIMIT} km um den gegebenen Standort "
                "konnten keine Daten für den Parameter "
                f"**{self.name_de}** gefunden werden."
            )
            logger.critical(
                gf.string_new_line_per_item(
                    [
                        "Distance limit reached.",
                        f"No data found within {cont.DWD_QUERY_DISTANCE_LIMIT} km.",
                    ],
                    leading_empty_lines=1,
                )
            )

        exe_time: float = time.monotonic() - start_time
        if exe_time > cont.DWD_QUERY_TIME_LIMIT:
            no_data = (
                "Es konnten innerhalb eines Zeitlimits von "
                f"{cont.DWD_QUERY_TIME_LIMIT} Sekunden "
                f"keine Daten für den Parameter **{self.name_de}** gefunden werden."
            )

            logger.critical(
                gf.string_new_line_per_item(
                    [
                        "Time limit reached.",
                        f"No data found within {cont.DWD_QUERY_TIME_LIMIT} s.",
                    ],
                    leading_empty_lines=1,
                )
            )

        return no_data


@dataclass
class DWDParameter:
    """Properties of DWD Parameter"""

    name: str
    available_resolutions: list[str]
    unit: str
    name_de: str | None = None
    location_lat: float | None = None
    location_lon: float | None = None
    resolution: str | None = None
    resolution_de: str | None = None
    data_frame: pl.DataFrame | None = None
    all_stations: pl.DataFrame | None = None
    closest_station: DWDStation = field(init=False)
    num_format: str = field(init=False)
    pandas_styler: str = field(init=False)

    def __post_init__(self) -> None:
        """Fill in fields"""
        self.num_format = f'#,##0.0" {self.unit.strip()}"'
        self.pandas_styler = "{:,.1f} " + self.unit
        self.closest_station = DWDStation()

    def station_info_from_station_df_and_id(self, station_id: str) -> None:
        """Fill in the station information from the station data frame"""

        if self.all_stations is not None:
            station_df: pl.DataFrame = self.all_stations.filter(
                pl.col("station_id") == station_id
            )
            if station_df.height == 1:
                self.closest_station = DWDStation(
                    station_id=station_df[0, "station_id"],
                    name=station_df[0, "name"],
                    height=station_df[0, "height"],
                    latitude=station_df[0, "latitude"],
                    longitude=station_df[0, "longitude"],
                    distance=station_df[0, "distance"],
                    state=station_df[0, "state"],
                )
