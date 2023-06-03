"""Classes and such"""

import pprint
from dataclasses import dataclass, field
from math import ceil
from typing import Any

import numpy as np
import plotly.graph_objects as go
import polars as pl

import modules.constants as cont


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
    obis: cont.ObisElectrical | None = None
    excel_number_format: str | None = None

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

    def get_all_num_formats(self) -> list[str]:
        """Get the Excel number formats for all lines"""
        return [(line.excel_number_format or "#.##0,0") for line in self.lines]

    def change_line_attribute(
        self, line_name: str, attribute: str, new_value: Any
    ) -> None:
        """Change the value of a specific attribute for a line (trace)"""
        for line in self.lines:
            if line.name == line_name:
                setattr(line, attribute, new_value)
                return
        raise LineNotFoundError(line_name)


@dataclass
class MetaAndDfs:
    """Class to combine data frames and the corresponding meta data"""

    meta: MetaData
    df: pl.DataFrame
    jdl: pl.DataFrame | None = None
    mon: pl.DataFrame | None = None
    df_multi: dict[int, pl.DataFrame] | None = None
    jdl_multi: dict[int, pl.DataFrame] | None = None
    mon_multi: dict[int, pl.DataFrame] | None = None


# ------ ↓ Vielleicht zukünftig ↓ --------


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
