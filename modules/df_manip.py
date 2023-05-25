"""Bearbeitung der Daten"""


from typing import TYPE_CHECKING, Any, NamedTuple

import numpy as np
import pandas as pd
import streamlit as st
from loguru import logger

from modules import constants as cont
from modules.general_functions import func_timer
from modules.logger_setup import LogLevels

if TYPE_CHECKING:
    import datetime as dt


@func_timer
def combine_date_time_cols_and_set_index(
    df: pd.DataFrame, col_date: str = "Datum", col_time: str = "Uhrzeit"
) -> pd.DataFrame:
    """Combine a date-column and a time-column to a datetime-index.

    Also sets the index in the DataFrame.

    Args:
        - df (DataFrame): DataFrame, das geändert werden soll
        - col_date (str, optional): Spalte mit Datumswerten. Defaults to "Datum".
        - col_time (str, optional): Spalte mit Uhrzeitwerten. Defaults to "Uhrzeit".

    Returns:
        - DataFrame: DataFrame mit Datum & Uhrzeit als Index
    """
    ind: pd.DatetimeIndex = (
        pd.to_datetime(df.loc[:, col_date].to_numpy(), format="%Y-%m-%d")
        + pd.to_timedelta(
            [x.hour for x in df.loc[:, col_time].to_numpy()], unit="hours"
        )
        + pd.to_timedelta(
            [x.minute for x in df.loc[:, col_time].to_numpy()], unit="minutes"
        )
    )

    return df.set_index(ind, drop=True)


@func_timer
def fix_am_pm(df: pd.DataFrame, time_column: str = "Zeitstempel") -> pd.DataFrame:
    """Zeitreihen ohne Unterscheidung zwischen vormittags und nachmittags

    (korrigiert den Bullshit, den man immer von der SWB bekommt)

    Args:
        - df (DataFrame): DataFrame to edit
        - time_column (str, optional): Column with time data. Defaults to "Zeitstempel".

    Returns:
        - DataFrame: edited DataFrame
    """
    col: pd.Series = df[time_column]

    # Stunden haben negative Differenz und Tag bleibt gleich
    if any(col.dt.hour.diff() < 0) and any(col.dt.day.diff() == 0):
        conditions: list = [
            (col.dt.day.diff() > 0),  # neuer Tag
            (col.dt.month.diff() != 0),  # neuer Monat
            (col.dt.year.diff() != 0),  # neues Jahr
            (
                (col.dt.hour.diff() < 0)  # Stunden haben negative Differenz
                & (col.dt.day.diff() == 0)  # Tag bleibt gleich
            ),
        ]

        choices: list[Any] = [
            pd.Timedelta(0, "h"),
            pd.Timedelta(0, "h"),
            pd.Timedelta(0, "h"),
            pd.Timedelta(12, "h"),
        ]

        offset: pd.Series = pd.Series(
            data=np.select(conditions, choices, default=np.nan),
            index=col.index,
            dtype="timedelta64[ns]",
        )

        offset[0] = pd.Timedelta(0)
        offset = offset.fillna(method="ffill")

        df[time_column] += offset

    return df


class CleanUpDLS(NamedTuple):
    """Named Tuple for return value of following function"""

    df_clean: pd.DataFrame
    df_deleted: pd.DataFrame


