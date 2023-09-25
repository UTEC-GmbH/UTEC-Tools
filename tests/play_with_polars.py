import pandas as pd
import polars as pl


def multi_year(df: pd.DataFrame) -> None:
    df_pl: pl.DataFrame = pl.from_pandas(df).with_columns(
        pl.Series(df.index).alias("index")
    )
    df_pl.select(
        pl.col("Index").dt.strftime("2020-%m-%d %H:%M:%S").str.strptime(pl.Datetime)
    )


def from_excel_import() -> None:
    # ...nur zum Ausprobieren
    st.session_state["df_pl"] = pl.from_pandas(df).with_columns(
        pl.Series(df.index).alias("index")
    )


discover: dict[str, dict[str, dict[str, str]]] = {
    "minute_1": {
        "precipitation_height": {"origin": "mm", "si": "kg / m ** 2"},
        "precipitation_height_droplet": {"origin": "mm", "si": "kg / m ** 2"},
        "precipitation_height_rocker": {"origin": "mm", "si": "kg / m ** 2"},
        "precipitation_index": {"origin": "-", "si": "-"},
    },
    "minute_5": {
        "precipitation_index": {"origin": "-", "si": "-"},
        "precipitation_height": {"origin": "mm", "si": "kg / m ** 2"},
        "precipitation_height_droplet": {"origin": "mm", "si": "kg / m ** 2"},
        "precipitation_height_rocker": {"origin": "mm", "si": "kg / m ** 2"},
    },
}
