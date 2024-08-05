"""Konstanten"""

import datetime as dt
import pathlib
from dataclasses import dataclass, field
from typing import Any, Callable, Literal

from wetterdienst import Settings
from wetterdienst.provider.dwd.observation import DwdObservationRequest

from modules import classes_constants as clc
from modules import streamlit_functions as sf

REPO_NAME: str = "UTEC-Tools"

# Current Working Directory
CWD: str = str(pathlib.Path.cwd())


@dataclass
class ButtonProps:
    """Properties of Buttons"""

    label: str
    key: str | None = None
    help_: str | None = None
    on_click: Callable | None = None
    args: Any | None = None
    kwargs: Any | None = None
    type_: Literal["primary", "secondary"] | None = None
    disabled: bool | None = None
    use_container_width: bool | None = None
    file_name: str | None = None
    mime: str | None = None

    def func_args(self) -> dict:
        """Dictionary without missing data"""
        return {
            key.strip("_"): val for key, val in self.__dict__.items() if val is not None
        }


@dataclass
class Buttons:
    """Class for st.button()"""

    standard = ButtonProps(label="Knöpfle")
    abbruch = ButtonProps(label="Abbrechen", key="but_cancel")
    reset = ButtonProps(
        label="💫 Auswertung neu starten 💫",
        key="but_complete_reset",
        use_container_width=True,
        help_="Auswertung zurücksetzen um andere Datei hochladen zu können.",
    )
    download_html = ButtonProps(
        label="💾 html-Datei herunterladen 💾",
        key="but_html_download",
        file_name=f"Interaktive_Auswertung_{dt.datetime.now().strftime('%Y-%m-%d-%H-%M')}.html",
        mime="application/xhtml+xml",
        use_container_width=True,
    )
    download_excel = ButtonProps(
        label="💾 Excel-Datei herunterladen 💾",
        key="but_excel_download",
        file_name=f"Datenausgabe_{dt.datetime.now().strftime('%Y-%m-%d-%H-%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
    download_weather = ButtonProps(
        label="💾 Wetterdaten herunterladen 💾",
        key="but_weather_download",
        use_container_width=True,
    )
    download_example = ButtonProps(
        label="Beispieldatei herunterladen",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


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


@dataclass
class GroupUnits:
    """Einheiten, die bei der Umrechnung von Zeitreihen
    mit dem Mittelwert zusammengefasst werden

    - mean_always: Einheiten, die immer gemittelt werden
    - sum_month: Enheiten, die bei der Berechnung von Monatswerten
        aufsummiert, sonst aber auch gemittelt werden.
    - mean_all: Alle Einheiten, die gemittelt werden
        (inklusive solcher, die nicht immer gemittelt werden)
    """

    mean_always: list[str]
    sum_month: list[str]
    mean_all: list[str] = field(init=False)

    def __post_init__(self) -> None:
        """Combine to get all"""
        self.mean_all = [*self.mean_always, *self.sum_month]

    def check(
        self, unit: str | None, attr: Literal["mean_all", "mean_always", "sum_month"]
    ) -> bool:
        """Check if a unit needs to be grouped as mean"""

        if unit is None:
            return False

        att: list[str] = getattr(self, attr)
        return unit.strip().lower() in [mean.strip().lower() for mean in att]


GROUP_MEAN = GroupUnits(
    mean_always=["°C", "K", "m³", "m³/h", "pa/m", "Pa/m", "m/s", "%", "rad", "°"],
    sum_month=["W", "kW", "MW"],
)


# Transparenz (Deckungsgrad) 0= durchsichtig, 1= undurchsichtig
ALPHA: dict[str, str] = {
    "bg": ", 0.5)",  # Hintergrund Beschriftungen
    "fill": ", 0.2)",  # fill von Linien etc.
}

REXEL_TEXT_BLOCKS: list[str] = ["Rexel Germany GmbH & Co. KG", "www.rexel.de"]


@dataclass
class ExcelMarkers:
    """Name of Markers for Index and Units in the Excel-File"""

    index: str = "↓ Index ↓"
    units: str = "→ Einheit →"


@dataclass
class SpecialCols:
    """Special Column Names"""

    index: str = ExcelMarkers.index
    original_index: str = "orgidx"
    smooth: str = "geglättet"
    temp: str = "Außentemperatur"


@dataclass
class Suffixes:
    """Suffixes"""

    col_smooth: str = f" {SpecialCols.smooth}"
    col_arbeit: str = " → Arbeit"
    col_leistung: str = " → Leistung"
    col_original_index: str = f" - {SpecialCols.original_index}"
    fig_tit_h: str = '<i><span style="font-size: 12px;"> (Stundenwerte)</span></i>'
    fig_tit_15: str = '<i><span style="font-size: 12px;"> (15-Minuten-Werte)</span></i>'
    h_line: str = "hline"


DATE_COLUMNS: list[str] = [SpecialCols.index, SpecialCols.original_index, "Datum"]


@dataclass
class TimeDaysIn:
    """How many Days in a ..."""

    leap_year: int = 366
    year: int = 365
    month_31: int = 31
    month_30: int = 30
    month_29: int = 29
    month_28: int = 28
    week: int = 7


@dataclass
class TimeHoursIn:
    """How many Hours in a ..."""

    leap_year: int = 366 * 24
    year: int = 365 * 24
    month_31: int = 31 * 24
    month_30: int = 30 * 24
    month_29: int = 29 * 24
    month_28: int = 28 * 24
    week: int = 7 * 24
    day: int = 24
    half_day: int = 12


@dataclass
class TimeMinutesIn:
    """How many Minutes in a ..."""

    leap_year: int = 366 * 24 * 60
    year: int = 365 * 24 * 60
    month_31: int = 31 * 24 * 60
    month_30: int = 30 * 24 * 60
    month_29: int = 29 * 24 * 60
    month_28: int = 28 * 24 * 60
    week: int = 7 * 24 * 60
    day: int = 24 * 60
    half_day: int = 12 * 60
    hour: int = 60
    half_hour: int = 30
    quarter_hour: int = 15


@dataclass
class TimeSecondsIn:
    """How many Seconds in a ..."""

    leap_year: int = 366 * 24 * 60 * 60
    year: int = 365 * 24 * 60 * 60
    month_31: int = 31 * 24 * 60 * 60
    month_30: int = 30 * 24 * 60 * 60
    month_29: int = 29 * 24 * 60 * 60
    month_28: int = 28 * 24 * 60 * 60
    week: int = 7 * 24 * 60 * 60
    day: int = 24 * 60 * 60
    half_day: int = 12 * 60 * 60
    hour: int = 60 * 60
    half_hour: int = 30 * 60
    quarter_hour: int = 15 * 60
    minute: int = 60


@dataclass
class TimeMillisecondsIn:
    """How many Milliseconds in a ..."""

    leap_year: int = 366 * 24 * 60 * 60 * 1000
    year: int = 365 * 24 * 60 * 60 * 1000
    month_31: int = 31 * 24 * 60 * 60 * 1000
    month_30: int = 30 * 24 * 60 * 60 * 1000
    month_29: int = 29 * 24 * 60 * 60 * 1000
    month_28: int = 28 * 24 * 60 * 60 * 1000
    week: int = 7 * 24 * 60 * 60 * 1000
    day: int = 24 * 60 * 60 * 1000
    half_day: int = 12 * 60 * 60 * 1000
    hour: int = 60 * 60 * 1000
    half_hour: int = 30 * 60 * 1000
    quarter_hour: int = 15 * 60 * 1000
    minute: int = 60 * 1000
    second: int = 1000


@dataclass
class TimeMicrosecondsIn:
    """How many Microseconds in a ..."""

    leap_year: int = 366 * 24 * 60 * 60 * 1000 * 1000
    year: int = 365 * 24 * 60 * 60 * 1000 * 1000
    month_31: int = 31 * 24 * 60 * 60 * 1000 * 1000
    month_30: int = 30 * 24 * 60 * 60 * 1000 * 1000
    month_29: int = 29 * 24 * 60 * 60 * 1000 * 1000
    month_28: int = 28 * 24 * 60 * 60 * 1000 * 1000
    week: int = 7 * 24 * 60 * 60 * 1000 * 1000
    day: int = 24 * 60 * 60 * 1000 * 1000
    half_day: int = 12 * 60 * 60 * 1000 * 1000
    hour: int = 60 * 60 * 1000 * 1000
    half_hour: int = 30 * 60 * 1000 * 1000
    quarter_hour: int = 15 * 60 * 1000 * 1000
    minute: int = 60 * 1000 * 1000
    second: int = 1000 * 1000
    millisecond: int = 1000


@dataclass
class TimeNanosecondsIn:
    """How many Nanoseconds in a ..."""

    leap_year: int = 366 * 24 * 60 * 60 * 1000 * 1000 * 1000
    year: int = 365 * 24 * 60 * 60 * 1000 * 1000 * 1000
    month_31: int = 31 * 24 * 60 * 60 * 1000 * 1000 * 1000
    month_30: int = 30 * 24 * 60 * 60 * 1000 * 1000 * 1000
    month_29: int = 29 * 24 * 60 * 60 * 1000 * 1000 * 1000
    month_28: int = 28 * 24 * 60 * 60 * 1000 * 1000 * 1000
    week: int = 7 * 24 * 60 * 60 * 1000 * 1000 * 1000
    day: int = 24 * 60 * 60 * 1000 * 1000 * 1000
    half_day: int = 12 * 60 * 60 * 1000 * 1000 * 1000
    hour: int = 60 * 60 * 1000 * 1000 * 1000
    half_hour: int = 30 * 60 * 1000 * 1000 * 1000
    quarter_hour: int = 15 * 60 * 1000 * 1000 * 1000
    minute: int = 60 * 1000 * 1000 * 1000
    second: int = 1000 * 1000 * 1000
    millisecond: int = 1000 * 1000
    microsecond: int = 1000


TIME_RESOLUTIONS: dict[Literal["15m", "1h", "1d", "1mo"], clc.TimeResolution] = {
    "15m": clc.TimeResolution(
        de="15-Minutenwerte",
        dwd="minute_10",
        polars="15m",
        delta=dt.timedelta(minutes=15),
    ),
    "1h": clc.TimeResolution(
        de="Stundenwerte", dwd="hourly", polars="1h", delta=dt.timedelta(hours=1)
    ),
    "1d": clc.TimeResolution(
        de="Tageswerte", dwd="daily", polars="1d", delta=dt.timedelta(days=1)
    ),
    "1mo": clc.TimeResolution(
        de="Monatswerte", dwd="monthly", polars="1mo", delta=dt.timedelta(weeks=4)
    ),
}


WETTERDIENST_SETTINGS = Settings(
    ts_shape="long",
    ts_si_units=False,
    ts_skip_empty=True,
    ts_skip_threshold=0.90,
    ts_skip_criteria="min",
    ts_dropna=True,
    ignore_env=True,
)

DWD_DISCOVER: dict[str, dict[str, dict[str, str]]] = DwdObservationRequest.discover()
DWD_ALL_PAR_DIC: dict = dict(
    sorted(
        {
            par_name: {
                "available_resolutions": {
                    res for res, par_dic in DWD_DISCOVER.items() if par_name in par_dic
                },
                "unit": " "
                + next(
                    dic[par_name]["origin"]
                    for dic in DWD_DISCOVER.values()
                    if par_name in dic
                ),
            }
            for par_name in {
                par
                for sublist in [list(dic.keys()) for dic in DWD_DISCOVER.values()]
                for par in sublist
            }
        }.items()
    )
)

# Params that raise errors
DWD_PROBLEMATIC_PARAMS: list[str] = [
    "cloud_cover_total_index",
    "temperature_soil_mean_100",
    "visibility_range_index",
    "water_equivalent_snow_depth",
    "water_equivalent_snow_depth_excelled",
    # "wind_direction_gust_max",
    "wind_force_beaufort",
    "wind_gust_max_last_3h",
    "wind_gust_max_last_6h",
    # "wind_speed_min",
    # "wind_speed_rolling_mean_max",
]
DWD_GOOD_PARAMS: set[str] = set(DWD_ALL_PAR_DIC) - set(DWD_PROBLEMATIC_PARAMS)

DWD_DEFAULT_PARAMS: list[str] = ["temperature_air_mean_200"]

DWD_PARAMS_POLYSUN: dict[str, str] = {
    "radiation_global": "Gh [W/m²]",
    "radiation_sky_short_wave_diffuse": "Dh [W/m²]",
    "temperature_air_mean_200": "Tamb [°C]",
    "radiation_sky_long_wave": "Lh [W/m²]",
    "wind_speed": "Vwndh [m/s]",
    "humidity": "Hrel [%]",
}


DWD_QUERY_TIME_LIMIT: float = sf.s_get("ni_limit_time") or 15  # seconds
DWD_QUERY_DISTANCE_LIMIT: float = sf.s_get("ni_limit_dist") or 150  # km


DWD_RESOLUTION_OPTIONS: dict[str, str] = {
    "Minutenwerte": "minute_1",
    "5-Minutenwerte": "minute_5",
    "10-Minutenwerte": "minute_10",
    "Stundenwerte": "hourly",
    "6-Stundenwerte": "6_hour",
    "mehrmals täglich": "subdaily",
    "Tageswerte": "daily",
    "Monateswerte": "monthly",
    "Jahreswerte": "annual",
}

DWD_PARAM_TRANSLATION: dict[str, str] = {
    "cloud_cover_total": "Wolkendecke",
    "humidity": "Relative Luftfeuchte",
    "humidity_absolute": "Absolute Luftfeuchte",
    "precipitation_duration": "Niederschlagsdauer",
    "precipitation_height": "Niederschlagshöhe",
    "pressure_air_sea_level": "Luftdruck auf Meereshöhe",
    "pressure_air_site": "Luftdruck am Standort",
    "pressure_vapor": "Dampfdruck",
    "radiation_global": "Globalstrahlung",
    "radiation_sky_long_wave": "Atmosphärische Gegenstrahlung",
    "radiation_sky_short_wave_diffuse": "Diffuse Stahlung",
    "snow_depth": "Schneehöhe",
    "snow_depth_new": "Schneehöhe Neu",
    "temperature_air_max_200": "Lufttemperatur (Max)",
    "temperature_air_max_200_mean": "Lufttemperatur (Max-Ø)",
    "temperature_air_mean_200": "Lufttemperatur",
    "temperature_air_min_200": "Lufttemperatur (Min)",
    "temperature_air_min_200_mean": "Lufttemperatur (Min-Ø)",
    "temperature_dew_point_mean_200": "Taupunkttemperatur (Ø)",
    "temperature_soil_mean_005": "Bodentemperatur in 5 cm Tiefe",
    "temperature_soil_mean_010": "Bodentemperatur in 10 cm Tiefe",
    "temperature_soil_mean_020": "Bodentemperatur in 20 cm Tiefe",
    "temperature_soil_mean_050": "Bodentemperatur in 50 cm Tiefe",
    "temperature_soil_mean_100": "Bodentemperatur in 1 m Tiefe",
    "temperature_wet_mean_200": "Bodentemperatur in 2 m Tiefe",
    "visibility_range": "Sichtweite",
    "weather": "Wetter",
    "wind_direction": "Windrichtung",
    "wind_direction_gust_max": "Windrichtung Maximalböhe",
    "wind_gust_max": "Maximalböhe",
    "wind_speed": "Windgeschwindigkeit",
    "wind_speed_min": "Minimale Windgeschwindigkeit",
    "wind_speed_rolling_mean_max": "Maximalen Windgeschwindigkeit (gleitendes Mittel)",
}

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
    arbeit=clc.SuffixUnit(Suffixes.col_arbeit, ["GWh", "MWh", "kWh", "Wh"]),
    leistung=clc.SuffixUnit(Suffixes.col_leistung, ["GW", "MW", "kW", "W"]),
    all_suffixes=[Suffixes.col_arbeit, Suffixes.col_leistung],
)


@dataclass
class Exclude:
    """Linien, die bei gewissen Operationen übersprungen werden"""

    base: tuple[str, str, str] = (
        Suffixes.h_line,
        Suffixes.col_smooth,
        SpecialCols.original_index,
    )
    index: tuple[str, str, str, str] = (
        Suffixes.h_line,
        Suffixes.col_smooth,
        SpecialCols.original_index,
        ExcelMarkers.index,
    )
    suff_arbeit: tuple[str, str, str, str] = (
        Suffixes.h_line,
        Suffixes.col_smooth,
        SpecialCols.original_index,
        ARBEIT_LEISTUNG.arbeit.suffix,
    )


ST_PAGES: clc.StPages = clc.StPages()


PDF_PAGE_WIDGET_WIDTH = 300

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
