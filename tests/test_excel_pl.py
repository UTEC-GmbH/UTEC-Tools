"""Tests for the excel_pl-module"""

from dataclasses import dataclass

import polars as pl

from modules import excel_pl as ex


@dataclass
class Asserts:
    """Stuff to test"""

    file_path: str
    df_height: int
    df_width: int
    meta_years: list[int]
    meta_temp_res: int
    meta_units_set: list[str]
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
            file_path="example_files/Auswertung Stromlastgang - einzelnes Jahr.xlsx",
            df_height=35032,
            df_width=7,
            meta_years=[2021],
            meta_temp_res=15,
            meta_units_set=[" kWh"],
        ),
        strom_multi=Asserts(
            file_path="example_files/Stromlastgang - mehrere Jahre.xlsx",
            df_height=105107,
            df_width=6,
            meta_years=[2017, 2018, 2019],
            meta_temp_res=15,
            meta_units_set=[" kW", " kWh"],
        ),
        heiz_multi=Asserts(
            file_path="example_files/Wärmelastgang - mehrere Jahre.xlsx",
            df_height=35036,
            df_width=5,
            meta_years=[2016, 2017, 2018, 2019],
            meta_temp_res=60,
            meta_units_set=[" kWh", " °C"],
        ),
    )

    def import_and_assert(self, expected: Asserts) -> None:
        """Compare actual results to expected results"""

        file: str = expected.file_path
        df, meta = ex.import_prefab_excel(file)

        results: Asserts = Asserts(
            file_path=file,
            df_is_df=isinstance(df, pl.DataFrame),
            df_height=df.height,
            df_width=df.width,
            df_orgidx="orgidx" in df.columns,
            df_type_index_dt=df.schema["↓ Index ↓"] == pl.Datetime(),
            df_type_data=str(
                set(
                    {
                        key: value
                        for key, value in df.schema.items()
                        if key not in ["↓ Index ↓", "orgidx"]
                    }.values()
                )
            ),
            meta_years=meta.years,
            meta_temp_res=meta.td_mean,
            meta_units_set=meta.units.set_units,
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
