"""Setup the 'loguru' module"""


import sys
from dataclasses import dataclass

import polars as pl
import streamlit as st
from loguru import logger

from modules import constants as cont


@dataclass(frozen=True)
class LevelProperties:
    """Logger Levels"""

    name: str
    custom: bool = False
    icon: str = "👉👈"
    time: str = "{time:HH:mm:ss}"
    info: str = "{module} -> {function} -> line: {line} | "
    blank_lines_before: int = 0
    blank_lines_after: int = 0

    def get_format(self) -> str:
        """Logger message Format erzeugen"""
        double_icon: int = 2
        nl_0: str = "\n" * self.blank_lines_before
        nl_1: str = "\n" * (self.blank_lines_after + 1)
        info: str = self.info
        time: str = self.time
        if len(self.icon) == double_icon:
            icon_0: str = self.icon[0]
            icon_1: str = self.icon[1]
        else:
            icon_0: str = self.icon
            icon_1: str = icon_0
        return f"{nl_0}{time} {icon_0} {info}{{message}} {icon_1} {nl_1}"


@dataclass
class LogLevels:
    """Logger Format"""

    info: LevelProperties
    debug: LevelProperties
    error: LevelProperties
    success: LevelProperties
    warning: LevelProperties
    critical: LevelProperties
    start: LevelProperties
    timer: LevelProperties
    new_run: LevelProperties
    func_start: LevelProperties
    data_frame: LevelProperties
    once_per_run: LevelProperties
    once_per_session: LevelProperties


LVLS = LogLevels(
    info=LevelProperties("info", icon="💡"),
    debug=LevelProperties("debug", icon="🐞"),
    error=LevelProperties("error", icon="😱"),
    success=LevelProperties("success", icon="🥳"),
    warning=LevelProperties("warning", icon="⚠️"),
    critical=LevelProperties("critical", icon="☠️"),
    start=LevelProperties(
        "start",
        icon="🔥🔥🔥",
        custom=True,
        info="",
        blank_lines_before=2,
        blank_lines_after=1,
    ),
    timer=LevelProperties("timer", icon="⏱", custom=True, info=""),
    new_run=LevelProperties(
        "new_run",
        icon="✨",
        custom=True,
        info="",
        blank_lines_before=2,
    ),
    func_start=LevelProperties(
        "func_start", icon="👉👈", custom=True, info="", blank_lines_before=1
    ),
    data_frame=LevelProperties(
        "data_frame",
        custom=True,
        icon="",
        time="",
        info="",
        blank_lines_after=1,
    ),
    once_per_run=LevelProperties("once_per_run", icon="👟", custom=True),
    once_per_session=LevelProperties(
        "once_per_session",
        icon="🦤🦤🦤",
        custom=True,
        info="",
        blank_lines_before=1,
        blank_lines_after=1,
    ),
)


def log_df(df: pl.DataFrame) -> None:
    """Put the head of the DataFrame in the log"""
    logger.log(
        LVLS.data_frame.name,
        f"DataFrame head: \n{df.head()} \n\nDataFrame properties: \n{df.describe()}",
    )


def logger_setup() -> None:
    """Set up the loguru logging module."""

    custom_levels: list[str] = [
        lvl for lvl in LVLS.__annotations__ if getattr(LVLS, lvl).custom
    ]

    for lvl in custom_levels:
        try:
            logger.level(lvl)
        except ValueError:
            logger.level(lvl, no=1)

    def format_of_lvl(record: dict) -> str:
        return getattr(LVLS, record["level"].name.lower()).get_format()

    logger.remove()

    logger.add(
        sink=sys.stderr,  # type: ignore
        level=1,
        format=format_of_lvl,  # type: ignore
    )

    file_sink: str = f"{cont.CWD}\\logs\\{{time:YYYY-MM-DD_HH-mm}}.log"
    handler_id: int = logger.add(file_sink, retention=2, delay=True)
    logger.remove(handler_id)  # Trigger retention policy

    logger.add(
        sink=file_sink,
        retention=2,
        level=1,
        format=format_of_lvl,  # type: ignore
    )

    st.session_state["logger_setup"] = True
    logger.log(LVLS.start.name, "Session Started. Logger Setup Complete.")
