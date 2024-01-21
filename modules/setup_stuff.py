"""general and page header setup"""

import locale
import os
import sys
from typing import Any

import dotenv
import plotly.io as pio
import sentry_sdk
import streamlit as st
from loguru import logger

from modules import classes_errors as cle
from modules import constants as cont
from modules import general_functions as gf
from modules import setup_logger as slog
from modules import streamlit_functions as sf
from modules import user_authentication as uauth


@gf.func_timer
def general_setup() -> None:
    """Setup general things (only done once)
    - streamlit page config
    - UTEC logo
    - logger setup (loguru)
    - language (locale)
    - secrets
    - plotly template (because streamlit overwrites it)
    - CSS hacks for section / widget labels
    - latest changes from GitHub
    - get user data from database
    """

    locale.setlocale(locale.LC_ALL, "")
    dotenv.load_dotenv(".streamlit/secrets.toml")
    pio.templates.default = "plotly"
    sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), traces_sample_rate=0.1)

    sf.s_add_once("UTEC_logo", gf.render_svg())

    st.markdown(cont.CSS_LABELS, unsafe_allow_html=True)

    sf.s_add_once("all_user_data", uauth.get_all_user_data())

    st.session_state["initial_setup"] = True
    logger.log(slog.LVLS.once_per_session.name, "Initial Setup Complete")


def page_header_setup(page: str) -> None:
    """Seitenkopf mit Logo, Titel (je nach Seite) und letzten Änderungen"""

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
            access_lvl_user: str | list | None = (
                None if sf.s_not_in("access_lvl") else sf.s_get("access_lvl")
            )
            if isinstance(access_lvl_user, str) and access_lvl_user in ("god"):
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
