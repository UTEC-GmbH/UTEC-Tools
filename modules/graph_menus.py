"""UI - Menus"""

import datetime as dt
import pathlib
from typing import TYPE_CHECKING, Any

import plotly.graph_objects as go
import streamlit as st

from modules import classes_data as cld
from modules import classes_errors as cle
from modules import constants as cont
from modules import export as ex
from modules import fig_creation as fig_cr
from modules import fig_general_functions as fgf
from modules import general_functions as gf
from modules import streamlit_functions as sf

if TYPE_CHECKING:
    import polars as pl


def sidebar_file_upload() -> Any:
    """Hochgeladene Excel-Datei"""

    with st.sidebar:
        sb_example: str | None = st.selectbox(
            "Beispieldateien",
            options=[
                phil.stem for phil in pathlib.Path.cwd().glob("example_files/*.xlsx")
            ],
            help=(
                """
                Bitte eine der Beispieldateien (egal welche) herunterladen
                und mit den zu untersuchenden Daten füllen.
                """
            ),
            key="sb_example_file",
        )

        with open(f"example_files/{sb_example}.xlsx", "rb") as exfile:
            st.download_button(
                **cont.Buttons.download_example.func_args(),
                data=exfile,
                file_name=f"{sb_example}.xlsx",
            )

        # benutze ausgewählte Beispieldatei direkt für debugging
        if sf.s_get("access_lvl") == "god":
            st.button("Beispieldatei direkt verwenden", "but_example_direct")

        st.markdown("---")
        st.file_uploader(
            label="Datei hochladen",
            type=["xlsx", "xlsm"],
            accept_multiple_files=False,
            help=(
                """
                Das Arbeitsblatt "Daten" in der Datei muss
                wie eine der Beispieldateien aufgebaut sein.
                """
            ),
            key="f_up",
        )

    return sf.s_get("f_up")


def base_settings(mdf: cld.MetaAndDfs) -> None:
    """Grundeinstellungen (Stundenwerte, JDL, Monatswerte)"""

    if not mdf.meta.td_mnts:
        return

    if mdf.meta.td_mnts == cont.TimeMinutesIn.hour:
        sf.s_set("cb_h", value=True)

    if mdf.meta.td_mnts < cont.TimeMinutesIn.hour or mdf.meta.multi_years:
        with st.sidebar, st.form("Grundeinstellungen"):
            cb_hourly_multiyear(mdf)

            sf.s_set("but_base_settings", st.form_submit_button("Knöpfle"))


def cb_hourly_multiyear(mdf: cld.MetaAndDfs) -> None:
    """Check Boxes for hourly and multi year data"""
    if not mdf.meta.td_mnts:
        return

    if mdf.meta.td_mnts < cont.TimeMinutesIn.hour:
        st.checkbox(
            label="Umrechnung in Stundenwerte",
            help=(
                """
                Die Werte aus der Excel-Tabelle werden 
                in Stundenwerte umgewandelt.  \n
                _(abhängig von der angebenen Einheit 
                entweder per Summe oder Mittelwert)_
                """
            ),
            value=False,
            disabled=False,
            key="cb_h",
        )

    if mdf.meta.multi_years:
        st.checkbox(
            label="mehrere Jahre übereinander",
            help=(
                """
                Die Werte in der Excel-Tabelle werden in Jahre 
                gruppiert und übereinander gezeichnet.
                """
            ),
            value=True,
            key="cb_multi_year",
            # disabled=True,
        )


