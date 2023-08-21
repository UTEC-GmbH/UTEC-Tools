"""Konstanten"""

from pathlib import Path
from typing import Literal

from modules import classes_constants as clc

REPO_NAME: str = "UTEC-Tools"

# Current Working Directory
CWD: str = str(Path.cwd())


# Aussehen der labels (Überschriften)
CSS_LABEL_1: str = "{font-size:1rem; font-weight:600;}"
CSS_LABEL_2: str = "{font-size:0.95rem; font-weight:600;}"

# CSS hacks for section / widget labels
CSS_LABELS: str = f"""
    <style>
        div.row-widget.stSelectbox > label {CSS_LABEL_1}
        div.row-widget.stMultiSelect > label {CSS_LABEL_1}
        [data-testid='stFileUploader'] > label {CSS_LABEL_1}
        div.streamlit-expanderHeader {CSS_LABEL_2}
    </style>
"""


# Menu für Ausfüllen von Linien
TRANSPARENCY_OPTIONS_SUFFIX: str = "% Transparenz"
TRANSPARENCY_OPTIONS: list[str] = ["keine Füllung"] + [
    f"{integer}{TRANSPARENCY_OPTIONS_SUFFIX}" for integer in range(0, 100, 20)
]

# Menu für Linientypen
LINE_TYPES: dict[str, str] = {
    "durchgezogen": "solid",
    "gepunktet": "dot",
    "gestrichelt": "dash",
    "gestrichelt lang": "longdash",
    "Strich-Punkt": "dashdot",
    "Strich-Punkt lang": "longdashdot",
    "gestrichelt 0,5%": "0.5%",
    "gestrichelt 0,75%": "0.75%",
    "gestrichelt 1,0%": "1.0%",
    "gestrichelt 1,75%": "1.25%",
    "keine": "solid",
}

FARBEN: dict[str, str] = {
    "weiß": "255, 255, 255",
    "schwarz": "0, 0, 0",
    "hellgrau": "200, 200, 200",
    "blau": "99, 110, 250",
    "rot": "239, 85, 59",
    "grün-blau": "0, 204, 150",
    "lila": "171, 99, 250",
    "orange": "255, 161, 90",
    "hellblau": "25, 211, 243",
    "rosa": "255, 102, 146",
    "hellgrün": "182, 232, 128",
    "pink": "255, 151, 255",
    "gelb": "254, 203, 82",
}

# negative Werte für Lieferung ins Netz etc.
NEGATIVE_VALUES: list[str] = [
    "Batteriebeladung",
    "Einsp",
    "Netzeinsp",
    "Stromeinsp",
    "Lieferung",
    "Stromlieferung",
]


# Theme for plots in streamlit app -> theme="streamlit" or theme=None
ST_PLOTLY_THEME: Literal["streamlit"] | None = None


# allgemeine liste von Einheiten
UNITS_GENERAL: list[str] = [
    "W",
    "kW",
    "MW",
    "Wh",
    "kWh",
    "MWh",
    "Wh/a",
    "kWh/a",
    "MWh/a",
    "g",
    "kg",
    "Mg",
    "t",
]


# Einheiten, bei denen der Mittelwert gebildet werden muss (statt Summe)
GRP_MEAN: list[str] = [
    " °c",
    " °C",
    " w",
    " W",
    " kw",
    " kW",
    " KW",
    " mw",
    " mW",
    " MW",
    " m³",
    " m³/h",
    " pa/m",
    " Pa/m",
    " m/s",
    " %",
]


# Transparenz (Deckungsgrad) 0= durchsichtig, 1= undurchsichtig
ALPHA: dict[str, str] = {
    "bg": ", 0.5)",  # Hintergrund Beschriftungen
    "fill": ", 0.2)",  # fill von Linien etc.
}

SUFFIXES: clc.Suffixes = clc.Suffixes(
    col_smooth=" geglättet",
    col_arbeit=" → Arbeit",
    col_leistung=" → Leistung",
    col_original_index=" - orgidx",
    fig_tit_h='<i><span style="font-size: 12px;"> (Stundenwerte)</span></i>',
    fig_tit_15='<i><span style="font-size: 12px;"> (15-Minuten-Werte)</span></i>',
    h_line="hline",
)