@func_timer
def clean_up_daylight_savings(df: pd.DataFrame) -> CleanUpDLS:
    """Zeitumstellung

    Bei der Zeitumstellung auf Sommerzeit wird die Uhr eine Stunde vor gestellt,
    sodass in der Zeitreihe eine Stunde fehlt. Falls das DataFrame diese Stunde
    enthält (z.B. mit nullen in der Stunde), werden diese Zeilen gelöscht.

    Bei der Zeitumstellung auf Winterzeit wird die Uhr eine Sunde zurück gestellt.
    Dadurch gibt es die Stunde doppelt in der Zeitreihe. Das erste Auftreten der
    doppelten Stunde wird gelöscht.

    Args:
        - df (pd.DataFrame): DataFrame to edit

    Returns:
        - dict[str, pd.DataFrame]:
            - "df_clean": edited DataFrame
            - "df_deleted": deleted data
    """
    # ind: pd.DatetimeIndex = pd.DatetimeIndex(data=df.index).round("s")
    ind: pd.DatetimeIndex = (
        df.index
        if isinstance(df.index, pd.DatetimeIndex)
        else pd.to_datetime(df.index, dayfirst=True)
    )
    # Sommerzeitumstellung: letzter Sonntag im Maerz - von 2h auf 3h
    summer: np.ndarray = (
        (ind.month == 3)  # Monat = 3 ---> März
        & (ind.day > (31 - 7))  # letzte Woche (Tag > 31-7)
        & (ind.weekday == 6)  # Wochentag = 6 ---> Sonntag
        & (ind.hour == 2)  # Stunde 2 wird ausgelassen
    )

    # Winterzeitumstellung: doppelte Stunde
    winter: np.ndarray = df.index.duplicated(keep="first")

    df_clean: pd.DataFrame = df[~summer & ~winter]
    df_deleted: pd.DataFrame = df[summer | winter]

    if len(df_deleted.index) > 0:
        logger.warning("Data deleted due to daylight savings.")
        logger.log(LogLevels.DATA_FRAME.name, df_deleted)
    else:
        logger.info("No data deleted due to daylight savings")

    return CleanUpDLS(df_clean=df_clean, df_deleted=df_deleted)


@func_timer
def interpolate_missing_data(df: pd.DataFrame, method: str = "akima") -> pd.DataFrame:
    """Findet stellen an denen sich von einer Zeile zur nächsten
    die Daten nicht ändern, löscht die Daten und interpoliert die Lücken

    Args:
        - df (pd.DataFrame): DataFrame to edit
        - method (str): method of interpolation. Defaults to "akima".

    Returns:
        - pd.DataFrame: edited DataFrame
    """

    df[df.diff() == 0] = np.nan

    return df.interpolate(method=method) or df


@func_timer
def del_smooth() -> None:
    """Löscht gegelättete Linien aus den DataFrames
    und Grafiken im Stremalit SessionState
    """

    # Spalten in dfs löschen
    for item in st.session_state:
        if isinstance(item, pd.DataFrame):
            for col in [str(col) for col in item.columns]:
                if cont.SMOOTH_SUFFIX in col:
                    item.drop(columns=[col], inplace=True)

    # Linien löschen
    lis_dat: list = [
        dat
        for dat in st.session_state["fig_base"].data
        if cont.SMOOTH_SUFFIX not in dat.name
    ]
    st.session_state["fig_base"].data = tuple(lis_dat)


@func_timer
def split_up_df_multi_years(df: pd.DataFrame) -> dict[int, pd.DataFrame]:
    """Split up a DataFrame that has data for multiple years into separate
    DataFrames for each year. The columns names are suffixed with the year.
    The index of all DataFrames is set to the year 2020.

    Args:
        - df (pd.DataFrame): DataFrame to edit

    Returns:
        - dict (int, pd.DataFrame):
            - key (int)= year
            - item (pd.DataFrame)= edited DataFrame
    """

    ind: pd.DatetimeIndex = pd.DatetimeIndex(data=df.index)
    years: list[int] = st.session_state["years"]

    df_multi: dict[int, pd.DataFrame] = {}
    for year in years:
        df_multi[year] = df[ind.year == year].copy()
        df_multi[year]["orgidx"] = df.loc[ind.year == year, :].index

        for col in [
            str(col)
            for col in df_multi[year].columns
            if all(exc not in str(col) for exc in cont.EXCLUDE)
        ]:
            new_col_name: str = f'{col.replace(" *h","")} {year}'
            if any(suff in col for suff in cont.ARBEIT_LEISTUNG.get_all_suffixes()):
                for suff in cont.ARBEIT_LEISTUNG.get_all_suffixes():
                    if suff in col:
                        new_col_name = f"{col.split(suff)[0]} {year}{suff}"

            df_multi[year] = df_multi[year].rename(columns={col: new_col_name})
            st.session_state["metadata"][new_col_name] = st.session_state["metadata"][
                col
            ].copy()

            st.session_state["metadata"][new_col_name]["tit"] = new_col_name

    for frame in df_multi.values():
        ind: pd.DatetimeIndex = pd.DatetimeIndex(frame.index)
        frame.index = pd.to_datetime(ind.strftime("2020-%m-%d %H:%M:%S"))

    return df_multi


