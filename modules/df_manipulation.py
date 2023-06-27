"""Bearbeitung der Daten"""


from typing import TYPE_CHECKING, Any, Literal

import numpy as np
import polars as pl
from loguru import logger

from modules import classes_data as cld
from modules import classes_errors as cle
from modules import constants as cont
from modules import general_functions as gf
from modules import meteorolog as met
from modules import setup_logger as slog

if TYPE_CHECKING:
    import datetime as dt

    import pandas as pd

COL_IND: str = cont.SPECIAL_COLS.index
COL_ORG: str = cont.SPECIAL_COLS.original_index


# FIX_AM_PM FUNKTIONIERT NOCH NICHT
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
                    .otherwise(pl.when(time_diff.dt.hour()))
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


def add_air_temperature(mdf: cld.MetaAndDfs) -> cld.MetaAndDfs:
    """Add air temperature for given address to the base data frame"""

    parameters: list[cld.DWDParameter] = met.meteo_df(mdf)

    for parameter in parameters:
        df_parameter: pl.DataFrame | None = parameter.data_frame
        if df_parameter is None:
            continue
        mdf.df = mdf.df.join(
            mdf.df.select(cont.SPECIAL_COLS.index)
            .join(df_parameter, on=cont.SPECIAL_COLS.index, how="outer")
            .sort(cont.SPECIAL_COLS.index)
            .interpolate()
            .fill_null(strategy="forward"),
            on=cont.SPECIAL_COLS.index,
        )
        par_nam: str = parameter.name_de or parameter.name
        mdf.meta.lines[par_nam] = cld.MetaLine(
            name=par_nam,
            name_orgidx=f"{par_nam}{cont.SUFFIXES.col_original_index}",
            orig_tit=par_nam,
            tit=par_nam,
            unit=parameter.unit,
        )

    return mdf


def split_multi_years(
    mdf: cld.MetaAndDfs, frame_to_split: Literal["df", "df_h", "mon"]
) -> dict[int, pl.DataFrame]:
    """Split into multiple years"""

    df: pl.DataFrame = getattr(mdf, frame_to_split)
    if not mdf.meta.years:
        raise cle.NotFoundError(entry="list of years", where="mdf.meta.years")

    df_multi: dict[int, pl.DataFrame] = {}
    for year in mdf.meta.years:
        col_rename: dict[str, str] = multi_year_column_rename(df, year)
        for old_name, new_name in col_rename.items():
            if new_name not in mdf.meta.lines:
                mdf.meta.lines[new_name] = mdf.meta.lines[old_name]

        df_multi[year] = (
            df.filter(pl.col(COL_IND).dt.year() == year)
            .with_columns(
                pl.col(COL_IND)
                .dt.strftime("2020-%m-%d %H:%M:%S")
                .str.strptime(pl.Datetime),
            )
            .rename(col_rename)
        )

    logger.debug("  \n".join(["Meta for following lines available:", *mdf.meta.lines]))

    return df_multi


def multi_year_column_rename(df: pl.DataFrame, year: int) -> dict[str, str]:
    """Rename columns for multi year data"""
    col_rename: dict[str, str] = {}
    for col in [col for col in df.columns if gf.check_if_not_exclude(col)]:
        new_col_name: str = f"{col} {year}"
        if any(suff in col for suff in cont.ARBEIT_LEISTUNG.all_suffixes):
            for suff in cont.ARBEIT_LEISTUNG.all_suffixes:
                if suff in col:
                    new_col_name = f"{col.split(suff)[0]} {year}{suff}"
        col_rename[col] = new_col_name
    return col_rename


@gf.func_timer
def df_h(mdf: cld.MetaAndDfs) -> cld.MetaAndDfs:
    """Stundenwerte aus anderer zeitlicher Auflösung"""

    cols: list[str] = [
        col for col in mdf.df.columns if gf.check_if_not_exclude(col, "suff_arbeit")
    ]

    mdf.df_h = (
        pl.DataFrame(
            [
                mdf.df.get_column(col).alias(
                    col.replace(cont.SUFFIXES.col_leistung, "").strip()
                )
                for col in [*cols, COL_ORG]
            ]
        )
        .sort(by=COL_IND)
        .groupby_dynamic(COL_IND, every="1h")
        .agg(
            [
                pl.col(col.replace(cont.SUFFIXES.col_leistung, "").strip()).mean()
                for col in [co for co in cols if co != COL_IND]
            ]
        )
        .with_columns(pl.col(COL_IND).alias(COL_ORG))
    )

    if mdf.meta.multi_years and gf.st_get("cb_multi_year"):
        mdf.df_h_multi = split_multi_years(mdf, "df_h")

    logger.success("DataFrame mit Stundenwerten erstellt.")
    logger.log(slog.LVLS.data_frame.name, mdf.df_h.head())
    logger.info("  \n".join(["Columns in mdf.df_h:", *mdf.df_h.columns]))

    gf.st_set("mdf", mdf)
    return mdf