EXCEL_MARKERS: clc.ExcelMarkers = clc.ExcelMarkers(
    index="↓ Index ↓",
    units="→ Einheit →",
)

SPECIAL_COLS: clc.SpecialCols = clc.SpecialCols(
    index=EXCEL_MARKERS.index,
    original_index=SUFFIXES.col_original_index.replace(" - ", ""),
    smooth=SUFFIXES.col_smooth,
    temp="Außentemperatur",
)

TIME_MS: clc.TimeMSec = clc.TimeMSec(
    half_day=12 * 60 * 60 * 1000,  # 43.200.000
    week=7 * 24 * 60 * 60 * 1000,  # 604.800.000
    month=30 * 24 * 60 * 60 * 1000,  # 2.592.000.000
)

TIME_MIN: clc.TimeMin = clc.TimeMin(
    hour=60,
    half_hour=30,
    quarter_hour=15,
)

DWD_RESOLUTION_OPTIONS: dict[str, str] = {
    "1 Minute": "minute_1",
    "5 Minuten": "minute_5",
    "10 Minuten": "minute_10",
    "Stunden": "hourly",
    "Tage": "daily",
    "Monate": "monthly",
}

DWD_TRANSLATION: dict[str, str] = {"temperature_air_mean_200": "Außentemperatur"}

FIG_TITLES: clc.FigIDs = clc.FigIDs(
    lastgang="Lastgang",
    jdl="Geordnete Jahresdauerlinie",
    mon="Monatswerte",
    days="Vergleich ausgewählter Tage",
)

FIG_KEYS: clc.FigIDs = clc.FigIDs(
    lastgang="fig_base",
    jdl="fig_jdl",
    mon="fig_mon",
    days="fig_days",
)

ARBEIT_LEISTUNG: clc.ArbeitLeistung = clc.ArbeitLeistung(
    arbeit=clc.SuffixUnit(SUFFIXES.col_arbeit, ["GWh", "MWh", "kWh", "Wh"]),
    leistung=clc.SuffixUnit(SUFFIXES.col_leistung, ["GW", "MW", "kW", "W"]),
    all_suffixes=[SUFFIXES.col_arbeit, SUFFIXES.col_leistung],
)

# Linien, die bei gewissen Operationen übersprungen werden
EXCLUDE: clc.Exclude = clc.Exclude(
    base=[
        SUFFIXES.h_line,
        SUFFIXES.col_smooth,
        SPECIAL_COLS.original_index,
    ],
    index=[
        SUFFIXES.h_line,
        SUFFIXES.col_smooth,
        SPECIAL_COLS.original_index,
        EXCEL_MARKERS.index,
    ],
    suff_arbeit=[
        SUFFIXES.h_line,
        SUFFIXES.col_smooth,
        SPECIAL_COLS.original_index,
        ARBEIT_LEISTUNG.arbeit.suffix,
    ],
)

ST_PAGES: clc.StPages = clc.StPages(
    login=clc.StPageProps("login", "UTEC Online Tools"),
    graph=clc.StPageProps("graph", "Grafische Datenauswertung", "Daten"),
    meteo=clc.StPageProps("meteo", "Meteorologische Daten", "Wetterdaten"),
    maps=clc.StPageProps("maps", "Kartografische Datenauswertung"),
)

# Umkreis für Meteostat-Stationen in Kilometern
WEATHERSTATIONS_MAX_DISTANCE = 700


# Parameter, die standardmäßig für den Download ausgewählt sind
METEO_DEFAULT_PARAMETER: list = [
    "Lufttemperatur in 2 m Höhe",
    "Globalstrahlung",
    "Windgeschwindigkeit",
    "Windrichtung",
]