def select_graphs(mdf: cld.MetaAndDfs) -> None:
    """Auswahl der anzuzeigenden Grafiken"""
    with st.sidebar, st.expander("anzuzeigende Grafiken", expanded=False), st.form(
        "anzuzeigende Grafiken"
    ):
        st.checkbox(
            label="geordnete Jahresdauerlinie",
            help=(
                """
                Die Werte aus der Excel-Tabelle werden 
                nach Größe sortiert ausgegeben.  \n
                _(Werden mehrere Jahre übereinander dargestellt, 
                werden auch hier die Werte in Jahre gruppiert 
                und übereinander dargestellt.)_
                """
            ),
            value=True,
            key="cb_jdl",
        )

        st.checkbox(
            label="Monatswerte",
            help=(
                """
                Aus den gegebenen Werten werden Monatswerte 
                (je nach gegebener Einheit) 
                entweder durch Aufsummieren oder 
                durch Bilden von Mittelwerten erzeugt 
                und als Liniengrafik dargestellt.
                """
            ),
            value=True,
            key="cb_mon",
        )

        st.markdown("###")
        st.markdown("---")

        # Tagesvergleiche
        st.checkbox(
            label="Tagesvergleich",
            help=(
                """
                Hier können Tage gewählt werden, 
                die übereinander als Liniengrafik dargestellt werden sollen.  \n
                _(z.B. zum Vergleich eines Wintertags mit 
                einem Sommertag oder Woche - Wochenende, etc.)_
                """
            ),
            value=False,
            key="cb_days",
            disabled=True,
        )

        st.number_input(
            label="Anzahl der Tage",
            min_value=2,
            value=2,
            format="%i",
            help=(
                """
                Wieveile Tage sollen verglichen werden?  \n
                _(Wird die Anzahl geändert muss auf "aktualisieren" 
                geklickt werden um weitere Felder anzuzeigen)_
                """
            ),
            key="ni_days",
        )

        input_days: int = sf.s_get("ni_days") or 0
        idx: pl.Series = mdf.df.get_column(cont.SpecialCols.original_index)
        if idx.dtype.is_temporal():
            maxi: dt.date | dt.datetime | dt.timedelta | None = idx.dt.max()
            mini: dt.date | dt.datetime | dt.timedelta | None = idx.dt.min()
            if isinstance(maxi, dt.timedelta | None) or isinstance(
                mini, dt.timedelta | None
            ):
                raise ValueError
            idx_max: dt.date = maxi.date() if isinstance(maxi, dt.datetime) else maxi
            idx_min: dt.date = mini.date() if isinstance(mini, dt.datetime) else mini
        else:
            idx_max: dt.date = dt.date(1981, 12, 31)
            idx_min: dt.date = dt.date(1981, 1, 1)
        for num in range(input_days):
            st.date_input(
                label=f"Tag {num + 1}",
                min_value=idx_min,
                max_value=idx_max,
                value=idx_min + dt.timedelta(days=num),
                key=f"day_{num!s}",
            )

        st.markdown("---")
        st.markdown("###")

        st.session_state["but_select_graphs"] = st.form_submit_button("Knöpfle")


def meteo_sidebar() -> None:
    """sidebar-Menu zur Außentemperatur"""
    with st.sidebar, st.expander("Außentemperatur", expanded=False), st.form(
        "Außentemperatur"
    ):
        st.checkbox(
            label="anzeigen",
            value=False,
            key="cb_temp",
            help=(
                """
                Außentemperaturen  werden 
                für den unten eingegebenen Ort heruntergeladen 
                und in den Grafiken eingefügt.
                """
            ),
        )

        st.text_area(
            label="Adresse",
            value=("Cuxhavener Str. 10  \n20217 Bremen"),
            help=(
                """
                Je genauer, desto besser, 
                aber es reicht auch nur eine Stadt.  \n
                _(Wird oben "anzeigen" ausgewählt und as Knöpfle gedrückt, 
                wird eine Karte eingeblendet, mit der kontrolliert werden kann, 
                ob die richtige Adresse gefunden wurde.)_
                """
            ),
            key="ta_adr",
        )

        if sf.s_get("cb_temp"):
            st.plotly_chart(
                fig_cr.cr_meteo_sidebar(),
                use_container_width=True,
                theme=cont.ST_PLOTLY_THEME,
            )

        st.markdown("###")
        st.session_state["but_meteo_sidebar"] = st.form_submit_button("Knöpfle")
        st.markdown("###")


def clean_outliers() -> None:
    """Menu zur Ausreißerbereinigung"""

    with st.sidebar, st.expander("Ausreißerbereinigung", expanded=False), st.form(
        "Ausreißerbereinigung"
    ):
        if "abs_max" not in st.session_state:
            st.session_state["abs_max"] = float(
                max(
                    line["y"].max()
                    for line in st.session_state["fig_base"].data
                    if "orgidx" not in line.name
                )
            )

        st.number_input(
            label="Bereinigung von Werten über:",
            value=st.session_state["abs_max"],
            format="%.0f",
            help=(
                """
                Ist ein Wert in den Daten höher als der hier eingegebene, 
                wird dieser Datenpunkt aus der Reihe gelöscht 
                und die Lücke interpoliert.
                """
            ),
            key="ni_outl",
            disabled=True,
        )

        st.markdown("###")

        st.session_state["but_clean_outliers"] = st.form_submit_button("Knöpfle")


