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
from modules import streamlit_functions as sf

if TYPE_CHECKING:
    import datetime as dt

    import pandas as pd

COL_IND: str = cont.SPECIAL_COLS.index
COL_ORG: str = cont.SPECIAL_COLS.original_index


def get_df_to_test_am_pm(file_path: str | None = None) -> pl.DataFrame:
    """Get a df to test the am-pm-function"""

    file_path = file_path or "tests/sample_data/Utbremer_Ring_189_2017.xlsx"
    xlsx_options: dict[str, Any] = {
        "skip_empty_lines": True,
        "skip_trailing_columns": True,
        # "dateformat": "%d.%m.%Y %T",
    }
    csv_options: dict[str, bool] = {"has_header": True, "try_parse_dates": False}
    df: pl.DataFrame = pl.read_excel(
        source=file_path,
        xlsx2csv_options=xlsx_options,
        read_csv_options=csv_options,
    )  # type: ignore

    return df.with_columns(
        pl.col("Zeitstempel").str.strptime(pl.Datetime, "%d.%m.%Y %T")
    )


def fix_am_pm(df: pl.DataFrame, time_column: str = "Zeitstempel") -> pl.DataFrame:
    """Zeitreihen ohne Unterscheidung zwischen vormittags und nachmittags

    (Beispieldatei: "tests/sample_data/Utbremer_Ring_189_2017.xlsx")

    col: Zeitspalte wird so geändert, dass es zwei mal täglich 00:00 bis 11:59 gibt
    offset: Zeitverschiebung um 12h am Nachmittag (0h am Vormittag)

    Args:
        - df (DataFrame): DataFrame, der bearbeitet werden soll
        - time_column (str, optional): Zeitspalte. Default: "Zeitstempel".

    Returns:
        - DataFrame: DataFrame mit korrigierter Zeitspalte
    """

    col: pl.DataFrame = df.select(
        pl.when(pl.col(time_column).dt.hour() == 12)
        .then(pl.col(time_column).dt.offset_by("-12h"))
        .otherwise(pl.col(time_column))
    )

    offset: pl.Series = (
        col.select(
            pl.when(pl.col(time_column).dt.day().diff().fill_null(1) > 0)
            .then(pl.duration(hours=0))
            .otherwise(
                pl.when(
                    (pl.col(time_column).dt.hour().diff() < 0)
                    & (pl.col(time_column).dt.day().diff() == 0)
                )
                .then(pl.duration(hours=12))
                .otherwise(pl.lit(None))
            )
        )
        .fill_null(strategy="forward")
        .to_series()
    )

    return df.with_columns((col.to_series() + offset).alias(time_column))


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


@gf.func_timer
def add_temperature_data(mdf: cld.MetaAndDfs) -> cld.MetaAndDfs:
    """Add air temperature for given address to the base data frame"""

    parameters: list[cld.DWDParameter] = met.meteo_df(mdf)

    for parameter in parameters:
        df_parameter: pl.DataFrame | None = parameter.data_frame
        if df_parameter is None:
            continue
        mdf.df = (
            mdf.df.join(
                mdf.df.select(cont.SPECIAL_COLS.index)
                .join(df_parameter, on=cont.SPECIAL_COLS.index, how="outer")
                .sort(cont.SPECIAL_COLS.index)
                .interpolate(),
                on=cont.SPECIAL_COLS.index,
            )
            .fill_null(strategy="forward")
            .fill_null(strategy="backward")
        )
        par_nam: str = parameter.name_de or parameter.name
        mdf.meta.lines[par_nam] = cld.MetaLine(
            name=par_nam,
            name_orgidx=f"{par_nam}{cont.SUFFIXES.col_original_index}",
            orig_tit=par_nam,
            tit=par_nam,
            unit=parameter.unit,
            unit_h=parameter.unit.strip("h"),
        )
    logger.info(
        gf.string_new_line_per_item(
            mdf.df.columns, "mdf.df.columns after adding weather data:"
        )
    )

    logger.debug(
        f"mdf.df['Außentemperatur'].null_count(): "
        f"{mdf.df['Außentemperatur'].null_count()}"
    )
    logger.debug(mdf.df.filter(pl.col("Außentemperatur").is_null()))

    return mdf


