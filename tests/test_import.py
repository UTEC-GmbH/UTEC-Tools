"""Tests for the import_pl-module"""

from dataclasses import dataclass, field

import polars as pl
import pytest

from modules import classes_constants as clc
from modules import classes_data as cld
from modules import constants as cont
from modules import excel_import as ex_in


@dataclass
class Result:
    """The files to test"""

    file: str
    df_height: int
    df_width: int
    df_columns: list[str]
    meta_lines: dict[str, cld.MetaLine]
    meta_all_units_as_dict: dict[str, str]
    meta_datetime: bool
    meta_years: list[int]
    meta_multi_years: bool
    meta_td_mnts: int
    meta_interval: str
    mdf: cld.MetaAndDfs = field(init=False)

    def __post_init__(self) -> None:
        """Import the file"""
        self.mdf = ex_in.import_prefab_excel(self.file)


ExpectedResults: list[Result] = [
    Result(
        file="example_files/Stromlastgang - 15min - 1 Jahr.xlsx",
        df_height=35032,
        df_width=17,
        df_columns=[
            "↓ Index ↓",
            "Strombedarf → Arbeit",
            "PV Produktion → Arbeit",
            "Netzeinspeisung → Arbeit",
            "PV Eigennutzung → Arbeit",
            "Bezug (1-1:1.29) → Arbeit",
            "Temperatur",
            "Bedarf in kW → Leistung",
            "PV in kW → Leistung",
            "orgidx",
            "Strombedarf → Leistung",
            "PV Produktion → Leistung",
            "Netzeinspeisung → Leistung",
            "PV Eigennutzung → Leistung",
            "Bedarf in kW → Arbeit",
            "PV in kW → Arbeit",
            "Bezug (1-1:1.29) → Leistung",
        ],
        meta_lines={
            "Strombedarf": cld.MetaLine(
                name="Strombedarf",
                name_orgidx="Strombedarf - orgidx",
                orig_tit="Strombedarf",
                tit="Strombedarf",
                unit=" kWh",
                unit_h=" kW",
                obis=None,
                excel_number_format="#,##0.0 kWh",
            ),
            "PV Produktion": cld.MetaLine(
                name="PV Produktion",
                name_orgidx="PV Produktion - orgidx",
                orig_tit="PV Produktion",
                tit="PV Produktion",
                unit=" kWh",
                unit_h=" kW",
                obis=None,
                excel_number_format="#,##0.0 kWh",
            ),
            "Netzeinspeisung": cld.MetaLine(
                name="Netzeinspeisung",
                name_orgidx="Netzeinspeisung - orgidx",
                orig_tit="Netzeinspeisung",
                tit="Netzeinspeisung",
                unit=" kWh",
                unit_h=" kW",
                obis=None,
                excel_number_format="#,##0.0 kWh",
            ),
            "PV Eigennutzung": cld.MetaLine(
                name="PV Eigennutzung",
                name_orgidx="PV Eigennutzung - orgidx",
                orig_tit="PV Eigennutzung",
                tit="PV Eigennutzung",
                unit=" kWh",
                unit_h=" kW",
                obis=None,
                excel_number_format="#,##0.0 kWh",
            ),
            "Temperatur": cld.MetaLine(
                name="Temperatur",
                name_orgidx="Temperatur - orgidx",
                orig_tit="Temperatur",
                tit="Temperatur",
                unit=" °C",
                unit_h=" °C",
                obis=None,
                excel_number_format='#,##0.00" °C"',
            ),
            "Bedarf in kW": cld.MetaLine(
                name="Bedarf in kW",
                name_orgidx="Bedarf in kW - orgidx",
                orig_tit="Bedarf in kW",
                tit="Bedarf in kW",
                unit=" kW",
                unit_h=" kW",
                obis=None,
                excel_number_format='#,##0.00" kW"',
            ),
            "PV in kW": cld.MetaLine(
                name="PV in kW",
                name_orgidx="PV in kW - orgidx",
                orig_tit="PV in kW",
                tit="PV in kW",
                unit=" kW",
                unit_h=" kW",
                obis=None,
                excel_number_format='#,##0.00" kW"',
            ),
            "Bezug (1-1:1.29)": cld.MetaLine(
                name="Bezug (1-1:1.29)",
                name_orgidx="Bezug (1-1:1.29) - orgidx",
                orig_tit="Strombez. 1-1:1.29.0",
                tit="Bezug (1-1:1.29)",
                unit=" kWh",
                unit_h=" kW",
                obis=clc.ObisElectrical(code_or_name="1-1:1.29"),
                excel_number_format="#,##0.0 kWh",
            ),
            "Strombedarf → Leistung": cld.MetaLine(
                name="Strombedarf → Leistung",
                name_orgidx="Strombedarf → Leistung - orgidx",
                orig_tit="Strombedarf → Leistung",
                tit="Strombedarf → Leistung",
                unit=" kW",
                unit_h=" kW",
                obis=None,
                excel_number_format="#,##0.0 kWh",
            ),
            "Strombedarf → Arbeit": cld.MetaLine(
                name="Strombedarf → Arbeit",
                name_orgidx="Strombedarf → Arbeit - orgidx",
                orig_tit="Strombedarf → Arbeit",
                tit="Strombedarf → Arbeit",
                unit=" kWh",
                unit_h=" kW",
                obis=None,
                excel_number_format="#,##0.0 kWh",
            ),
            "PV Produktion → Leistung": cld.MetaLine(
                name="PV Produktion → Leistung",
                name_orgidx="PV Produktion → Leistung - orgidx",
                orig_tit="PV Produktion → Leistung",
                tit="PV Produktion → Leistung",
                unit=" kW",
                unit_h=" kW",
                obis=None,
                excel_number_format="#,##0.0 kWh",
            ),
            "PV Produktion → Arbeit": cld.MetaLine(
                name="PV Produktion → Arbeit",
                name_orgidx="PV Produktion → Arbeit - orgidx",
                orig_tit="PV Produktion → Arbeit",
                tit="PV Produktion → Arbeit",
                unit=" kWh",
                unit_h=" kW",
                obis=None,
                excel_number_format="#,##0.0 kWh",
            ),
            "Netzeinspeisung → Leistung": cld.MetaLine(
                name="Netzeinspeisung → Leistung",
                name_orgidx="Netzeinspeisung → Leistung - orgidx",
                orig_tit="Netzeinspeisung → Leistung",
                tit="Netzeinspeisung → Leistung",
                unit=" kW",
                unit_h=" kW",
                obis=None,
                excel_number_format="#,##0.0 kWh",
            ),
            "Netzeinspeisung → Arbeit": cld.MetaLine(
                name="Netzeinspeisung → Arbeit",
                name_orgidx="Netzeinspeisung → Arbeit - orgidx",
                orig_tit="Netzeinspeisung → Arbeit",
                tit="Netzeinspeisung → Arbeit",
                unit=" kWh",
                unit_h=" kW",
                obis=None,
                excel_number_format="#,##0.0 kWh",
            ),
            "PV Eigennutzung → Leistung": cld.MetaLine(
                name="PV Eigennutzung → Leistung",
                name_orgidx="PV Eigennutzung → Leistung - orgidx",
                orig_tit="PV Eigennutzung → Leistung",
                tit="PV Eigennutzung → Leistung",
                unit=" kW",
                unit_h=" kW",
                obis=None,
                excel_number_format="#,##0.0 kWh",
            ),
            "PV Eigennutzung → Arbeit": cld.MetaLine(
                name="PV Eigennutzung → Arbeit",
                name_orgidx="PV Eigennutzung → Arbeit - orgidx",
                orig_tit="PV Eigennutzung → Arbeit",
                tit="PV Eigennutzung → Arbeit",
                unit=" kWh",
                unit_h=" kW",
                obis=None,
                excel_number_format="#,##0.0 kWh",
            ),
            "Bedarf in kW → Arbeit": cld.MetaLine(
                name="Bedarf in kW → Arbeit",
                name_orgidx="Bedarf in kW → Arbeit - orgidx",
                orig_tit="Bedarf in kW → Arbeit",
                tit="Bedarf in kW → Arbeit",
                unit=" kWh",
                unit_h=" kW",
                obis=None,
                excel_number_format='#,##0.00" kW"',
            ),
            "Bedarf in kW → Leistung": cld.MetaLine(
                name="Bedarf in kW → Leistung",
                name_orgidx="Bedarf in kW → Leistung - orgidx",
                orig_tit="Bedarf in kW → Leistung",
                tit="Bedarf in kW → Leistung",
                unit=" kW",
                unit_h=" kW",
                obis=None,
                excel_number_format='#,##0.00" kW"',
            ),
            "PV in kW → Arbeit": cld.MetaLine(
                name="PV in kW → Arbeit",
                name_orgidx="PV in kW → Arbeit - orgidx",
                orig_tit="PV in kW → Arbeit",
                tit="PV in kW → Arbeit",
                unit=" kWh",
                unit_h=" kW",
                obis=None,
                excel_number_format='#,##0.00" kW"',
            ),
            "PV in kW → Leistung": cld.MetaLine(
                name="PV in kW → Leistung",
                name_orgidx="PV in kW → Leistung - orgidx",
                orig_tit="PV in kW → Leistung",
                tit="PV in kW → Leistung",
                unit=" kW",
                unit_h=" kW",
                obis=None,
                excel_number_format='#,##0.00" kW"',
            ),
            "Bezug (1-1:1.29) → Leistung": cld.MetaLine(
                name="Bezug (1-1:1.29) → Leistung",
                name_orgidx="Bezug (1-1:1.29) → Leistung - orgidx",
                orig_tit="Bezug (1-1:1.29) → Leistung",
                tit="Bezug (1-1:1.29) → Leistung",
                unit=" kW",
                unit_h=" kW",
                obis=clc.ObisElectrical(code_or_name="1-1:1.29"),
                excel_number_format="#,##0.0 kWh",
            ),
            "Bezug (1-1:1.29) → Arbeit": cld.MetaLine(
                name="Bezug (1-1:1.29) → Arbeit",
                name_orgidx="Bezug (1-1:1.29) → Arbeit - orgidx",
                orig_tit="Bezug (1-1:1.29) → Arbeit",
                tit="Bezug (1-1:1.29) → Arbeit",
                unit=" kWh",
                unit_h=" kW",
                obis=clc.ObisElectrical(code_or_name="1-1:1.29"),
                excel_number_format="#,##0.0 kWh",
            ),
        },
        meta_all_units_as_dict={
            "Strombedarf": " kWh",
            "PV Produktion": " kWh",
            "Netzeinspeisung": " kWh",
            "PV Eigennutzung": " kWh",
            "Temperatur": " °C",
            "Bedarf in kW": " kW",
            "PV in kW": " kW",
            "Bezug (1-1:1.29)": " kWh",
            "Strombedarf → Leistung": " kW",
            "Strombedarf → Arbeit": " kWh",
            "PV Produktion → Leistung": " kW",
            "PV Produktion → Arbeit": " kWh",
            "Netzeinspeisung → Leistung": " kW",
            "Netzeinspeisung → Arbeit": " kWh",
            "PV Eigennutzung → Leistung": " kW",
            "PV Eigennutzung → Arbeit": " kWh",
            "Bedarf in kW → Arbeit": " kWh",
            "Bedarf in kW → Leistung": " kW",
            "PV in kW → Arbeit": " kWh",
            "PV in kW → Leistung": " kW",
            "Bezug (1-1:1.29) → Leistung": " kW",
            "Bezug (1-1:1.29) → Arbeit": " kWh",
        },
        meta_datetime=True,
        meta_years=[2021],
        meta_multi_years=False,
        meta_td_mnts=15,
        meta_interval="15min",
    ),
    Result(
        file="example_files/Stromlastgang - 15min - 2 Jahre.xlsx",
        df_height=70071,
        df_width=11,
        df_columns=[
            "↓ Index ↓",
            "Bezug (1-1:1.29) → Leistung",
            "Lieferung (1-1:2.29) → Leistung",
            "PV-Anlage → Arbeit",
            "Bedarf → Arbeit",
            "Temperatur",
            "orgidx",
            "PV-Anlage → Leistung",
            "Bedarf → Leistung",
            "Bezug (1-1:1.29) → Arbeit",
            "Lieferung (1-1:2.29) → Arbeit",
        ],
        meta_lines={
            "PV-Anlage": cld.MetaLine(
                name="PV-Anlage",
                name_orgidx="PV-Anlage - orgidx",
                orig_tit="PV-Anlage",
                tit="PV-Anlage",
                unit=" kWh",
                unit_h=" kW",
                obis=None,
                excel_number_format="#,##0.0 kWh",
            ),
            "Bedarf": cld.MetaLine(
                name="Bedarf",
                name_orgidx="Bedarf - orgidx",
                orig_tit="Bedarf",
                tit="Bedarf",
                unit=" kWh",
                unit_h=" kW",
                obis=None,
                excel_number_format='#,##0.00" kWh"',
            ),
            "Temperatur": cld.MetaLine(
                name="Temperatur",
                name_orgidx="Temperatur - orgidx",
                orig_tit="Temperatur",
                tit="Temperatur",
                unit=" °C",
                unit_h=" °C",
                obis=None,
                excel_number_format='#,##0.00" °C"',
            ),
            "Bezug (1-1:1.29)": cld.MetaLine(
                name="Bezug (1-1:1.29)",
                name_orgidx="Bezug (1-1:1.29) - orgidx",
                orig_tit="Bezug (1-1:1.29.0)",
                tit="Bezug (1-1:1.29)",
                unit=" kW",
                unit_h=" kW",
                obis=clc.ObisElectrical(code_or_name="1-1:1.29"),
                excel_number_format='#,##0.00" kW"',
            ),
            "Lieferung (1-1:2.29)": cld.MetaLine(
                name="Lieferung (1-1:2.29)",
                name_orgidx="Lieferung (1-1:2.29) - orgidx",
                orig_tit="Einsp. (1-1:2.29.0)",
                tit="Lieferung (1-1:2.29)",
                unit=" kW",
                unit_h=" kW",
                obis=clc.ObisElectrical(code_or_name="1-1:2.29"),
                excel_number_format='#,##0.00" kW"',
            ),
            "PV-Anlage → Leistung": cld.MetaLine(
                name="PV-Anlage → Leistung",
                name_orgidx="PV-Anlage → Leistung - orgidx",
                orig_tit="PV-Anlage → Leistung",
                tit="PV-Anlage → Leistung",
                unit=" kW",
                unit_h=" kW",
                obis=None,
                excel_number_format="#,##0.0 kWh",
            ),
            "PV-Anlage → Arbeit": cld.MetaLine(
                name="PV-Anlage → Arbeit",
                name_orgidx="PV-Anlage → Arbeit - orgidx",
                orig_tit="PV-Anlage → Arbeit",
                tit="PV-Anlage → Arbeit",
                unit=" kWh",
                unit_h=" kW",
                obis=None,
                excel_number_format="#,##0.0 kWh",
            ),
            "Bedarf → Leistung": cld.MetaLine(
                name="Bedarf → Leistung",
                name_orgidx="Bedarf → Leistung - orgidx",
                orig_tit="Bedarf → Leistung",
                tit="Bedarf → Leistung",
                unit=" kW",
                unit_h=" kW",
                obis=None,
                excel_number_format='#,##0.00" kWh"',
            ),
            "Bedarf → Arbeit": cld.MetaLine(
                name="Bedarf → Arbeit",
                name_orgidx="Bedarf → Arbeit - orgidx",
                orig_tit="Bedarf → Arbeit",
                tit="Bedarf → Arbeit",
                unit=" kWh",
                unit_h=" kW",
                obis=None,
                excel_number_format='#,##0.00" kWh"',
            ),
            "Bezug (1-1:1.29) → Arbeit": cld.MetaLine(
                name="Bezug (1-1:1.29) → Arbeit",
                name_orgidx="Bezug (1-1:1.29) → Arbeit - orgidx",
                orig_tit="Bezug (1-1:1.29) → Arbeit",
                tit="Bezug (1-1:1.29) → Arbeit",
                unit=" kWh",
                unit_h=" kW",
                obis=clc.ObisElectrical(code_or_name="1-1:1.29"),
                excel_number_format='#,##0.00" kW"',
            ),
            "Bezug (1-1:1.29) → Leistung": cld.MetaLine(
                name="Bezug (1-1:1.29) → Leistung",
                name_orgidx="Bezug (1-1:1.29) → Leistung - orgidx",
                orig_tit="Bezug (1-1:1.29) → Leistung",
                tit="Bezug (1-1:1.29) → Leistung",
                unit=" kW",
                unit_h=" kW",
                obis=clc.ObisElectrical(code_or_name="1-1:1.29"),
                excel_number_format='#,##0.00" kW"',
            ),
            "Lieferung (1-1:2.29) → Arbeit": cld.MetaLine(
                name="Lieferung (1-1:2.29) → Arbeit",
                name_orgidx="Lieferung (1-1:2.29) → Arbeit - orgidx",
                orig_tit="Lieferung (1-1:2.29) → Arbeit",
                tit="Lieferung (1-1:2.29) → Arbeit",
                unit=" kWh",
                unit_h=" kW",
                obis=clc.ObisElectrical(code_or_name="1-1:2.29"),
                excel_number_format='#,##0.00" kW"',
            ),
            "Lieferung (1-1:2.29) → Leistung": cld.MetaLine(
                name="Lieferung (1-1:2.29) → Leistung",
                name_orgidx="Lieferung (1-1:2.29) → Leistung - orgidx",
                orig_tit="Lieferung (1-1:2.29) → Leistung",
                tit="Lieferung (1-1:2.29) → Leistung",
                unit=" kW",
                unit_h=" kW",
                obis=clc.ObisElectrical(code_or_name="1-1:2.29"),
                excel_number_format='#,##0.00" kW"',
            ),
        },
        meta_all_units_as_dict={
            "PV-Anlage": " kWh",
            "Bedarf": " kWh",
            "Temperatur": " °C",
            "Bezug (1-1:1.29)": " kW",
            "Lieferung (1-1:2.29)": " kW",
            "PV-Anlage → Leistung": " kW",
            "PV-Anlage → Arbeit": " kWh",
            "Bedarf → Leistung": " kW",
            "Bedarf → Arbeit": " kWh",
            "Bezug (1-1:1.29) → Arbeit": " kWh",
            "Bezug (1-1:1.29) → Leistung": " kW",
            "Lieferung (1-1:2.29) → Arbeit": " kWh",
            "Lieferung (1-1:2.29) → Leistung": " kW",
        },
        meta_datetime=True,
        meta_years=[2017, 2018],
        meta_multi_years=True,
        meta_td_mnts=15,
        meta_interval="15min",
    ),
    Result(
        file="example_files/Wärmelastgang - 1h - 3 Jahre.xlsx",
        df_height=26277,
        df_width=5,
        df_columns=[
            "↓ Index ↓",
            "Wärmebedarf",
            "BHKW",
            "Temperatur",
            "orgidx",
        ],
        meta_lines={
            "Wärmebedarf": cld.MetaLine(
                name="Wärmebedarf",
                name_orgidx="Wärmebedarf - orgidx",
                orig_tit="Wärmebedarf",
                tit="Wärmebedarf",
                unit=" kWh",
                unit_h=" kW",
                obis=None,
                excel_number_format='#,##0.0" kWh"',
            ),
            "BHKW": cld.MetaLine(
                name="BHKW",
                name_orgidx="BHKW - orgidx",
                orig_tit="BHKW",
                tit="BHKW",
                unit=" kWh",
                unit_h=" kW",
                obis=None,
                excel_number_format='#,##0.00" kWh"',
            ),
            "Temperatur": cld.MetaLine(
                name="Temperatur",
                name_orgidx="Temperatur - orgidx",
                orig_tit="Temperatur",
                tit="Temperatur",
                unit=" °C",
                unit_h=" °C",
                obis=None,
                excel_number_format='#,##0.00" °C"',
            ),
        },
        meta_all_units_as_dict={
            "Wärmebedarf": " kWh",
            "BHKW": " kWh",
            "Temperatur": " °C",
        },
        meta_datetime=True,
        meta_years=[2016, 2017, 2018],
        meta_multi_years=True,
        meta_td_mnts=60,
        meta_interval="1h",
    ),
]