@func_timer
def df_multi_y(df: pd.DataFrame) -> None:
    """Mehrere Jahre"""

    years: list[int] = st.session_state["years"]

    df_multi: dict[int, pd.DataFrame] = split_up_df_multi_years(df)

    st.session_state["dic_df_multi"] = df_multi

    # df geordnete Jahresdauerlinie
    if st.session_state.get("cb_jdl"):
        dic_jdl: dict[int, pd.DataFrame] = {y: jdl(df_multi[y]) for y in years}
        st.session_state["dic_jdl"] = dic_jdl

    # df Monatswerte
    if st.session_state.get("cb_mon"):
        dic_mon: dict[int, pd.DataFrame] = {
            year: mon(df_multi[year], st.session_state["metadata"], year)
            for year in years
        }

        st.session_state["dic_mon"] = dic_mon


@func_timer
def h_from_other(df: pd.DataFrame, meta: dict[str, Any] | None = None) -> pd.DataFrame:
    """Stundenwerte aus anderer zeitlicher Auflösung"""

    df_h: pd.DataFrame = pd.DataFrame()
    metadata: dict[str, Any] = meta or st.session_state["metadata"]
    extended_exclude: list[str] = [
        *cont.EXCLUDE,
        cont.ARBEIT_LEISTUNG.arbeit.suffix,
    ]
    suff_leistung: str = cont.ARBEIT_LEISTUNG.leistung.suffix

    for col in [
        str(col)
        for col in df.columns
        if all(excl not in str(col) for excl in extended_exclude)
    ]:
        col_h: str = f"{col} *h".replace(suff_leistung, "")
        if col.endswith(" *h"):
            df_h[col_h] = df[col].copy()
        else:
            metadata[col_h] = metadata[col].copy()

        if metadata["index"]["td_mean"] < pd.Timedelta(hours=1):
            if metadata[col]["unit"] in cont.GRP_MEAN:
                df_h[col_h] = df[col].resample("H").mean()
            else:
                df_h[col_h] = df[col].resample("H").sum()

        if metadata["index"]["td_mean"] == pd.Timedelta(hours=1):
            df_h[col_h] = df[col].copy()

    df_h["orgidx"] = df_h.index.copy()
    df_h = df_h.infer_objects()
    st.session_state["metadata"] = metadata

    logger.success("DataFrame mit Stundenwerten erstellt.")
    logger.log(LogLevels.DATA_FRAME.name, df_h.head())

    return df_h


def check_if_hourly_resolution(
    df: pd.DataFrame, **kwargs: dict[str, Any]
) -> pd.DataFrame:
    """Check if the given DataFrame is in hourly resolution.
    If not, give out DataFrame in hourly resolution

    Args:
        - df (pd.DataFrame): The DataFrame in question
        - dic_meta (dict, optional): Metadata. Defaults to st.session_state["metadata"].

    Returns:
        - pd.DataFrame: DataFrame in hourly resolution
    """
    metadata: dict[str, Any] = kwargs.get("meta") or st.session_state["metadata"]
    extended_exclude: list[str] = [
        *cont.EXCLUDE,
        cont.ARBEIT_LEISTUNG.arbeit.suffix,
    ]
    suff_leistung: str = cont.ARBEIT_LEISTUNG.leistung.suffix

    ind_td: pd.Timedelta = pd.to_timedelta(df.index.to_series().diff()).mean()
    df_h: pd.DataFrame = pd.DataFrame()
    if ind_td.round("min") < pd.Timedelta(hours=1):
        df_h = h_from_other(df)
    else:
        logger.info("df schon in Stundenauflösung")
        for col in [
            str(col)
            for col in df.columns
            if all(excl not in str(col) for excl in extended_exclude)
        ]:
            col_h: str = f"{col} *h".replace(suff_leistung, "")
            df_h[col_h] = df[col].copy()
            metadata[col_h] = metadata[col].copy()
            if "metadata" in st.session_state:
                st.session_state["metadata"][col_h] = metadata[col].copy()

    df_h = df_h.infer_objects()

    return df_h


