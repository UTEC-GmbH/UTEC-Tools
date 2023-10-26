"""Menus für die Meteorologie-Seite"""

import datetime as dt
import re
from typing import Any

import polars as pl
import streamlit as st
from loguru import logger

from modules import classes_data as cld
from modules import constants as cont
from modules import export as ex
from modules import general_functions as gf
from modules import meteorolog as met
from modules import streamlit_functions as sf
import modules.meteo_classes


def sidebar_address_dates() -> None:
    """Adresse und Daten"""
    now: dt.datetime = dt.datetime.now()

    with st.sidebar, st.form("Standort und Daten"):
        st.text_area(
            label="Adresse",
            value="Cuxhavener Str. 10  \n20217 Bremen",
            help=(
                """
                Je genauer, desto besser, 
                aber es reicht auch nur eine Stadt.  \n
                _(Es wird eine Karte angezeigt, mit der kontrolliert werden kann, 
                ob die richtige Adresse gefunden wurde.)_
                """
            ),
            key="ta_adr",
        )

        cols: list = st.columns([60, 40])
        with cols[0]:
            st.date_input(
                label="Startdatum",
                format="DD.MM.YYYY",
                value=dt.date(now.year, 1, 1),
                key="di_start",
            )
        with cols[1]:
            st.time_input(label="Zeit", value=dt.time(0, 0), key="ti_start")

        cols: list = st.columns([60, 40])
        with cols[0]:
            st.date_input(
                label="Enddatum",
                format="DD.MM.YYYY",
                value=dt.date(now.year, now.month, now.day - 1),
                key="di_end",
            )
        with cols[1]:
            st.time_input(label="Zeit", value=dt.time(23, 59), key="ti_end")

        st.selectbox(
            label="Gewünschte Datenauflösung",
            options=[res.de for res in cont.TIME_RESOLUTIONS.values()],
            index=list(cont.TIME_RESOLUTIONS.keys()).index("1h"),
            help=(
                """
                Es liegen nicht immer Daten in der gewünschten Auflösung direkt vor.  \n
                Falls nötig, werden Daten mit anderer Auflösung interpoliert, bzw.  \n
                per Mittelwert oder Summe auf die gewünschte Auflösung gebracht.  \n
                """
            ),
            key="sb_resolution",
        )

        st.toggle(
            label="Polysun Wetterdaten",
            value=False,
            key="tog_polysun",
            help=(
                """
                Wetterdaten, die in Polysun eingelesen werden können.  \n  \n
                Falls nicht anders angegeben, werden die Daten in stündlicher
                auflösung erzeugt. Standardmäßig werden folgende Parameter gewählt:  \n
                - Globalstrahlung [Wh/m2]  \n
                - Diffuse Strahlung [Wh/m2]  \n
                - Langwällige Strahlung [Wh/m2]  \n
                - Lufttemperatur [°C]  \n
                - Windgeschwindigkeit [m/s]  \n
                - Relative Luftfeuchte [%]
                """
            ),
        )

        st.markdown("###")
        st.session_state["but_addr_dates"] = st.form_submit_button(
            "Knöpfle", use_container_width=True
        )


@gf.func_timer
def sidebar_dwd_query_limits() -> None:
    """DWD Zeit- und Entfernungsgrenzen"""

    with st.sidebar, st.expander("Sucheinstellungen"), st.form("DWD Query Limits"):
        st.number_input(
            label="Entfernung [km]",
            value=150,
            help=(
                """
                Bei der Suche nach Wetterdaten werden Wetterstationen in einem 
                Umkreis bis zur hier vorgegebenen Entfernung einbezogen.  
                """
            ),
            format="%i",
            key="ni_limit_dist",
        )
        st.number_input(
            label="Zeitlimit [s]",
            value=15,
            help=(
                """
                Die Suche nach Wetterdaten läuft für die hier eingegebene Zeit. 
                Wird in dieser Zeit keine Wetterstation mit Daten gefunden, 
                wird angenommen, dass keine Daten vorhanden sind.  
                """
            ),
            format="%i",
            key="ni_limit_time",
        )

        st.session_state["but_dwd_query_limits"] = st.form_submit_button(
            "Knöpfle", use_container_width=True
        )


