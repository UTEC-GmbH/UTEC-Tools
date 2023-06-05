"""Bearbeitung der Daten"""


from dataclasses import replace
from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd
import polars as pl
import streamlit as st
from loguru import logger

from modules import classes as cl
from modules import constants as cont
from modules import general_functions as gf
from modules import setup_logger as slog

if TYPE_CHECKING:
    import datetime as dt


@gf.func_timer
def fix_am_pm(df: pl.DataFrame, time_column: str = "Zeitstempel") -> pl.DataFrame:
    """Zeitreihen ohne Unterscheidung zwischen vormittags und nachmittags

    (korrigiert den Bullshit, den man immer von der SWB bekommt)

    Args:
        - df (DataFrame): DataFrame to edit
        - time_column (str, optional): Column with time data. Defaults to "Zeitstempel".

    Returns:
        - DataFrame: edited DataFrame
    """
    col: pl.Series = df.get_column(time_column)

    # Stunden haben negative Differenz und Tag bleibt gleich
    if any(col.dt.hour().diff() < 0) and any(col.dt.day().diff() == 0):
        conditions: list = [
            (col.dt.day().diff() > 0),  # neuer Tag
            (col.dt.month().diff() != 0),  # neuer Monat
            (col.dt.year().diff() != 0),  # neues Jahr
            (
                (col.dt.hour().diff() < 0)  # Stunden haben negative Differenz
                & (col.dt.day().diff() == 0)  # Tag bleibt gleich
            ),
        ]

        choices: list[Any] = [
            pl.duration(hours=0),
            pl.duration(hours=0),
            pl.duration(hours=0),
            pl.duration(hours=12),
        ]

        offset: pl.Series = pl.Series(
            name="offset",
            values=np.select(conditions, choices, default=pl.lit(None)),
        )

        offset[0] = pl.duration(hours=0)
        offset.fill_null(strategy="forward")

        df[time_column] += offset

        time_diff: pl.Series = df.get_column(time_column)

        new_day: pl.Series = time_diff.dt.day().diff() > 0
        midday: pl.Series = (time_diff.dt.hour() < 0) & (time_diff.dt.day() == 0)

        df = df.with_columns(
            [
                pl.when(
                    (time_diff.dt.day().diff() > 0)
                    | (time_diff.dt.month().diff() != 0)
                    | (time_diff.dt.year().diff() != 0)
                )
                .then(pl.duration(hours=0))
                .otherwise(
                    pl.when((time_diff.dt.hour() < 0) & (time_diff.dt.day() == 0))
                    .then(pl.duration(hours=12))
                    .otherwise(pl.when((time_diff.dt.hour())))
                )
                .alias("change")
                .fill_null(strategy="forward")
            ]
        )

    return df


@gf.func_timer
def interpolate_missing_data(df: pl.DataFrame, method: str = "akima") -> pl.DataFrame:
    """Findet stellen an denen sich von einer Zeile zur nächsten
    die Daten nicht ändern, löscht die Daten und interpoliert die Lücken

    Args:
        - df (pd.DataFrame): DataFrame to edit
        - method (str): method of interpolation. Defaults to "akima".

    Returns:
        - pd.DataFrame: edited DataFrame
    """
    df_pd: pd.DataFrame = df.to_pandas().set_index(cont.ExcelMarkers.index)
    df_pd[df_pd.diff() == 0] = np.nan

    df_pd = df_pd.interpolate(method=method) or df_pd
    df_pl: pl.DataFrame = pl.from_pandas(df_pd)
    return df_pl


@gf.func_timer
def split_up_df_multi_years(mdf: cl.MetaAndDfs) -> cl.MetaAndDfs:
    """Split up a DataFrame that has data for multiple years into separate
    DataFrames for each year. The columns names are suffixed with the year.
    The index of all DataFrames is set to the year 2020.

    Args:
        - df (DataFrame): DataFrame to split
        - meta (MetaData): meta data

    Returns:
        - dict (int, pd.DataFrame):
            - key (int): year
            - item (DataFrame): DataFrame for the year in 'key'
        - meta (MetaData): meta data
    """
    index: str = cont.ExcelMarkers.index
    years: list[int] = mdf.meta.years or []

    df_multi: dict[int, pl.DataFrame] = {}
    for year in years:
        df_filtered: pl.DataFrame = mdf.df.filter(pl.col(index).dt.year() == year)
        df_multi[year][cont.ORIGINAL_INDEX_COL] = df_filtered.get_column(
            cont.ORIGINAL_INDEX_COL
        )
        df_filtered = mdf.df.with_columns(
            pl.col(index).dt.strftime("2020-%m-%d %H:%M:%S").str.strptime(pl.Datetime)
        )

        for col in [
            column
            for column in df_filtered.columns
            if all(exc not in column for exc in cont.EXCLUDE)
        ]:
            new_col_name: str = f'{col.replace(" *h","")} {year}'
            if any(suff in col for suff in cont.ARBEIT_LEISTUNG.get_all_suffixes()):
                for suff in cont.ARBEIT_LEISTUNG.get_all_suffixes():
                    if suff in col:
                        new_col_name = f"{col.split(suff)[0]} {year}{suff}"

            df_filtered = df_filtered.rename({col: new_col_name})
            new_line: cl.MetaLine = replace(
                mdf.meta.get_line_by_name(col), name=new_col_name
            )
            mdf.meta.lines += [replace(new_line, tit=new_col_name)]

        df_multi[year] = df_filtered

    mdf.df_multi = df_multi

    return mdf