@func_timer
def jdl(df: pd.DataFrame) -> pd.DataFrame:
    # sourcery skip: remove-unnecessary-cast
    """Jahresdauerlinie"""

    df_h: pd.DataFrame = check_if_hourly_resolution(df)

    df_jdl: pd.DataFrame = pd.DataFrame(
        index=range(1, len(df_h.index) + 1),
        columns=[c for c in df_h.columns if c != "orgidx"],
    )

    for col in [str(col) for col in df_jdl.columns]:
        df_col: pd.DataFrame = df_h.sort_values(
            col, ascending=bool(df_h[col].mean() < 0)
        )

        df_jdl[col] = df_col[col].to_numpy()

        df_jdl[col + "_orgidx"] = (
            df_col["orgidx"].to_numpy() if "orgidx" in df_col.columns else df_col.index
        )

    df_jdl = df_jdl.infer_objects()
    st.session_state["df_jdl"] = df_jdl

    logger.success("DataFrame für Jahresdauerlinie erstellt.")
    logger.log(LogLevels.DATA_FRAME.name, df_jdl.head())

    return df_jdl


@func_timer
def mon(df: pd.DataFrame, meta: dict, year: int | None = None) -> pd.DataFrame:
    """Monatswerte"""

    df_h: pd.DataFrame = check_if_hourly_resolution(df, meta=meta)

    df_mon: pd.DataFrame = df_h.resample("M").sum(numeric_only=True)
    df_mon.columns = [str(col).replace("*h", "*mon") for col in df_mon.columns]

    if mean_cols := [
        str(col)
        for col in df_h.columns
        if meta[col]["unit"]
        in [unit for unit in cont.GRP_MEAN if unit not in [" kWh", " kW"]]
    ]:
        for col in mean_cols:
            df_mon[str(col).replace("*h", "*mon")] = df_h[col].resample("M").mean()

    for col in df_mon.columns:
        meta[col] = meta[str(col).replace("*mon", "*h")].copy()
        meta[col]["unit"] = " kWh" if meta[col]["unit"] == " kW" else meta[col]["unit"]

    ind: pd.DatetimeIndex = pd.DatetimeIndex(df_mon.index)
    df_mon.index = pd.to_datetime(ind.strftime("%Y-%m-15"))

    if year:
        df_mon["orgidx"] = [
            df_mon.index[x].replace(year=year) for x in range(len(df_mon.index))
        ]
    else:
        df_mon["orgidx"] = df_mon.index.copy()

    df_mon = df_mon.infer_objects()

    st.session_state["df_mon"] = df_mon

    logger.success("DataFrame mit Monatswerten erstellt.")
    logger.log(LogLevels.DATA_FRAME.name, df_mon.head())

    return df_mon


@func_timer
def dic_days(df: pd.DataFrame) -> None:
    """Create Dictionary for Days"""

    st.session_state["dic_days"] = {}
    for num in range(int(st.session_state["ni_days"])):
        date: dt.date = st.session_state[f"day_{str(num)}"]
        item: pd.DataFrame = df.loc[[f"{date:%Y-%m-%d}"]].copy()

        indx: pd.DatetimeIndex = pd.DatetimeIndex(item.index)
        item["orgidx"] = indx.copy()
        item.index = pd.to_datetime(indx.strftime("2020-1-1 %H:%M:%S"))

        st.session_state["dic_days"][f"{date:%d. %b %Y}"] = item
