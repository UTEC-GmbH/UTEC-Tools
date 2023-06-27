"""Classes and such for Figs"""

from dataclasses import dataclass, field
from math import ceil
from typing import Any

import numpy as np
import plotly.graph_objects as go
from loguru import logger

from modules import fig_formatting as fform
from modules import general_functions as gf


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
class FigProp:
    """Calss to hold plotly figure properties"""

    fig: go.Figure
    st_key: str
    data: FigData | None = None
    layout: FigLayout | None = None
    annos: FigAnno | None = None

    def update_fig(self) -> None:
        """Update a figure (after settings in main window)"""
        self.fig = fform.update_main(self.fig)


@dataclass
class Figs:
    """Class to hold plotly figures"""

    base: FigProp | None = None
    jdl: FigProp | None = None
    mon: FigProp | None = None
    days: FigProp | None = None

    def list_all_figs(self) -> list[FigProp]:
        """Get a list of all figs as custom types"""
        return [
            getattr(self, fig)
            for fig in self.__dataclass_fields__
            if getattr(self, fig)
        ]

    def write_all_to_st(self) -> None:
        """Write all figs to streamlit"""
        gf.st_set("figs", self)
        if valid_figs := self.list_all_figs():
            logger.debug(
                f"figs with data: "
                f"{[fig.st_key for fig in valid_figs if fig is not None]}"
            )
            for fig in valid_figs:
                gf.st_set(fig.st_key, fig.fig)

    def update_all_figs(self) -> None:
        """Update all figs"""
        if valid_figs := self.list_all_figs():
            logger.debug(
                f"figs with data: "
                f"{[fig.st_key for fig in valid_figs if fig is not None]}"
            )
            for fig in valid_figs:
                fig.update_fig()
