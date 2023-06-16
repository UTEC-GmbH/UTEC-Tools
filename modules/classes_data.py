"""Classes and such"""

import pprint
from dataclasses import dataclass
from typing import Any, Literal

import polars as pl

from modules import classes_constants as clc
from modules import classes_errors as cle
from modules import constants as cont
from modules import general_functions as gf


@dataclass
class MetaLine:
    """Class for meta data of lines (traces)"""

    name: str
    name_orgidx: str
    orig_tit: str
    tit: str
    unit: str | None = None
    unit_h: str | None = None
    obis: clc.ObisElectrical | None = None
    excel_number_format: str | None = None

    def __repr__(self) -> str:
        """Customize the representation to give a dictionary"""
        return pprint.pformat(vars(self), sort_dicts=False)


@dataclass
class MetaData:
    """Meta Daten

    Attrs:
        - lines (list[MetaLine]): Liste aller Linien (Spalten)
        - datetime (bool): Ob eine Spalten mit Zeiten gefunden wurde
        - years (list[int]): Liste der Jahre, für die Daten vorliegen
        - multi_years (bool): Ob Daten für mehrere Jahre vorliegen
        - td_mnts (int): Zeitliche Auflösung der Daten in Minuten
        - td_interval (str): "h" bei stündlichen Daten, "15min" bei 15-Minuten-Daten
    """

    lines: list[MetaLine]
    datetime: bool = False
    years: list[int] | None = None
    multi_years: bool | None = None
    td_mnts: int | None = None
    td_interval: str | None = None

    def __repr__(self) -> str:
        """Customize the representation to give a dictionary"""
        return pprint.pformat(vars(self))

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

    def copy_line_meta_with_new_name(self, old_name: str, new_name: str) -> None:
        """Add an entry in the list of lines in the meta data
        by copying the meta data of a line and giving it a new name"""

        old_line: MetaLine = self.get_line_by_name(old_name)
        new_line: MetaLine = MetaLine(**vars(old_line))
        new_line.name = new_name
        new_line.tit = new_name
        new_line.name_orgidx = (
            f"{new_name}{cont.SUFFIXES.col_original_index}"
            if cont.SUFFIXES.col_original_index not in new_name
            else new_name
        )
        self.lines += [new_line]

    def as_dict(self) -> dict[str, Any]:
        """Get all MetaData as a dictionary"""
        lines: list[dict] = []
        for line in self.lines:
            dic: dict = {}
            for key, val in vars(line).items():
                dic[key] = vars(val) if isinstance(val, clc.ObisElectrical) else val
                lines.append(dic)

        return {
            "lines": lines,
            "datetime": self.datetime,
            "years": self.years,
            "multi_years": self.multi_years,
            "td_mnts": self.td_mnts,
            "td_interval": self.td_interval,
        }


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
        df_multi: dict[int, pl.DataFrame] = getattr(self, df)
        if not isinstance(df_multi, dict):
            raise TypeError

        if self.meta.years:
            for year in self.meta.years:
                lines.extend(
                    [
                        col
                        for col in df_multi[year].columns
                        if gf.check_if_not_exclude(col)
                    ]
                )

        return lines
