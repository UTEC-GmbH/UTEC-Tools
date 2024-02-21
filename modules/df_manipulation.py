# sourcery skip: no-complex-if-expressions
"""Bearbeitung der Daten"""


import datetime as dt
import functools
import operator
from typing import Any, Literal

import polars as pl
from loguru import logger
from scipy import interpolate

from modules import classes_data as cld
from modules import classes_errors as cle
from modules import constants as cont
from modules import general_functions as gf
from modules import meteorolog as met
from modules import setup_logger as slog
from modules import streamlit_functions as sf

COL_IND: str = cont.SpecialCols.index
COL_ORG: str = cont.SpecialCols.original_index


def get_df_to_test_am_pm(file_path: str | None = None) -> pl.DataFrame:
    """Get a df to test the am-pm-function"""

    file_path = file_path or "tests/sample_data/Utbremer_Ring_189_2017.xlsx"
    xlsx_options: dict[str, Any] = {
        "skip_empty_lines": True,
        "skip_trailing_columns": True,
        # "dateformat": "%d.%m.%Y %H:%M",
    }
    csv_options: dict[str, bool] = {"has_header": True, "try_parse_dates": False}
    df: pl.DataFrame = pl.read_excel(
        source=file_path,
        xlsx2csv_options=xlsx_options,
        read_csv_options=csv_options,
    )  # type: ignore

    return df.with_columns(
        pl.col("Zeitstempel").str.strptime(pl.Datetime, "%d.%m.%Y %H:%M")
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
        pl.when(pl.col(time_column).dt.hour() == cont.TimeHoursIn.half_day)
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


def interpolate_where_no_diff(
    df: pl.DataFrame, columns_to_inspect: list[str] | None = None
) -> pl.DataFrame:
    """Create gaps where the values don't change and interpolate using Akima"""

    if COL_IND not in df.columns:
        raise cle.NotFoundError(entry=COL_IND, where="data frame columns")

    cols: list[str] = columns_to_inspect or df.columns

    df = df.with_columns(
        pl.when(pl.col(col).diff() == 0).then(None).otherwise(pl.col(col)).keep_name()
        for col in cols
    )

    no_nulls: pl.DataFrame = df.drop_nulls()
    index: pl.Series = no_nulls[COL_IND]
    return df.with_columns(
        pl.Series(
            col,
            interpolate.Akima1DInterpolator(x=index, y=no_nulls[col])(df[COL_IND]),
        )
        for col in cols
        if COL_IND not in col and any(df[col].is_null())
    )


def upsample_hourly_to_15min(
    df: pl.DataFrame, units: dict[str, str], index_column: str | None = None
) -> pl.DataFrame:
    """Stundenwerte in 15-Minuten-Werte umwandeln"""

    col_index: str = index_column or cont.SpecialCols.index
    if col_index not in df.columns:
        raise cle.NotFoundError(entry=col_index, where="data frame columns")
    if not df[col_index].dtype.is_temporal():
        raise TypeError

    df_up: pl.DataFrame = (
        df.sort(col_index)
        .upsample(COL_IND, every="15m")
        .with_columns(
            pl.when(
                units.get(col, "").strip().lower()
                in ["", *[unit.strip().lower() for unit in cont.GROUP_MEAN.mean_all]]
            )
            .then(pl.col(col))
            .otherwise(pl.col(col) / 4)
            .keep_name()
            for col in df.columns
        )
    )

    # return df_up.with_columns(
    #     pl.Series(
    #         col,
    #         interpolate.Akima1DInterpolator(x=df[COL_IND], y=df_up.drop_nulls()[col])(
    #             df_up[COL_IND]
    #         ),
    #     )
    #     for col in cols
    #     if COL_IND not in col and cont.SPECIAL_COLS.original_index not in col
    # )
    return interpolate_missing_data_akima(df_up, col_index)


def interpolate_missing_data_akima(
    df: pl.DataFrame, index_column: str | None = None
) -> pl.DataFrame:
    """Interpolate missing data"""

    col_index: str = index_column or cont.SpecialCols.index
    if col_index not in df.columns:
        raise cle.NotFoundError(entry=col_index, where="data frame columns")
    if not df[col_index].dtype.is_temporal():
        raise TypeError

    cols: list[str] = [
        col
        for col in df.columns
        if col_index not in col
        and any(df[col].is_null())
        and df[col].dtype.is_numeric()
    ]

    no_nulls: pl.DataFrame = df.drop_nulls()
    index: pl.Series = no_nulls[col_index]
    return df.sort(col_index).with_columns(
        pl.Series(
            col,
            interpolate.Akima1DInterpolator(x=index, y=no_nulls[col])(df[col_index]),
        )
        for col in cols
    )


@gf.func_timer
def add_temperature_data(mdf: cld.MetaAndDfs) -> cld.MetaAndDfs:
    """Add air temperature for given address to the base data frame"""

    sf.s_set("selected_params", ["temperature_air_mean_200"])
    parameters: list[cld.DWDParam] = met.meteo_df_for_temp_in_graph(mdf)

    for param in parameters:
        if param.closest_available_res is None:
            raise ValueError

        df_parameter: pl.DataFrame | None = param.closest_available_res.data
        if df_parameter is None:
            continue
        mdf.df = (
            mdf.df.join(
                mdf.df.select(cont.SpecialCols.index)
                .join(df_parameter, on=cont.SpecialCols.index, how="outer_coalesce")
                .sort(cont.SpecialCols.index)
                .interpolate(),
                on=cont.SpecialCols.index,
                join_nulls=True,
            )
            .fill_null(strategy="forward")
            .fill_null(strategy="backward")
        )
        par_nam: str = param.name_de
        mdf.meta.lines[par_nam] = cld.MetaLine(
            name=par_nam,
            name_orgidx=f"{par_nam} - {cont.Suffixes.col_original_index}",
            orig_tit=par_nam,
            tit=par_nam,
            unit=param.unit,
            unit_h=param.unit.strip("h"),
        )
    logger.info(
        gf.string_new_line_per_item(
            mdf.df.columns, "mdf.df.columns after adding weather data:"
        )
    )

    logger.debug(
        f"mdf.df['Lufttemperatur'].null_count(): "
        f"{mdf.df['Lufttemperatur'].null_count()}"
    )
    logger.debug(mdf.df.filter(pl.col("Lufttemperatur").is_null()))

    return mdf


@gf.func_timer
def split_multi_years(
    mdf: cld.MetaAndDfs, frame_to_split: Literal["df", "df_h", "mon"]
) -> cld.MetaAndDfs:
    """Split the specified data frame within a MetaAndDfs object
    into multiple data frames based on the years present in the meta data.

    Args:
        - mdf (cld.MetaAndDfs): MetaAndDfs object containing the data frame to split.
        - frame_to_split (Literal["df", "df_h", "mon"]): Name of data frame to split.
            Must be one of "df", "df_h", or "mon".

    Returns:
        - cld.MetaAndDfs: The updated MetaAndDfs object with the split data frames.

    Raises:
        - ValueError: If frame_to_split parameter is not one of the specified options.
        - cle.NotFoundError: If the list of years is not present in the meta data.

    """

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

    for year, df in df_multi.items():
        logger.success(f"DataFrame for Year {year}:")
        slog.log_df(df)

    if frame_to_split == "df":
        mdf.df_multi = df_multi
    elif frame_to_split == "df_h":
        mdf.df_h_multi = df_multi
    else:
        mdf.mon_multi = df_multi

    return mdf


def multi_year_column_rename(df: pl.DataFrame, year: int) -> dict[str, str]:
    """Renames columns in a DataFrame for multi-year data.

    Args:
        - df: The DataFrame to rename columns for.
        - year: The year to append to the column names.

    Returns:
        - A dictionary mapping the original column names to the renamed column names.

    """
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
def change_temporal_resolution(
    df: pl.DataFrame,
    units: dict[str, str],
    requested_resolution: Literal["15m", "1h", "1d", "1mo"],
) -> pl.DataFrame:
    """Make a df with the requested temporal resolution

    Args:
        - df (pl.DataFrame): A DataFrame containing temporal and non-temporal data.
        - units (dict[str, str]): A dictionary mapping column names
            to their respective units.
        - requested_resolution (Literal["15m", "1h", "1d", "1mo"]): A string
            representing the requested temporal resolution.

    Returns:
        - pl.DataFrame: A DataFrame with the requested temporal resolution.
            The non-temporal data is aggregated based on the requested resolution.

    Raises:
        - TypeError: If the time column is not temporal.
        - ValueError: If the original resolution is zero.

    Example Usage:
        df_15 = pl.DataFrame(
            {
                "Datum": pl.datetime_range(
                    dt.datetime(2020, 2, 7, 9),
                    dt.datetime(2020, 2, 7, 11),
                    "15m",
                    eager=True
                ),
                "Vals": [2,4,8,9,6,1,4,2,1,]
            }
        )
        units = {"Vals": "kW"}
        requested_resolution = "1h"
        df_h = change_temporal_resolution(df, units, requested_resolution)
        print(df_h)

    Output:
        ┌─────────────────────┬──────┐
        │ Datum               ┆ Vals │
        │ ---                 ┆ ---  │
        │ datetime[μs]        ┆ f64  │
        ╞═════════════════════╪══════╡
        │ 2020-02-07 09:00:00 ┆ 5.75 │
        │ 2020-02-07 10:00:00 ┆ 3.25 │
        │ 2020-02-07 11:00:00 ┆ 1.0  │
        └─────────────────────┴──────┘

    """

    cols: list[str] = df.columns
    value_cols: list[str] = [
        col for col in cols if not df.get_column(col).dtype.is_temporal()
    ]
    time_col: str = next(
        iter(col for col in cols if df.get_column(col).dtype.is_temporal())
    )
    time_col_dat: pl.Series = df.get_column(time_col)
    if not time_col_dat.dtype.is_temporal():
        raise TypeError

    max_date: dt.datetime = time_col_dat.max()  # type: ignore
    min_date: dt.datetime = time_col_dat.min()  # type: ignore

    timedelta_mean: Any = time_col_dat.diff().mean()
    if not isinstance(timedelta_mean, float):
        raise TypeError

    original_resolution: dt.timedelta = dt.timedelta(microseconds=timedelta_mean)
    if original_resolution == dt.timedelta(0):
        raise ValueError

    requested_timedelta: dt.timedelta = cont.TIME_RESOLUTIONS[
        requested_resolution
    ].delta

    # Downsample data if the original resolution is higher than the requested
    if original_resolution < requested_timedelta:
        logger.info("Downsampling data to requested resolution...")
        return df.group_by_dynamic(time_col, every=requested_resolution).agg(
            [
                (
                    pl.col(col).mean()
                    if cont.GROUP_MEAN.check(units[col], "mean_all")
                    else pl.col(col).sum()
                )
                for col in value_cols
            ]
        )

    # Upsample data if the original resolution is lower than the requested
    # DataFrame with just the date column in the requested resolution
    df_res: pl.DataFrame = pl.DataFrame(
        {
            time_col: pl.datetime_range(
                min_date, max_date, requested_resolution, eager=True
            )
        }
    )

    # Join the original DataFrame with df_res to get a DataFrame with missing data
    df_join: pl.DataFrame = (
        df_res.join(df, on=time_col, how="outer_coalesce")
        .sort(by=time_col)
        .with_columns(
            pl.when(None or cont.GROUP_MEAN.check(units[col], "mean_all"))
            .then(pl.col(col))
            .otherwise(pl.col(col) * (requested_timedelta / original_resolution))
            .keep_name()
            for col in value_cols
        )
    )

    # interpolate the missing data using the "Akima"-method
    # !!! this step may lead to inaccuracies !!!
    return interpolate_missing_data_akima(df_join, time_col)


@gf.func_timer
def df_h_mdf(mdf: cld.MetaAndDfs) -> cld.MetaAndDfs:
    """Stundenwerte aus anderer zeitlicher Auflösung"""

    cols: list[str] = [
        col for col in mdf.df.columns if gf.check_if_not_exclude(col, "suff_arbeit")
    ]

    mdf.df_h = (
        pl.DataFrame(
            [
                mdf.df.get_column(col).alias(
                    col.replace(cont.Suffixes.col_leistung, "").strip()
                )
                for col in [*cols, COL_ORG]
            ]
        )
        .sort(by=COL_IND)
        .group_by_dynamic(COL_IND, every="1h")
        .agg(
            [
                pl.col(col.replace(cont.Suffixes.col_leistung, "").strip()).mean()
                for col in [co for co in cols if co != COL_IND]
            ]
        )
        .with_columns(pl.col(COL_IND).alias(COL_ORG))
    )

    if mdf.meta.multi_years and sf.s_get("cb_multi_year"):
        mdf = split_multi_years(mdf, "df_h")

    if mdf.df_h is not None:
        logger.success("DataFrame mit Stundenwerten erstellt.")
        slog.log_df(mdf.df_h)
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

    mdf = mdf if isinstance(mdf.df_h, pl.DataFrame) else df_h_mdf(mdf)

    if mdf.df_h is None:
        raise ValueError

    # Zeit-Spalte für jede Linie kopieren um sie zusammen sortieren zu können
    cols_without_index: list[str] = [
        col for col in mdf.df_h.columns if gf.check_if_not_exclude(col)
    ]
    jdl_first_stage: pl.DataFrame = mdf.df_h.with_columns(
        [pl.col(COL_IND).alias(f"{col} - {COL_ORG}") for col in cols_without_index]
    )

    if mdf.meta.multi_years and mdf.meta.years and mdf.df_h_multi:
        jdl_separate_df: list[pl.DataFrame] = [
            df.select(pl.col(col, COL_ORG))
            .sort(col, descending=True)
            .rename({col: col, COL_ORG: f"{col} - {COL_ORG}"})
            for df in mdf.df_h_multi.values()
            for col in df.columns
            if gf.check_if_not_exclude(col)
        ]
        for df in jdl_separate_df:
            if df.height < cont.TimeHoursIn.leap_year:
                df.extend(
                    pl.DataFrame(
                        {
                            col: [None] * (cont.TimeHoursIn.leap_year - df.height)
                            for col in df.columns
                        }
                    ).cast(dict(df.schema))
                )
        jdl_separate: list[list[pl.Series]] = [
            df.get_columns() for df in jdl_separate_df
        ]
    else:
        jdl_separate = [
            jdl_first_stage.select(pl.col(col, f"{col} - {COL_ORG}"))
            .sort(col, descending=True)
            .get_columns()
            for col in cols_without_index
        ]

    mdf.jdl = pl.DataFrame(
        functools.reduce(operator.iadd, jdl_separate, [])
    ).with_row_index(cont.SpecialCols.index)

    logger.success("DataFrame für Jahresdauerlinie erstellt.")
    slog.log_df(mdf.jdl)
    logger.info(gf.string_new_line_per_item(mdf.jdl.columns, "Columns in mdf.jdl:"))

    sf.s_set("mdf", mdf)
    return mdf


@gf.func_timer
def calculate_monthly_values(mdf: cld.MetaAndDfs) -> cld.MetaAndDfs:
    """Calculate monthly values from the input dataframe.

    Args:
        - mdf (cld.MetaAndDfs): The input MetaAndDfs object containing the dataframe.

    Returns:
        - cld.MetaAndDfs: Modified MetaAndDfs object with the monthly values dataframe.

    Raises:
        - ValueError: If the input dataframe is None.

    """

    mdf = mdf if isinstance(mdf.df_h, pl.DataFrame) else df_h_mdf(mdf)
    if mdf.df_h is None:
        raise ValueError

    cols_without_index: list[str] = [
        col for col in mdf.df_h.columns if gf.check_if_not_exclude(col)
    ]

    mdf.mon = (
        mdf.df_h.group_by_dynamic(COL_IND, every="1mo")
        .agg(
            [
                (
                    pl.col(col).mean()
                    if (cont.GROUP_MEAN.check(mdf.meta.lines[col].unit, "mean_always"))
                    else pl.col(col).sum()
                )
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
        logger.success("DataFrame with monthly values created.")
        logger.log(slog.LVLS.data_frame.name, mdf.mon.head())
        logger.info(gf.string_new_line_per_item(mdf.mon.columns, "Columns in mdf.mon:"))

    sf.s_set("mdf", mdf)
    return mdf


# !!! MUSS NOCH ÜBERARBEITET WERDEN !!!
@gf.func_timer
def dic_days(mdf: cld.MetaAndDfs) -> None:
    """Create Dictionary for Days"""

    sf.s_set("dic_days", {})
    for num in range(int(sf.s_get("ni_days") or 0)):
        date: dt.date = sf.s_get(f"day_{num}")
        item: pl.DataFrame = mdf.df.filter(f"{date:%Y-%m-%d}").with_columns(
            pl.col(COL_IND).dt.strftime("2020-1-1 %H:%M:%S").str.strptime(pl.Datetime),
        )

        sf.s_set(f"dic_days_{num}", item)