@gf.func_timer
def parameter_selection() -> None:
    """DWD-Parameter data editor"""

    param_data: list[dict] = [
        {
            "Parameter": par.name_de,
            "Einheit": par.unit,
            "Auswahl": par.name_en
            in (
                cont.DWD_PARAMS_POLYSUN
                if sf.s_get("tog_polysun")
                else cont.DWD_DEFAULT_PARAMS
            ),
        }
        for par in met.ALL_PARAMETERS.values()
    ]

    st.markdown("###")
    with st.form("Parameter"):
        edited: list[dict] = st.data_editor(
            data=sorted(
                sorted(param_data, key=lambda s: s["Parameter"]),
                key=lambda sort: sort["Auswahl"],
                reverse=True,
            ),
            use_container_width=True,
            key="de_parameter",
        )
        st.session_state["but_param"] = st.form_submit_button(
            "Knöpfle", use_container_width=True
        )

    selected: list[str] = [
        next(
            (
                name_en
                for name_en, name_de in cont.DWD_PARAM_TRANSLATION.items()
                if name_de == par["Parameter"]
            ),
            None,  # type: ignore
        )
        or par["Parameter"]
        for par in edited
        if par["Auswahl"]
    ]
    sf.s_set("selected_params", selected)

    #  logger.debug(f"Selected Params: {selected}")

    if any(
        sf.s_get(but)
        for but in [
            "but_param",
            "but_dwd_query_limits",
            "but_addr_dates",
            cont.BUTTONS.download_weather.key,
        ]
    ) or (
        len(selected) == len(cont.DWD_DEFAULT_PARAMS)
        and all(par in selected for par in cont.DWD_DEFAULT_PARAMS)
    ):
        params: list[
            modules.meteo_classes.DWDParam
        ] = met.collect_meteo_data_for_list_of_parameters(
            parameter_names=sf.s_get("selected_params") or cont.DWD_DEFAULT_PARAMS,
            temporal_resolution=sf.s_get("sb_resolution") or "Stundenwerte",
        )
        sf.s_set("dwd_params", params)

        st.dataframe(
            data=[
                {
                    "Parameter": param.name_de,
                    "Auflösung": param.closest_available_res.name_de,
                    "Wetterstation": param.closest_available_res.closest_station.name,
                    "Entfernung": param.closest_available_res.closest_station.distance,
                }
                for param in params
                if param.closest_available_res is not None
            ],
            column_config={
                "Entfernung": st.column_config.NumberColumn(
                    format="%.2f km", width="small"
                ),
            },
            use_container_width=True,
        )

        explanation_of_results(params)


def explanation_of_results(params: list[modules.meteo_classes.DWDParam]) -> Any:
    """Comments on the results depending on the collected data"""

    logger.debug(
        gf.string_new_line_per_item(
            [f"{par.name_de}: {par.requested_res_name_en}" for par in params],
            "Requested Resolutions:",
            1,
            1,
        )
    )

    logger.debug(
        gf.string_new_line_per_item(
            [
                f"{par.name_de}: {par.closest_available_res.name_en}"
                for par in params
                if par.closest_available_res is not None
            ],
            "Closest Resolutions:",
            1,
            1,
        )
    )

    logger.debug(
        gf.string_new_line_per_item(
            [
                f"{par.name_de}: {par.closest_available_res.no_data}"
                for par in params
                if par.closest_available_res is not None
            ],
            "No Data:",
            1,
            1,
        )
    )

    if any(
        (
            par.closest_available_res is not None
            and isinstance(par.closest_available_res.no_data, str)
        )
        for par in params
    ):
        all_no_data_strings: list[str] = [
            par.closest_available_res.no_data
            for par in params
            if par.closest_available_res is not None
            and isinstance(par.closest_available_res.no_data, str)
        ]
        return st.warning(
            "\n\n".join(
                [
                    "⚡ **Es konnten nicht für alle Parameter Daten gefunden werden!** ⚡",
                    *all_no_data_strings,
                ]
            )
        )

    if any(
        (
            par.closest_available_res is not None
            and par.closest_available_res.name_en != par.requested_res_name_en
        )
        for par in params
    ):
        pars_with_other_res: list[modules.meteo_classes.DWDParam] = [
            par
            for par in params
            if par.closest_available_res is not None
            and par.closest_available_res.name_en != par.requested_res_name_en
        ]
        if (
            len(pars_with_other_res) <= 1
            and pars_with_other_res[0].closest_available_res is not None
        ):
            return st.info(
                "Die Daten für den Parameter "
                f"__{pars_with_other_res[0].name_de}__ "
                "wurden nicht in der gewünschten Auflösung gefunden. "
                "Sie wurden in der Auflösung "
                f"__{pars_with_other_res[0].closest_available_res.name_de}__ "
                "geladen und umgerechnet. Dabei können geringfügige "
                "Ungenauigkeiten entstanden sein."
            )

        joined_par_names: str = "\n".join([par.name_de for par in pars_with_other_res])
        return st.info(
            f"Die Daten für die Parameter:\n\n {joined_par_names} \n\n"
            "wurden nicht in der gewünschten Auflösung gefunden. "
            "Sie wurden in einer anderen Auflösung (siehe Tabelle) "
            "geladen und umgerechnet. Dabei können geringfügige "
            "Ungenauigkeiten entstanden sein."
        )
    return st.success("_Daten für alle Parameter in gewünschter Auflösung gefunden._")


