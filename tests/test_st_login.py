"""Test the login page with the Streamlit testing framework"""

import datetime as dt
import os
from dataclasses import dataclass
from typing import Any

import pytest
from dotenv import load_dotenv
from loguru import logger
from streamlit.testing.v1 import AppTest

from modules import constants as cont
from modules import general_functions as gf
from modules import setup_logger as slog
from modules import setup_stuff

load_dotenv(".streamlit/secrets.toml")
slog.logger_setup()


def st_get(at: AppTest, key: str) -> Any:
    """Get a session_state entry"""
    try:
        return at.session_state[key]
    except KeyError:
        return None


@dataclass
class User:
    """Login data and expected results"""

    user: str
    pw: str
    expected_authentication_status: bool
    expected_access_lvl: list | None
    expected_access_until: dt.date | None


USERS: list[User] = [
    User(
        user="utec",
        pw=os.getenv("PW_UTEC", "wrong_password"),
        expected_authentication_status=True,
        expected_access_lvl=["full"],
        expected_access_until=dt.date.max,
    ),
    User(
        user="fl",
        pw=os.getenv("PW_FL", "wrong_password"),
        expected_authentication_status=True,
        expected_access_lvl=["god"],
        expected_access_until=dt.date.max,
    ),
    User(
        user="wrong_user",
        pw="wront_password",
        expected_authentication_status=False,
        expected_access_lvl=None,
        expected_access_until=None,
    ),
]


def run_app_and_login(user: str = "", pw: str = "") -> AppTest:
    """Run the app and login if user and password are given"""

    # logger setup and general page config (Favicon, etc.)
    gf.log_new_run()
    setup_stuff.general_setup()

    at: AppTest = AppTest.from_file(
        script_path="app_pages/00_login.py",
        default_timeout=cont.TimeSecondsIn.minute,
    )
    at.run()

    if user and pw:
        next(ti for ti in at.text_input if ti.label == "Username").input(user)
        next(ti for ti in at.text_input if ti.label == "Password").input(pw)
        at.run()
        at.button("FormSubmitter:Login-Login").click()

    return at.run()


def test_app_loading() -> None:
    """Tests if the app starts without exception"""
    at: AppTest = run_app_and_login()

    assert not at.exception


@pytest.mark.parametrize(
    "user,at", [(user, run_app_and_login(user.user, user.pw)) for user in USERS]
)
class TestUsers:
    """Test login with username and password"""

    def test_no_exception(self, user: User, at: AppTest) -> None:
        """Check if login leads to an exception"""
        logger.info(f"Testing user '{user.user}'")
        assert not at.exception

    def test_authentication_status(self, user: User, at: AppTest) -> None:
        """Check if the authentication status is correct"""
        assert (
            st_get(at, "authentication_status") == user.expected_authentication_status
        )

    def test_access_lvl(self, user: User, at: AppTest) -> None:
        """Check if the access level is correct"""
        assert st_get(at, "access_lvl") == user.expected_access_lvl

    def test_access_until(self, user: User, at: AppTest) -> None:
        """Check if the access until is correct"""
        assert st_get(at, "access_until") == user.expected_access_until
