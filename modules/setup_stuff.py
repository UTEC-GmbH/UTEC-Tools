"""general and page header setup"""

import locale
import sys
from typing import Any, Callable

import plotly.io as pio
import sentry_sdk
import streamlit as st
from dotenv import load_dotenv
from loguru import logger

from modules import constants as cont
from modules.general_functions import func_timer, get_com_date, render_svg
from modules.user_authentication import get_all_user_data


def initial_setup() -> None:
    """initial setup (only done once)
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

    sentry_sdk.init(
        dsn="https://273efaa76e074599b496947d33907e59@o4504852467810304.ingest.sentry.io/4504852472659968",
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=1.0,
    )

    if st.session_state.get("initial_setup"):
        return

    logger_setup()

    # general page config (Favicon, etc.)
    st.set_page_config(
        page_title="UTEC Online Tools",
        page_icon="logo/UTEC_logo.png",
        layout="wide",
    )

    if "dic_exe_time" not in st.session_state:
        st.session_state["dic_exe_time"] = {}

    # UTEC Logo
    st.session_state["UTEC_logo"] = render_svg()

    # language, secrets, templates, etc.
    locale.setlocale(locale.LC_ALL, "")
    load_dotenv(".streamlit/secrets.toml")
    pio.templates.default = "plotly"

    # CSS hacks for section / widget labels
    st.markdown(
        f"""
            <style>
                div.row-widget.stSelectbox > label {cont.CSS_LABEL_1}
                div.row-widget.stMultiSelect > label {cont.CSS_LABEL_1}
                [data-testid='stFileUploader'] > label {cont.CSS_LABEL_1}
                div.streamlit-expanderHeader {cont.CSS_LABEL_2}
            </style>
        """,
        unsafe_allow_html=True,
    )

    # latest changes from GitHub
    get_com_date()

    # all user data from database
    st.session_state["all_user_data"] = get_all_user_data()

    st.session_state["initial_setup"] = True
    logger.log("ONCE_per_RUN", "initial setup done")


@func_timer()
def logger_setup() -> None:
    """Setup the loguru Logging module"""
    logger_path: str = f"{cont.CWD}\\logs\\"
    logger_file: str = "log_{time:YYYY-MM-DD}.log"

    formats_levels: dict[str, str] = {
        "DEBUG": "{time:HH:mm:ss} | 🐞 | {module} -> {function} -> line: {line} | {message}  🐞  🐞|",
        "INFO": "{time:HH:mm:ss} | 👉 | {module} -> {function} -> line: {line} | {message} | 👈 |",
        "SUCCESS": "{time:HH:mm:ss} | 🥳 | {module} -> {function} -> line: {line} | {message} | 🥳 |",
        "WARNING": "{time:HH:mm:ss} | ⚠️ | {module} -> {function} -> line: {line} | {message} | ⚠️ |",
        "ERROR": "{time:HH:mm:ss} | 😱 | {module} -> {function} -> line: {line} | {message} | 😱 |",
        "CRITICAL": "{time:HH:mm:ss} | ☠️ | {module} -> {function} -> line: {line} | {message} | ☠️ |",
        "TIMER": "{time:HH:mm:ss} | ⏱  | {message} | ⏱  |",
        "ONCE_per_RUN": "{time:HH:mm:ss} | 👟 | {module} -> {function} -> line: {line} | {message} | 👟 |",
        "ONCE_per_SESSION": "\n\n{time:HH:mm:ss} | 🔥 | {module} -> {function} -> line: {line} | {message} | 🔥 |\n\n",
    }
    custom_levels: list[str] = [
        "TIMER",
        "ONCE_per_RUN",
        "ONCE_per_SESSION",
    ]
    logger.remove()

    def level_filter(level: str) -> Callable:
        def is_level(record: dict) -> Any:
            return record["level"].name == level

        return is_level

    for lvl, format_of_lvl in formats_levels.items():
        if lvl in custom_levels:
            logger.level(lvl, no=1)

        logger.add(
            sink=sys.stderr,
            level=1,
            filter=level_filter(lvl),
            format=format_of_lvl,
        )

        logger.add(
            sink=f"{logger_path}{logger_file}",
            mode="a",
            retention=3,
            catch=True,
            level=1,
            filter=level_filter(lvl),
            format=format_of_lvl,
        )

    logger.log("ONCE_per_SESSION", "🚀 Session Started, Log Initiated 🚀")


@func_timer()
def page_header_setup(page: str) -> None:
    """Seitenkopf mit Logo, Titel (je nach Seite) und letzte Änderungen"""

    st.session_state["page"] = page
    st.session_state["title_container"] = st.container()

    with st.session_state["title_container"]:
        columns: list = st.columns(2)

        # Logo
        with columns[0]:
            st.write(st.session_state["UTEC_logo"], unsafe_allow_html=True)

        # Version info (latest changes and python version)
        with columns[1]:
            st.write(
                f"""
                    <i><span style="line-height: 110%; font-size: 12px; float:right; text-align:right">
                        letzte Änderungen:<br>
                        {st.session_state["com_date"]:%d.%m.%Y}   {st.session_state["com_date"]:%H:%M}<br><br>
                        "{st.session_state["com_msg"]}"
                    </span></i>
                """,
                unsafe_allow_html=True,
            )

            access_lvl_user: str | list | None = st.session_state.get("access_lvl")
            if isinstance(access_lvl_user, str) and access_lvl_user in ("god"):
                st.write(
                    f"""
                        <i><span style="line-height: 110%; font-size: 12px; float:right; text-align:right">
                            (Python version {sys.version.split()[0]})
                        </span></i>
                    """,
                    unsafe_allow_html=True,
                )

        st.title(cont.PAGES[page]["page_tit"])
        st.markdown("---")

    logger.log("ONCE_per_RUN", f"page header for page '{page}' created")
