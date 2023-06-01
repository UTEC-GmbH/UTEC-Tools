"""Bullshit data"""

from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl


def import_sample_pl(time_col: str = "Zeitstempel", year: int = 2017) -> pl.DataFrame:
    """Import a sample file"""

    cwd: str = str(Path.cwd())
    phil: str = f"{cwd}\\tests\\sample_data\\Utbremer_Ring_189_{year}.xlsx"
    df: pl.DataFrame = pl.read_excel(phil)
    df = df.select(
        [pl.col(time_col).str.strptime(pl.Datetime, "%d.%m.%Y %T")]
        + [pl.col(col).cast(pl.Float32) for col in df.columns if col != time_col]
    )
    return df


def import_sample_pd(time_col: str = "Zeitstempel", year: int = 2017) -> pd.DataFrame:
    """Import a sample file"""

    cwd: str = str(Path.cwd())
    phil: str = f"{cwd}\\tests\\sample_data\\Utbremer_Ring_189_{year}.xlsx"
    df: pd.DataFrame = pd.read_excel(phil)

    return df


def fix_am_pm_pd(df: pd.DataFrame, time_column: str = "Zeitstempel") -> pd.DataFrame:
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

        choices: list[pd.Timedelta] = [
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


def fix_am_pm_pl(df: pl.DataFrame, time_column: str = "Zeitstempel") -> pl.DataFrame:
    """Zeitreihen ohne Unterscheidung zwischen vormittags und nachmittags

    (korrigiert den Bullshit, den man immer von der GEG bekommt)

    Args:
        - df (DataFrame): DataFrame to edit
        - time_column (str, optional): Column with time data. Defaults to "Zeitstempel".

    Returns:
        - DataFrame: edited DataFrame
    """

    time_diff: pl.Series = df.get_column(time_column)

    new_day: pl.Series = (time_diff.dt.day().diff() > 0) | (
        time_diff.dt.day().diff().is_null()
    )
    during_day: pl.Series = (time_diff.dt.hour().diff() < 0) & (
        time_diff.dt.day().diff() == 0
    )

    df = df.with_columns(
        [
            pl.when(new_day)
            .then(pl.duration(hours=12))
            .otherwise(
                pl.when(during_day).then(pl.duration(hours=12)).otherwise(pl.lit(None))
            )
            .alias("change")
            .fill_null(strategy="forward")
        ]
    )

    return df
