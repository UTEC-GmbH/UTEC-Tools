"""Experimente und Versuche"""

from pathlib import Path

import pandas as pd
import polars as pl

EX_FOLDER: str = f"{Path.cwd()}\\experiments"
EX_FILE: str = "Leipzig FedEx Stundenwerte.xlsx"
IDX: str = "Datum"


def get_df_from_excel(file: str = f"{EX_FOLDER}\\{EX_FILE}") -> None:
    """Excel Import via csv-conversion"""

    xlsx_options: dict[str, str | bool] = {
        "skip_empty_lines": True,
        "skip_trailing_columns": True,
        "dateformat": "%d.%m.%Y %T",
    }
    csv_options: dict[str, bool] = {"has_header": True, "try_parse_dates": True}

    df: pl.DataFrame = pl.read_excel(
        file,
        xlsx2csv_options=xlsx_options,
        read_csv_options=csv_options,
    )

    df = (
        df.select(
            [pl.col(IDX).str.strptime(pl.Datetime, "%d.%m.%Y %T").dt.round("1m")]
            + [pl.col(col).cast(pl.Float32) for col in df.columns if col != IDX]
        )
        .set_sorted(column=IDX)
        .upsample(time_column=IDX, every="15m")
    )

    df_pd: pd.DataFrame = df.to_pandas().set_index(IDX)

    df_pd = df_pd.interpolate(method="akima")
    df_aki: pl.DataFrame = pl.from_pandas(df_pd)

    df_aki.write_excel(f"{EX_FOLDER}\\akima.xlsx", hide_gridlines=True)

    df_lin = df.interpolate()

    df_lin.write_excel(f"{EX_FOLDER}\\linear.xlsx", hide_gridlines=True)

    df_ff = df.fill_null(strategy="forward")

    df_ff.write_excel(f"{EX_FOLDER}\\fill.xlsx", hide_gridlines=True)
