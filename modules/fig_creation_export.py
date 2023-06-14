"""plots erstellen und in session_state schreiben"""


from pathlib import Path
from typing import Any

import plotly.graph_objects as go
import streamlit as st
from loguru import logger

from modules import classes_data as cl
from modules import classes_figs as clf
from modules import constants as cont
from modules import fig_annotations as fig_anno
from modules import fig_formatting as fig_format
from modules import fig_general_functions as fgf
from modules import general_functions as gf
from modules import plotly_plots as ploplo


# Grund-Grafik
@gf.func_timer
def cr_fig_base(mdf: cl.MetaAndDfs) -> go.Figure:
    """Lastgang erstellen"""

    min_amount_vals: int = 20

    tit_res: str = ""
    if gf.st_get("cb_h"):
        tit_res = cont.SUFFIXES.fig_tit_h
    elif mdf.meta.td_mnts == cont.TIME_MIN.quarter_hour:
        tit_res = cont.SUFFIXES.fig_tit_15

    tit: str = f"{cont.FIG_TITLES.lastgang}{tit_res}"

    if gf.st_get("cb_multi_year"):
        fig: go.Figure = ploplo.line_plot_y_overlay(mdf, title=tit)
    else:
        fig: go.Figure = ploplo.line_plot(
            mdf,
            "df_h" if gf.st_get("cb_h") else "df",
            title=tit,
        )

    logger.debug(fig.to_dict)

    data: dict[str, dict[str, Any]] = fgf.fig_data_as_dic(fig)
    layout: dict[str, Any] = fgf.fig_layout_as_dic(fig)

    fig = fig_anno.add_arrows_min_max(fig, data=data, layout=layout)
    colorway: list[str] = fgf.get_colorway(fig, data=data, layout=layout)

    # geglättete Linien
    max_val: int = int(
        max(
            len(trace["x"])
            for trace in data.values()
            if len(trace["x"]) > min_amount_vals
        )
        // 3
    )
    max_val = int(max_val + 1 if max_val % 2 == 0 else max_val)
    st.session_state["smooth_max_val"] = max_val
    start_val: int = max_val // 5
    st.session_state["smooth_start_val"] = int(
        start_val + 1 if start_val % 2 == 0 else start_val
    )

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

    logger.success("fig_base created")
    return fig


@gf.func_timer
def cr_fig_jdl(mdf: cl.MetaAndDfs) -> go.Figure:
    """Jahresdauerlinie erstellen"""

    tit: str = f"{cont.FIG_TITLES.jdl}{cont.SUFFIXES.fig_tit_h}"

    if gf.st_get("cb_multi_year"):
        fig: go.Figure = ploplo.line_plot_y_overlay(mdf, "jdl", title=tit)
    else:
        fig: go.Figure = ploplo.line_plot(mdf, "jdl", title=tit)

    data: dict[str, dict[str, Any]] = fgf.fig_data_as_dic(fig)
    layout: dict[str, Any] = fgf.fig_layout_as_dic(fig)

    fig = fig_anno.add_arrows_min_max(fig, data=data, layout=layout)
    colorway: list[str] = fgf.get_colorway(fig, data=data, layout=layout)

    # updates
    fig.update_layout(
        title_text=fig.layout.meta.get("title"),
        legend={"yanchor": "top", "y": 0.975, "xanchor": "right", "x": 0.975},
    )
    fig = fig_format.standard_axes_and_layout(fig, x_tickformat=",d")

    x_min: int = min(min(d.x) for d in fig.data)
    x_max: int = max(max(d.x) for d in fig.data)

    if 7000 < x_max < 9000:
        fig.update_xaxes(
            range=[x_min, 9000],
        )

    # colours
    for count, (line, line_dat) in enumerate(data.items()):
        if len(line_dat["x"]) > 0 and "hline" not in line:
            fig = fig.update_traces(
                {"line_color": colorway[count].lower()}, {"name": line}
            )

    logger.success("fig_jdl created")

    return fig