def smooth() -> None:
    """Einstellungen für die geglätteten Linien"""

    with st.sidebar, st.expander("geglättete Linien", expanded=False), st.form(
        "geglättete Linien"
    ):
        st.checkbox(
            label="anzeigen",
            value=True,
            key="cb_smooth",
            help=("Anzeige geglätteter Linien (gleitender Durchschnitt)"),
        )
        st.slider(
            label="Glättung",
            min_value=1,
            max_value=st.session_state["smooth_max_val"],
            value=st.session_state["smooth_start_val"],
            format="%i",
            step=2,
            help=(
                """
                Je niedriger die Zahl, 
                desto weniger wird die Ursprungskurve geglättet.
                """
            ),
            key="gl_win",
        )

        st.number_input(
            label="Polynom",
            value=3,
            format="%i",
            help=(
                """
                Grad der polinomischen Linie  \n
                _(normalerweise passen 2 oder 3 ganz gut)_
                """
            ),
            key="gl_deg",
        )

        st.markdown("###")

        st.session_state["but_smooth"] = st.form_submit_button("Knöpfle")


def h_v_lines(fig: go.Figure | None = None) -> None:
    """Menu für horizontale und vertikale Linien"""
    fig = fig or sf.s_get("fig_base")
    if fig is None:
        return

    with (
        st.sidebar,
        st.expander("horizontale / vertikale Linien", expanded=False),
        st.form("horizontale / vertikale Linien"),
    ):
        h_v_lines_menu(fig)

        st.session_state["but_h_v_lines"] = st.form_submit_button("Knöpfle")


def h_v_lines_menu(fig: go.Figure) -> None:
    """Menu for horizontal and vertical lines"""
    st.markdown("__horizontale Linie einfügen__")

    st.text_input(label="Bezeichnung", value="", key="ti_hor")

    st.number_input(
        value=0.0,
        label="y-Wert",
        format="%f",
        help=(
            """
                Bei diesem Wert wird eine horizontale Linie eingezeichnet.  \n
                _(Zum Löschen einfach "0" eingeben und Knöpfle drücken.)_
                """
        ),
        key="ni_hor",
        step=1.0,
    )

    if len(fgf.get_set_of_visible_y_axes(fig)) > 1:
        st.selectbox(
            label="Y-Achse",
            options=fgf.get_set_of_visible_y_axes(fig),
            help=(
                """
                    Die Y-Achse, auf die sich die Linie beziehen soll.  \n
                    (nicht wundern - die Reihenfolge ist "y", "y2", "y3" etc.)
                    """
            ),
            key="sb_h_line_y",
        )

    # st.multiselect(
    #     label= 'ausfüllen',
    #     options= [
    #         line.name for line in fig_base.data
    #         if len(line.x) > 0 and
    #         not any([ex in line.name for ex in fuan.exclude])
    #     ],
    #     help=(
    #         '''Diese Linie(n) wird (werden) zwischen X-Achse und
    #           hozizontaler Linie ausgefüllt.'''
    #     ),
    #     key= 'ms_fil'
    # )

    st.checkbox(
        label="gestrichelt",
        help=("Soll die horizontale Linie gestrichelt sein?"),
        value=True,
        key="cb_hor_dash",
    )

    st.markdown("###")


