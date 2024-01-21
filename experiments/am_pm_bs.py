"""Bullshit data"""

from pathlib import Path

import polars as pl


def import_sample_pl(time_col: str = "Zeitstempel", year: int = 2017) -> pl.DataFrame:
    """Import a sample file"""

    cwd: str = str(Path.cwd())
    phil: str = f"{cwd}\\tests\\sample_data\\Utbremer_Ring_189_{year}.xlsx"
    df: pl.DataFrame = pl.read_excel(phil)

    return df.select(
        [pl.col(time_col).str.strptime(pl.Datetime, "%d.%m.%Y %H:%M")]
        + [pl.col(col).cast(pl.Float32) for col in df.columns if col != time_col]
    )


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

    return df.with_columns(
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
