"""Bearbeitung der Daten"""


from typing import TYPE_CHECKING, Any, Literal

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

COL_IND: str = cont.ExcelMarkers.index
COL_ORG: str = cont.ORIGINAL_INDEX_COL


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
    df_pd: pd.DataFrame = df.to_pandas().set_index(COL_IND)
    df_pd[df_pd.diff() == 0] = np.nan

    df_pd = df_pd.interpolate(method=method) or df_pd
    df_pl: pl.DataFrame = pl.from_pandas(df_pd)
    return df_pl


def split_multi(mdf: cl.MetaAndDfs, frame_to_split: str) -> pl.DataFrame:
    """Split into multiple years"""

    df: pl.DataFrame = getattr(mdf, frame_to_split)
    df_multi: dict[int, pl.DataFrame] = {}
    for year in mdf.meta.years:
        df_filtered: pl.DataFrame = (
            df.filter(pl.col(COL_IND).dt.year() == year)
            .with_columns(
                pl.col(COL_IND)
                .dt.strftime("2020-%m-%d %H:%M:%S")
                .str.strptime(pl.Datetime),
            )
            .rename(
                {
                    col: f"{col} {year}"
                    for col in [
                        col for col in df.columns if col not in [COL_IND, COL_ORG]
                    ]
                }
            )
        )

        df_multi[year] = df_filtered

    return df_multi


@gf.func_timer
def df_h(mdf: cl.MetaAndDfs) -> cl.MetaAndDfs:
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
        .sort(by=COL_IND)
        .groupby_dynamic(COL_IND, every="1h")
        .agg(
            [
                pl.col(
                    col.replace(cont.ARBEIT_LEISTUNG.leistung.suffix, "").strip()
                ).mean()
                for col in [co for co in cols if co != COL_IND]
            ]
        )
        .with_columns(pl.col(COL_IND).alias(COL_ORG))
    )

    if len(mdf.meta.years) > 1:
        # df_h_multi: dict[int, pl.DataFrame] = {}
        # for year in mdf.meta.years:
        #     df_filtered: pl.DataFrame = (
        #         mdf.df_h.filter(pl.col(COL_IND).dt.year() == year)
        #         .with_columns(
        #             pl.col(COL_IND)
        #             .dt.strftime("2020-%m-%d %H:%M:%S")
        #             .str.strptime(pl.Datetime),
        #         )
        #         .rename(
        #             {
        #                 col: f"{col} {year}"
        #                 for col in [
        #                     col
        #                     for col in mdf.df_h.columns
        #                     if col not in [COL_IND, COL_ORG]
        #                 ]
        #             }
        #         )
        #     )

        #     df_h_multi[year] = df_filtered

        mdf.df_h_multi = split_multi(mdf, "df_h")

    logger.success("DataFrame mit Stundenwerten erstellt.")
    logger.log(slog.LVLS.data_frame.name, mdf.df_h.head())

    return mdf


@gf.func_timer
def jdl(mdf: cl.MetaAndDfs) -> cl.MetaAndDfs:
    """Jahresdauerlinie"""

    if mdf.df_h is None:
        mdf.df_h = df_h(mdf)

    # Zeit-Spalte für jede Linie kopieren um sie zusammen sortieren zu können
    cols_without_index = [
        col for col in mdf.df_h.columns if col not in [COL_IND, COL_ORG]
    ]
    jdl_first_stage: pl.DataFrame = mdf.df_h.with_columns(
        [pl.col(COL_IND).alias(f"{col} - {COL_ORG}") for col in cols_without_index]
    )

    if len(mdf.meta.years) > 1:
        jdl_separate = [
            jdl_first_stage.select(pl.col(col, f"{col} - {COL_ORG}"))
            .filter(pl.col(f"{col} - {COL_ORG}").dt.year() == year)
            .sort(col, descending=True)
            .rename(
                {
                    col: f"{col} {year}",
                    f"{col} - {COL_ORG}": f"{col} - {COL_ORG} {year}",
                }
            )
            .get_columns()
            for year in mdf.meta.years
            for col in cols_without_index
        ]
    else:
        jdl_separate = [
            jdl_first_stage.select(pl.col(col, f"{col} - {COL_ORG}"))
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

    if mdf.df_h is None:
        mdf.df_h = df_h(mdf)

    cols_without_index = [
        col for col in mdf.df_h.columns if col not in [COL_IND, COL_ORG]
    ]
    mdf.mon: pl.DataFrame = mdf.df_h.groupby_dynamic(COL_IND, every="1mo").agg(
        [
            pl.col(col).mean()
            if mdf.meta.get_line_by_name(col).unit in cont.GRP_MEAN
            else pl.col(col).sum()
            for col in cols_without_index
        ]
    )

    if len(mdf.meta.years) > 1:
        # mon_multi: dict[int, pl.DataFrame] = {}
        # for year in mdf.meta.years:
        #     df_filtered: pl.DataFrame = (
        #         mdf.mon.filter(pl.col(COL_IND).dt.year() == year)
        #         .with_columns(
        #             pl.col(COL_IND)
        #             .dt.strftime("2020-%m-%d %H:%M:%S")
        #             .str.strptime(pl.Datetime),
        #         )
        #         .rename(
        #             {
        #                 col: f"{col} {year}"
        #                 for col in [
        #                     col
        #                     for col in mdf.mon.columns
        #                     if col not in [COL_IND, COL_ORG]
        #                 ]
        #             }
        #         )
        #     )

        #     df_h_multi[year] = df_filtered

        mdf.mon_multi = split_multi(mdf, "mon")

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