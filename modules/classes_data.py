"""Classes and such"""

import datetime as dt
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Self

import polars as pl
import toml
from geopy.geocoders import Nominatim
from loguru import logger

from modules import classes_constants as clc
from modules import classes_errors as cle
from modules import constants as cont
from modules import general_functions as gf

if TYPE_CHECKING:
    import geopy


@dataclass
class TimeSpan:
    """Start- und Endzeit"""

    start: dt.datetime
    end: dt.datetime


@dataclass
class Location:
    """Location data

    Attributes:
        address (str | None): The address of the location.
        latitude (float | None): The latitude coordinate of the location.
        longitude (float | None): The longitude coordinate of the location.
        altitude (float | None): The altitude of the location.
        attr_size (float | None): Additional attribute for size.
        attr_colour (float | None): Additional attribute for color.
        name (str | None): The name of the location.
        address_geopy (str | None): The address obtained from geopy.
        street (str | None): The street name of the location.
        house_number (int | None): The house number of the location.
        post_code (int | None): The postal code of the location.
        city (str | None): The city of the location.
        suburb (str | None): The suburb of the location.
        country (str | None): The country of the location.

    Methods:
        fill_using_geopy() -> Self:
            Retrieves location data based on the provided address or coordinates.
            loc = Location("Bremen").fill_using_geopy()

        from_address(address: str | None) -> Self:
            Retrieves location data based on the given address.
            loc = Location().from_address("Bremen")

        from_coordinates(latitude: float | None, longitude: float | None) -> Self:
            Retrieves location data based on the given latitude and longitude.
            loc = Location().from_coordinates(53.0758196, 8.8071646)

        get_data(location: tuple[float, float] | str) -> None:
            Fetches the location data using the geopy library. (used internally)
    """

    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    altitude: float | None = None
    attr_size: float | None = None
    attr_colour: float | None = None
    name: str | None = None
    address_geopy: str | None = None
    street: str | None = None
    house_number: int | None = None
    post_code: int | None = None
    city: str | None = None
    suburb: str | None = None
    country: str | None = None

    def fill_using_geopy(self) -> Self:
        """Retrieves location data based on the provided address or coordinates.

        Returns:
            Location
        Example:
            loc = Location("Bremen").fill_using_geopy()
            loc = Location(latitude: 53.075819, longitude: 8.807164).fill_using_geopy()
        """

        if all(
            [
                isinstance(self.address, str),
                isinstance(self.latitude, float),
                isinstance(self.longitude, float),
            ]
        ):
            logger.critical("Too much information - Address and Coordinates given!")
            raise ValueError

        if isinstance(self.address, str):
            self.get_data(self.address)
            logger.info("Location data collected from given address.")

        elif isinstance(self.latitude, float) and isinstance(self.longitude, float):
            self.get_data((self.latitude, self.longitude))
            logger.info("Location data collected from given coordinates")

        return self

    def from_address(self, address: str | None) -> Self:
        """Retrieves location data from a given address.
        The address can either be given as attribute of this function
        or taken from self.address.

        Returns:
            Location
        Example:
            loc = Location().from_address("Bremen")
            loc = Location("Bremen").from_address()
        """
        if isinstance(address, str):
            self.address = address
        if not isinstance(self.address, str):
            raise TypeError
        self.get_data(self.address)

        return self

    def from_coordinates(self, latitude: float | None, longitude: float | None) -> Self:
        """Get location data from given coordinates.
        The coordinates can either be given as attribute of this function
        or taken from self.latitude and self.longitude respectively.

        Returns:
            Location
        Example:
            loc = Location().from_coordinates(53.075819, 8.807164)
            loc = Location(latitude: 53.075819, longitude: 8.807164).from_coordinates()
        """
        if isinstance(latitude, float) and isinstance(longitude, float):
            self.latitude = latitude
            self.longitude = longitude

        if not isinstance(self.latitude, float) or not isinstance(
            self.longitude, float
        ):
            raise TypeError
        self.get_data((self.latitude, self.longitude))

        return self

    def get_data(self, location: tuple[float, float] | str) -> None:
        """Fetches the location data using the geopy library. (used internally)"""

        user_agent_secret: str | None = os.environ.get(
            "GEO_USER_AGENT", toml.load(".streamlit/secrets.toml").get("GEO_USER_AGENT")
        )

        if user_agent_secret is None:
            raise cle.NotFoundError(entry="GEO_USER_AGENT", where="Secrets")

        geolocator: Nominatim = Nominatim(user_agent=user_agent_secret)

        if isinstance(location, str):
            query = geolocator.geocode(location, exactly_one=True).point  # type: ignore
        elif isinstance(location, tuple):
            query = location
        else:
            raise TypeError

        geopy_loc: geopy.Location = geolocator.reverse(
            query=query,
            exactly_one=True,
            addressdetails=True,
        )  # type: ignore
        addr: dict = geopy_loc.raw["address"]

        self.latitude = geopy_loc.latitude
        self.longitude = geopy_loc.longitude
        self.address_geopy = geopy_loc.address
        self.street = addr.get("road", "unbekannt")
        self.city = addr.get("city")
        self.suburb = addr.get("suburb")
        self.country = addr.get("country")

        geopy_hn = addr.get("house_number")
        if isinstance(geopy_hn, int):
            self.house_number = geopy_hn
        elif isinstance(geopy_hn, str) and geopy_hn.isnumeric():
            self.house_number = int(geopy_hn)
        else:
            self.house_number = None

        geopy_pc = addr.get("postcode")
        if isinstance(geopy_pc, int):
            self.post_code = geopy_pc
        elif isinstance(geopy_pc, str) and geopy_pc.isnumeric():
            self.post_code = int(geopy_pc)
        else:
            self.post_code = None


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
    location: Location | None = None

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
