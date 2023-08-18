"""General Purpose Functions"""

import base64
import datetime as dt
import json
import locale
import time
from collections import Counter
from collections.abc import Callable
from typing import Any, Literal

import numpy as np
import streamlit as st
import streamlit_lottie as stlot
from loguru import logger

from modules import constants as cont
from modules import general_functions as gf
from modules import setup_logger as slog
from modules import streamlit_functions as sf


def log_new_run() -> None:
    """Log new run"""
    sf.s_add_once("number of runs", 0)
    run_number: int = sf.s_get("number of runs") or 0
    sf.s_set("number of runs", run_number + 1)
    logger.log(slog.LVLS.new_run.name, f"NEW RUN ( # {sf.s_get('number of runs')} )")


def lottie_spinner(func: Callable) -> Callable:
    """Decorator fancy animated spinners while a function runs.

    Returns:
        - Callable: Function to spin around
    """

    def wrapper(*args, **kwargs) -> Any:
        with stlot.st_lottie_spinner(
            gf.load_lottie_file("animations/bored.json"), height=400
        ):
            result: Any = func(*args, **kwargs)
        return result

    return wrapper


def func_timer(func: Callable) -> Callable:
    """Decorator for measuring the execution time of a function.

    The execution time is writen in the streamlit session state
    and printed in the logs.

    Returns:
        - Callable: Function to be measured
    """

    def wrapper(*args, **kwargs) -> Any:
        start_time: float = time.monotonic()
        try:
            logger.level(slog.LVLS.func_start.name)
        except ValueError:
            slog.logger_setup()

        logger.log(
            slog.LVLS.func_start.name,
            f"function '{func.__module__} -> {func.__name__}' started",
        )

        result: Any = func(*args, **kwargs)

        exe_time: float = time.monotonic() - start_time

        if "dic_exe_time" not in st.session_state:
            st.session_state["dic_exe_time"] = {}
        if "dic_exe_time" in st.session_state:
            st.session_state["dic_exe_time"][func.__name__] = exe_time

        logger.log(
            slog.LVLS.timer.name,
            f"execution time of '{func.__module__} -> {func.__name__}': "
            f"{exe_time:.4f} s",
        )

        return result

    return wrapper


def string_new_line_per_item(
    list_or_dic: list | dict,
    title: str | None = None,
    leading_empty_lines: int = 0,
) -> str:
    """Generate a string that separates each item of the given object with a new line.
    (mainly for logging)

    Args:
        - list_or_dic (list | dict): List or Dictionary to be represented as string.
        - title (str | None, optional): First line of the string. Defaults to None.
        - leading_empty_lines (int, optional): Start the string with x empty lines.
            Defaults to 0.

    Returns:
        - str: String with elements separated by "backslash n"
    """

    if isinstance(list_or_dic, list):
        return "\n" * leading_empty_lines + "\n".join(
            [f"'{title}'", *list_or_dic] if title else [*list_or_dic]
        )
    if isinstance(list_or_dic, dict):
        return "\n" * leading_empty_lines + "\n".join(
            [f"'{title}'"] + [f"{key}: '{val}'" for key, val in list_or_dic.items()]
            if title
            else [f"{key}: '{val}'" for key, val in list_or_dic.items()]
        )
    return "Error: given objekt not a list or dictionary"


def flatten_list_of_lists(list_of_lists: list[list]) -> list:
    """Flatten a list of lists"""
    return [item for sublist in list_of_lists for item in sublist]


def load_lottie_file(path: str) -> dict:
    """Load a Lottie-animation by providing a json-file.

    Args:
        - path (str): path to json-file

    Returns:
        - dict: animation
    """
    with open(path) as file:
        return json.load(file)


def show_lottie_animation(path: str, height: int, **kwargs) -> None:
    """Show a Lottie animation in a Streamlit app

    kwargs:
        speed: int = 1,
        reverse: bool = False,
        loop: bool | int = True,
        quality: Literal['low', 'medium', 'high'] = "medium",
        height: int | None = None,
        width: int | None = None,
    """

    with open(path) as file:
        js = json.load(file)

    stlot.st_lottie(
        js,
        height=height,
        speed=kwargs.get("speed") or 1,
        key=kwargs.get("key"),
        reverse=kwargs.get("reverse") or False,
        loop=kwargs.get("loop") or True,
        quality=kwargs.get("quality") or "medium",
        width=kwargs.get("width") or None,
    )


