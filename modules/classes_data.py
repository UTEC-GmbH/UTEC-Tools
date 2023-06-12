"""Classes and such"""

import pprint
from dataclasses import dataclass
from typing import Any

import polars as pl

import modules.classes_constants as cont
from modules import classes_errors as cle


@dataclass
class MetaUnits:
    """Class for meta data of units"""

    all_units: list[str]
    set_units: list[str]

    def __repr__(self) -> str:
        """Customize the representation to give a dictionary"""
        return pprint.pformat(vars(self), sort_dicts=False, compact=True)


@dataclass
class MetaLine:
    """Class for meta data of lines (traces)"""

    name: str
    name_orgidx: str
    orig_tit: str
    tit: str
    unit: str | None = None
    y_axis: str = "y"
    obis: cont.ObisElectrical | None = None
    excel_number_format: str | None = None

    def __repr__(self) -> str:
        """Customize the representation to give a dictionary"""
        return pprint.pformat(vars(self), sort_dicts=False)


@dataclass
class MetaData:
    """Meta Daten

    Attrs:
        - units (MetaUnits): Einheiten aller Linien -> Liste aller und set
        - lines (list[MetaLine]): Liste aller Linien (Spalten)
        - datetime (bool): Ob eine Spalten mit Zeiten gefunden wurde
        - years (list[int]): Liste der Jahre, für die Daten vorliegen
        - multi_years (bool): Ob Daten für mehrere Jahre vorliegen
        - td_mnts (int): Zeitliche Auflösung der Daten in Minuten
        - td_interval (str): "h" bei stündlichen Daten, "15min" bei 15-Minuten-Daten
    """

    units: MetaUnits
    lines: list[MetaLine]
    datetime: bool = False
    years: list[int] | None = None
    multi_years: bool | None = None
    td_mnts: int | None = None
    td_interval: str | None = None

    def __repr__(self) -> str:
        """Customize the representation to give a dictionary"""
        return pprint.pformat(vars(self), sort_dicts=False)

    def get_line_by_name(self, line_name: str) -> MetaLine:
        """Get the line object from the string of the line name"""
        lines: list[MetaLine] = [line for line in self.lines if line.name == line_name]
        if not lines:
            raise cle.LineNotFoundError(line_name)
        if len(lines) > 1:
            raise cle.MultipleLinesFoundError(line_name)
        return lines[0]

    def get_all_line_names(self) -> list[str]:
        """Return a list of all line names"""
        return [line.name for line in self.lines]

    def get_all_num_formats(self) -> list[str]:
        """Get the Excel number formats for all lines"""
        return [(line.excel_number_format or "#.##0,0") for line in self.lines]

    def get_line_attribute(self, line_name: str, attribute: str) -> Any:
        """Get the value of a specific attribute for a line (trace)"""
        for line in self.lines:
            if line.name == line_name:
                return getattr(line, attribute)
        raise cle.LineNotFoundError(line_name)

    def change_line_attribute(
        self, line_name: str, attribute: str, new_value: Any
    ) -> None:
        """Change the value of a specific attribute for a line (trace)"""
        for line in self.lines:
            if line.name == line_name:
                setattr(line, attribute, new_value)
                return
        raise cle.LineNotFoundError(line_name)


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
