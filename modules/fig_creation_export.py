"""
plots erstellen und in session_state schreiben
"""

import os
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from modules import constants as cont
from modules import fig_annotations as fig_anno
from modules import fig_formatting as fig_format
from modules import fig_general_functions as fgf
from modules import plotly_plots as ploplo
from modules.general_functions import func_timer, render_svg


# Grund-Grafik
@func_timer
def cr_fig_base() -> go.Figure:
    """Lastgang erstellen"""

    meta: dict = st.session_state["metadata"]

    tit_res: str = ""
    if st.session_state.get("cb_h"):
        tit_res = cont.FIG_TITLE_SUFFIXES["suffix_Stunden"]
    elif meta["index"]["td_mean"] == pd.Timedelta(minutes=15):
        tit_res = cont.FIG_TITLE_SUFFIXES["suffix_15min"]

    tit: str = f'{cont.FIG_TITLES["lastgang"]}{tit_res}'

    if st.session_state.get("cb_multi_year"):
        fig: go.Figure = ploplo.line_plot_y_overlay(
            dic_df=st.session_state["dic_df_multi"],
            meta=meta,
            years=st.session_state["years"],
            title=tit,
        )
    else:
        fig: go.Figure = ploplo.line_plot(
            df=st.session_state["df_h"]
            if st.session_state.get("cb_h")
            else st.session_state["df"],
            meta=meta,
            title=tit,
        )

    data: dict[str, dict[str, Any]] = fgf.fig_data_as_dic(fig)
    layout: dict[str, Any] = fgf.fig_layout_as_dic(fig)

    fig = fig_anno.add_arrows_min_max(fig, data=data, layout=layout)
    colorway: list[str] = fgf.get_colorway(fig, data=data, layout=layout)

    # geglättete Linien
    max_val: int = int(
        max(len(trace["x"]) for trace in data.values() if len(trace["x"]) > 20) // 3
    )
    max_val = int(max_val + 1 if max_val % 2 == 0 else max_val)
    st.session_state["smooth_max_val"] = max_val
    start_val: int = max_val // 5
    st.session_state["smooth_start_val"] = int(
        start_val + 1 if start_val % 2 == 0 else start_val
    )

    # fig = fig_anno.smooth(fig, data=data)

    # updates
    fig = fig.update_layout(
        title_text=layout["meta"]["title"],
    )
    fig = fig_format.standard_axes_and_layout(fig)

    # range slider und "zoom"-Knöpfle
    fig = fig_format.add_range_slider(fig)

    # colours
    for count, (line, line_dat) in enumerate(data.items()):
        if len(line_dat["x"]) > 0 and "hline" not in line:
            fig = fig.update_traces(
                {"line_color": colorway[count].lower()}, {"name": line}
            )

    return fig


@func_timer
def cr_fig_jdl() -> None:
    """Jahresdauerlinie erstellen"""

    tit: str = f'{cont.FIG_TITLES["jdl"]}{cont.FIG_TITLE_SUFFIXES["suffix_Stunden"]}'

    if st.session_state.get("cb_multi_year"):
        st.session_state["fig_jdl"] = ploplo.line_plot_y_overlay(
            st.session_state["dic_jdl"],
            st.session_state["metadata"],
            st.session_state["years"],
            title=tit,
        )
    else:
        st.session_state["fig_jdl"] = ploplo.line_plot(
            st.session_state["df_jdl"],
            st.session_state["metadata"],
            title=tit,
        )

    # Pfeile an Maxima
    fig_anno.add_arrows_min_max(st.session_state["fig_jdl"])

    # updates
    st.session_state["fig_jdl"].update_layout(
        title_text=st.session_state["fig_jdl"].layout.meta.get("title"),
        legend={"yanchor": "top", "y": 0.975, "xanchor": "right", "x": 0.975},
    )
    st.session_state["fig_jdl"] = fig_format.standard_axes_and_layout(
        st.session_state["fig_jdl"], x_tickformat=",d"
    )

    st.session_state["fig_jdl"].update_traces(
        legendgroup=None,
        legendgrouptitle=None,
    )
    x_min = min(min(d.x) for d in st.session_state["fig_jdl"].data)
    x_max = max(max(d.x) for d in st.session_state["fig_jdl"].data)

    if 7000 < x_max < 9000:
        st.session_state["fig_jdl"].update_xaxes(
            range=[x_min, 9000],
        )


@func_timer
def cr_fig_mon() -> None:
    """Monatswerte erstellen"""

    if st.session_state.get("cb_multi_year"):
        st.session_state["fig_mon"] = ploplo.line_plot_y_overlay(
            st.session_state["dic_mon"],
            st.session_state["metadata"],
            st.session_state["years"],
            title=cont.FIG_TITLES["mon"],
        )
    else:
        st.session_state["fig_mon"] = ploplo.line_plot(
            st.session_state["df_mon"],
            st.session_state["metadata"],
            title=cont.FIG_TITLES["mon"],
        )

    # Pfeile an Maxima
    fig_anno.add_arrows_min_max(st.session_state["fig_mon"])

    st.session_state["fig_mon"].update_layout(
        xaxis_tickformat="%b<br>%Y"
        if st.session_state.get("cb_multi_year") is False
        else "%b",
        xaxis_tickformatstops=[
            {
                "dtickrange": [None, None],
                "value": "%b<br>%Y"
                if st.session_state.get("cb_multi_year") is False
                else "%b",
            },
        ],
        title_text=st.session_state["fig_mon"].layout.meta.get("title"),
        legend={"yanchor": "top", "y": 0.975, "xanchor": "right", "x": 0.975},
    )

    st.session_state["fig_mon"] = fig_format.standard_axes_and_layout(
        st.session_state["fig_mon"]
    )

    st.session_state["fig_mon"].update_traces(
        mode="markers+lines",
        line={"dash": "dash", "width": 1},
        marker={"size": 10},
        legendgroup=None,
        legendgrouptitle=None,
    )


