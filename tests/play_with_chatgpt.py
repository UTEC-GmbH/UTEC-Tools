"""play with ChatGPT"""

# sourcery skip: avoid-global-variables

"""
How can I replace multiple strings in a list of strings?
"""

from typing import Literal

import polars as pl

from modules import classes_data as cl
from modules import classes_errors as cle
from modules import constants as cont
from modules import general_functions as gf

COL_IND: str = cont.SPECIAL_COLS.index
COL_ORG: str = cont.SPECIAL_COLS.original_index


class MultiYearSplitter:
    """Split into multiple years"""

    def __init__(self, mdf: cl.MetaAndDfs) -> None:
        """Initialize"""
        self.mdf = mdf

    def split_multi_years(
        self, frame_to_split: Literal["df", "df_h", "mon"]
    ) -> dict[int, pl.DataFrame]:
        """Split into multiple years"""

        df: pl.DataFrame = getattr(self.mdf, frame_to_split)
        if not self.mdf.meta.years:
            raise cle.NoYearsError

        df_multi: dict[int, pl.DataFrame] = {}
        for year in self.mdf.meta.years:
            col_rename: dict[str, str] = self.multi_year_column_rename(df, year)
            self.add_meta_data(col_rename)

            df_multi[year] = (
                df.filter(pl.col(COL_IND).dt.year() == year)
                .with_columns(
                    pl.col(COL_IND)
                    .dt.strftime("2020-%m-%d %H:%M:%S")
                    .str.strptime(pl.Datetime),
                )
                .rename(col_rename)
            )

        return df_multi

    def multi_year_column_rename(self, df: pl.DataFrame, year: int) -> dict[str, str]:
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

    def add_meta_data(self, col_rename: dict[str, str]) -> None:
        """Add Metadata for multi year data"""
        for old_name, new_name in col_rename.items():
            if new_name not in self.mdf.meta.get_all_line_names():
                self.mdf.meta.copy_line_meta_with_new_name(old_name, new_name)
