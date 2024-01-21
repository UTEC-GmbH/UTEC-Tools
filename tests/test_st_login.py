"""Test the login page with the Streamlit testing framework"""

import datetime as dt

from streamlit.testing.v1 import AppTest

from modules import constants as cont


def run_app_and_login(user: str = "", pw: str = "") -> AppTest:
    """Run the app and login if user and password are given"""
    at: AppTest = AppTest.from_file(
        script_path="00_🔑_login.py", default_timeout=cont.TimeSecondsIn.minute
    )
    at.run()

    if user and pw:
        at.text_input[0].input(user)
        at.text_input[1].input(pw)
        at.run()
        at.button[0].click()

    return at.run()


def test_app_loading() -> None:
    """Tests if the app starts without exception"""
    at: AppTest = run_app_and_login()

    assert not at.exception
    assert at.session_state["authentication_status"] is None


def test_login_utec() -> None:
    """Test login with username and password for general UTEC account"""
    at: AppTest = run_app_and_login(user="UTEC", pw="füralle")
    assert not at.exception

    expected_session_state: dict = {
        "authentication_status": True,
        "access_lvl": "full",
        "access_until": dt.date.max,
    }

    for key, value in expected_session_state.items():
        assert at.session_state[key] == value