@pytest.mark.parametrize("result", list(ExpectedResults))
class TestDF:
    """Class for all the tests for the data frames"""

    def test_df_height(self, result: Result) -> None:
        """Check if the height of the main data frame is correct."""
        assert result.mdf.df.height == result.df_height

    def test_df_width(self, result: Result) -> None:
        """Check if the width of the main data frame is correct."""
        assert result.mdf.df.width == result.df_width

    def test_df_columns(self, result: Result) -> None:
        """Check if the columns of the main data frame are correct."""
        assert result.mdf.df.columns == result.df_columns

    def test_df_is_df(self, result: Result) -> None:
        """Check if the main data frame is a polars DataFrame."""
        assert isinstance(result.mdf.df, pl.DataFrame)

    def test_df_type_index_dt(self, result: Result) -> None:
        """Check if the index of the main data frame is datetime."""
        assert result.mdf.df.schema[cont.SpecialCols.index] == pl.Datetime()

    def test_df_orgidx(self, result: Result) -> None:
        """Check if the index of the main data was copied and renamed."""
        assert cont.SpecialCols.original_index in result.mdf.df.columns

    def test_df_type_data(
        self, result: Result, expected_type: str = r"{Float32}"
    ) -> None:
        """Check if the data of the main data frame is of the correct type."""
        assert (
            str(
                set(
                    {
                        key: value
                        for key, value in result.mdf.df.schema.items()
                        if key
                        not in [
                            cont.SpecialCols.index,
                            cont.SpecialCols.original_index,
                        ]
                    }.values()
                )
            )
            == expected_type
        )


