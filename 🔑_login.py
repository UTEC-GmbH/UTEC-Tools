"""
login page
"""

from datetime import date, datetime
from typing import Any, Dict, List

import streamlit as st
import streamlit_authenticator as stauth
from loguru import logger
from streamlit_lottie import st_lottie

from modules import constants as cont
from modules import setup_stuff
from modules import streamlit_menus as sm
from modules import user_authentication as uauth
from modules.general_functions import func_timer, load_lottie_file

# page setup
setup_stuff.initial_setup()

setup_stuff.page_header_setup(page="login")


# @func_timer
def display_login_page() -> None:
    """Login-Page with two columns
    - login with username and password
    - lottie-animation
    """
    columns: List = st.columns(2)

    with columns[0]:
        login_section()
    with columns[1]:
        st_lottie(
            load_lottie_file("animations/login.json"), height=450, key="lottie_login"
        )


# @func_timer
def login_section() -> None:
    """user authentication part of the login page"""

    user_credentials: Dict[str, Dict[str, Any]] = uauth.format_user_credentials()
    authenticator: stauth.Authenticate = stauth.Authenticate(
        credentials=user_credentials,
        cookie_name="utec_tools",
        key="uauth",
        cookie_expiry_days=30,
    )

    authenticator.login("Login", "main")

    if st.session_state["authentication_status"]:
        access_granted()

        st.markdown("###")
        authenticator.logout("Logout", "main")

    elif st.session_state["authentication_status"] is None:
        st.warning("Bitte Benutzernamen und Passwort eingeben")
    else:
        st.error("Benutzername oder Passwort falsch")
        logger.error("Benutzername oder Passwort falsch")


def access_granted() -> None:
    """if access is granted, do this..."""

    # determine the access level
    user_key: str = st.session_state["username"]
    all_users: Dict[str, Dict[str, Any]] = st.session_state["all_user_data"]
    access_lvl_user: str | List = all_users[user_key]["access_lvl"]
    st.session_state["access_lvl"] = access_lvl_user

    # log used username and access level
    if st.session_state.get("logged_username") != user_key:
        logger.success(f"logged in as: {user_key}, access level: {access_lvl_user}")
        st.session_state["logged_username"] = user_key

    if access_lvl_user in ("god", "full"):
        st.session_state["access_pages"] = list(cont.PAGES)
        st.session_state["access_until"] = date.max
    else:
        st.session_state["access_pages"] = access_lvl_user
        st.session_state["access_until"] = datetime.strptime(
            all_users[user_key]["access_until"], "%Y-%m-%d"
        ).date()

    if st.session_state.get("username") in ["utec"]:
        st.markdown(uauth.infos_warnings_errors("access_UTEC"))

    else:
        st.markdown(uauth.infos_warnings_errors("access_other"))

        if st.session_state["access_until"] < date.max:
            st.markdown(uauth.infos_warnings_errors("access_until"))
        else:
            st.markdown(uauth.infos_warnings_errors("access_level"))

        for page in st.session_state["access_pages"]:
            if page != "login":
                st.markdown(f"- {cont.PAGES[page]['page_tit']}")

    if access_lvl_user == "god":
        god_mode()


def god_mode() -> None:
    """special stuff for users with access level 'god'"""

    sm.user_accounts()
    # neuen Benutzer eintragen
    if st.session_state.get("butt_sub_new_user"):
        with st.spinner("Momentle bitte, Benutzer wird hinzugefügt..."):
            uauth.insert_new_user(
                st.session_state["new_user_user"],
                st.session_state["new_user_name"],
                st.session_state["new_user_email"],
                st.session_state["new_user_pw"],
                st.session_state["new_user_access"],
                str(st.session_state["new_user_until"]),
            )

    # Benutzer löschen
    if st.session_state.get("butt_sub_del_user"):
        uauth.delete_user()


display_login_page()