def sort_list_by_occurance(list_of_stuff: list[Any]) -> list[Any]:
    """Given a list of stuff, which can have multiple same elements,
    this function returns a list sorted by the number of occurances
    of same elements, where same elements are combined.

    Example: list_of_stuff = ["kW", "kWh", "kWh", "°C"]
    returns: ['kWh', 'kW', '°C']

    -> 'kWh' is first, because it's in the original list twice


    Args:
        - list_of_stuff (list): list with multiple same elements

    Returns:
        - list: Set in list form, sorted by number of occurances
    """

    return [elem for elem, count in Counter(list_of_stuff).most_common()]


def render_svg(svg_path: str = "logo/UTEC_logo_text.svg") -> str:
    """SVG-Bild wird so codiert, dass es in Streamlit und html dargestellt werden kann.

    Args:
        - svg_path (str, optional): relativer Pfad zur svg-Datei.
            Defaults to "logo/UTEC_logo_text.svg".

    Returns:
        - str: Bild in string-format
    """

    with open(svg_path) as lines:
        svg: str = "".join(lines.readlines())
        b64: str = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    return f'<img src="data:image/svg+xml;base64,{b64}"/>'


def text_with_hover(text: str, hovtxt: str) -> str:
    """CSS-Hack für Überschrift mit mouse-over-tooltip.

    use like this: st.markdown(text_with_hover, unsafe_allow_html=True)


    Args:
        - text (str): Der Text, der Überschrift.
        - hovtxt (str): Der Text, der bei mouse-over angezeigt werden soll.

    Returns:
        - str: Text und Hovertext in html-Format
    """

    return f"""
        <html>
            <body>
                <span style="{cont.CSS_LABEL_1[1:-1]}; float:left; text-align:left;">
                    <div title="{hovtxt}">
                        {text}
                    </div>
            </body>
        </html>
        """


def number_as_string(value: float) -> str:
    """Zahl als Text mit Nachkommastellen je nach Ziffern in Zahl.
    ...kann z.B. für Anmerkungen (Pfeile) oder Hovertexte in Plots verwendet werden.

    Die Zahl wird je nach Größe gerundet.
    Momentane Einstellung: 3 Ziffern
        → ab 100 keine Nachkommastellen
        → zw. 10 und 100: 1 Nachkommastelle
        → unter 10: 2 Nachkommastellen


    Args:
        - value (float): Zahl mit Nachkommastellen

    Returns:
        - str: Zahl als Text mit Nachkommastellen je nach Anzahl Ziffern
    """
    locale.setlocale(locale.LC_ALL, "")
    four_digits = 1000
    three_digits = 100
    if abs(value) >= four_digits:
        return locale.format_string("%.0f", value, grouping=True)
    if abs(value) >= three_digits:
        return locale.format_string("%.0f", value, grouping=True)
    two_digits = 10

    return (
        locale.format_string("%.1f", value, grouping=True)
        if abs(value) >= two_digits
        else locale.format_string("%.2f", value, grouping=True)
    )


def start_of_month(dt_obj: dt.datetime | np.datetime64) -> dt.datetime:
    """Replace the day of a datetime with '1' to get the start of the month"""

    if isinstance(dt_obj, np.datetime64):
        dt_object: dt.datetime = dt_obj.astype("M8[M]").astype(dt.datetime)
    else:
        dt_object = dt_obj
    return dt_object.replace(day=1)


def end_of_month(dt_obj: dt.datetime | np.datetime64) -> dt.datetime:
    """Find the last day of the month of a given datetime
    The day 28 exists in every month. 4 days later, it's always next month.
    Subtracting the number of the current day brings us back one month.

    Args:
        - any_day (dt.datetime): datetime value in question

    Returns:
        - dt.datetime: datetime value where the day is the last day of that month
    """

    if isinstance(dt_obj, np.datetime64):
        dt_object: dt.datetime = dt_obj.astype("M8[M]").astype(dt.datetime)
    else:
        dt_object = dt_obj
    next_month: dt.datetime = dt_object.replace(day=28) + dt.timedelta(
        days=4
    )  # Jump to next month
    return next_month - dt.timedelta(days=next_month.day)


def check_if_not_exclude(
    line: str, exclude: Literal["base", "index", "suff_arbeit"] = "index"
) -> bool:
    """Check if a line is in the exclude list.

    Args:
        - line (str): line to check
        - exclude (Literal["base", "index", "suff_arbeit"]):
            exclude list to check (from cont.EXCLUDE)
            - base: "hline", smooth (suffix), original index
            - index: base + Excel index marker
            - suff_arbeit: index + arbeit (suffix)

    Returns:
        - bool: True if line is not in exclude list
    """
    return all(excl not in line for excl in getattr(cont.EXCLUDE, exclude))