@gf.func_timer
def cr_fig_mon(mdf: cl.MetaAndDfs) -> go.Figure:
    """Monatswerte erstellen"""

    if gf.st_get("cb_multi_year"):
        fig: go.Figure = ploplo.line_plot_y_overlay(
            mdf, "mon", title=cont.FIG_TITLES.mon
        )
    else:
        fig: go.Figure = ploplo.line_plot(mdf, "mon", title=cont.FIG_TITLES.mon)

    # Pfeile an Maxima
    data: dict[str, dict[str, Any]] = fgf.fig_data_as_dic(fig)
    layout: dict[str, Any] = fgf.fig_layout_as_dic(fig)

    fig = fig_anno.add_arrows_min_max(fig, data=data, layout=layout)
    colorway: list[str] = fgf.get_colorway(fig, data=data, layout=layout)

    fig.update_layout(
        xaxis_tickformat="%b<br>%Y" if gf.st_get("cb_multi_year") is False else "%b",
        xaxis_tickformatstops=[
            {
                "dtickrange": [None, None],
                "value": "%b<br>%Y" if gf.st_get("cb_multi_year") is False else "%b",
            },
        ],
        title_text=fig.layout.meta.get("title"),
        legend={"yanchor": "top", "y": 0.975, "xanchor": "right", "x": 0.975},
    )

    fig = fig_format.standard_axes_and_layout(fig)

    fig.update_traces(
        mode="markers+lines",
        line={"dash": "dash", "width": 1},
        marker={"size": 10},
    )

    # colours
    for count, (line, line_dat) in enumerate(data.items()):
        if len(line_dat["x"]) > 0 and "hline" not in line:
            fig = fig.update_traces(
                {"line_color": colorway[count].lower()}, {"name": line}
            )
    logger.success("fig_mon created")

    return fig


@gf.func_timer
def cr_fig_days(mdf: cl.MetaAndDfs) -> None:
    """Tagesvergleiche"""

    tit_res: str = ""
    if gf.st_get("cb_h"):
        tit_res = cont.FIG_TITLES.suff_stunden
    elif st.session_state["metadata"]["td_mean"] == 15:
        tit_res = cont.FIG_TITLES.suff_15min

    tit: str = f"{cont.FIG_TITLES.tage}{tit_res}"

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


@gf.func_timer
def plot_figs(figs: clf.Figs) -> None:
    """Grafiken darstellen"""

    with st.container():
        st.plotly_chart(
            figs.base.fig,
            use_container_width=True,
            config=fig_format.plotly_config(height=450),
            theme=cont.ST_PLOTLY_THEME,
        )

        if all(
            [
                gf.st_get("cb_jdl"),
                gf.st_get("cb_mon"),
                figs.jdl is not None,
                figs.mon is not None,
            ]
        ):
            st.markdown("###")

            columns: list = st.columns(2)
            with columns[0]:
                st.plotly_chart(
                    figs.jdl.fig,
                    use_container_width=True,
                    config=fig_format.plotly_config(),
                    theme=cont.ST_PLOTLY_THEME,
                )
                if gf.st_get("cb_days") and figs.days is not None:
                    st.markdown("###")
                    st.plotly_chart(
                        figs.days.fig,
                        use_container_width=True,
                        config=fig_format.plotly_config(),
                        theme=cont.ST_PLOTLY_THEME,
                    )

            with columns[1]:
                st.plotly_chart(
                    figs.mon.fig,
                    use_container_width=True,
                    config=fig_format.plotly_config(),
                    theme=cont.ST_PLOTLY_THEME,
                )

        elif gf.st_get("cb_jdl") and not gf.st_get("cb_mon"):
            st.markdown("###")

            st.plotly_chart(
                figs.jdl.fig,
                use_container_width=True,
                config=fig_format.plotly_config(),
                theme=cont.ST_PLOTLY_THEME,
            )
            if gf.st_get("cb_days"):
                st.markdown("###")
                st.plotly_chart(
                    figs.days.fig,
                    use_container_width=True,
                    config=fig_format.plotly_config(),
                    theme=cont.ST_PLOTLY_THEME,
                )

        elif gf.st_get("cb_mon") and not gf.st_get("cb_jdl"):
            st.markdown("###")

            st.plotly_chart(
                figs.mon.fig,
                use_container_width=True,
                config=fig_format.plotly_config(),
                theme=cont.ST_PLOTLY_THEME,
            )
            if gf.st_get("cb_days"):
                st.markdown("###")
                st.plotly_chart(
                    figs.days.fig,
                    use_container_width=True,
                    config=fig_format.plotly_config(),
                    theme=cont.ST_PLOTLY_THEME,
                )


@gf.func_timer
def html_exp(f_pn: str = "export\\interaktive_grafische_Auswertung.html") -> None:
    """html-Export"""

    if Path.exists(Path(f_pn)):
        Path.unlink(Path(f_pn))

    with open(f_pn, "w", encoding="utf-8") as fil:
        fil.write("<!DOCTYPE html>")
        fil.write("<title>Interaktive Grafische Datenauswertung</title>")
        fil.write("<head><style>")
        fil.write("h1{text-align: left; font-family: sans-serif;}")
        fil.write("body{width: 85%; margin-left:auto; margin-right:auto}")
        fil.write("</style></head>")
        fil.write('<body><h1><a href="https://www.utec-bremen.de/">')
        fil.write(gf.render_svg())
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
