"""Trying to figure out how to aling y = 0"""

from dataclasses import dataclass, field

import plotly.graph_objects as go

PLOTLY_INTERNAL_PADDING_FACTOR: float = 1 / 16

"""
given values:
y_min
y_max
y_padding_min
y_padding_max

y2_min
y2_max

values to find:
y2_padding_min
y2_padding_max

relation:
(0-y_min-y_padding_min)/(y_max+y_padding_max-y_min-y_padding_min) = 
(0-y2_min-y2_padding_min)/(y2_max+y2_padding_max-y2_min-y2_padding_min)

"""


@dataclass
class AxisRange:
    """Range of an axis"""

    data: list[float]
    min_value: float = field(init=False)
    max_value: float = field(init=False)
    padding_min: float = field(init=False)
    padding_max: float = field(init=False)
    min_range: float = field(init=False)
    max_range: float = field(init=False)
    range: list[float] = field(init=False)
    zero_position: float = field(init=False)

    def __post_init__(self) -> None:
        """Fill fields"""
        pipf: float = 1 / 16  # Plotly internal padding factor
        self.min_value = min(self.data)
        self.max_value = max(self.data)
        self.padding_min = (
            0 if self.min_value == 0 else abs(self.max_value - self.min_value) * pipf
        )
        self.padding_max = (
            0 if self.max_value == 0 else abs(self.max_value - self.min_value) * pipf
        )
        self.min_range = self.min_value - self.padding_min
        self.max_range = self.max_value + self.padding_max
        self.range = [self.min_range, self.max_range]
        self.zero_position = (0 - self.min_range) / (self.max_range - self.min_range)

    def range_from_given_padding(self, padding: float) -> None:
        """Calculate range with padding"""

        self.padding_min = 0 if self.min_value == 0 else padding
        self.padding_max = 0 if self.max_value == 0 else padding
        self.min_range = self.min_value - self.padding_min
        self.max_range = self.max_value + self.padding_max
        self.range = [self.min_range, self.max_range]
        self.zero_position = (0 - self.min_range) / (self.max_range - self.min_range)


@dataclass
class YRanges:
    """Ranges for y-axis"""

    y_range: AxisRange
    y2_range: AxisRange


def y_axis_ranges(fig: go.Figure) -> YRanges:
    """Finding the ranges in order to align y = 0

    https://stackoverflow.com/questions/76289470/plotly-barplot-with-two-y-axis-aligned-at-zero
    """
    fig_data: dict = {trace.get("name"): trace for trace in fig.to_dict()["data"]}

    data_y: list[float] = [
        value
        for tup in [val["y"] for val in fig_data.values() if val["yaxis"] == "y"]
        for value in tup
    ]

    y_range: AxisRange = AxisRange(data_y)

    data_y2: list[float] = [
        value
        for tup in [val["y"] for val in fig_data.values() if val["yaxis"] == "y2"]
        for value in tup
    ]

    y2_range: AxisRange = AxisRange(data_y2)

    if y_range.zero_position < y2_range.zero_position:
        y_padding: float = abs(
            (
                y2_range.zero_position * (y_range.max_range - y_range.min_range)
                + y_range.min_range
            )
            / (1 - 2 * y2_range.zero_position)
        )
        y_range.range_from_given_padding(y_padding)
    else:
        y2_padding: float = abs(
            (
                y_range.zero_position * (y2_range.max_range - y2_range.min_range)
                + y2_range.min_range
            )
            / (1 - 2 * y_range.zero_position)
        )

        y2_range.range_from_given_padding(y2_padding)

    return YRanges(y_range, y2_range)