@gf.func_timer
def jdl(mdf: cld.MetaAndDfs) -> cld.MetaAndDfs:
    """Jahresdauerlinie"""

    mdf = mdf if isinstance(mdf.df_h, pl.DataFrame) else df_h(mdf)

    if mdf.df_h is None:
        raise ValueError

    # Zeit-Spalte für jede Linie kopieren um sie zusammen sortieren zu können
    cols_without_index: list[str] = [
        col for col in mdf.df_h.columns if gf.check_if_not_exclude(col)
    ]
    jdl_first_stage: pl.DataFrame = mdf.df_h.with_columns(
        [pl.col(COL_IND).alias(f"{col} - {COL_ORG}") for col in cols_without_index]
    )

    if mdf.meta.multi_years and mdf.meta.years:
        jdl_separate: list[list[pl.Series]] = [
            jdl_first_stage.select(pl.col(col, f"{col} - {COL_ORG}"))
            .filter(pl.col(f"{col} - {COL_ORG}").dt.year() == year)
            .sort(col, descending=True)
            .rename(
                {
                    col: f"{col} {year}",
                    f"{col} - {COL_ORG}": f"{col} {year} - {COL_ORG}",
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

    mdf.jdl = pl.DataFrame(sum(jdl_separate, [])).with_row_count(
        cont.SPECIAL_COLS.index
    )

    logger.success("DataFrame für Jahresdauerlinie erstellt.")
    logger.log(slog.LVLS.data_frame.name, mdf.jdl.head())
    logger.info("  \n".join(["Columns in mdf.jdl:", *mdf.jdl.columns]))

    gf.st_set("mdf", mdf)
    return mdf


@gf.func_timer
def mon(mdf: cld.MetaAndDfs) -> cld.MetaAndDfs:
    """Monatswerte"""

    mdf = mdf if isinstance(mdf.df_h, pl.DataFrame) else df_h(mdf)
    if mdf.df_h is None:
        raise ValueError

    cols_without_index: list[str] = [
        col for col in mdf.df_h.columns if gf.check_if_not_exclude(col)
    ]

    mdf.mon = (
        mdf.df_h.groupby_dynamic(COL_IND, every="1mo")
        .agg(
            [
                pl.col(col).mean()
                if mdf.meta.lines[col].unit in cont.GRP_MEAN
                else pl.col(col).sum()
                for col in cols_without_index
            ]
        )
        .with_columns(
            [
                pl.col(COL_IND).alias(COL_ORG),
                pl.col(COL_IND)
                .dt.strftime("%Y-%m-15 %H:%M:%S")
                .str.strptime(pl.Datetime),
            ]
        )
    )

    if mdf.meta.multi_years and gf.st_get("cb_multi_year"):
        mdf.mon_multi = split_multi_years(mdf, "mon")

    logger.success("DataFrame mit Monatswerten erstellt.")
    logger.log(slog.LVLS.data_frame.name, mdf.mon.head())
    logger.info("  \n".join(["Columns in mdf.mon:", *mdf.mon.columns]))

    gf.st_set("mdf", mdf)
    return mdf


# !!! MUSS NOCH ÜBERARBEITET WERDEN !!!
@gf.func_timer
def dic_days(mdf: cld.MetaAndDfs) -> None:
    """Create Dictionary for Days"""

    gf.st_set("dic_days", {})
    for num in range(int(gf.st_get("ni_days"))):
        date: dt.date = gf.st_get(f"day_{num}")
        item: pl.DataFrame = mdf.df.filter(f"{date:%Y-%m-%d}").with_columns(
            pl.col(COL_IND).dt.strftime("2020-1-1 %H:%M:%S").str.strptime(pl.Datetime),
        )

        gf.st_set(f"dic_days_{num}", item)
