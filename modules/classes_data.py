"""Classes and such"""

import datetime as dt
import time
from dataclasses import dataclass, field
from typing import Literal

import polars as pl
from loguru import logger
from wetterdienst.provider.dwd.observation import DwdObservationRequest

from modules import classes_constants as clc
from modules import constants as cont
from modules import general_functions as gf
from modules import streamlit_functions as sf


@dataclass
class GitCommit:
    """Github commit message for the page header"""

    date: dt.datetime | str
    major: str
    minor: str

    def write_all_to_session_state(self) -> None:
        """Put all collected Commit information into st_session_state"""
        for attr in self.__dataclass_fields__:
            sf.s_set(f"GitCommit_{attr}", getattr(self, attr))


@dataclass
class TimeSpan:
    """Start- und Endzeit"""

    start: dt.datetime
    end: dt.datetime


@dataclass
class Location:
    """Location data"""

    name: str | None
    latitude: float
    longitude: float
    attr_size: float | None = None
    attr_colour: float | None = None


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
    closest_station: DWDStation | None = None
    data: pl.DataFrame | None = None
    no_data: str | None = "No Data Available"


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
        self.name_de = cont.DWD_PARAM_TRANSLATION.get(self.name_en, "unbekannt")

    def fill_all_resolutions(self) -> None:
        """Get data for available resolutions"""

        for res in self.resolutions.list_all_res_names_en():
            if res in self.available_resolutions:
                att_dic: dict = self.get_data(res)
                for key, value in att_dic.items():
                    setattr(getattr(self.resolutions, res), key, value)

    def fill_specific_resolution(self, resolution: str) -> None:
        """Get data for a chosen resolution"""
        res: str = cont.DWD_RESOLUTION_OPTIONS.get(resolution) or resolution
        if res not in self.available_resolutions:
            return

        att_dic: dict = self.get_data(res)
        for key, value in att_dic.items():
            setattr(getattr(self.resolutions, res), key, value)

    def get_data(self, resolution: str) -> dict:
        """Get the values for every available resolution
        from the closest station that has data.
        """
        if self.location is None or self.time_span is None:
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

            values = (
                request.filter_by_station_id(station_id).values.all().df  # noqa: PD011
            )

            if not values.is_empty():
                data_frame = values
                closest_station_df: pl.DataFrame = all_stations.filter(
                    pl.col("station_id") == station_id
                )

                for key in DWDStation.__dataclass_fields__:
                    value: str | float = (
                        station_id
                        if key == "station_id"
                        else pl.first(closest_station_df.get_column(key))
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

    def check_time_distance(
        self, station_id: str, all_stations: pl.DataFrame, start_time: float
    ) -> str | None:
        """Check if a station has data"""
        logger.info(f"checking station id '{station_id}'")
        no_data: str | None = None
        distance: float = pl.first(
            all_stations.filter(pl.col("station_id") == station_id).get_column(
                "distance"
            )
        )

        if distance > cont.DWD_QUERY_DISTANCE_LIMIT:
            no_data = (
                "In einem Umkreis von "
                f"{cont.DWD_QUERY_DISTANCE_LIMIT} km "
                "konnten keine Daten gefunden werden."
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
            no_data = "Es konnten in angemessener Zeit keine Daten gefunden werden."

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


@dataclass
class MetaLine:
    """Class for meta data of lines (traces)

    Line for testing:
    line = MetaLine(
      "test", "test_org", "Org Title", "Title", obis=clc.ObisElectrical("1-1:1.29.0")
    )
    """

    name: str
    name_orgidx: str
    orig_tit: str
    tit: str
    unit: str | None = None
    unit_h: str | None = None
    obis: clc.ObisElectrical | None = None
    excel_number_format: str | None = None

    def as_dic(self) -> dict:
        """Dictionary representation"""
        return {
            attr: getattr(self, attr).as_dic()
            if isinstance(getattr(self, attr), clc.ObisElectrical)
            else getattr(self, attr)
            for attr in self.__dataclass_fields__
        }

    def __repr__(self) -> str:
        """Customize the representation to give a dictionary"""
        return f"[{gf.string_new_line_per_item(self.as_dic())}]"


@dataclass
class MetaData:
    """Meta Daten

    Attrs:
        - lines (dict[str,MetaLine]): Dictionary aller Linien (Spalten).
            Dictionary key ist der Linienname.
        - datetime (bool): Ob eine Spalten mit Zeiten gefunden wurde
        - years (list[int]): Liste der Jahre, für die Daten vorliegen
        - multi_years (bool): Ob Daten für mehrere Jahre vorliegen
        - td_mnts (int): Zeitliche Auflösung der Daten in Minuten
        - td_interval (str): "h" bei stündlichen Daten, "15min" bei 15-Minuten-Daten
    """

    lines: dict[str, MetaLine]
    datetime: bool = False
    years: list[int] | None = None
    multi_years: bool | None = None
    td_mnts: int | None = None
    td_interval: str | None = None

    def as_dic(self) -> dict:
        """Dictionary representation"""
        return {
            attr: {name: line.as_dic() for name, line in self.lines.items()}
            if attr == "lines"
            else getattr(self, attr)
            for attr in self.__dataclass_fields__
        }

    def __repr__(self) -> str:
        """Customize the representation to give a dictionary"""
        return f"[{gf.string_new_line_per_item(self.as_dic())}]"

    def all_units_as_dict(self) -> dict:
        """Dictionary (key=name, value=unit)"""
        return {line.name: line.unit for line in self.lines.values()}

    def copy_line(self, line_to_copy: str, new_line_name: str) -> MetaLine:
        """Create a MetaLine-object with the same attrs under a new name"""

        new_line = MetaLine(
            new_line_name,
            f"{new_line_name}{cont.SUFFIXES.col_original_index}"
            if cont.SUFFIXES.col_original_index not in new_line_name
            else new_line_name,
            new_line_name,
            new_line_name,
        )
        for attr in self.lines[line_to_copy].as_dic():
            if getattr(new_line, attr) is None:
                setattr(new_line, attr, getattr(self.lines[line_to_copy], attr))
        return new_line


@dataclass
class MetaAndDfs:
    """Class to combine data frames and the corresponding meta data

    Attrs:
        - meta (MetaData): Meta Data
        - df (pl.DataFrame): main data frame imported from excel file
        - df_h (pl.DataFrame | None): df in hourly resolution
        - jdl (pl.DataFrame | None): Jahresdauerlinie
        - mon (pl.DataFrame | None): monthly data
        - df_multi (dict[int, pl.DataFrame] | None): grouped by year
        - df_h_multi (dict[int, pl.DataFrame] | None): grouped by year
        - mon_multi (dict[int, pl.DataFrame] | None): grouped by year
    """

    meta: MetaData
    df: pl.DataFrame
    df_h: pl.DataFrame | None = None
    jdl: pl.DataFrame | None = None
    mon: pl.DataFrame | None = None
    df_multi: dict[int, pl.DataFrame] | None = None
    df_h_multi: dict[int, pl.DataFrame] | None = None
    mon_multi: dict[int, pl.DataFrame] | None = None

    def get_lines_in_multi_df(
        self, df: Literal["df_multi", "df_h_multi", "mon_multi"] = "df_multi"
    ) -> list[str]:
        """Get all lines in the multi-year data frame"""

        lines: list[str] = []
        df_dic: dict[int, pl.DataFrame] = getattr(self, df)
        if not isinstance(df_dic, dict):
            raise TypeError

        if self.meta.years:
            for year in self.meta.years:
                df_year: pl.DataFrame | None = df_dic.get(year)
                if df_year is None:
                    raise TypeError
                lines.extend(
                    [col for col in df_year.columns if gf.check_if_not_exclude(col)]
                )

        return lines

    def as_dic(self) -> dict:
        """Dictionary representation"""
        return {attr: getattr(self, attr) for attr in self.__dataclass_fields__}
