"""Test the login page with the Streamlit testing framework"""

from dataclasses import dataclass

import polars as pl
import pytest
from loguru import logger
from plotly import graph_objects as go
from streamlit.testing.v1 import AppTest

from modules import classes_data as cld
from modules import classes_figs as clf
from modules import constants as cont
from modules import general_functions as gf
from modules import setup_logger as slog
from modules import setup_stuff

FILES: list[str] = [
    "example_files/Stromlastgang - 15min - 1 Jahr.xlsx",
    "example_files/Stromlastgang - 15min - 2 Jahre.xlsx",
    "example_files/Wärmelastgang - 1h - 3 Jahre.xlsx",
]


def run_app_from_file(file: str) -> AppTest:
    """Run the app on the graph-page and import the chosen file"""

    # logger setup and general page config (Favicon, etc.)
    slog.logger_setup()
    gf.log_new_run()
    setup_stuff.general_setup()

    at: AppTest = AppTest.from_file(
        script_path="pages/01_📈_Grafische_Datenauswertung.py",
        default_timeout=cont.TimeSecondsIn.minute,
    )

    # fake correct username and password
    at.session_state["authentication_status"] = True

    # import Excel-file
    at.session_state["f_up"] = file

    return at.run()


def get_fig_class(at: AppTest, fig: str) -> clf.FigProp:
    """Get the fig class for a given fig"""
    figs: clf.Figs = at.session_state["figs"]
    return getattr(figs, fig)


@dataclass
class StructureFig:
    """Elements to test"""

    file: str
    st_key: str
    data_available: bool
    layout_available: bool


EXPECTED_BASE_FIGS: list[StructureFig] = [
    StructureFig(
        file="example_files/Stromlastgang - 15min - 1 Jahr.xlsx",
        st_key=cont.FIG_KEYS.lastgang,
        data_available=True,
        layout_available=True,
    )
]


@pytest.mark.parametrize(
    "fig,expected",
    [
        (
            get_fig_class(run_app_from_file(file), "base"),
            next(res for res in EXPECTED_BASE_FIGS if res.file == file),
        )
        for file in FILES
    ],
)
class TestBaseFigs:
    """Class of tests"""

    def test_base(self, fig: clf.FigProp, expected: StructureFig) -> None:
        """Check if the base fig is available"""
        logger.info(f"Checking file '{expected.file}'")
        assert fig is not None

    def test_st_key(self, fig: clf.FigProp, expected: StructureFig) -> None:
        """Check if the main data frame is a polars DataFrame."""
        assert fig.st_key == expected.st_key
