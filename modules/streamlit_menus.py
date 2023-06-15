"""UI - Menus"""

import datetime
import secrets
from glob import glob
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from modules import classes_data as cl
from modules import constants as cont
from modules import excel_download as ex
from modules import fig_creation_export as fig_cr
from modules import fig_general_functions as fgf
from modules import general_functions as gf
from modules import meteorolog as meteo
from modules import user_authentication as uauth


@gf.func_timer
def user_accounts() -> None:
    """Benutzerkontensteuerung"""

    st.markdown("###")
    st.markdown("---")

    lis_butt: list[str] = [
        "butt_add_new_user",
        "butt_del_user",
    ]

    # Knöpfle für neuen Benutzer, Benutzer löschen...
    if not any(gf.st_get(butt) for butt in lis_butt):
        st.button("Liste aller Konten", "butt_list_all")
        st.button("Neuen Benutzer hinzufügen", "butt_add_new_user")
        st.button("Benutzer löschen", "butt_del_user")
        st.button("Benutzerdaten ändern", "butt_change_user", disabled=True)
        st.markdown("###")

    # Menu für neuen Benutzer
    if gf.st_get("butt_add_new_user"):
        new_user_form()
        st.button("abbrechen")
    st.session_state["butt_sub_new_user"] = gf.st_get(
        "FormSubmitter:Neuer Benutzer-Knöpfle"
    )

    # Menu zum Löschen von Benutzern
    if gf.st_get("butt_del_user"):
        delete_user_form()
        st.button("abbrechen")
    st.session_state["butt_sub_del_user"] = gf.st_get(
        "FormSubmitter:Benutzer löschen-Knöpfle"
    )

    if gf.st_get("butt_list_all"):
        st.markdown("---")
        list_all_accounts()


@gf.func_timer
def delete_user_form() -> None:
    """Benutzer löschen"""

    users: dict[str, dict[str, str]] = uauth.get_all_user_data()
    with st.form("Benutzer löschen"):
        st.multiselect(
            label="Benutzer wählen, die gelöscht werden sollen",
            options=[
                f"{user['key']} ({user['name']})"
                for user in users.values()
                if user["key"] not in ("utec", "fl")
            ],
            key="ms_del_users",
        )

        st.markdown("###")
        st.form_submit_button("Knöpfle")


@gf.func_timer
def new_user_form() -> None:
    """Neuen Benutzer hinzufügen"""
    with st.form("Neuer Benutzer"):
        st.text_input(
            label="Benutzername",
            key="new_user_user",
            help=("Benutzername, wei er für den login benutzt wird - z.B. fl"),
        )
        st.text_input(
            label="Passwort",
            key="new_user_pw",
            help=("...kann ruhig auch etwas 'merkbares' sein."),
            value=secrets.token_urlsafe(8),
        )
        st.date_input(
            label="Benutzung erlaubt bis:",
            key="new_user_until",
            min_value=datetime.date.today(),
            value=datetime.date.today() + datetime.timedelta(weeks=3),
        )
        st.text_input(
            label="Name oder Firma",
            key="new_user_name",
            help=("z.B. Florian"),
            value="UTEC",
        )
        st.text_input(
            label="E-Mail Adresse",
            key="new_user_email",
            help=("z.B. info@utec-bremen.de"),
            value="info@utec-bremen.de",
        )
        st.multiselect(
            label="Zugriffsrechte",
            key="new_user_access",
            help=("Auswahl der Module, auf die dieser Benutzer zugreifen darf."),
            options=[
                key for key in cont.ST_PAGES.get_all_short() if key not in ("login")
            ],
            default=[
                key for key in cont.ST_PAGES.get_all_short() if key not in ("login")
            ],
        )

        st.markdown("###")
        st.form_submit_button("Knöpfle")


@gf.func_timer
def list_all_accounts() -> None:
    """Liste aller Benutzerkonten"""
    users: dict[str, dict[str, str]] = uauth.get_all_user_data()

    df_users = pd.DataFrame()
    df_users["Benutzername"] = [user["key"] for user in users.values()]
    df_users["Name"] = [user["name"] for user in users.values()]
    df_users["Verfallsdatum"] = [user["access_until"] for user in users.values()]
    df_users["Zugriffsrechte"] = [str(user["access_lvl"]) for user in users.values()]

    st.dataframe(df_users)
    st.button("ok")


