"""Test the login page with the Streamlit testing framework"""

import pathlib

from plotly import graph_objects as go
from streamlit.testing.v1 import AppTest

from modules import classes_figs as clf
from modules import constants as cont
from modules import general_functions as gf
from modules import setup_logger as slog
from modules import setup_stuff

EX_FILES = list(pathlib.Path("example_files").iterdir())


def run_app_and_login(phil: pathlib.Path) -> AppTest:
    """Run the app on the given page"""

    at: AppTest = AppTest.from_file("pages/01_📈_Grafische_Datenauswertung.py")

    # logger setup and logging run
    slog.logger_setup()
    gf.log_new_run()

    # general page config (Favicon, etc.)
    setup_stuff.general_setup()

    # fake correct username and password
    at.session_state["authentication_status"] = True

    # import Excel-file
    at.session_state["f_up"] = phil

    return at.run(timeout=60)


def test_app_loading() -> None:
    """Tests if the app runs without exception"""

    for file in EX_FILES:
        at: AppTest = run_app_and_login(file)
        figs: clf.Figs = at.session_state["figs"]
        assert not at.exception
        assert isinstance(figs.base, clf.FigProp)
        assert isinstance(figs.base.fig, go.Figure)
        assert figs.base.st_key == cont.FIG_KEYS.lastgang
