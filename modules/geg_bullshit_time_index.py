"""fix bullshit geg index"""

import os
from io import BytesIO
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import pandas.io.formats.excel

pandas.io.formats.excel.ExcelFormatter.header_style = None  # type: ignore

FOLDER: str = "P:\\Haustechnik\\861 Focke Wulf Siedlung West\\8. LP 1-2 Vorplanung\\Kesseldimensionierung\\WMZ-Daten"


def import_files_in_folder(folder: str = FOLDER) -> Dict[str, pd.DataFrame]:
    """Import files into a Dictionary of dfs"""

    files = os.listdir(folder)
    for file in files:
        if file.startswith("~$"):
            files.remove(file)

    cols = ["Zeitstempel", "momentane Wärmeleistung kW"]

    dic = {file: pd.read_excel(f"{folder}\\{file}") for file in files}

    for df in dic.values():
        for col_head in df.columns:
            if all(col not in col_head for col in cols):
                df.drop(col_head, axis=1, inplace=True)

    return dic


def fix_bullshit_index(df: pd.DataFrame, bs_name: str = "Zeitstempel") -> pd.DataFrame:
    """repair the bullshit time index

    Args:
        df (pd.DataFrame): DataFrame with the bullshit index
        bs_name (str, optional): Name of the bullshit column. Defaults to "Zeitstempel".

    Returns:
        tuple[pd.DataFrame, pd.DataFrame]: repaired df with proper index (original, hourly values)
    """

    bs_col: pd.Series = df[bs_name]
    bs_col = pd.to_datetime(bs_col, format="%d.%m.%Y %I:%M:%S")

    for col in df.columns:
        if col != bs_name:
            df[col] = pd.to_numeric(df[col], "coerce")

    # wenn Stunden negative Differenz haben und Tag gleich bleibt
    if any(bs_col.dt.hour.diff().values < 0) and any(bs_col.dt.day.diff().values == 0):
        conditions = [
            (bs_col.dt.day.diff().values > 0),  # neuer Tag
            (bs_col.dt.month.diff().values != 0),  # neuer Monat
            (bs_col.dt.year.diff().values != 0),  # neues Jahr
            (
                (bs_col.dt.hour.diff().values < 0) & (bs_col.dt.day.diff().values == 0)
            ),  # Stunden mit negativer Differenz und Tag bleibt gleich
        ]

        choices: List = [
            pd.Timedelta(0, "h"),
            pd.Timedelta(0, "h"),
            pd.Timedelta(0, "h"),
            pd.Timedelta(12, "h"),
        ]

        offset = pd.Series(
            data=np.select(conditions, choices, default=np.nan),
            index=bs_col.index,
            dtype="timedelta64[ns]",
        )

        offset[0] = pd.Timedelta(0)
        offset.fillna(method="ffill", inplace=True)

        bs_col += offset

    df[bs_name] = bs_col
    df.set_index(bs_name, inplace=True)
    df = df[~df.index.duplicated(keep="first")]

    df_h: pd.DataFrame = df.resample("H").mean()
    for col in df_h.columns:
        df_h.loc[df_h[col].diff() == 0, col] = np.nan
        df_h = df_h.interpolate("akima")  # 'akima'

    return df_h


def excel_hourly(dic: Dict[str, pd.DataFrame]) -> None:
    """create Excel-file

    Args:
        dic (Dict[str, pd.DataFrame]): _description_
    """
    offset_col = 2
    offset_row = 4

    with pd.ExcelWriter(
        f"{FOLDER}\\python_output.xlsx",
        engine="xlsxwriter",
        datetime_format="dd.mm.yyyy hh:mm",
        date_format="dd.mm.yyyy",
    ) as writer:
        for key, df in dic.items():
            ws_name = str(key).split("_", maxsplit=1)[1].strip(".xlsx")
            dic_num_formats = {key: '#,##0.0" kW"' for key in df.columns}

            df.to_excel(
                writer,
                sheet_name=ws_name,
                startrow=offset_row,
                startcol=offset_col,
            )

            wkb = writer.book  # pylint: disable=no-member
            wks = writer.sheets[ws_name]

            # Formatierung
            wks.hide_gridlines(2)
            dic_format_base = {
                "bold": False,
                "font_name": "Arial",
                "font_size": 10,
                "align": "right",
                "border": 0,
            }

            # erste Spalte
            dic_format_col1 = dic_format_base.copy()
            dic_format_col1["align"] = "left"
            cell_format = wkb.add_format(dic_format_col1)
            wks.set_column(offset_col, offset_col, 18, cell_format)

            # erste Zeile
            dic_format_header = dic_format_base.copy()
            dic_format_header["bottom"] = 1
            cell_format = wkb.add_format(dic_format_header)
            wks.write(offset_row, offset_col, "Datum", cell_format)
            for col, header in enumerate(df.columns):
                wks.write(offset_row, col + 1 + offset_col, header, cell_format)

            # Spaltenbreiten
            dic_col_width = {col: len(col) + 1 for col in df.columns}

            for num_format in dic_num_formats.values():
                dic_format_num = dic_format_base.copy()
                dic_format_num["num_format"] = num_format
                col_format = wkb.add_format(dic_format_num)

                for cnt, col in enumerate(df.columns):
                    if dic_num_formats[col] == num_format:
                        wks.set_column(
                            cnt + offset_col + 1,
                            cnt + offset_col + 1,
                            dic_col_width[col],
                            col_format,
                        )


def fix_all_and_export() -> None:
    """do it"""
    dic = import_files_in_folder()
    dic_fixed = {key: fix_bullshit_index(df) for key, df in dic.items()}
    excel_hourly(dic_fixed)