METEO_CODES: clc.MeteoCodes = clc.MeteoCodes(
    temp=clc.MeteoParameter(
        original_name="Air Temperature",
        title="Lufttemperatur in 2 m Höhe",
        unit="°C",
        category_utec="Temperaturen",
        default_parameter=True,
    ),
    dwpt=clc.MeteoParameter(
        original_name="Dew Point",
        title="Taupunkt",
        unit="°C",
        category_utec="Temperaturen",
        default_parameter=False,
    ),
    prcp=clc.MeteoParameter(
        original_name="Total Precipitation",
        title="Niederschlag",
        unit="mm",
        category_utec="Feuchte, Luftdruck, Niederschlag",
        default_parameter=False,
    ),
    wdir=clc.MeteoParameter(
        original_name="Wind (From) Direction",
        title="Windrichtung",
        unit="°",
        category_utec="Sonne und Wind",
        default_parameter=True,
    ),
    wspd=clc.MeteoParameter(
        original_name="Average Wind Speed",
        title="Windgeschwindigkeit",
        unit="km/h",
        category_utec="Sonne und Wind",
        default_parameter=True,
    ),
    wpgt=clc.MeteoParameter(
        original_name="Wind Peak Gust",
        title="max. Windböe",
        unit="km/h",
        category_utec="Sonne und Wind",
        default_parameter=False,
    ),
    rhum=clc.MeteoParameter(
        original_name="Relative Humidity",
        title="rel. Luftfeuchtigkeit",
        unit="%",
        category_utec="Feuchte, Luftdruck, Niederschlag",
        default_parameter=False,
    ),
    pres=clc.MeteoParameter(
        original_name="Sea-Level Air Pressure",
        title="Luftdruck (Meereshöhe)",
        unit="hPa",
        category_utec="Feuchte, Luftdruck, Niederschlag",
        default_parameter=False,
    ),
    snow=clc.MeteoParameter(
        original_name="Snow Depth",
        title="Schneehöhe",
        unit="m",
        category_utec="Feuchte, Luftdruck, Niederschlag",
        default_parameter=False,
    ),
    tsun=clc.MeteoParameter(
        original_name="Total Sunshine Duration",
        title="Sonnenstunden",
        unit="min",
        category_utec="Sonne und Wind",
        default_parameter=False,
    ),
)


HEX_PER_CENT: dict[int, str] = {
    0: "00",
    1: "03",
    2: "05",
    3: "08",
    4: "0A",
    5: "0D",
    6: "0F",
    7: "12",
    8: "14",
    9: "17",
    10: "19",
    11: "1C",
    12: "1F",
    13: "21",
    14: "24",
    15: "26",
    16: "29",
    17: "2B",
    18: "2E",
    19: "30",
    20: "33",
    21: "36",
    22: "38",
    23: "3B",
    24: "3D",
    25: "40",
    26: "42",
    27: "45",
    28: "47",
    29: "4A",
    30: "4D",
    31: "4F",
    32: "52",
    33: "54",
    34: "57",
    35: "59",
    36: "5C",
    37: "5E",
    38: "61",
    39: "63",
    40: "66",
    41: "69",
    42: "6B",
    43: "6E",
    44: "70",
    45: "73",
    46: "75",
    47: "78",
    48: "7A",
    49: "7D",
    50: "80",
    51: "82",
    52: "85",
    53: "87",
    54: "8A",
    55: "8C",
    56: "8F",
    57: "91",
    58: "94",
    59: "96",
    60: "99",
    61: "9C",
    62: "9E",
    63: "A1",
    64: "A3",
    65: "A6",
    66: "A8",
    67: "AB",
    68: "AD",
    69: "B0",
    70: "B3",
    71: "B5",
    72: "B8",
    73: "BA",
    74: "BD",
    75: "BF",
    76: "C2",
    77: "C4",
    78: "C7",
    79: "C9",
    80: "CC",
    81: "CF",
    82: "D1",
    83: "D4",
    84: "D6",
    85: "D9",
    86: "DB",
    87: "DE",
    88: "E0",
    89: "E3",
    90: "E6",
    91: "E8",
    92: "EB",
    93: "ED",
    94: "F0",
    95: "F2",
    96: "F5",
    97: "F7",
    98: "FA",
    99: "FC",
}