@func_timer
def cr_fig_days() -> None:
    """Tagesvergleiche"""

    tit_res: str = ""
    if st.session_state.get("cb_h"):
        tit_res = cont.FIG_TITLE_SUFFIXES["suffix_Stunden"]
    elif st.session_state["metadata"]["index"]["td_mean"] == pd.Timedelta(minutes=15):
        tit_res = cont.FIG_TITLE_SUFFIXES["suffix_15min"]

    tit: str = f'{cont.FIG_TITLES["tage"]}{tit_res}'

    st.session_state["fig_days"] = ploplo.line_plot_day_overlay(
        st.session_state["dic_days"], st.session_state["metadata"], tit, "fig_days"
    )

    # updates
    st.session_state["fig_days"].update_layout(
        title_text=st.session_state["fig_days"].layout.meta.get("title"),
    )
    st.session_state["fig_days"] = fig_format.standard_axes_and_layout(
        st.session_state["fig_days"]
    )

    st.session_state["fig_days"].update_xaxes(
        tickformat="%H:%M",
        tickformatstops=[
            {"dtickrange": [None, None], "value": "%H:%M"},
        ],
    )


@func_timer
def plot_figs() -> None:
    """Grafiken darstellen"""

    with st.container():
        st.plotly_chart(
            st.session_state["fig_base"],
            use_container_width=True,
            config=fig_format.plotly_config(height=450),
            theme=cont.ST_PLOTLY_THEME,
        )

        if st.session_state.get("cb_jdl") and st.session_state.get("cb_mon"):
            st.markdown("###")

            columns: list = st.columns(2)
            with columns[0]:
                st.plotly_chart(
                    st.session_state["fig_jdl"],
                    use_container_width=True,
                    config=fig_format.plotly_config(),
                    theme=cont.ST_PLOTLY_THEME,
                )
                if st.session_state.get("cb_days"):
                    st.markdown("###")
                    st.plotly_chart(
                        st.session_state["fig_days"],
                        use_container_width=True,
                        config=fig_format.plotly_config(),
                        theme=cont.ST_PLOTLY_THEME,
                    )

            with columns[1]:
                st.plotly_chart(
                    st.session_state["fig_mon"],
                    use_container_width=True,
                    config=fig_format.plotly_config(),
                    theme=cont.ST_PLOTLY_THEME,
                )

        elif st.session_state.get("cb_jdl") and not st.session_state.get("cb_mon"):
            st.markdown("###")

            st.plotly_chart(
                st.session_state["fig_jdl"],
                use_container_width=True,
                config=fig_format.plotly_config(),
                theme=cont.ST_PLOTLY_THEME,
            )
            if st.session_state.get("cb_days"):
                st.markdown("###")
                st.plotly_chart(
                    st.session_state["fig_days"],
                    use_container_width=True,
                    config=fig_format.plotly_config(),
                    theme=cont.ST_PLOTLY_THEME,
                )

        elif st.session_state.get("cb_mon") and not st.session_state.get("cb_jdl"):
            st.markdown("###")

            st.plotly_chart(
                st.session_state["fig_mon"],
                use_container_width=True,
                config=fig_format.plotly_config(),
                theme=cont.ST_PLOTLY_THEME,
            )
            if st.session_state.get("cb_days"):
                st.markdown("###")
                st.plotly_chart(
                    st.session_state["fig_days"],
                    use_container_width=True,
                    config=fig_format.plotly_config(),
                    theme=cont.ST_PLOTLY_THEME,
                )


@func_timer
def html_exp(f_pn: str = "export\\interaktive_grafische_Auswertung.html") -> None:
    """html-Export"""

    if os.path.exists(f_pn):
        os.remove(f_pn)

    with open(f_pn, "w", encoding="utf-8") as fil:
        fil.write("<!DOCTYPE html>")
        fil.write("<title>Interaktive Grafische Datenauswertung</title>")
        fil.write("<head><style>")
        fil.write("h1{text-align: left; font-family: sans-serif;}")
        fil.write("body{width: 85%; margin-left:auto; margin-right:auto}")
        fil.write("</style></head>")
        fil.write('<body><h1><a href="https://www.utec-bremen.de/">')
        fil.write(render_svg())
        fil.write("</a><br /><br />")
        fil.write("Interaktive Grafische Datenauswertung")
        fil.write("</h1><br /><hr><br /><br />")

        fil.write("<style>")
        fil.write("#las{width: 100%; margin-left:auto; margin-right:auto; }")

        if any(
            "Jahresdauerlinie" in st.session_state[fig].layout.meta.get("title")
            for fig in st.session_state["lis_figs"]
        ):
            fil.write("#jdl{width: 45%; float: left; margin-right: 5%; }")
            fil.write("#mon{width: 45%; float: right; margin-left: 5%; }")
        else:
            fil.write("#mon{width: 45%; float: left; margin-right: 5%; }")

        fil.write("</style>")

        for fig in st.session_state["lis_figs"]:
            fig_type: str = fgf.fig_type_by_title(st.session_state[fig])
            if "las" in fig_type:
                fil.write('<div id="las">')
            elif "jdl" in fig_type:
                fil.write('<div id="jdl">')
            elif "mon" in fig_type:
                fil.write('<div id="mon">')

            fil.write(
                st.session_state[fig].to_html(
                    full_html=False, config=fig_format.plotly_config()
                )
            )

            fil.write("<br /><br /><hr><br /><br /><br /></div>")

        fil.write("</body></html>")
