"""Debugging with ChatGPT"""

from dataclasses import dataclass, field

import streamlit as st
from loguru import logger


@dataclass
class MessageLog:
    """Represents an Error with a message and an optional log message."""

    message: str
    log: str | None = None

    def show_error(self) -> None:
        """Writes a log message and a streamlit error for a specified error type."""
        if self.log:
            logger.error(self.log)
        st.error(self.message)


@dataclass
class CustomError:
    """Contains instances of the MessageLog class for each error type."""

    if "access_until" in st.session_state:
        until: str | None = (
            st.session_state["access_until"]
            or f"{st.session_state['access_until']:%d.%m.%Y}"
        )
    else:
        until = None

    no_access = MessageLog(
        message=(
            "Mit diesem Benutzerkonto haben Sie keinen Zugriff auf dieses Modul."
            "\n\n"
            "Bitte nehmen Sie Kontakt mit UTEC auf."
        ),
        log="no access to page (module)",
    )

    no_login = MessageLog(
        message="Bitte anmelden! (login auf der linken Seite)", log="not logged in"
    )

    too_late = MessageLog(
        message=(
            f"""
                Zugriff war nur bis {until} gestattet.  \n  \n
                Bitte nehmen Sie Kontakt mit UTEC auf.
            """
        ),
        log="access for user expired",
    )

    access_utec = MessageLog(
        message=(
            """
            Du bist mit dem allgemeinen UTEC-Account angemeldet.  \n  \n
            Viel Spaß mit den Tools!
        """
        )
    )

    access_other = MessageLog(message=(f"Angemeldet als '{gf.st_get('name')}'."))

    access_until = MessageLog(
        message=(
            f"""
            Mit diesem Account kann auf folgende Module bis zum 
            {until} zugegriffen werden:
        """
        )
    )

    access_level = MessageLog(
        message=("Mit diesem Account kann auf folgende Module zugegriffen werden:")
    )
