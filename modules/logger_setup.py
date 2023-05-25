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
        nl_0: str = "\n" * self.blank_lines_before
        nl_1: str = "\n" * (self.blank_lines_after + 1)
        info: str = self.info
        time: str = self.time
        if len(self.icon) == 2:
            icon_0: str = self.icon[0]
            icon_1: str = self.icon[1]
        else:
            icon_0: str = self.icon
            icon_1: str = icon_0
        return f"{nl_0}{time} {icon_0} {info}{{message}} {icon_1} {nl_1}"


@dataclass
class LogLevels:
    """Logger Format"""

    INFO: LevelProperties
    DEBUG: LevelProperties
    ERROR: LevelProperties
    SUCCESS: LevelProperties
    WARNING: LevelProperties
    CRITICAL: LevelProperties
    START: LevelProperties
    TIMER: LevelProperties
    NEW_RUN: LevelProperties
    FUNC_START: LevelProperties
    DATA_FRAME: LevelProperties
    ONCE_PER_RUN: LevelProperties
    ONCE_PER_SESSION: LevelProperties


def all_log_levels() -> LogLevels:
    """All Log Levels"""
    return LogLevels(
        INFO=LevelProperties("INFO", icon="💡"),
        DEBUG=LevelProperties("DEBUG", icon="🐞"),
        ERROR=LevelProperties("ERROR", icon="😱"),
        SUCCESS=LevelProperties("SUCCESS", icon="🥳"),
        WARNING=LevelProperties("WARNING", icon="⚠️"),
        CRITICAL=LevelProperties("CRITICAL", icon="☠️"),
        START=LevelProperties(
            "START",
            icon="🔥🔥🔥",
            custom=True,
            info="",
            blank_lines_before=2,
            blank_lines_after=1,
        ),
        TIMER=LevelProperties("TIMER", icon="⏱", custom=True, info=""),
        NEW_RUN=LevelProperties(
            "NEW_RUN",
            icon="✨",
            custom=True,
            info="",
            blank_lines_before=2,
        ),
        FUNC_START=LevelProperties(
            "FUNC_START", icon="👉👈", custom=True, info="", blank_lines_before=1
        ),
        DATA_FRAME=LevelProperties(
            "DATA_FRAME",
            custom=True,
            icon="",
            time="",
            info="",
            blank_lines_after=1,
        ),
        ONCE_PER_RUN=LevelProperties("ONCE_PER_RUN", icon="👟", custom=True),
        ONCE_PER_SESSION=LevelProperties(
            "ONCE_PER_SESSION",
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
        all_log_levels().DATA_FRAME.name,
        f"DataFrame head: \n{df.head()} \n\nDataFrame properties: \n{df.describe()}",
    )


def logger_setup() -> None:
    """Set up the loguru logging module."""
    log_levels: LogLevels = all_log_levels()
    custom_levels: list[str] = [
        lvl for lvl in log_levels.__annotations__ if getattr(log_levels, lvl).custom
    ]

    for lvl in custom_levels:
        try:
            logger.level(lvl)
        except ValueError:
            logger.level(lvl, no=1)

    def format_of_lvl(record: dict) -> str:
        return getattr(log_levels, record["level"].name).get_format()

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
    logger.log(log_levels.START.name, "Session Started. Logger Setup Complete.")
