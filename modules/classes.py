"""Classes and such"""

import pprint
import re
from dataclasses import dataclass, field
from enum import Enum
from math import ceil
from typing import Any, NamedTuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from loguru import logger

from modules.constants import OBIS_ELECTRICAL, ObisDic


class LineNotFoundError(Exception):
    """Error Message if Line not found (e.g. change_line_attribute)"""

    def __init__(self, line_name: str) -> None:
        """Initiate"""
        super().__init__(f"Line '{line_name}' not found.")


class MultipleLinesFoundError(Exception):
    """Error Message if multiple lines were found (e.g. get_line_by_name)"""

    def __init__(self, line_name: str) -> None:
        """Initiate"""
        super().__init__(f"Multiple lines with name '{line_name}' found.")


class MarkerPosition(NamedTuple):
    """Named Tuple for return value of function in following class"""

    row: int
    col: int


class MarkerType(Enum):
    """Enum for marker_type in following class"""

    INDEX = "index"
    UNITS = "units"


@dataclass
class ExcelMarkers:
    """Name of Markers for Index and Units in the Excel-File"""

    marker_type: MarkerType
    marker_string: str = field(init=False)
    error_not_found: str = field(init=False)
    error_multiple: str = field(init=False)

    def __post_init__(self) -> None:
        """Check if code is valid and fill in the fields"""

        if self.marker_type not in MarkerType:
            err_msg: str = "Kein gültiger Marker Typ!"
            logger.critical(err_msg)
            raise ValueError(err_msg)

        self.marker_string = (
            "↓ Index ↓" if self.marker_type == MarkerType.INDEX else "→ Einheit →"
        )
        self.error_not_found = (
            f"Marker {self.marker_string} not found in the DataFrame."
        )
        self.error_multiple = (
            f"Multiple Markers {self.marker_string} found in the DataFrame."
        )

    def get_marker_position(self, df: pd.DataFrame) -> MarkerPosition:
        """Get the row- and column-number of the marker in the DataFrame.


        Args:
            - df (pd.DataFrame): DataFrame to search in

        Raises:
            - ValueError: If marker can't be found or is found multiple times

        Returns:
            - MarkerPosition: row (int), col (int)
        """
        pos: tuple = np.where(df == self.marker_string)
        logger.debug(pos)
        if any([len(pos[0]) < 1, len(pos[1]) < 1]):
            logger.error(self.error_not_found)
            if self.marker_type == MarkerType.UNITS:
                pos = np.where(df == "↓ Index ↓")
                pos[0][0] = max(pos[0][0] - 1, 0)

        if any([len(pos[0]) > 1, len(pos[1]) > 1]):
            raise ValueError(self.error_multiple)

        logger.success(
            f"Marker {self.marker_string} found in row {pos[0][0]}, column {pos[1][0]}"
        )

        return MarkerPosition(row=pos[0][0], col=pos[1][0])


@dataclass
class ObisElectrical:
    """OBIS-Codes für elektrische Zähler.

    Raises
        - ValueError: Falls der Code nicht mit '1' anfängt,
            ist es kein Code für eletrische Zähler.
    """

    code_or_name: str
    pattern: str = r"1-\d*:\d*\.\d*"
    code: str = field(init=False)
    medium: str = "Elektrizität"
    messgroesse: str = field(init=False)
    messart: str = field(init=False)
    unit: str = field(init=False)
    name: str = field(init=False)
    name_kurz: str = field(init=False)
    name_lang: str = field(init=False)

    def __repr__(self) -> str:
        """Customize the representation to give a dictionary"""
        return pprint.pformat(vars(self), sort_dicts=False)

    def __post_init__(self) -> None:
        """Check if code is valid and fill in the fields"""
        pat_match: re.Match[str] | None = re.search(self.pattern, self.code_or_name)
        if pat_match is None:
            err_msg: str = "Kein gültiger OBIS-Code für elektrische Zähler!"
            logger.critical(err_msg)
            raise ValueError(err_msg)
        self.code = pat_match[0]
        code_r: str = self.code.replace(":", "-").replace(".", "-").replace("~*", "-")
        code_l: list[str] = code_r.split("-")
        code_messgr: str = code_l[2]
        code_messart: str = code_l[3]
        dic: ObisDic = OBIS_ELECTRICAL

        self.messgroesse = dic["messgroesse"][code_messgr]["bez"]
        self.messart = dic["messart"][code_messart]["bez"]
        self.unit = f' {dic["messgroesse"][code_messgr]["unit"]}'
        self.name = f'{dic["messgroesse"][code_messgr]["alt_bez"]} ({self.code})'
        self.name_kurz = dic["messgroesse"][code_messgr]["alt_bez"]
        self.name_lang = (
            f'{dic["messgroesse"][code_messgr]["bez"]} '
            f'[{dic["messgroesse"][code_messgr]["unit"]}] - '
            f'{dic["messart"][code_messart]["bez"]} ({self.code})'
        )


