"""Classes and such"""

import time
from dataclasses import dataclass, field
from datetime import datetime as dt
from typing import Literal

import polars as pl
from wetterdienst.provider.dwd.observation import DwdObservationRequest

from modules import classes_constants as clc
from modules import constants as cont
from modules import general_functions as gf
from modules import meteorolog as met
from modules import streamlit_functions as sf


@dataclass
class GitCommit:
    """Github commit message for the page header"""

    date: dt | str
    major: str
    minor: str

    def write_all_to_session_state(self) -> None:
        """Put all collected Commit information into st_session_state"""
        for attr in self.__dataclass_fields__:
            sf.s_set(f"GitCommit_{attr}", getattr(self, attr))


@dataclass
class TimeSpan:
    """Start- und Endzeit"""

    start: dt
    end: dt


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

    all_stations: pl.DataFrame
    closest_station: DWDStation
    data: pl.DataFrame


@dataclass
class DWDParam:
    """DWD Parameter"""

    name_en: str
    available_resolutions: list[str]
    unit: str
    name_de: str | None = None
    location: Location | None = None
    time_span: TimeSpan | None = None

    res_minute_1: DWDResData | None = None
    res_minute_5: DWDResData | None = None
    res_minute_10: DWDResData | None = None
    res_hourly: DWDResData | None = None
    res_6_hour: DWDResData | None = None
    res_subdaily: DWDResData | None = None
    res_daily: DWDResData | None = None
    res_monthly: DWDResData | None = None
    res_annal: DWDResData | None = None

    def fill_resolutions(self) -> None:
        """Get data for available resolutions"""

        for res in cont.DWD_RESOLUTION_OPTIONS.values():
            if res in self.available_resolutions:
                setattr(self, f"res_{res}", self.get_data(res))

    def get_data(self, resolution: str) -> DWDResData:
        """Get the values for every available resolution
        from the closest station that has data.
        """
        if self.location is None or self.time_span is None:
            raise ValueError

        request = DwdObservationRequest(
            parameter=self.name_en,
            resolution=resolution,
            start_date=self.time_span.start,
            end_date=self.time_span.end,
            settings=met.WETTERDIENST_SETTINGS,
        )

        all_stations: pl.DataFrame = request.filter_by_distance(
            latlon=(self.location.latitude, self.location.longitude),
            distance=cont.WEATHERSTATIONS_MAX_DISTANCE,
        ).df

        closest_station: DWDStation = DWDStation()

        data_frame: pl.DataFrame = pl.DataFrame()
        start_time: float = time.monotonic()
        max_time: float = cont.DWD_QUERY_TIME_LIMIT
        for station_id in all_stations.get_column("station_id"):
            exe_time: float = time.monotonic() - start_time
            while exe_time < max_time:
                values: pl.DataFrame = (
                    request.filter_by_station_id(station_id)  # noqa: PD011
                    .values.all()
                    .df
                )
                if not values.is_empty():
                    data_frame = values
                    closest_station_df: pl.DataFrame = all_stations.filter(
                        pl.col("station_id") == station_id
                    )
                    closest_station = DWDStation(
                        station_id=station_id,
                        name=pl.first(closest_station_df.get_column("name")),
                        state=pl.first(closest_station_df.get_column("state")),
                        height=pl.first(closest_station_df.get_column("height")),
                        latitude=pl.first(closest_station_df.get_column("latitude")),
                        longitude=pl.first(closest_station_df.get_column("longitude")),
                        distance=pl.first(closest_station_df.get_column("distance")),
                    )

        return DWDResData(
            all_stations=all_stations, closest_station=closest_station, data=data_frame
        )


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
