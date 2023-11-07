"""Test the login page with the Streamlit testing framework"""

from streamlit.testing.v1 import AppTest


def run_app_and_login(user: str = "", password: str = "") -> AppTest:
    """Run the app and login if user and password are given"""
    at: AppTest = AppTest.from_file("00_🔑_login.py")
    at.run()

    if user and password:
        at.text_input("Username").input(user)
        at.text_input("Password").input(password)

    return at.run()


def test_app_loading() -> None:
    """Tests if the app starts without exception"""
    at: AppTest = run_app_and_login()

    assert not at.exception