@gf.func_timer
def df_multi_y(mdf: cl.MetaAndDfs) -> cl.MetaAndDfs:
    """Mehrere Jahre"""

    years: list[int] = mdf.meta.years or []

    mdf = split_up_df_multi_years(mdf)

    gf.st_new("dic_df_multi", mdf.df_multi)

    if not mdf.df_multi:
        return mdf

    # df geordnete Jahresdauerlinie
    if gf.st_check("cb_jdl"):
        mdf.jdl_multi = {y: jdl(mdf.df_multi[y]) for y in years}
        gf.st_new("dic_jdl", mdf.jdl_multi)

    # df Monatswerte
    if gf.st_check("cb_mon"):
        mdf.mon_multi = {
            year: mon(mdf.df_multi[year], st.session_state["metadata"], year)
            for year in years
        }
        gf.st_new("dic_mon", mdf.mon_multi)

    return mdf


@gf.func_timer
def h_from_other(mdf: cl.MetaAndDfs) -> cl.MetaAndDfs:
    """Stundenwerte aus anderer zeitlicher Auflösung"""

    extended_exclude: list[str] = [
        *cont.EXCLUDE,
        cont.ARBEIT_LEISTUNG.arbeit.suffix,
    ]
    cols = [
        col
        for col in mdf.df.columns
        if all(excl not in col for excl in extended_exclude)
    ]

    mdf.df_h = (
        pl.DataFrame(
            [
                mdf.df.get_column(col).alias(
                    col.replace(cont.ARBEIT_LEISTUNG.leistung.suffix, "").strip()
                )
                for col in cols
            ]
        )
        .sort(by=cont.ExcelMarkers.index)
        .groupby_dynamic(cont.ExcelMarkers.index, every="1h")
        .agg(
            [
                pl.col(
                    col.replace(cont.ARBEIT_LEISTUNG.leistung.suffix, "").strip()
                ).mean()
                for col in [co for co in cols if co != cont.ExcelMarkers.index]
            ]
        )
    )

    logger.success("DataFrame mit Stundenwerten erstellt.")
    logger.log(slog.LVLS.data_frame.name, mdf.df_h.head())

    return mdf


# def check_if_hourly_resolution(
#     df: pd.DataFrame, **kwargs: dict[str, Any]
# ) -> pd.DataFrame:
#     """Check if the given DataFrame is in hourly resolution.
#     If not, give out DataFrame in hourly resolution

#     Args:
#         - df (pd.DataFrame): The DataFrame in question
#         - dic_meta (dict, optional): Metadata. Defaults to st.session_state["metadata"].

#     Returns:
#         - pd.DataFrame: DataFrame in hourly resolution
#     """
#     metadata: dict[str, Any] = kwargs.get("meta") or st.session_state["metadata"]
#     extended_exclude: list[str] = [
#         *cont.EXCLUDE,
#         cont.ARBEIT_LEISTUNG.arbeit.suffix,
#     ]
#     suff_leistung: str = cont.ARBEIT_LEISTUNG.leistung.suffix

#     ind_td: pd.Timedelta = pd.to_timedelta(df.index.to_series().diff()).mean()
#     df_h: pd.DataFrame = pd.DataFrame()
#     if ind_td.round("min") < pd.Timedelta(hours=1):
#         df_h = h_from_other(df)
#     else:
#         logger.info("df schon in Stundenauflösung")
#         for col in [
#             str(col)
#             for col in df.columns
#             if all(excl not in str(col) for excl in extended_exclude)
#         ]:
#             col_h: str = f"{col} *h".replace(suff_leistung, "")
#             df_h[col_h] = df[col].copy()
#             metadata[col_h] = metadata[col].copy()
#             if "metadata" in st.session_state:
#                 st.session_state["metadata"][col_h] = metadata[col].copy()

#     df_h = df_h.infer_objects()

#     return df_h


@gf.func_timer
def jdl(mdf: cl.MetaAndDfs) -> cl.MetaAndDfs:
    # sourcery skip: remove-unnecessary-cast
    """Jahresdauerlinie"""

    cols_without_index = [
        col for col in mdf.df_h.columns if col != cont.ExcelMarkers.index
    ]
    jdl_first_stage: pl.DataFrame = mdf.df_h.with_columns(
        [
            pl.col(cont.ExcelMarkers.index).alias(f"{col} - {cont.ORIGINAL_INDEX_COL}")
            for col in cols_without_index
        ]
    )

    jdl_separate = [
        jdl_first_stage.select(pl.col(col, f"{col} - {cont.ORIGINAL_INDEX_COL}"))
        .sort(col, descending=True)
        .get_columns()
        for col in cols_without_index
    ]
    mdf.jdl = pl.DataFrame(sum(jdl_separate, [])).with_row_count("Stunden")
    logger.success("DataFrame für Jahresdauerlinie erstellt.")
    logger.log(slog.LVLS.data_frame.name, mdf.jdl.head())

    return mdf


@gf.func_timer
def mon(mdf: cl.MetaAndDfs) -> cl.MetaAndDfs:
    """Monatswerte"""

    if not mdf.df_h:
        return mdf

    cols_without_index = [
        col for col in mdf.df_h.columns if col != cont.ExcelMarkers.index
    ]
    mdf.mon: pl.DataFrame = mdf.df_h.groupby_dynamic(
        cont.ExcelMarkers.index, every="1mo"
    ).agg(
        [
            pl.col(col).mean()
            if mdf.meta.get_line_by_name(col).unit in cont.GRP_MEAN
            else pl.col(col).sum()
            for col in cols_without_index
        ]
    )

    logger.success("DataFrame mit Monatswerten erstellt.")
    logger.log(slog.LVLS.data_frame.name, mdf.mon.head())


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

    return df_mon


@gf.func_timer
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