@pytest.mark.parametrize("result", list(ExpectedResults))
class TestMeta:
    """Class for all the tests for the meta data"""

    def test_meta_lines(self, result: Result) -> None:
        """Check if meta data for each line are filled in correctly."""
        assert result.mdf.meta.lines == result.meta_lines

    def test_meta_all_units_as_dict(self, result: Result) -> None:
        """Check if all units are in the meta data."""
        assert result.mdf.meta.all_units_as_dict() == result.meta_all_units_as_dict

    def test_meta_datetime(self, result: Result) -> None:
        """Check if the date column is a datetime in the meta data."""
        assert result.mdf.meta.datetime == result.meta_datetime

    def test_meta_years(self, result: Result) -> None:
        """Check if the years are found in the meta data."""
        assert result.mdf.meta.years == result.meta_years

    def test_meta_multi_years(self, result: Result) -> None:
        """Check if multi year is correct in the meta data."""
        assert result.mdf.meta.multi_years == result.meta_multi_years

    def test_meta_td_mnts(self, result: Result) -> None:
        """Check if the interval in the meta data is correct."""
        assert result.mdf.meta.td_mnts == result.meta_td_mnts

    def test_meta_interval(self, result: Result) -> None:
        """Check if the interval in the meta data is correct."""
        assert result.mdf.meta.td_interval == result.meta_interval
