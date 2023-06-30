"""Streamlit functions so I don't have to write 'st.session_state' all the time"""

from typing import Any

import streamlit as st
from loguru import logger


def s_get(key: str) -> Any:
    """Shorter version of st.session_state.get(key)"""
    return st.session_state.get(key)


def s_in(key: str | list[str]) -> bool:
    """Check if a key is in the st.session_state"""
    if isinstance(key, str):
        return key in st.session_state
    return all(key_element in st.session_state for key_element in key)


def s_not_in(key: str) -> bool:
    """Check if a key is not in the st.session_state"""
    return key not in st.session_state


def s_add_once(key: str, value: Any) -> None:
    """Add something to streamlit's session_state if it doesn't exist yet."""
    if key not in st.session_state:
        st.session_state[key] = value


def s_set(key: str, value: Any) -> None:
    """Add an item to streamlit's session_state
    or replace it, if it alread exists
    """
    st.session_state[key] = value


def s_delete(key: str) -> None:
    """Eintrag in st.session_state löschen"""

    if s_in(key):
        del st.session_state[key]
        logger.warning(f"st.session_state Eintrag {key} gelöscht")


def s_reset_graph() -> None:
    """Delete the entire st.session_state"""
    initial_keys: list[str] = [
        "number of runs",
        "access_lvl",
        "butt_list_all",
        "all_user_data",
        "lottie_login",
        "butt_change_user",
        "name",
        "page",
        "logger_setup",
        "dic_exe_time",
        "username",
        "title_container",
        "butt_del_user",
        "access_until",
        "com_date",
        "logged_username",
        "init",
        "logout",
        "com_msg",
        "butt_add_new_user",
        "butt_sub_del_user",
        "access_pages",
        "authentication_status",
        "butt_sub_new_user",
        "UTEC_logo",
        "initial_setup",
    ]
    for key in st.session_state:
        if key not in initial_keys:
            del st.session_state[key]
    logger.warning("App zurückgesetzt")