def display_options_main_col_settings() -> dict[str, dict]:
    """Settings for the columns of the main display options
    (controlling line color, type, etc.)

    Returns:
        dict[str, dict]:
            - "Title" -> column header with hover-text | "width" -> width of the column
                - "name" -> name of line
                - "vis" -> visibility of line (show line or not)
                - "colour" -> line colour
                - "type" -> line type (e.g. solid, dashed, etc.)
                - "fill" -> fill the line to y=0 and transparency of the fill
                - "anno" -> show an arrow pointing to the maximim value of the line
    """
    return {
        # "name": {
        #     "Title": gf.text_with_hover("Linie", "Bezeichnung der Linie"),
        #     "width": 3,
        # },
        "vis": {
            "Title": gf.text_with_hover("Linie", "Linien, die angezeigt werden sollen"),
            "width": 4,
        },
        "colour": {
            "Title": gf.text_with_hover("Farbe", "Linienfarbe wählen"),
            "width": 1,
        },
        "type": {
            "Title": gf.text_with_hover("Linientyp", "Linie gestrichelt darstellen?"),
            "width": 2,
        },
        "fill": {
            "Title": gf.text_with_hover(
                "Füllen (Transparenz)",
                "Linien, die zur x-Achse ausgefüllt werden sollen",
            ),
            "width": 2,
        },
        "markers": {
            "Title": gf.text_with_hover(
                "Punkte", "Markierung (Punkt) an jedem Datenpunkt und deren Größe"
            ),
            "width": 2,
        },
        "anno": {
            "Title": gf.text_with_hover("Maximum", "Maxima als Anmerkung mit Pfeil"),
            "width": 4,
        },
    }


def display_options_main() -> bool:
    """Hauptmenu für die Darstellungsoptionen (Linienfarben, Füllung, etc.)"""

    with st.expander("Anzeigeoptionen", expanded=False), st.form("Anzeigeoptionen"):
        # columns
        columns: dict[str, dict] = display_options_main_col_settings()
        cols: list = st.columns([col["width"] for col in columns.values()])

        # Überschriften
        for count, col in enumerate(columns):
            with cols[count]:
                st.markdown("###")
                st.markdown(columns[col]["Title"], unsafe_allow_html=True)

        # Check Boxes for line visibility, fill and color
        fig: go.Figure | None = sf.s_get("fig_base")
        if not fig:
            raise cle.NotFoundError(entry="fig_base", where="Streamlit Session_State")

        fig_data: dict[str, dict[str, Any]] = fgf.fig_data_as_dic(fig)
        fig_layout: dict[str, Any] = fgf.fig_layout_as_dic(fig)
        colorway: list[str] = fgf.get_colorway(fig)
        lines: list[dict] = [
            line for line in fig_data.values() if gf.check_if_not_exclude(line["name"])
        ]

        for count, line in enumerate(lines):
            cols: list = st.columns([col["width"] for col in columns.values()])
            line_name: str = line["name"]
            line_color: str = colorway[count]
            if len(line["x"]) > 0 and line_name is not None and line_color is not None:
                with cols[list(columns).index("vis")]:
                    st.checkbox(
                        label=line_name,
                        value=all(
                            part not in line_name
                            for part in [
                                cont.Suffixes.col_smooth,
                                cont.Suffixes.col_arbeit,
                            ]
                        ),
                        key=f"cb_vis_{line_name}",
                    )
                with cols[list(columns).index("colour")]:
                    st.color_picker(
                        label=line_name,
                        value=line_color,
                        key=f"cp_{line_name}",
                        label_visibility="collapsed",
                    )
                with cols[list(columns).index("type")]:
                    st.selectbox(
                        label=line_name,
                        key=f"sb_line_dash_{line_name}",
                        label_visibility="collapsed",
                        options=list(cont.LINE_TYPES),
                    )
                with cols[list(columns).index("markers")]:
                    lvl2_1, lvl2_2 = st.columns([1, 3])
                    with lvl2_1:
                        st.checkbox(
                            label="Punkte",
                            value=False,
                            key=f"cb_markers_{line_name}",
                            label_visibility="collapsed",
                        )
                    with lvl2_2:
                        st.number_input(
                            label="Punkte",
                            value=6,
                            key=f"ni_markers_{line_name}",
                            label_visibility="collapsed",
                        )
                with cols[list(columns).index("fill")]:
                    st.selectbox(
                        label=line_name,
                        key=f"sb_fill_{line_name}",
                        label_visibility="collapsed",
                        options=cont.TRANSPARENCY_OPTIONS,
                    )

                # Check Boxes for annotations
                anno_name: str = ""
                for anno in [
                    anno["name"]
                    for anno in fig_layout["annotations"]
                    if gf.check_if_not_exclude(anno["name"])
                    and gf.check_if_not_exclude(line_name)
                ]:
                    if line_name in anno:
                        anno_name = anno.split(": ")[0]

                if anno_name:
                    with cols[list(columns).index("anno")]:
                        st.checkbox(
                            label=anno_name,
                            value=False,
                            key=f"cb_anno_{anno_name}",
                        )

        st.markdown("###")
        but_upd_main: bool = st.form_submit_button("Knöpfle")

    return but_upd_main