@gf.func_timer
def sidebar_file_upload() -> Any:
    """Hochgeladene Excel-Datei"""

    with st.sidebar, st.expander(
        "Auszuwertende Daten", expanded=not bool(gf.st_get("f_up"))
    ):
        # Download
        sb_example: str | None = st.selectbox(
            "Beispieldateien",
            options=[
                x.replace("/", "\\").split("\\")[-1].replace(".xlsx", "")
                for x in glob("example_files/*.xlsx")
            ],
            help=(
                """
                Bitte eine der Beispieldateien (egal welche) herunterladen
                und mit den zu untersuchenden Daten füllen.
                """
            ),
        )

        with open(f"example_files/{sb_example}.xlsx", "rb") as exfile:
            st.download_button(
                label="Beispieldatei herunterladen",
                data=exfile,
                file_name=f"{sb_example}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        # benutze ausgewählte Beispieldatei direkt für debugging
        if gf.st_get("access_lvl") == "god":
            st.button("Beispieldatei direkt verwenden", "but_example_direct")
            st.button("RESET", "but_reset")

        if gf.st_get("but_reset"):
            gf.st_delete("f_up")

        # Upload
        sample_direct: str = f"example_files/{sb_example}.xlsx"
        if gf.st_get("but_example_direct") or gf.st_get("f_up") == sample_direct:
            f_up = sample_direct
            st.session_state["f_up"] = f_up

        else:
            st.markdown("---")
            f_up = st.file_uploader(
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

    return f_up


@gf.func_timer
def base_settings(mdf: cl.MetaAndDfs) -> None:
    """Grundeinstellungen (Stundenwerte, JDL, Monatswerte)"""

    if not mdf.meta.td_mnts:
        return

    if mdf.meta.td_mnts == cont.TIME_MIN.hour:
        gf.st_set("cb_h", value=True)

    if mdf.meta.td_mnts < cont.TIME_MIN.hour or mdf.meta.multi_years:
        with st.sidebar, st.form("Grundeinstellungen"):
            if mdf.meta.td_mnts < cont.TIME_MIN.hour:
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

            gf.st_set("but_base_settings", st.form_submit_button("Knöpfle"))


@gf.func_timer
def select_graphs(mdf: cl.MetaAndDfs) -> None:
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
            # disabled=True,
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

        for num in range(int(gf.st_get("ni_days"))):
            st.date_input(
                label=f"Tag {num + 1!s}",
                min_value=mdf.df.get_column(cont.SPECIAL_COLS.original_index).min(),
                max_value=mdf.df.get_column(cont.SPECIAL_COLS.original_index).max(),
                value=mdf.df.get_column(cont.SPECIAL_COLS.original_index).min()
                + pd.DateOffset(days=num),
                key=f"day_{num!s}",
            )

        st.markdown("---")
        st.markdown("###")

        st.session_state["but_select_graphs"] = st.form_submit_button("Knöpfle")


@gf.func_timer
def meteo_sidebar(page: str) -> None:
    """sidebar-Menu zur Außentemperatur"""
    with st.sidebar, st.expander("Außentemperatur", expanded=False), st.form(
        "Außentemperatur"
    ):
        st.warning("temporär außer Betrieb")

        if page in ("graph"):
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
                disabled=True,
            )

        if page in ("meteo"):
            st.number_input(
                label="von (Jahr)",
                format="%i",
                value=2020,
                help=(
                    """
                        Falls nur ein Jahr ausgegeben werden soll, 
                        in beide Felder das gleiche Jahr eingeben.
                        """
                ),
                key="meteo_start_year",
                disabled=True,
            )

            st.number_input(
                label="bis (Jahr)",
                format="%i",
                value=2020,
                key="meteo_end_year",
                disabled=True,
            )

            st.markdown("###")

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
            # placeholder= 'Cuxhavener Str. 10, 20217 Bremen',
            # autocomplete= '',
            key="ti_adr",
            disabled=True,
        )

        st.markdown("###")
        st.session_state["but_meteo_sidebar"] = st.form_submit_button(
            "Knöpfle", disabled=True
        )
        st.markdown("###")


@gf.func_timer
def meteo_params_main() -> None:
    """Wetterdaten-Menu auf der Hauptseite"""

    cats = meteo.LIS_CAT_UTEC
    all_params = meteo.LIS_PARAMS
    set_params = []
    for par in all_params:
        if par.tit_de not in [param.tit_de for param in set_params]:
            set_params.append(par)

    with st.expander("Datenauswahl", expanded=False), st.form("Meteo Datenauswahl"):
        columns: list = st.columns(4)
        float_align: str = "; float:left; text-align:left;"

        for cnt, col in enumerate(columns):
            with col:
                st.markdown("###")
                st.markdown(
                    f"""
                        <html>
                            <body>
                                <span style="{cont.CSS_LABEL_1[1:-1]}{float_align}">
                                    <div>{cats[cnt]}</div>
                            </body>
                        </html>
                        """,
                    unsafe_allow_html=True,
                )

                for par in set_params:
                    if par.cat_utec == cats[cnt]:
                        st.checkbox(
                            label=par.tit_de,
                            key=f"cb_{par.tit_de}",
                            value=par.default,
                            disabled=True,
                        )

        st.session_state["but_meteo_main"] = st.form_submit_button("Knöpfle")


@gf.func_timer
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


@gf.func_timer
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


@gf.func_timer
def h_v_lines(fig: go.Figure | None = None) -> None:
    """Menu für horizontale und vertikale Linien"""
    fig = fig or gf.st_get("fig_base")
    if fig is None:
        return

    with st.sidebar, st.expander(
        "horizontale / vertikale Linien", expanded=False
    ), st.form("horizontale / vertikale Linien"):
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

        st.session_state["but_h_v_lines"] = st.form_submit_button("Knöpfle")


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