def base_fig() -> go.Figure:
    """Create the first figure"""
    # sample data
    y_axis_1: dict[str, str | list] = {
        "name": "first y-axis",
        "y_values": [200, 0, 10, 50, 130],
        "y_axis": "y",
        "fill": "tozeroy",
    }
    y_axis_2: dict[str, str | list] = {
        "name": "second y-axis",
        "y_values": [-3, 0, 4, -2, -5],
        "y_axis": "y2",
        "fill": "tozeroy",
    }

    # base fig with no special changes in layout
    fig: go.Figure = go.Figure()
    for trace in [y_axis_1, y_axis_2]:
        fig.add_trace(
            go.Scatter(
                name=trace["name"],
                y=trace["y_values"],
                yaxis=trace["y_axis"],
                fill=trace["fill"],
            )
        )
    fig = fig.update_layout(
        {
            "title": {"text": "Base"},
            "legend": {"orientation": "h"},
            "yaxis2": {
                "side": "right",
                "overlaying": "y",
                "tickmode": "sync",
            },
        }
    )

    fig.show()
    return fig


def align_y_axes(fig: go.Figure) -> None:
    """Fuction to try out different combinations of y-axis properties."""

    fig_new: go.Figure = fig.update_layout(
        {
            "title": {"text": "Modified"},
            "legend": {"orientation": "h"},
            "yaxis": {
                "side": "left",
                "tickmode": "sync",
                "range": y_axis_ranges(fig).y_range.range,
            },
            "yaxis2": {
                "side": "right",
                "overlaying": "y",
                "tickmode": "sync",
                "range": y_axis_ranges(fig).y2_range.range,
            },
        }
    )
    fig_new.show()


@dataclass
class YAxis:
    """Range of an axis"""

    values: list[float]
    min_value: float = field(init=False)
    max_value: float = field(init=False)
    padding_min: float = field(init=False)
    padding_max: float = field(init=False)
    min_range: float = field(init=False)
    max_range: float = field(init=False)
    range: list[float] = field(init=False)
    zero_position: float = field(init=False)

    def __post_init__(self) -> None:
        """Fill fields"""
        pipf: float = 1 / 16  # Plotly internal padding factor
        self.min_value = min(self.values)
        self.max_value = max(self.values)
        self.padding_min = (
            0 if self.min_value == 0 else abs(self.max_value - self.min_value) * pipf
        )
        self.padding_max = (
            0 if self.max_value == 0 else abs(self.max_value - self.min_value) * pipf
        )
        self.min_range = self.min_value - self.padding_min
        self.max_range = self.max_value + self.padding_max
        self.range = [self.min_range, self.max_range]
        self.zero_position = (0 - self.min_range) / (self.max_range - self.min_range)


def align_y_axes_from_post(fig: go.Figure | None = None) -> None:
    """https://stackoverflow.com/questions/76289470/plotly-barplot-with-two-y-axis-aligned-at-zero"""

    fig = fig or base_fig()
    fig_data: dict = {trace.get("name"): trace for trace in fig.to_dict()["data"]}

    y1_values: list[float] = [
        value
        for tup in [val["y"] for val in fig_data.values() if val["yaxis"] == "y"]
        for value in tup
    ]
    y1: YAxis = YAxis(y1_values)

    y2_values: list[float] = [
        value
        for tup in [val["y"] for val in fig_data.values() if val["yaxis"] == "y2"]
        for value in tup
    ]
    y2: YAxis = YAxis(y2_values)

    if y1.zero_position < y2.zero_position:
        y1_zero_pos_absolute: float = (y1.max_range - y1.min_range) * y2.zero_position

        y1_min_range_new: float = y1.min_range - y1_zero_pos_absolute
        y1.range = [y1_min_range_new, y1.max_range]
    else:
        y2_min_range_new: float = y1.zero_position * (y2.max_range - y2.min_range)
        y2_max_range_new: float = (1 - y1.zero_position) * (y2.max_range - y2.min_range)
        y2.range = [y2_min_range_new, y2_max_range_new]

    fig_new: go.Figure = fig.update_layout(
        {
            "title": {"text": "Modified"},
            "legend": {"orientation": "h"},
            "yaxis": {
                "side": "left",
                "tickmode": "sync",
                "range": y1.range,
            },
            "yaxis2": {
                "side": "right",
                "overlaying": "y",
                "tickmode": "sync",
                "range": y2.range,
            },
        }
    )
    fig_new.show()
