"""Test the login page with the Streamlit testing framework"""

from dataclasses import dataclass, field
from typing import Literal

import pytest
from plotly import graph_objects as go
from streamlit.testing.v1 import AppTest

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


def get_fig_from_session_state(at: AppTest, fig: str) -> clf.FigProp:
    """Get the fig class for a given fig"""
    figs: clf.Figs = at.session_state["figs"]
    return getattr(figs, fig)


@dataclass
class FigElements:
    """Elements to test"""

    file: str
    fig_type: Literal["base", "jdl", "mon"]
    st_key: str


EXPECTED: list[FigElements] = [
    FigElements(
        file="example_files/Stromlastgang - 15min - 1 Jahr.xlsx",
        fig_type="base",
        st_key=cont.FIG_KEYS.lastgang,
    ),
    FigElements(
        file="example_files/Stromlastgang - 15min - 2 Jahre.xlsx",
        fig_type="base",
        st_key=cont.FIG_KEYS.lastgang,
    ),
    FigElements(
        file="example_files/Wärmelastgang - 1h - 3 Jahre.xlsx",
        fig_type="base",
        st_key=cont.FIG_KEYS.lastgang,
    ),
    FigElements(
        file="example_files/Stromlastgang - 15min - 1 Jahr.xlsx",
        fig_type="jdl",
        st_key=cont.FIG_KEYS.jdl,
    ),
    FigElements(
        file="example_files/Stromlastgang - 15min - 2 Jahre.xlsx",
        fig_type="jdl",
        st_key=cont.FIG_KEYS.jdl,
    ),
    FigElements(
        file="example_files/Wärmelastgang - 1h - 3 Jahre.xlsx",
        fig_type="jdl",
        st_key=cont.FIG_KEYS.jdl,
    ),
    FigElements(
        file="example_files/Stromlastgang - 15min - 1 Jahr.xlsx",
        fig_type="mon",
        st_key=cont.FIG_KEYS.mon,
    ),
    FigElements(
        file="example_files/Stromlastgang - 15min - 2 Jahre.xlsx",
        fig_type="mon",
        st_key=cont.FIG_KEYS.mon,
    ),
    FigElements(
        file="example_files/Wärmelastgang - 1h - 3 Jahre.xlsx",
        fig_type="mon",
        st_key=cont.FIG_KEYS.mon,
    ),
]


@dataclass
class Results:
    """File and App"""

    file: str
    at: AppTest = field(init=False)
    base: clf.FigProp = field(init=False)
    jdl: clf.FigProp = field(init=False)
    mon: clf.FigProp = field(init=False)
    expected_base: FigElements = field(init=False)
    expected_jdl: FigElements = field(init=False)
    expected_mon: FigElements = field(init=False)

    def __post_init__(self) -> None:
        """Fill in fields"""
        self.at = run_app_from_file(self.file)
        self.base = get_fig_from_session_state(self.at, "base")
        self.jdl = get_fig_from_session_state(self.at, "jdl")
        self.mon = get_fig_from_session_state(self.at, "mon")
        self.expected_base = next(
            elem
            for elem in EXPECTED
            if elem.file == self.file and elem.fig_type == "base"
        )
        self.expected_jdl = next(
            elem
            for elem in EXPECTED
            if elem.file == self.file and elem.fig_type == "jdl"
        )
        self.expected_mon = next(
            elem
            for elem in EXPECTED
            if elem.file == self.file and elem.fig_type == "mon"
        )


@pytest.mark.parametrize("results", [Results(file) for file in FILES])
@pytest.mark.parametrize("fig", ["base", "jdl", "mon"])
class TestBaseFigs:
    """Class of tests"""

    def test_fig_exists(self, results: Results, fig: str) -> None:
        """Check if the base fig is available"""

        assert getattr(results, fig) is not None

    def test_st_key(self, results: Results, fig: str) -> None:
        """Check if the main data frame is a polars DataFrame."""
        fig_in_st: clf.FigProp = getattr(results, fig)
        expected_results: FigElements = getattr(results, f"expected_{fig}")

        assert fig_in_st.st_key == expected_results.st_key
