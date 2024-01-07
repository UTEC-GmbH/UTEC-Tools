"""Tests for the excel_pl-module"""

from dataclasses import dataclass

import polars as pl

from modules import classes_data as cld
from modules import excel_import as ex_in


@dataclass
class Asserts:
    """Stuff to test"""

    file_path: str
    df_height: int
    df_width: int
    df_columns: list[str]
    meta_years: list[int]
    meta_temp_res: int
    df_type_index_dt: bool = True
    df_type_data: str = r"{Float32}"
    df_orgidx: bool = True
    df_is_df: bool = True


@dataclass
class ExpectedResults:
    """Test files"""

    strom_einzel: Asserts
    strom_multi: Asserts
    heiz_multi: Asserts


class TestImportPrefabExcel:
    """Tests for the main import function"""

    expected: ExpectedResults = ExpectedResults(
        strom_einzel=Asserts(
            file_path="example_files/Stromlastgang - 15min - 1 Jahr.xlsx",
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
            meta_years=[2021],
            meta_temp_res=15,
        ),
        strom_multi=Asserts(
            file_path="example_files/Stromlastgang - 15min - 2 Jahre.xlsx",
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
            meta_years=[2017, 2018],
            meta_temp_res=15,
        ),
        heiz_multi=Asserts(
            file_path="example_files/Wärmelastgang - 1h - 3 Jahre.xlsx",
            df_height=26277,
            df_width=5,
            df_columns=["↓ Index ↓", "Wärmebedarf", "BHKW", "Temperatur", "orgidx"],
            meta_years=[2016, 2017, 2018],
            meta_temp_res=60,
        ),
    )

    def import_and_assert(self, expected: Asserts) -> None:
        """Compare actual results to expected results"""

        file: str = expected.file_path
        mdf: cld.MetaAndDfs = ex_in.import_prefab_excel(file)

        results: Asserts = Asserts(
            file_path=file,
            df_is_df=isinstance(mdf.df, pl.DataFrame),
            df_height=mdf.df.height,
            df_width=mdf.df.width,
            df_columns=mdf.df.columns,
            df_orgidx="orgidx" in mdf.df.columns,
            df_type_index_dt=mdf.df.schema["↓ Index ↓"] == pl.Datetime(),
            df_type_data=str(
                set(
                    {
                        key: value
                        for key, value in mdf.df.schema.items()
                        if key not in ["↓ Index ↓", "orgidx"]
                    }.values()
                )
            ),
            meta_years=mdf.meta.years,
            meta_temp_res=mdf.meta.td_mnts,
        )

        assert results == expected

    def test_import_single_year_strom_data(self) -> None:
        """Test importing the default example file for single year strom data."""
        self.import_and_assert(self.expected.strom_einzel)

    def test_import_multi_year_strom_data(self) -> None:
        """Test importing the default example file for multi-year strom data."""
        self.import_and_assert(self.expected.strom_multi)

    def test_import_multi_year_heizung_data(self) -> None:
        """Test importing the default example file for multi-year heizung data."""
        self.import_and_assert(self.expected.heiz_multi)