@dataclass(kw_only=True)
class FigTrace:
    """change"""

    fig: go.Figure
    trace_name: str
    x_vals: np.ndarray = field(init=False)
    y_vals: np.ndarray = field(init=False)
    visible: bool = field(init=False)
    mode: str = field(init=False)
    legendgroup: str = field(init=False)

    def __post_init__(self) -> None:
        """Fill in the fields"""
        trace: go.Scatter = go.Scatter()
        for dat in self.fig.data:
            if isinstance(dat, go.Scatter) and go.Scatter(dat).name == self.trace_name:
                trace = dat

        if isinstance(trace.x, np.ndarray):
            self.x_vals = trace.x

        if isinstance(trace.y, np.ndarray):
            self.y_vals = trace.y

        if isinstance(trace.visible, bool):
            self.visible = trace.visible

        if isinstance(trace.mode, str):
            self.mode = trace.mode

        if isinstance(trace.legendgroup, str):
            self.legendgroup = trace.legendgroup


@dataclass(kw_only=False)
class FigData:
    """change"""

    fig: go.Figure
    trace_names: list[str] = field(init=False)
    traces: dict[str, FigTrace] = field(init=False)

    def __post_init__(self) -> None:
        """Fill in the fields"""

        self.trace_names = [
            str(entry.name) for entry in self.fig.data if isinstance(entry, go.Scatter)
        ]

        self.traces = {
            trace: FigTrace(fig=self.fig, trace_name=trace)
            for trace in self.trace_names
        }


@dataclass(kw_only=False)
class FigLayout:
    """change"""

    fig: go.Figure
    colorway: list[str] = field(init=False)
    layout: dict[str, Any] = field(init=False)
    meta: dict = field(init=False)
    title: str = field(init=False)

    def __post_init__(self) -> None:
        """Fill in the fields"""

        self.layout = {item: self.fig.layout[item] for item in self.fig.layout}

        self.title = self.fig.layout["title"]["text"]

        self.meta = self.fig.layout["meta"]

        colorway: list[str] = list(self.fig.layout["template"]["layout"]["colorway"])
        if len(colorway) < len(list(self.fig.data)):
            colorway *= ceil(len(list(self.fig.data)) / len(colorway))

        self.colorway = colorway


@dataclass(kw_only=False)
class FigAnno:
    """change"""

    fig: go.Figure
    anno_name: str


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
    orig_tit: str
    tit: str
    unit: str | None = None
    y_axis: str = "y"
    obis: ObisElectrical | None = None

    def __repr__(self) -> str:
        """Customize the representation to give a dictionary"""
        return pprint.pformat(vars(self), sort_dicts=False)


@dataclass
class MetaData:
    """Class for meta data"""

    units: MetaUnits
    lines: list[MetaLine]
    datetime: bool = False
    years: list[int] | None = None
    td_mean: int | None = None
    td_interval: str | None = None

    def __repr__(self) -> str:
        """Customize the representation to give a dictionary"""
        return pprint.pformat(vars(self), sort_dicts=False)

    def get_line_by_name(self, line_name: str) -> MetaLine:
        """Get the line object from the string of the line name"""
        lines: list[MetaLine] = [line for line in self.lines if line.name == line_name]
        if not lines:
            raise LineNotFoundError(line_name)
        if len(lines) > 1:
            raise MultipleLinesFoundError(line_name)
        return lines[0]

    def get_all_line_names(self) -> list[str]:
        """Return a list of all line names"""
        return [line.name for line in self.lines]

    def change_line_attribute(
        self, line_name: str, attribute: str, new_value: Any
    ) -> None:
        """Change the value of a specific attribute for a line (trace)"""
        for line in self.lines:
            if line.name == line_name:
                setattr(line, attribute, new_value)
                return
        raise LineNotFoundError(line_name)
