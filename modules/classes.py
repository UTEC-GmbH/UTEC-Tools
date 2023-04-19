"""Classes and such"""

import re
from dataclasses import dataclass, field
from math import ceil
from typing import Any, List, Dict

import numpy as np
import plotly.graph_objects as go
from loguru import logger

from modules.constants import OBIS_ELECTRICAL, ObisDic


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
