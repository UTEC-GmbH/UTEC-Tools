"""Test the login page with the Streamlit testing framework"""

from streamlit.testing.v1 import AppTest

from modules import general_functions as gf
from modules import setup_logger as slog
from modules import setup_stuff


def run_app_and_login() -> AppTest:
    """Run the app on the given page"""

    at: AppTest = AppTest.from_file("pages/01_📈_Grafische_Datenauswertung.py")

    # logger setup and logging run
    slog.logger_setup()
    gf.log_new_run()

    # general page config (Favicon, etc.)
    setup_stuff.general_setup()

    # fake correct username and password
    at.session_state["authentication_status"] = True

    return at.run()


def test_app_loading() -> None:
    """Tests if the app starts without exception"""
    at: AppTest = run_app_and_login()

    assert not at.exception
