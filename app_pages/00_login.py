"""login page"""

import datetime as dt
from typing import Any

import streamlit as st
import streamlit_authenticator as stauth
import streamlit_lottie as stlot
from loguru import logger

from modules import constants as cont
from modules import general_functions as gf
from modules import setup_stuff
from modules import streamlit_functions as sf
from modules import user_authentication as uauth

setup_stuff.page_header_setup(page=cont.ST_PAGES.login.short)


@gf.func_timer
def display_login_page() -> None:
    """Login-Page with two columns
    - login with username and password
    - lottie-animation
    """
    columns: list = st.columns(2)

    with columns[0]:
        login_section()
    with columns[1]:
        stlot.st_lottie(
            gf.load_lottie_file("animations/login.json"), height=450, key="lottie_login"
        )


@gf.func_timer
def login_section() -> None:
    """User authentication part of the login page"""

    authenticator: stauth.Authenticate = sf.s_add_once(
        "authenticator",
        stauth.Authenticate(
            credentials={"usernames": cont.USERS},
            cookie_name="utec_tools",
            cookie_key="uauth",
            cookie_expiry_days=30.0,
        ),
    )

    authenticator.login(fields={"Username": "Benutzername", "Password": "Passwort"})

    logger.debug(
        f"authentication_status in Session State: {sf.s_get('authentication_status')}"
    )

    if sf.s_get("authentication_status"):
        access_granted()

        st.markdown("---")
        authenticator.logout("Logout", "main")

    elif sf.s_get("authentication_status") is None:
        st.warning("Bitte Benutzernamen und Passwort eingeben")
    else:
        st.error("Benutzername oder Passwort falsch")
        logger.error("Benutzername oder Passwort falsch")


@gf.func_timer
def access_granted() -> None:
    """If access is granted, do this..."""

    # determine the access level
    user_key: str = sf.s_get("username") or "Unknown"
    all_users: dict[str, dict[str, Any]] = sf.s_get("all_user_data") or {}
    access_lvl_user: list = all_users[user_key]["access_lvl"]
    sf.s_set("access_lvl", access_lvl_user)

    # log used username and access level
    if sf.s_not_in("logged_username") or sf.s_get("logged_username") != user_key:
        logger.success(
            f"""
            logged in as: '{user_key}' (name:'{sf.s_get("name")}')
            access level: '{access_lvl_user}'
            """
        )
        sf.s_set("logged_username", user_key)

    if any(lvl in access_lvl_user for lvl in ("god", "full")):
        sf.s_set("access_pages", cont.ST_PAGES.get_all_short())
        sf.s_set("access_until", dt.date.max)
    else:
        sf.s_set("access_pages", access_lvl_user)
        sf.s_set(
            "access_until",
            (
                dt.datetime.strptime(all_users[user_key]["access_until"], "%Y-%m-%d")
                .astimezone()
                .date()
            ),
        )

    if sf.s_get("username") in ["utec"]:
        st.markdown(uauth.MessageLog.access_utec.message)

    else:
        if uauth.MessageLog.access_other is not None:
            st.markdown(uauth.MessageLog.access_other.message)

        if st.session_state["access_until"] < dt.date.max:
            st.markdown(uauth.MessageLog.access_until.message)
        else:
            st.markdown(uauth.MessageLog.access_level.message)

        for page in st.session_state["access_pages"]:
            if page != "login":
                st.markdown(f"- {cont.ST_PAGES.get_title(page)}")


display_login_page()

logger.success("Login Page loaded")
