"""general and page header setup"""

import datetime as dt
import locale
import os
import sys
from pathlib import Path
from typing import Any

import dotenv
import github as gh
import pandas.io.formats.excel
import plotly.io as pio
import pytz
import sentry_sdk
import streamlit as st
from loguru import logger

from modules import classes_data as cld
from modules import classes_errors as cle
from modules import constants as cont
from modules import general_functions as gf
from modules import setup_logger as slog
from modules import streamlit_functions as sf
from modules import user_authentication as uauth


@gf.func_timer
def get_commit_message_date() -> None:
    """Write git commit from GitHub to the session_state (for the header).

    To create a new personal access token in GitHub:
    on github.com click on the profile and go into
    settings -> developer settings -> personal access tokens
    """

    logger.info("Loading Git commit...")

    utc: pytz.BaseTzInfo = pytz.timezone("UTC")
    eur: pytz.BaseTzInfo = pytz.timezone("Europe/Berlin")
    date_now: dt.datetime = dt.datetime.now()
    tz_diff: float = (
        utc.localize(date_now) - eur.localize(date_now).astimezone(utc)
    ).seconds / 3600

    personal_access_token: str | None = os.environ.get("GITHUB_PAT")
    if not personal_access_token:
        logger.error("Invalid GITHUB_PAT!")
        return

    gith: gh.Github = gh.Github(personal_access_token)

    repo = gith.get_user().get_repo(cont.REPO_NAME)
    if not repo:
        logger.error("Repository could not be found.")
        return

    branch = repo.get_branch("main")
    if not branch:
        logger.error("Failed to get 'main' branch for repository.")
        return

    latest_commit = repo.get_commit(branch.commit.sha).commit
    com_date = latest_commit.author.date + dt.timedelta(hours=tz_diff)
    major: str = ""  # commit message
    minor: str = ""  # comment of merge
    commit_page = repo.get_commits(branch.commit.sha).get_page(0)
    for commit in commit_page:
        message = commit.commit.message.split("\n\n")
        minor = message[0]
        if len(message) > 1:
            major = message[1]
            break

    cld.GitCommit(com_date, major, minor).write_all_to_session_state()


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
    pandas.io.formats.excel.ExcelFormatter.header_style = None  # type: ignore
    sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), traces_sample_rate=0.1)

    sf.s_add_once("UTEC_logo", gf.render_svg())

    st.markdown(cont.CSS_LABELS, unsafe_allow_html=True)

    get_commit_message_date()

    sf.s_add_once("all_user_data", uauth.get_all_user_data())

    exp_dir: Path = Path(f"{Path.cwd()}/export")
    if Path.exists(exp_dir):
        logger.info(f"Pfad '{exp_dir}' für die Ausgabe bereits vorhanden")
    else:
        Path.mkdir(exp_dir)
        logger.info(f"Pfad '{exp_dir}' für die Ausgabe erstellt")

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

        # Version info (latest changes and python version)
        with columns[1]:
            # f'{sf.s_get("GitCommit_major")}<br>'
            # f'({sf.s_get("GitCommit_minor")})'
            st.write(
                '<span style="line-height: 110%; font-size: 12px; '
                'float:right; text-align:right"><i>'
                "letzte Änderungen: "
                f'{sf.s_get("GitCommit_date"):%d.%m.%Y %H:%M}<br><br>'
                "</span></i>",
                unsafe_allow_html=True,
            )

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
