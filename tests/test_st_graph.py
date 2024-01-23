"""Test the login page with the Streamlit testing framework"""


import pathlib
import random
from dataclasses import dataclass

import polars as pl
from loguru import logger
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


def general_mdf(at: AppTest) -> None:
    """Asserts about mdf that should work on any file"""
    mdf: cld.MetaAndDfs = at.session_state["mdf"]

    # check if data frame and meta data are in session state
    assert mdf is not None

    for name, df in {
        "standard": mdf.df,
        "hourly": mdf.df_h,
        "jdl": mdf.jdl,
        "monthly": mdf.mon,
    }.items():
        # check if data frames are of the correct type
        assert isinstance(df, pl.DataFrame)

        # check if the date column is imported correctly
        if name == "jdl":
            assert df[cont.ExcelMarkers.index].dtype.is_numeric()
        else:
            assert df[cont.ExcelMarkers.index].dtype.is_temporal()


def general_figs(at: AppTest) -> clf.Figs:
    """Asserts about figs that should work on any file"""

    # TODO
    """
    Sobald Plotly plots in AppTest unterstützt werden,
    sollten die Grafiken direkt verwendet und nicht mehr
    aus dem Session_State geholt werden !!!
    """
    figs: clf.Figs = at.session_state["figs"]

    for fig in [figs.base, figs.jdl, figs.mon]:
        assert fig is not None
        assert isinstance(fig, clf.FigProp)
        assert isinstance(fig.fig, go.Figure)

    return figs


def general_base(at: AppTest) -> clf.FigProp:
    """Asserts about figs.base that should work on any file"""
    # mdf: cld.MetaAndDfs = at.session_state["mdf"]
    figs: clf.Figs = at.session_state["figs"]

    assert figs.base is not None
    assert figs.base.st_key == cont.FIG_KEYS.lastgang
    assert isinstance(figs.base.fig.data, tuple)
    assert figs.base.fig.layout is not None

    return figs.base


def test_hourly_from_15min() -> None:
    """Test if changing the resolution to hourly works"""

    for file in ALL_EX_FILES:
        if "15min" not in file:
            continue
        at: AppTest = run_app(file)
        assert not at.exception

        fig_base_before: clf.FigProp = general_base(at)

        if at.checkbox(key="cb_h").value:
            at.checkbox(key="cb_h").uncheck()
        else:
            at.checkbox(key="cb_h").check()
        at.button(key="FormSubmitter:Grundeinstellungen-Knöpfle").click().run()
        assert not at.exception

        fig_base: clf.FigProp = general_base(at)
        assert (
            fig_base_before.fig.layout["title"]["text"]
            != fig_base.fig.layout["title"]["text"]
        )

        if at.checkbox("cb_h"):
            assert cont.Suffixes.fig_tit_h in fig_base.fig.layout["title"]["text"]
        else:
            assert cont.Suffixes.fig_tit_15 in fig_base.fig.layout["title"]["text"]


def test_toggle_multi_year_overlay() -> None:
    """Test if changing the yearly overlay works"""

    for file in ALL_EX_FILES:
        if "1 Jahr" in file:
            continue
        at: AppTest = run_app(file)
        assert not at.exception

        fig_base_before: clf.FigProp = general_base(at)
        traces_before: list[str] = [
            str(entry.name)
            for entry in fig_base_before.fig.data
            if isinstance(entry, go.Scatter)
        ]

        if at.checkbox(key="cb_multi_year").value:
            at.checkbox(key="cb_multi_year").uncheck()
        else:
            at.checkbox(key="cb_multi_year").check()
        at.button(key="FormSubmitter:Grundeinstellungen-Knöpfle").click().run()
        assert not at.exception

        fig_base: clf.FigProp = general_base(at)
        traces_after: list[str] = [
            str(entry.name)
            for entry in fig_base.fig.data
            if isinstance(entry, go.Scatter)
        ]

        if at.checkbox(key="cb_multi_year"):
            assert len(traces_after) < len(traces_before)
        else:
            assert len(traces_after) > len(traces_before)


def test_general_things_for_all_example_files() -> None:
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