@gf.func_timer
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
        fig: go.Figure = st.session_state["fig_base"]
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
                # with cols[list(columns).index("name")]:
                #     st.markdown(line_name)
                with cols[list(columns).index("vis")]:
                    st.checkbox(
                        label=line_name,
                        value=all(
                            part not in line_name
                            for part in [
                                cont.SUFFIXES.col_smooth,
                                cont.SUFFIXES.col_arbeit,
                            ]
                        ),
                        key=f"cb_vis_{line_name}",
                        # label_visibility="collapsed",
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

                show_cb: bool = True
                if any(suff in line_name for suff in cont.ARBEIT_LEISTUNG.all_suffixes):
                    suff: str = [
                        suff
                        for suff in cont.ARBEIT_LEISTUNG.all_suffixes
                        if suff in line_name
                    ][0]
                    anno_name: str = anno_name.replace(suff, "")
                    if "first_suff" not in st.session_state:
                        st.session_state["first_suff"] = suff
                    if suff != st.session_state["first_suff"]:
                        show_cb = False

                if show_cb:
                    with cols[list(columns).index("anno")]:
                        st.checkbox(
                            label=anno_name,
                            value=False,
                            key=f"cb_anno_{anno_name}",
                        )

        st.markdown("###")
        but_upd_main: bool = st.form_submit_button("Knöpfle")

    return but_upd_main


@gf.func_timer
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
            line_name: str = f'{line["name"]}{cont.SUFFIXES.col_smooth}'
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


@gf.func_timer
def downloads(page: str = "graph") -> None:
    """Dateidownloads"""

    if "meteo" in page:
        if st.session_state["meteo_start_year"] == st.session_state["meteo_end_year"]:
            xl_file_name: str = (
                f"Wetterdaten {st.session_state['meteo_start_year']}.xlsx"
            )
        else:
            start: int = min(
                st.session_state["meteo_start_year"], st.session_state["meteo_end_year"]
            )
            end: int = max(
                st.session_state["meteo_start_year"], st.session_state["meteo_end_year"]
            )
            xl_file_name = f"Wetterdaten {start}-{end}.xlsx"
    else:
        xl_file_name = "Datenausgabe.xlsx"

    if "graph" in page and not any([gf.st_get("but_html"), gf.st_get("but_xls")]):
        st.markdown("###")
        # st.subheader("Downloads")

        # html-Datei
        st.button(
            label="html-Datei erzeugen",
            key="but_html",
            help="""Nach dem Erzeugen der html-Datei 
            erscheint ein Knöpfle zum herunterladen.""",
        )

        # Excel-Datei
        st.button(
            "Excel-Datei erzeugen",
            key="but_xls",
            help="""Nach dem Erzeugen der Excel-Datei erscheint 
            ein Knöpfle zum herunterladen.""",
        )

    if gf.st_get("but_html"):
        with st.spinner("Momentle bitte - html-Datei wird erzeugt..."):
            fig_cr.html_exp()

        cols: list = st.columns(3)

        with cols[1]:
            f_pn = "export/interaktive_grafische_Auswertung.html"
            with open(f_pn, "rb") as exfile:
                st.download_button(
                    label="html-Datei herunterladen",
                    data=exfile,
                    file_name=f_pn.rsplit("/", maxsplit=1)[-1],
                    mime="application/xhtml+xml",
                )
            st.button("abbrechen")

        with cols[0]:
            st.success("html-Datei hier herunterladen → → →")
        with cols[2]:
            st.success("← ← ← html-Datei hier herunterladen")

        st.markdown("---")

    if any(
        gf.st_get(key)
        for key in (
            "but_xls",
            "but_meteo_sidebar",
            "but_meteo_main",
            "excel_download",
            "cancel_excel_download",
        )
    ):
        with st.spinner("Momentle bitte - Excel-Datei wird erzeugt..."):
            if page in ("graph"):
                dic_df_ex: dict = {
                    x.name: {
                        "df": pd.DataFrame(data=x.y, index=x.x, columns=[x.name]),
                        "unit": st.session_state["metadata"][x.name].get("unit"),
                    }
                    for x in [
                        d
                        for d in st.session_state["fig_base"].data
                        if gf.check_if_not_exclude(d.name)
                    ]
                }

                df_ex: pd.DataFrame = pd.concat(
                    [dic_df_ex[df]["df"] for df in dic_df_ex], axis=1
                )
                st.session_state["df_ex"] = df_ex

            if page in ("meteo"):
                df_ex = gf.st_get("meteo_data")

            dat = ex.excel_download(df_ex, page)

        cols: list = st.columns(3)

        with cols[1]:
            st.download_button(
                label="Excel-Datei herunterladen",
                data=dat,
                file_name=xl_file_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="excel_download",
            )

            if "graph" in page:
                st.button("abbrechen", key="cancel_excel_download")

        with cols[0]:
            st.success("Excel-Datei hier herunterladen → → →")
        with cols[2]:
            st.success("← ← ← Excel-Datei hier herunterladen")
