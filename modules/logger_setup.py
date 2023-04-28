"""Setup the 'loguru' module"""


import sys
from dataclasses import dataclass

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
            ic_0: str = self.icon[0]
            ic_1: str = self.icon[1]
        else:
            ic_0: str = self.icon
            ic_1: str = ic_0
        return f"{nl_0}{time} {ic_0} {info}{{message}} {ic_1} {nl_1}"


@dataclass
class LogLevel:
    """Logger Format"""

    INFO: LevelProperties = LevelProperties("INFO", icon="💡")
    DEBUG: LevelProperties = LevelProperties("DEBUG", icon="🐞")
    ERROR: LevelProperties = LevelProperties("ERROR", icon="😱")
    SUCCESS: LevelProperties = LevelProperties("SUCCESS", icon="🥳")
    WARNING: LevelProperties = LevelProperties("WARNING", icon="⚠️")
    CRITICAL: LevelProperties = LevelProperties("CRITICAL", icon="☠️")
    START: LevelProperties = LevelProperties(
        "START",
        icon="🔥🔥🔥",
        custom=True,
        info="",
        blank_lines_before=2,
        blank_lines_after=1,
    )
    TIMER: LevelProperties = LevelProperties("TIMER", icon="⏱", custom=True, info="")
    NEW_RUN: LevelProperties = LevelProperties(
        "NEW_RUN",
        icon="✨",
        custom=True,
        info="",
        blank_lines_before=2,
    )
    FUNC_START: LevelProperties = LevelProperties(
        "FUNC_START", icon="👉👈", custom=True, info="", blank_lines_before=1
    )
    DATA_FRAME: LevelProperties = LevelProperties(
        "DATA_FRAME",
        custom=True,
        icon="",
        time="",
        info="",
        blank_lines_after=1,
    )
    ONCE_PER_RUN: LevelProperties = LevelProperties(
        "ONCE_PER_RUN", icon="👟", custom=True
    )
    ONCE_PER_SESSION: LevelProperties = LevelProperties(
        "ONCE_PER_SESSION",
        icon="🦤🦤🦤",
        custom=True,
        info="",
        blank_lines_before=1,
        blank_lines_after=1,
    )


def logger_setup() -> None:
    """Set up the loguru logging module."""

    custom_levels: list[str] = [
        lvl for lvl in LogLevel.__annotations__ if getattr(LogLevel, lvl).custom
    ]

    for lvl in custom_levels:
        try:
            logger.level(lvl)
        except ValueError:
            logger.level(lvl, no=1)

    def format_of_lvl(record: dict) -> str:
        return getattr(LogLevel, record["level"].name).get_format()

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
    logger.log(LogLevel.START.name, "Session Started. Logger Setup Complete.")
