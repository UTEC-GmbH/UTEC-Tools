"""
General Purpose Functions
"""

import base64
import datetime as dt
import json
import time
from collections import Counter
from typing import Any, Callable

import streamlit as st
from loguru import logger

from modules import constants as cont


def func_timer(func: Callable) -> Callable:
    """Decorator for measuring the execution time of a function.

    The execution time is writen in the streamlit session state
    and printed in the logs.

    Returns:
        - Callable: Function to be measured
    """

    def wrapper(*args, **kwargs) -> Any:
        start_time: float = time.monotonic()

        if "dic_exe_time" not in st.session_state:
            st.session_state["dic_exe_time"] = {}

        result: Any = func(*args, **kwargs)

        exe_time: float = time.perf_counter() - start_time
        st.session_state["dic_exe_time"][func.__name__] = exe_time
        logger.log("TIMER", f"execution time of '{func.__name__}': {exe_time:.4f} s")

        return result

    return wrapper


def load_lottie_file(path: str) -> dict:
    """Load a Lottie-animatio by providing a json-file.

    Args:
        - path (str): path to json-file

    Returns:
        - dict: animation
    """
    with open(path) as file:
        return json.load(file)


def del_session_state_entry(key: str) -> None:
    """Eintrag in st.session_state löschen

    Args:
        - key (str): zu löschender Eintrag
    """

    if key in st.session_state:
        del st.session_state[key]

        logger.warning(f"st.session_state Eintrag {key} gelöscht")


def sort_list_by_occurance(list_of_stuff: list[Any]) -> list[Any]:
    """Given a list of stuff, which can have multiple same elements,
    this function returns a list sorted by the number of occurances
    of same elements, where same elements are combined.

    Example: list_of_stuff = ["kW", "kWh", "kWh", "°C"]
    returns: ['kWh', 'kW', '°C']

    -> 'kWh' is first, because it's in the original list twice


    Args:
        - list_of_stuff (list): List with multiple same elements

    Returns:
        - list: Set in list form, sorted by number of occurances
    """

    return sorted(Counter(list_of_stuff), key=list_of_stuff.count, reverse=True)


@func_timer
def render_svg(svg_path: str = "logo/UTEC_logo_text.svg") -> str:
    """SVG-Bild wird so codiert, dass es in Streamlit und html dargestellt werden kann.

    Args:
        - svg_path (str, optional): relativer Pfad zur svg-Datei. Defaults to "logo/UTEC_logo_text.svg".

    Returns:
        - str: Bild in string-format
    """

    logger.success(f"svg-Datei '{svg_path}' codiert")
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


def nachkomma(value: float) -> str:
    """Zahl als Text mit Nachkommastellen je nach Ziffern in Zahl.
    ...kann z.B. für Anmerkungen (Pfeile) oder Hovertexte in Plots verwendet werden.

    Der Punkt als Trennzeichen wird mit Komma ersetzt und die Zahl wird
    je nach Größe gerundet.
    Momentane Einstellung: 3 Ziffern
        → ab 100 keine Nachkommastellen
        → zw. 10 und 100: 1 Nachkommastelle
        → unter 10: 2 Nachkommastellen


    Args:
        - value (float): Zahl mit Nachkommastellen

    Returns:
        - str: Zahl als Text mit Nachkommastellen je nach Anzahl Ziffern
    """
    if abs(value) >= 1000:
        return str(f"{value:,.0f}").replace(",", ".")
    if abs(value) >= 100:
        return str(f"{value:,.0f}").replace(".", ",")
    if abs(value) >= 10:
        return str(f"{value:,.1f}").replace(".", ",")

    return str(f"{value:,.2f}").replace(".", ",")


def last_day_of_month(any_day: dt.datetime) -> dt.datetime:
    """Find the last day of the month of a given datetime
    The day 28 exists in every month. 4 days later, it's always next month.
    Subtracting the number of the current day brings us back one month.

    Args:
        - any_day (dt.datetime): datetime value in question

    Returns:
        - dt.datetime: datetime value where the day is the last day of that month
    """

    next_month: dt.datetime = any_day.replace(day=28) + dt.timedelta(days=4)

    return next_month - dt.timedelta(days=next_month.day)
