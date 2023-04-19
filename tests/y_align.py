"""Trying to figure out how to aling y = 0"""

from typing import Any

import plotly.graph_objects as go


def sample_fig_y_align() -> Dict[str, go.Figure]:
    """Fuction to try out different combinations of y-axis properties.

    Returns:
        - Dict[str, go.Figure]: Dictionary of figures
    """

    # sample data
    y_axis_1: Dict[str, Any] = {
        "name": "first y-axis",
        "y_values": [200, 8, 0, 250, 110],
        "y_axis": "y",
        "fill": "tozeroy",
    }
    y_axis_2: Dict[str, Any] = {
        "name": "second y-axis",
        "y_values": [-3, -1, 4, -2, 2],
        "y_axis": "y2",
        "fill": "tozeroy",
    }

    # base fig with no special changes in layout
    fig_base: go.Figure = go.Figure()
    for trace in [y_axis_1, y_axis_2]:
        fig_base.add_trace(
            go.Scatter(
                name=trace["name"],
                y=trace["y_values"],
                yaxis=trace["y_axis"],
                fill=trace["fill"],
            )
        )
    fig_base.update_layout(
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
    fig_base.show()

    # layout changes to try and align y = 0
    tests_y2: Dict[str, Dict[str, Any]] = {
        "from post": {  # https://community.plotly.com/t/align-multiple-y-axis-to-one-value-in-plotly/44500
            "rangemode": "tozero",
            "scaleanchor": "y",
            "scaleratio": 1,
            "constraintoward": "bottom",
        },
        "config_1": {
            "scaleanchor": "y",
            "constrain": "domain",
            "constraintoward": "bottom",
        },
        "config_2": {
            "scaleanchor": "y",
            "constrain": "range",
            "constraintoward": "bottom",
        },
        "config_3": {
            "anchor": "x",
        },
        "config_4": {
            "matches": "y",
            "autorange": True,
        },
    }

    figs: Dict[str, go.Figure] = {
        test_key: go.Figure(
            fig_base.update_layout(
                {
                    "title": {"text": str(test_Dict)},
                    "yaxis2": test_Dict,
                }
            )
        )
        for (test_key, test_Dict) in list(tests_y2.items())
    }

    for test_fig in figs:
        figs[test_fig].show()

    return figs
