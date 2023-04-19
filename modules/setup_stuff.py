"""general and page header setup"""

import datetime as dt
import locale
import os
import sys
from typing import Any, Dict, List

import plotly.io as pio
import sentry_sdk
import streamlit as st
from dotenv import load_dotenv
from github import Github
from loguru import logger
from pytz import BaseTzInfo, timezone

from modules import constants as cont
from modules.general_functions import func_timer, render_svg
from modules.user_authentication import get_all_user_data


# @func_timer
def get_commit_message_date() -> Dict[str, dt.datetime | str]:
    """Commit message and date from GitHub to show in the header.


    To create a new personal access token in GitHub:
    on github.com click on the profile and go into
    settings -> developer settings -> personal access tokens

    Returns:
        - Dict[str, dt.datetime | str]:
            - "com_date" (dt.datetime): date of commit
            - "com_mst" (str): commit message
    """

    personal_access_token: str | None = os.environ.get("GITHUB_PAT")
    if personal_access_token is None:
        logger.error("GITHUB_PAT environment variable not set.")
        return {
            "com_date": "ERROR",
            "com_msg": "GITHUB_PAT environment variable not set.",
        }

    utc: BaseTzInfo = timezone("UTC")
    eur: BaseTzInfo = timezone("Europe/Berlin")
    date_now: dt.datetime = dt.datetime.now()
    tz_diff: float = (
        utc.localize(date_now) - eur.localize(date_now).astimezone(utc)
    ).seconds / 3600

    gith: Github = Github(personal_access_token)
    repo: Any = gith.get_user().get_repo(cont.REPO_NAME)
    branch: Any = repo.get_branch("main")
    sha: Any = branch.commit.sha
    commit: Any = repo.get_commit(sha).commit

    return {
        "com_date": commit.author.date + dt.timedelta(hours=tz_diff),
        "com_msg": commit.message.split("\n")[-1],
    }


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

    if st.session_state.get("initial_setup"):
        return

    # language, secrets, templates, etc.
    locale.setlocale(locale.LC_ALL, "")
    load_dotenv(".streamlit/secrets.toml")
    pio.templates.default = "plotly"
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        traces_sample_rate=0.1,
    )

    logger_setup()

    # general page config (Favicon, etc.)
    st.set_page_config(
        page_title="UTEC Online Tools",
        page_icon="logo/UTEC_logo.png",
        layout="wide",
    )

    # UTEC Logo
    if "UTEC_logo" not in st.session_state:
        st.session_state["UTEC_logo"] = render_svg()

    # CSS hacks for section / widget labels
    st.markdown(
        cont.CSS_LABELS,
        unsafe_allow_html=True,
    )

    # latest changes from GitHub
    if any(entry not in st.session_state for entry in ["com_date", "com_msg"]):
        st.session_state["com_date"] = get_commit_message_date()["com_date"]
        st.session_state["com_msg"] = get_commit_message_date()["com_msg"]

    # all user data from database
    if "all_user_data" not in st.session_state:
        st.session_state["all_user_data"] = get_all_user_data()

    st.session_state["initial_setup"] = True
    logger.log("ONCE_per_RUN", "initial setup done")


# @func_timer
def logger_setup() -> None:
    """Setup the loguru Logging module"""

    format_time: str = "\n{time:HH:mm:ss}"
    format_mesg: str = "{module} -> {function} -> line: {line} | {message}"

    standard_levels = {
        level: f"{format_time} | {icon} | {format_mesg} | {icon} |"
        for level, icon in {
            "DEBUG": "🐞",
            "INFO": "👉",
            "SUCCESS": "🥳",
            "WARNING": "⚠️",
            "ERROR": "😱",
            "CRITICAL": "☠️",
        }.items()
    }
    custom_levels: Dict[str, str] = {
        "TIMER": f"{format_time} | ⏱  | {{message}} | ⏱  |",
        "ONCE_per_RUN": f"{format_time} | 👟 | {format_mesg} | 👟 |",
        "ONCE_per_SESSION": f"\n\n{format_time} 🔥🔥🔥 {{message}}\n\n",
    }
    all_levels: Dict[str, str] = standard_levels | custom_levels

    for lvl in custom_levels:
        try:
            logger.level(lvl)
        except ValueError:
            logger.level(lvl, no=1)

    def format_of_lvl(record: Dict) -> str:
        return all_levels[record["level"].name]

    logger.remove()

    logger.add(
        sink=sys.stderr,  # type: ignore
        level=1,
        format=format_of_lvl,  # type: ignore
        colorize=True,
    )

    file_sink: str = f"{cont.CWD}/logs/log_{{time:YYYY-MM-DD}}.log"
    logger.add(
        sink=file_sink,
        rotation="1 day",
        retention=3,
        mode="a",
        catch=True,
        level=1,
        format=format_of_lvl,  # type: ignore
        colorize=True,
    )

    logger.log("ONCE_per_SESSION", "🚀 Session Started, Log Initiated 🚀")


@func_timer
def page_header_setup(page: str) -> None:
    """Seitenkopf mit Logo, Titel (je nach Seite) und letzten Änderungen"""

    st.session_state["page"] = page
    st.session_state["title_container"] = st.container()

    with st.session_state["title_container"]:
        columns: List = st.columns(2)

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

            access_lvl_user: str | List | None = st.session_state.get("access_lvl")
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
