"""user authentication"""

import datetime as dt
from dataclasses import dataclass
from typing import Any

import streamlit as st
from loguru import logger

from modules import streamlit_functions as sf


@dataclass
class MessageLogLvl2:
    """Represents an Error with a message and an optional log message."""

    message: str
    log: str | None = None

    def show_message(self) -> None:
        """Write a log message and a streamlit error for a specified error type."""

        if self.log:
            logger.error(self.log)
        st.error(self.message)


@dataclass
class MessageLog:
    """Contains instances of the MessageLog class for each error type."""

    until: str | None
    if "access_until" in st.session_state:
        until = (
            st.session_state["access_until"]
            or f"{st.session_state['access_until']:%d.%m.%Y}"
        )
    else:
        until = None

    no_access = MessageLogLvl2(
        message=(
            "Mit diesem Benutzerkonto haben Sie keinen Zugriff auf dieses Modul."
            "\n\n"
            "Bitte nehmen Sie Kontakt mit UTEC auf."
        ),
        log="no access to page (module)",
    )

    no_login = MessageLogLvl2(
        message="Bitte anmelden! (login auf der linken Seite)", log="not logged in"
    )

    too_late = MessageLogLvl2(
        message=(
            f"Zugriff war nur bis {until} gestattet."
            "\n\n"
            "Bitte nehmen Sie Kontakt mit UTEC auf."
        ),
        log="access for user expired",
    )

    access_utec = MessageLogLvl2(
        message=(
            "Du bist mit dem allgemeinen UTEC-Account angemeldet."
            "\n\n"
            "Viel Spaß mit den Tools!"
        )
    )

    access_other = MessageLogLvl2("Angemeldung Erfolgreich.")

    access_until = MessageLogLvl2(
        message=(
            "Mit diesem Account kann auf folgende Module bis zum "
            f"{until} zugegriffen werden:"
        )
    )

    access_level = MessageLogLvl2(
        message=("Mit diesem Account kann auf folgende Module zugegriffen werden:")
    )


def authentication(page: str) -> bool:
    """Check Authentication"""

    # Prüfung ob Benutzer Zugirff auf die aktuelle Seite hat
    access_pages: Any = sf.s_get("access_pages")
    if not isinstance(access_pages, list):
        logger.error("Problem with list of access pages")
        return False

    if not sf.s_get("authentication_status"):
        MessageLog.no_login.show_message()
        return False

    if page not in access_pages:
        MessageLog.no_access.show_message()
        return False

    # Prüfung ob Zugriffsrechte abgelaufen sind
    access_until: Any | None = sf.s_get("access_until")
    if (
        isinstance(access_until, dt.date)
        and access_until < dt.datetime.now(tz=dt.timezone.utc).date()
    ):
        MessageLog.too_late.show_message()
        return False

    return True
