"""Test the login page with the Streamlit testing framework"""


import pathlib
import random
from dataclasses import dataclass

import polars as pl
from plotly import graph_objects as go
from streamlit.testing.v1 import AppTest

from modules import classes_data as cld
from modules import classes_figs as clf
from modules import constants as cont
from modules import general_functions as gf
from modules import setup_logger as slog
from modules import setup_stuff


@dataclass
class ExFiles:
    """Example Files"""

    strom_einzel: str = "example_files/Stromlastgang - 15min - 1 Jahr.xlsx"
    strom_multi: str = "example_files/Stromlastgang - 15min - 2 Jahre.xlsx"
    warme_multi: str = "example_files/Wärmelastgang - 1h - 3 Jahre.xlsx"


ALL_EX_FILES: list[str] = [
    str(file)
    for file in pathlib.Path("example_files").rglob("*")
    if file.is_file() and file.suffix.lower() in {".xlsx", ".xlsm"}
]


def choose_random_exfile() -> str:
    """Choose a random file from the example_files folder"""

    folder = pathlib.Path("example_files")
    excel_files: list[str] = [
        str(file)
        for file in folder.rglob("*")
        if file.is_file() and file.suffix.lower() in {".xlsx", ".xlsm"}
    ]

    return random.choice(excel_files)  # noqa: S311


def run_app(file: str) -> AppTest:
    """Run the app on the graph-page and import the chosen file"""
    at: AppTest = AppTest.from_file(
        script_path="pages/01_📈_Grafische_Datenauswertung.py",
        default_timeout=cont.InSec.minute,
    )
    # logger setup and general page config (Favicon, etc.)
    slog.logger_setup()
    gf.log_new_run()
    setup_stuff.general_setup()

    # fake correct username and password
    at.session_state["authentication_status"] = True

    # import Excel-file
    at.session_state["f_up"] = file

    return at.run()


def general_mdf(at: AppTest) -> None:
    """Asserts about mdf that should work on any file"""
    mdf: cld.MetaAndDfs = at.session_state["mdf"]

    assert mdf is not None
    assert isinstance(mdf.df, pl.DataFrame)
    assert isinstance(mdf.df_h, pl.DataFrame)
    assert isinstance(mdf.jdl, pl.DataFrame)
    assert isinstance(mdf.mon, pl.DataFrame)


def general_figs(at: AppTest) -> None:
    """Asserts about figs that should work on any file"""

    figs: clf.Figs = at.session_state["figs"]

    assert figs.base is not None
    assert figs.jdl is not None
    assert figs.mon is not None


def general_base(at: AppTest) -> None:
    """Asserts about figs.base that should work on any file"""
    # mdf: cld.MetaAndDfs = at.session_state["mdf"]
    figs: clf.Figs = at.session_state["figs"]

    assert figs.base is not None
    assert isinstance(figs.base, clf.FigProp)
    assert isinstance(figs.base.fig, go.Figure)
    assert figs.base.st_key == cont.FIG_KEYS.lastgang
    assert isinstance(figs.base.fig.data, tuple)


def test_all_ex_files() -> None:
    """Tests that should work for any Excel-file"""

    for file in ALL_EX_FILES:
        at: AppTest = run_app(file)
        assert not at.exception

        general_mdf(at)
        general_figs(at)
        general_base(at)


def test_graphs_single_year_strom() -> None:
    """Tests for specified example_file"""
    at: AppTest = run_app(ExFiles.strom_einzel)
    assert not at.exception

    mdf: cld.MetaAndDfs = at.session_state["mdf"]
    figs: clf.Figs = at.session_state["figs"]

    assert mdf is not None
    assert figs.base is not None
