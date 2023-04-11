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
