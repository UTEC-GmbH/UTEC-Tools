"""Test the login page with the Streamlit testing framework"""


import pathlib
import random
from dataclasses import dataclass

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


def test_any_and_all_files() -> None:
    """Tests that should work for any Excel-file"""

    all_ex_files: list[str] = [
        str(file)
        for file in pathlib.Path("example_files").rglob("*")
        if file.is_file() and file.suffix.lower() in {".xlsx", ".xlsm"}
    ]

    for file in all_ex_files:
        at: AppTest = run_app(file)
        assert not at.exception

        mdf: cld.MetaAndDfs = at.session_state["mdf"]

        figs: clf.Figs = at.session_state["figs"]
        assert figs.base is not None
        assert isinstance(figs.base, clf.FigProp)
        assert isinstance(figs.base.fig, go.Figure)
        assert figs.base.st_key == cont.FIG_KEYS.lastgang
        assert isinstance(figs.base.fig.data, tuple)

        lines_base: list[go.Scatter] = [
            line
            for line in figs.base.fig.data
            if all([isinstance(line, go.Scatter), line.name not in cont.EXCLUDE.index])
        ]

        assert len(lines_base) == len(
            [col for col in mdf.df.columns if col not in cont.EXCLUDE.index]
        )


def test_graphs_single_year_strom() -> None:
    """Tests for specified example_file"""

    at: AppTest = run_app(ExFiles.strom_einzel)
    mdf: cld.MetaAndDfs = at.session_state["mdf"]
    figs: clf.Figs = at.session_state["figs"]

    assert mdf is not None
    assert figs.base is not None
