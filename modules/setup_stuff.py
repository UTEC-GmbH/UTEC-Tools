"""general and page header setup"""

import datetime as dt
import locale
import os
import sys
from typing import Any, Dict, List

import plotly.io as pio

# import plotly.io as pio
import sentry_sdk
import streamlit as st
from dotenv import load_dotenv
from github import Github
from loguru import logger
from pytz import BaseTzInfo, timezone

from modules import constants as cont
from modules.classes import LogLevel
from modules.general_functions import func_timer, render_svg, st_add
from modules.user_authentication import get_all_user_data


@func_timer
@st.cache_data
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

    utc: BaseTzInfo = timezone("UTC")
    eur: BaseTzInfo = timezone("Europe/Berlin")
    date_now: dt.datetime = dt.datetime.now()
    tz_diff: float = (
        utc.localize(date_now) - eur.localize(date_now).astimezone(utc)
    ).seconds / 3600

    personal_access_token: str | None = os.environ.get("GITHUB_PAT")
    if not personal_access_token:
        err_msg: str = "GITHUB_PAT environment variable not set."
        logger.error(err_msg)
        return {"com_date": "ERROR", "com_msg": err_msg}

    gith: Github = Github(personal_access_token)

    repo: Any = gith.get_user().get_repo(cont.REPO_NAME)
    if not repo:
        err_msg = "Failed to get repository."
        logger.error(err_msg)
        return {"com_date": "ERROR", "com_msg": err_msg}

    branch: Any = repo.get_branch("main")

    if not branch:
        err_msg = "Failed to get 'main' branch for repository."
        logger.error(err_msg)
        return {"com_date": "ERROR", "com_msg": err_msg}

    commit: Any = repo.get_commit(branch.commit.sha).commit

    return {
        "com_date": commit.author.date + dt.timedelta(hours=tz_diff),
        "com_msg": commit.message.split("\n")[-1],
    }


@func_timer
def general_setup() -> None:
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

    locale.setlocale(locale.LC_ALL, "")
    load_dotenv(".streamlit/secrets.toml")
    pio.templates.default = "plotly"
    sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), traces_sample_rate=0.1)

    st_add("UTEC_logo", render_svg())
    # if not st.session_state.get("UTEC_logo"):
    #     st.session_state["UTEC_logo"] = render_svg()

    st.markdown(
        cont.CSS_LABELS,
        unsafe_allow_html=True,
    )

    # if any(entry not in st.session_state for entry in ["com_date", "com_msg"]):
    #     commit: Dict[str, dt.datetime | str] = get_commit_message_date()
    #     st.session_state["com_date"] = commit["com_date"]
    #     st.session_state["com_msg"] = commit["com_msg"]

    st_add("all_user_data", get_all_user_data())
    # if "all_user_data" not in st.session_state:
    #     st.session_state["all_user_data"] = get_all_user_data()

    st.session_state["initial_setup"] = True
    logger.log(LogLevel.ONCE_PER_SESSION.name, "Initial Setup Complete")


def logger_setup() -> None:
    """Setup the loguru Logging module"""

    custom_levels: List[str] = [
        lvl for lvl in LogLevel.__annotations__ if getattr(LogLevel, lvl).custom
    ]

    for lvl in custom_levels:
        try:
            logger.level(lvl)
        except ValueError:
            logger.level(lvl, no=1)

    def format_of_lvl(record: Dict) -> str:
        return getattr(LogLevel, record["level"].name).get_format()

    logger.remove()

    logger.add(
        sink=sys.stderr,  # type: ignore
        level=1,
        format=format_of_lvl,  # type: ignore
    )

    logger.add(
        sink=f"{cont.CWD}\\logs\\{{time:YYYY-MM-DD_HH-mm}}.log",
        # rotation="1 second",
        retention=2,
        level=1,
        format=format_of_lvl,  # type: ignore
    )

    st.session_state["logger_setup"] = True
    logger.log(LogLevel.START.name, "Session Started. Logger Setup Complete.")


@func_timer
def page_header_setup(page: str) -> None:
    """Seitenkopf mit Logo, Titel (je nach Seite) und letzten Änderungen"""

    st.session_state["page"] = page
    st.session_state["title_container"] = st.container()

    with st.session_state["title_container"]:
        columns: List = st.columns(2)

        # Logo
        # if "UTEC_logo" not in st.session_state:
        #     st.session_state["UTEC_logo"] = render_svg()
        st_add("UTEC_logo", render_svg())
        with columns[0]:
            st.write(st.session_state["UTEC_logo"], unsafe_allow_html=True)

        # Version info (latest changes and python version)
        if any(entry not in st.session_state for entry in ["com_date", "com_msg"]):
            st.session_state["com_date"] = get_commit_message_date()["com_date"]
            st.session_state["com_msg"] = get_commit_message_date()["com_msg"]
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

    logger.log(LogLevel.ONCE_PER_RUN.name, f"page header for page '{page}' created")
