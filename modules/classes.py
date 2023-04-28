"""Classes and such"""

import re
from dataclasses import dataclass, field
from enum import Enum
from math import ceil
from typing import Any, Dict, List, NamedTuple, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from loguru import logger

from modules.constants import OBIS_ELECTRICAL, ObisDic


class MarkerPosition(NamedTuple):
    """Named Tuple for return value of function in following class"""

    row: int
    col: int


class MarkerType(Enum):
    """Enum for marker_type in following class"""

    INDEX = "index"
    UNITS = "units"


@dataclass(frozen=True)
class LevelProperties:
    """Logger Levels"""

    name: str
    custom: bool = False
    icon: str = "👉👈"
    time: str = "{time:HH:mm:ss}"
    info: str = "{module} -> {function} -> line: {line} | "
    blank_lines_before: int = 0
    blank_lines_after: int = 0

    def get_format(self) -> str:
        """Logger message Format erzeugen"""
        nl_0: str = "\n" * self.blank_lines_before
        nl_1: str = "\n" * (self.blank_lines_after + 1)
        info: str = self.info
        time: str = self.time
        if len(self.icon) == 2:
            ic_0: str = self.icon[0]
            ic_1: str = self.icon[1]
        else:
            ic_0: str = self.icon
            ic_1: str = ic_0
        return f"{nl_0}{time} {ic_0} {info}{{message}} {ic_1} {nl_1}"


@dataclass
class LogLevel:
    """Logger Format"""

    INFO: LevelProperties = LevelProperties("INFO", icon="💡")
    DEBUG: LevelProperties = LevelProperties("DEBUG", icon="🐞")
    ERROR: LevelProperties = LevelProperties("ERROR", icon="😱")
    SUCCESS: LevelProperties = LevelProperties("SUCCESS", icon="🥳")
    WARNING: LevelProperties = LevelProperties("WARNING", icon="⚠️")
    CRITICAL: LevelProperties = LevelProperties("CRITICAL", icon="☠️")
    START: LevelProperties = LevelProperties(
        "START",
        icon="🔥🔥🔥",
        custom=True,
        info="",
        blank_lines_before=2,
        blank_lines_after=1,
    )
    TIMER: LevelProperties = LevelProperties("TIMER", icon="⏱", custom=True, info="")
    NEW_RUN: LevelProperties = LevelProperties(
        "NEW_RUN",
        icon="✨",
        custom=True,
        info="",
        blank_lines_before=2,
    )
    FUNC_START: LevelProperties = LevelProperties(
        "FUNC_START", icon="👉👈", custom=True, info="", blank_lines_before=1
    )
    DATA_FRAME: LevelProperties = LevelProperties(
        "DATA_FRAME",
        custom=True,
        icon="",
        time="",
        info="",
        blank_lines_after=1,
    )
    ONCE_PER_RUN: LevelProperties = LevelProperties(
        "ONCE_PER_RUN", icon="👟", custom=True
    )
    ONCE_PER_SESSION: LevelProperties = LevelProperties(
        "ONCE_PER_SESSION",
        icon="🦤🦤🦤",
        custom=True,
        info="",
        blank_lines_before=1,
        blank_lines_after=1,
    )


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
            logger.critical("Kein gültiger Marker Typ!")
            raise ValueError("Kein gültiger Marker Typ!")

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
        marker_position: Tuple = np.where(df == self.marker_string)
        if any([len(marker_position[0]) < 1, len(marker_position[1]) < 1]):
            raise ValueError(self.error_not_found)
        if any([len(marker_position[0]) > 1, len(marker_position[1]) > 1]):
            raise ValueError(self.error_multiple)

        logger.success(
            f"Marker {self.marker_string} found in row {marker_position[0][0]}, column {marker_position[1][0]}"
        )

        return MarkerPosition(row=marker_position[0][0], col=marker_position[1][0])


@dataclass
class ObisElectrical:
    """OBIS-Codes für elektrische Zähler


    Raises:
        - ValueError: Falls der Code nicht mit '1' anfängt, ist es kein Code für eletrische Zähler.
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

    def __post_init__(self) -> None:
        """Check if code is valid and fill in the fields"""
        pat_match: re.Match[str] | None = re.search(self.pattern, self.code_or_name)
        if pat_match is None:
            logger.critical("Kein gültiger OBIS-Code")
            raise ValueError("Kein gültiger OBIS-Code für elektrische Zähler!")
        self.code = pat_match[0]
        code_r: str = self.code.replace(":", "-").replace(".", "-").replace("~*", "-")
        code_l: List[str] = code_r.split("-")
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
        """fill in the fields"""
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


# todo: change
@dataclass(kw_only=False)
class FigData:
    """change"""

    fig: go.Figure
    trace_names: List[str] = field(init=False)
    traces: Dict[str, FigTrace] = field(init=False)

    def __post_init__(self) -> None:
        """fill in the fields"""

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
    colorway: List[str] = field(init=False)
    layout: Dict[str, Any] = field(init=False)
    meta: Dict = field(init=False)
    title: str = field(init=False)

    def __post_init__(self) -> None:
        """fill in the fields"""

        self.layout = {item: self.fig.layout[item] for item in self.fig.layout}

        self.title = self.fig.layout["title"]["text"]

        self.meta = self.fig.layout["meta"]

        colorway: List[str] = list(self.fig.layout["template"]["layout"]["colorway"])
        if len(colorway) < len(list(self.fig.data)):
            colorway *= ceil(len(list(self.fig.data)) / len(colorway))

        self.colorway = colorway


@dataclass(kw_only=False)
class FigAnno:
    """change"""

    fig: go.Figure
    anno_name: str
