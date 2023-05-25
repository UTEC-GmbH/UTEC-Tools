"""Tests for functions in df_manip.py"""

from typing import Any

import pandas as pd

from modules import constants as cont
from modules import df_manip as dfm
from modules import excel as ex
from tests import sample_data as sd


def test_h_from_other() -> None:
    """Leistung / Arbeit"""
    df: pd.DataFrame = sd.sample_df("single", "15")
    meta: dict[str, dict[str, Any]] = sd.sample_dic_meta(df)

    df_con: pd.DataFrame
    meta_new: dict[str, dict[str, Any]]

    df_con, meta_new = ex.convert_15min_kwh_to_kw(df, meta)

    suffixes: list[str] = cont.ARBEIT_LEISTUNG.get_all_suffixes()

    df_h: pd.DataFrame = dfm.h_from_other(df_con, meta_new)

    no_suffix_in_cols: bool = all(
        suff not in str(col) for suff in suffixes for col in df_h.columns
    )

    assert no_suffix_in_cols