def display_smooth_main() -> bool:
    """Hauptmenu für die Darstellungsoptionen (Linienfarben, Füllung, etc.)"""

    with st.expander("Anzeigeoptionen für geglättete Linien", expanded=False), st.form(
        "Anzeigeoptionen für geglättete Linien"
    ):
        col_general: list = st.columns([3, 1])
        with col_general[0]:
            st.slider(
                label="Glättung",
                min_value=1,
                max_value=st.session_state["smooth_max_val"],
                value=st.session_state["smooth_start_val"],
                format="%i",
                step=2,
                help=(
                    """
                    Je niedriger die Zahl, 
                    desto weniger wird die Ursprungskurve geglättet.
                    """
                ),
                key="gl_win",
            )
        with col_general[1]:
            st.number_input(
                label="Polynom",
                value=3,
                format="%i",
                help=(
                    """
                    Grad der polinomischen Linie  \n
                    _(normalerweise passen 2 oder 3 ganz gut)_
                    """
                ),
                key="gl_deg",
            )

        st.markdown("---")

        # columns
        columns: dict[str, dict] = display_options_main_col_settings()
        cols: list = st.columns([col["width"] for col in columns.values()])

        # Überschriften
        for count, col in enumerate(columns):
            if count < 3:
                with cols[count]:
                    st.markdown("###")
                    st.markdown(columns[col]["Title"], unsafe_allow_html=True)

        # Check Boxes for line visibility, fill and color
        fig: go.Figure = st.session_state["fig_base"]
        fig_data: dict[str, dict[str, Any]] = fgf.fig_data_as_dic(fig)
        colorway: list[str] = fgf.get_colorway(fig)
        lines: list[dict] = [
            line for line in fig_data.values() if gf.check_if_not_exclude(line["name"])
        ]

        for count, line in enumerate(lines):
            cols: list = st.columns([col["width"] for col in columns.values()])
            line_name: str = f'{line["name"]}{cont.Suffixes.col_smooth}'
            line_color: str = colorway[count + len(lines)]
            if (
                len(line["x"]) > 0
                and "hline" not in line_name
                and line_name is not None
                and line_color is not None
            ):
                # with cols[list(columns).index("name")]:
                #     st.markdown(line_name)
                with cols[list(columns).index("vis")]:
                    st.checkbox(
                        label=line_name,
                        value=False,
                        key=f"cb_vis_{line_name}",
                        # label_visibility="collapsed",
                    )
                with cols[list(columns).index("type")]:
                    st.selectbox(
                        label=line_name,
                        key=f"sb_line_dash_{line_name}",
                        label_visibility="collapsed",
                        options=list(cont.LINE_TYPES),
                        index=1,
                    )
                with cols[list(columns).index("colour")]:
                    st.color_picker(
                        label=line_name,
                        value=line_color,
                        key=f"cp_{line_name}",
                        label_visibility="collapsed",
                    )

                with cols[list(columns).index("fill")]:
                    st.empty()

                with cols[list(columns).index("anno")]:
                    st.empty()

        st.markdown("###")
        but_smooth: bool = st.form_submit_button("Knöpfle")

    st.markdown("###")

    return but_smooth


def downloads(mdf: cld.MetaAndDfs) -> None:
    """Dateidownloads"""

    st.download_button(**cont.Buttons.download_html.func_args(), data=ex.html_graph())

    dic_df_ex: dict[str, pl.DataFrame] = {"Daten": mdf.df}
    if mdf.df_h is not None:
        dic_df_ex["Stundenwerte"] = mdf.df_h
    if mdf.jdl is not None:
        dic_df_ex["Jahresdauerlinie"] = mdf.jdl
    if mdf.mon is not None:
        dic_df_ex["Monatswerte"] = mdf.mon

    st.download_button(
        **cont.Buttons.download_excel.func_args(),
        data=ex.excel_download(dic_df_ex, mdf.meta),
    )
