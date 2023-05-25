"""Tests for functions in excel.py"""

from typing import Any

import pandas as pd

from modules import constants as cont
from modules import excel as ex
from tests import sample_data as sd


def test_conversion_15min_arbeit_leistung() -> None:
    """Leistung / Arbeit"""
    df: pd.DataFrame = sd.sample_df("single", "15")
    meta: dict[str, dict[str, Any]] = sd.sample_dic_meta(df)

    df_con: pd.DataFrame
    meta_new: dict[str, dict[str, Any]]

    df_con, meta_new = ex.convert_15min_kwh_to_kw(df, meta)

    suffixes: list[str] = cont.ARBEIT_LEISTUNG.get_all_suffixes()
    suff_arbeit: str = cont.ARBEIT_LEISTUNG.arbeit.suffix
    suff_leistung: str = cont.ARBEIT_LEISTUNG.leistung.suffix

    any_col_has_suffix: bool = any(
        (suffix in str(col) for suffix in suffixes) for col in df_con.columns
    )

    leistung_is_4_times_arbeit: list[bool] = []
    for col in [str(col) for col in df_con.columns]:
        if suff_arbeit in col:
            leist_col: str = col.replace(suff_arbeit, suff_leistung)
            if all(df_con[col] == df_con[leist_col] / 4):
                leistung_is_4_times_arbeit.append(True)

    assert any_col_has_suffix
    assert meta_new["index"]
    assert all(leistung_is_4_times_arbeit)
