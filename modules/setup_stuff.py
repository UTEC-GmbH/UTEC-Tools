"""general and page header setup"""

import locale
import sys
from typing import Any

import dotenv
import plotly.io as pio
import streamlit as st
import streamlit_authenticator as stauth
from loguru import logger

from modules import classes_errors as cle
from modules import constants as cont
from modules import general_functions as gf
from modules import setup_logger as slog
from modules import streamlit_functions as sf


@gf.func_timer
def general_setup() -> None:
    """Set up general things (only done once)
    - language (locale)
    - secrets
    - plotly template (because streamlit overwrites it)
    - UTEC logo
    - CSS hacks for section / widget labels
    - get user data from database
    """

    logger.log(slog.LVLS.once_per_session.name, "Initial Setup Started")

    locale.setlocale(locale.LC_ALL, "")
    dotenv.load_dotenv(".streamlit/secrets.toml")
    pio.templates.default = "plotly"
    sf.s_add_once("UTEC_logo", gf.render_svg())
    st.markdown(cont.CSS_LABELS, unsafe_allow_html=True)
    sf.s_add_once("all_user_data", cont.USERS)

    st.session_state["initial_setup"] = True
    logger.log(slog.LVLS.once_per_session.name, "Initial Setup Complete")


def page_header_setup(page: str) -> None:
    """Seitenkopf mit Logo, Titel (je nach Seite) und letzten Änderungen"""

    if page != cont.ST_PAGES.login.short:
        authenticator: Any = sf.s_get("authenticator")
        if not isinstance(authenticator, stauth.Authenticate):
            logger.critical("authenticator not initiated correctly")
            raise ValueError
        authenticator.login(location="unrendered")
        logger.debug("unrendered authenticator.login created")

    sf.s_set("page", page)
    sf.s_set("title_container", st.container())
    tit_cont: Any | None = sf.s_get("title_container")
    if not tit_cont:
        raise cle.NotFoundError(entry="title_container", where="Session State")

    with tit_cont:
        columns: list = st.columns(2)

        with columns[0]:
            st.write(sf.s_get("UTEC_logo"), unsafe_allow_html=True)

        # Version info (Python version)
        with columns[1]:
            if sf.s_get("access_lvl") == ["god"]:
                st.write(
                    (
                        '<span style="line-height: 110%; font-size: 12px; '
                        'float:right; text-align:right"><i>'
                        f"<br><br>(Python version {sys.version.split()[0]})"
                        "</span></i>"
                    ),
                    unsafe_allow_html=True,
                )

        st.title(cont.ST_PAGES.get_title(page))
        st.markdown("---")

    logger.log(slog.LVLS.once_per_run.name, f"page header for page '{page}' created")
