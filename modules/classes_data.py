"""Classes and such"""

from dataclasses import dataclass
from datetime import datetime as dt
from typing import Literal

import polars as pl

from modules import classes_constants as clc
from modules import general_functions as gf


@dataclass
class TimeSpan:
    """Start- und Endzeit"""

    start: dt
    end: dt


@dataclass
class DWDParameter:
    """Properties of DWD Parameter"""

    name: str
    available_resolutions: list[str]
    unit: str
    closest_station_id: str | None = None
    resolution: str | None = None
    data_frame: pl.DataFrame | None = None


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