def download_weatherdata() -> None:
    """Data as Excel-File"""

    dat: list[modules.meteo_classes.DWDParam] = sf.s_get(
        "dwd_params"
    ) or met.collect_meteo_data_for_list_of_parameters(
        parameter_names=sf.s_get("selected_params") or cont.DWD_DEFAULT_PARAMS,
    )

    address_from_text_area: str = sf.s_get("ta_adr") or ""
    address: str = re.sub(
        r"\s+",
        " ",
        re.sub(r"\s+", " ", address_from_text_area.replace("\n", ", ")).replace(
            " ,", ","
        ),
    )
    file_name_city: str = f" -{address}-"

    file_name_time: str = ""
    if dat[0].time_span is not None:
        file_name_time = (
            f" {dat[0].time_span.start.date()} bis {dat[0].time_span.end.date()}"
        )
    file_suffix: str = f"{file_name_city}{file_name_time}"
    df_ex: pl.DataFrame = met.df_from_param_list(dat)

    if sf.s_get("tog_polysun"):
        download_polysun(df_ex, file_suffix)
    else:
        download_excel(df_ex, dat, file_suffix)


def download_polysun(df_ex: pl.DataFrame, file_suffix: str) -> None:
    """Wenn 'Datei erzeugen'-Knopf gedrückt wurde"""

    df_ex = (
        pl.DataFrame({"Time [s]": range(0, cont.TIME_SEC.year, cont.TIME_SEC.hour)})
        .join(
            df_ex.with_columns(
                (
                    pl.col("Datum")
                    - dt.datetime(df_ex.get_column("Datum")[0].year, 1, 1, 0, 0)
                )
                .dt.seconds()
                .alias("Time [s]")
            ),
            "Time [s]",
            "left",
        )
        .fill_null(0)
    ).select(
        [
            pl.col("Time [s]"),
            *[
                pl.col(name_en).alias(poly)
                for name_en, poly in cont.DWD_PARAMS_POLYSUN.items()
                if name_en in df_ex.columns
            ],
        ]
    )

    st.download_button(
        **cont.BUTTONS.download_weather.func_args(),
        data=f"# {df_ex.write_csv()}",
        file_name=f"Polysun Wetterdaten{file_suffix}.csv",
        mime="text/csv",
    )


def download_excel(
    df_ex: pl.DataFrame, dat: list[modules.meteo_classes.DWDParam], file_suffix: str
) -> None:
    """Download Excel-file"""
    meta: cld.MetaData = cld.MetaData(
        lines={
            par.name_de: cld.MetaLine(
                name=par.name_de,
                name_orgidx="Datum",
                orig_tit=par.name_de,
                tit=par.name_de,
                unit=par.unit,
                excel_number_format=par.num_format,
            )
            for par in dat
        }
    )

    st.download_button(
        **cont.BUTTONS.download_weather.func_args(),
        data=ex.excel_download({cont.ST_PAGES.meteo.excel_ws_name: df_ex}, meta),
        file_name=f"Wetterdaten{file_suffix}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
