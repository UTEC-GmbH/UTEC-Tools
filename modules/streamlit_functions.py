"""Streamlit functions so I don't have to write 'st.session_state' all the time"""

from typing import Any

import streamlit as st
from loguru import logger


def st_in(key: str | list[str]) -> bool:
    """Check if a key is in the st.session_state"""
    if isinstance(key, str):
        return key in st.session_state
    return all(key_element in st.session_state for key_element in key)


def st_delete(key: str) -> None:
    """Eintrag in st.session_state löschen"""

    if st_in(key):
        del st.session_state[key]
        logger.warning(f"st.session_state Eintrag {key} gelöscht")


def st_set(key: str, value: Any) -> None:
    """Add an item to streamlit's session_state
    or replace it, if it alread exists
    """
    st.session_state[key] = value


def st_add_once(key: str, value: Any) -> None:
    """Add something to streamlit's session_state if it doesn't exist yet.
    Args:
        - key (str)
        - value (Any)
    """
    if key not in st.session_state:
        st.session_state[key] = value


def st_not_in(key: str) -> bool:
    """Check if a key is not in the st.session_state"""
    return key not in st.session_state


def st_get(key: str) -> Any:
    """Shorter version of st.session_state.get(key)"""
    return st.session_state.get(key)