@gf.func_timer
def split_multi_years(
    mdf: cld.MetaAndDfs, frame_to_split: Literal["df", "df_h", "mon"]
) -> cld.MetaAndDfs:
    """Split into multiple years"""
    if frame_to_split not in ["df", "df_h", "mon"]:
        raise ValueError

    logger.info(f"Splitting Data Frame '{frame_to_split}'")

    df: pl.DataFrame = getattr(mdf, frame_to_split)
    if not mdf.meta.years:
        raise cle.NotFoundError(entry="list of years", where="mdf.meta.years")

    df_multi: dict[int, pl.DataFrame] = {}
    for year in mdf.meta.years:
        col_rename: dict[str, str] = multi_year_column_rename(df, year)
        for old_name, new_name in col_rename.items():
            if new_name not in mdf.meta.lines:
                # old_line: cld.MetaLine = mdf.meta.lines[old_name]
                # new_line: cld.MetaLine = cld.MetaLine("tmp", "tmp", "tmp", "tmp")
                # for attr in old_line.as_dic():
                #     setattr(new_line, attr, getattr(old_line, attr))
                # new_line.tit = new_name
                # new_line.name_orgidx = f"{new_name}{cont.SUFFIXES.col_original_index}"
                # mdf.meta.lines[new_name] = new_line
                mdf.meta.lines[new_name] = mdf.meta.copy_line(old_name, new_name)

        df_multi[year] = (
            df.filter(pl.col(COL_IND).dt.year() == year)
            .with_columns(
                pl.col(COL_IND)
                .dt.strftime("2020-%m-%d %H:%M:%S")
                .str.strptime(pl.Datetime),
            )
            .rename(col_rename)
        )

        # logger debug
        if any(df_multi[year][col].null_count() > 0 for col in df_multi[year].columns):
            for col in df_multi[year].columns:
                if df_multi[year][col].null_count() > 0:
                    logger.debug(f"Null value found in column '{col}'")
        else:
            logger.debug("No null values found")

    if frame_to_split == "df":
        mdf.df_multi = df_multi
    elif frame_to_split == "df_h":
        mdf.df_h_multi = df_multi
    else:
        mdf.mon_multi = df_multi

    return mdf


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

    if mdf.meta.multi_years and sf.s_get("cb_multi_year"):
        mdf = split_multi_years(mdf, "df_h")

    if mdf.df_h is not None:
        logger.success("DataFrame mit Stundenwerten erstellt.")
        logger.log(slog.LVLS.data_frame.name, mdf.df_h.head())
        logger.info(
            gf.string_new_line_per_item(mdf.df_h.columns, "Columns in mdf.df_h:")
        )

    sf.s_set("mdf", mdf)
    return mdf


@gf.func_timer
def jdl(mdf: cld.MetaAndDfs) -> cld.MetaAndDfs:
    """Jahresdauerlinie"""

    if isinstance(mdf.df_h, pl.DataFrame):
        logger.info("Vorhandenes df_h für jdl übernommen")
    else:
        logger.info("df_h wird für jdl neu erstellt")

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
    logger.info(gf.string_new_line_per_item(mdf.jdl.columns, "Columns in mdf.jdl:"))

    sf.s_set("mdf", mdf)
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

    if mdf.meta.multi_years and sf.s_get("cb_multi_year"):
        mdf = split_multi_years(mdf, "mon")

    if mdf.mon is not None:
        logger.success("DataFrame mit Monatswerten erstellt.")
        logger.log(slog.LVLS.data_frame.name, mdf.mon.head())
        logger.info(gf.string_new_line_per_item(mdf.mon.columns, "Columns in mdf.mon:"))

    sf.s_set("mdf", mdf)
    return mdf


# !!! MUSS NOCH ÜBERARBEITET WERDEN !!!
@gf.func_timer
def dic_days(mdf: cld.MetaAndDfs) -> None:
    """Create Dictionary for Days"""

    sf.s_set("dic_days", {})
    for num in range(int(sf.s_get("ni_days"))):
        date: dt.date = sf.s_get(f"day_{num}")
        item: pl.DataFrame = mdf.df.filter(f"{date:%Y-%m-%d}").with_columns(
            pl.col(COL_IND).dt.strftime("2020-1-1 %H:%M:%S").str.strptime(pl.Datetime),
        )

        sf.s_set(f"dic_days_{num}", item)
