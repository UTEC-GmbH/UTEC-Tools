"""Konstanten"""

from pathlib import Path
from typing import Literal, TypeAlias, TypedDict

REPO_NAME: str = "UTEC-Tools"

# Current Working Directory
CWD: str = str(Path.cwd())

DURATIONS_IN_MS: dict[str, int] = {
    "half_day": 12 * 60 * 60 * 1000,  # 43.200.000
    "week": 7 * 24 * 60 * 60 * 1000,  # 604.800.000
    "month": 30 * 24 * 60 * 60 * 1000,  # 2.592.000.000
}


# Type Alias für nested dict of stings
DicStrNest: TypeAlias = dict[str, dict[str, str]]

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

# Spalte zur Speicherung der Datumswerte vor Sortierung für JDL
COL_ORG_DATE: str = "cutomdata"

# Anhang für geglättete Linien
SMOOTH_SUFFIX: str = " geglättet"

# Titel der Grafiken
FIG_TITLES: dict[str, str] = {
    "lastgang": "Lastgang",
    "jdl": "Geordnete Jahresdauerlinie",
    "mon": "Monatswerte",
    "tage": "Vergleich ausgewählter Tage",
}
FIG_TITLE_SUFFIXES: dict[str, str] = {
    "suffix_Stunden": '<i><span style="font-size: 12px;"> (Stundenwerte)</span></i>',
    "suffix_15min": '<i><span style="font-size: 12px;"> (15-Minuten-Werte)</span></i>',
}


class ArLeiDic(TypedDict):
    """dictionary type definition for ARBEIT_LEISTUNG dictionary"""

    suffix: dict[str, str]
    units: dict[str, list[str]]


ARBEIT_LEISTUNG: ArLeiDic = {
    "suffix": {"Leistung": " → Leistung", "Arbeit": " → Arbeit"},
    "units": {
        "Arbeit": ["GWh", "MWh", "kWh", "Wh"],
        "Leistung": ["GW", "MW", "kW", "W"],
    },
}


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

# Linien, die bei gewissen Operationen übersprungen werden
EXCLUDE: list[str] = [SMOOTH_SUFFIX, "hline", "orgidx"]

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

PAGES: DicStrNest = {
    "login": {
        "page_tit": "UTEC Online Tools",
    },
    "graph": {
        "page_tit": "Grafische Datenauswertung",
    },
    "meteo": {
        "page_tit": "Meteorologische Daten",
    },
}


# Transparenz (Deckungsgrad) 0= durchsichtig, 1= undurchsichtig
ALPHA: dict[str, str] = {
    "bg": ", 0.5)",  # Hintergrund Beschriftungen
    "fill": ", 0.2)",  # fill von Linien etc.
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

PLOTFARBE: dict[str, str] = {
    "Ost-West": FARBEN["hellgrün"],
    "Süd": FARBEN["gelb"],
    "Bedarf": FARBEN["blau"],
    "Produktion": FARBEN["hellblau"],
    "Eigenverbrauch": FARBEN["rot"],
    "Netzbezug": FARBEN["lila"],
}


# obis Elektrizität (Medium == 1)
OBIS_PATTERN_EL: str = r"1-\d*:\d*\.\d*"  # fnmatch "*1-*:*.*"


class ObisDic(TypedDict):
    """dictionary type definition for OBIS Code dictionary"""

    medium: dict[str, str]
    messgroesse: DicStrNest
    messart: DicStrNest


OBIS_ELECTRICAL: ObisDic = {
    "medium": {"1": "Elektrizität"},
    "messgroesse": {
        "1": {"bez": "Wirkleistung (+)", "unit": "kWh", "alt_bez": "Bezug"},
        "2": {"bez": "Wirkleistung (-)", "unit": "kWh", "alt_bez": "Lieferung"},
        "3": {"bez": "Blindenergie (+)", "unit": "kvarh", "alt_bez": "Blinden. Bezug"},
        "4": {
            "bez": "Blindenergie (-)",
            "unit": "kvarh",
            "alt_bez": "Blinden. Lieferung",
        },
        "5": {"bez": "Blindenergie QI", "unit": "kvarh", "alt_bez": "Blinden. QI"},
        "6": {"bez": "Blindenergie QII", "unit": "kvarh", "alt_bez": "Blinden. QII"},
        "7": {"bez": "Blindenergie QIII", "unit": "kvarh", "alt_bez": "Blinden. QIII"},
        "8": {"bez": "Blindenergie QIV", "unit": "kvarh", "alt_bez": "Blinden. QIV"},
        "9": {"bez": "Scheinenergie (+)", "unit": "kVA", "alt_bez": "Scheinen. Bezug"},
        "10": {
            "bez": "Scheinenergie (-)",
            "unit": "kVA",
            "alt_bez": "Scheinen. Lieferung",
        },
        "11": {"bez": "Strom", "unit": "A", "alt_bez": "Strom"},
        "12": {"bez": "Spannung", "unit": "V", "alt_bez": "Spannung"},
        "13": {
            "bez": "Leistungsfaktor Durchschnitt",
            "unit": "-",
            "alt_bez": "P-Faktor",
        },
        "14": {"bez": "Frequenz", "unit": "Hz", "alt_bez": "Frequenz"},
        "15": {
            "bez": "Wirkenergie QI+QII+QIII+QIV",
            "unit": "kWh",
            "alt_bez": "Wirken. QI+QII+QIII+QIV",
        },
        "16": {
            "bez": "Wirkenergie QI+QII+QIII+QIV",
            "unit": "kWh",
            "alt_bez": "Wirken. QI+QII+QIII+QIV",
        },
        "17": {"bez": "Wirkenergie QI", "unit": "kWh", "alt_bez": "Wirken. QI"},
        "18": {"bez": "Wirkenergie QII", "unit": "kWh", "alt_bez": "Wirken. QII"},
        "19": {"bez": "Wirkenergie QIII", "unit": "kWh", "alt_bez": "Wirken. QIII"},
        "20": {"bez": "Wirkenergie QIV", "unit": "kWh", "alt_bez": "Wirken. QIV"},
        "21": {"bez": "Wirkenergie L1 (+)", "unit": "kWh", "alt_bez": "L1 Bezug"},
        "22": {"bez": "Wirkenergie L1 (-)", "unit": "kWh", "alt_bez": "L1 Lieferung"},
        "23": {
            "bez": "Blindenergie L1 (+)",
            "unit": "kvarh",
            "alt_bez": "L1 Blinden. Bezug",
        },
        "24": {
            "bez": "Blindenergie L1 (-)",
            "unit": "kvarh",
            "alt_bez": "L1 Blinden. Lieferung",
        },
        "25": {
            "bez": "Blindenergie L1 QI",
            "unit": "kvarh",
            "alt_bez": "L1 Blinden. QI",
        },
        "26": {
            "bez": "Blindenergie L1 QII",
            "unit": "kvarh",
            "alt_bez": "L1 Blinden. QII",
        },
        "27": {
            "bez": "Blindenergie L1 QIII",
            "unit": "kvarh",
            "alt_bez": "L1 Blinden. QIII",
        },
        "28": {
            "bez": "Blindenergie L1 QIV",
            "unit": "kvarh",
            "alt_bez": "L1 Blinden. QIV",
        },
        "29": {
            "bez": "Scheinenergie L1 (+)",
            "unit": "kVA",
            "alt_bez": "L1 Scheinen. Bezug",
        },
        "30": {
            "bez": "Scheinenergie L1 (-)",
            "unit": "kVA",
            "alt_bez": "L1 Scheinen. Lieferung",
        },
        "31": {"bez": "I L1", "unit": "A", "alt_bez": "L1 Strom"},
        "32": {"bez": "U PH-N L1", "unit": "V", "alt_bez": "L1 Spannung"},
        "33": {"bez": "Leistungsfaktor L1", "unit": "-", "alt_bez": "L1 P-Faktor"},
        "34": {"bez": "Frequenz L1", "unit": "Hz", "alt_bez": "L1 Frequenz"},
        "35": {
            "bez": "Wirkenergie L1 QI+QII+QIII+QIV",
            "unit": "kWh",
            "alt_bez": "L1 Wirken. QI+QII+QIII+QIV",
        },
        "36": {
            "bez": "Wirkenergie L1 QI+QII+QIII+QIV",
            "unit": "kWh",
            "alt_bez": "L1 Wirken. QI+QII+QIII+QIV",
        },
        "37": {"bez": "Wirkenergie L1 QI", "unit": "kWh", "alt_bez": "L1 Wirken. QI"},
        "38": {"bez": "Wirkenergie L1 QII", "unit": "kWh", "alt_bez": "L1 Wirken. QII"},
        "39": {
            "bez": "Wirkenergie L1 QIII",
            "unit": "kWh",
            "alt_bez": "L1 Wirken. QIII",
        },
        "40": {"bez": "Wirkenergie L1 QIV", "unit": "kWh", "alt_bez": "L1 Wirken. QIV"},
        "41": {"bez": "Wirkenergie L2 (+)", "unit": "kWh", "alt_bez": "L2 Bezug"},
        "42": {"bez": "Wirkenergie L2 (-)", "unit": "kWh", "alt_bez": "L2 Lieferung"},
        "43": {
            "bez": "Blindenergie L2 (+)",
            "unit": "kvarh",
            "alt_bez": "L2 Blinden. Bezug",
        },
        "44": {
            "bez": "Blindenergie L2 (-)",
            "unit": "kvarh",
            "alt_bez": "L2 Blinden. Lieferung",
        },
        "45": {
            "bez": "Blindenergie L2 QI",
            "unit": "kvarh",
            "alt_bez": "L2 Blinden. QI",
        },
        "46": {
            "bez": "Blindenergie L2 QII",
            "unit": "kvarh",
            "alt_bez": "L2 Blinden. QII",
        },
        "47": {
            "bez": "Blindenergie L2 QIII",
            "unit": "kvarh",
            "alt_bez": "L2 Blinden. QIII",
        },
        "48": {
            "bez": "Blindenergie L2 QIV",
            "unit": "kvarh",
            "alt_bez": "L2 Blinden. QIV",
        },
        "49": {
            "bez": "Scheinenergie L2 (+)",
            "unit": "kVA",
            "alt_bez": "L2 Scheinen. Bezug",
        },
        "50": {
            "bez": "Scheinenergie L2 (-)",
            "unit": "kVA",
            "alt_bez": "L2 Scheinen. Lieferung",
        },
        "51": {"bez": "I L2", "unit": "A", "alt_bez": "L2 Strom"},
        "52": {"bez": "U PH-N L2", "unit": "V", "alt_bez": "L2 Spannung"},
        "53": {"bez": "Leistungsfaktor L2", "unit": "-", "alt_bez": "L2 P-Faktor"},
        "54": {"bez": "Frequenz L2", "unit": "Hz", "alt_bez": "L2 Frequenz"},
        "55": {
            "bez": "Wirkenergie L2 QI+QII+QIII+QIV",
            "unit": "kWh",
            "alt_bez": "L2 Wirken. QI+QII+QIII+QIV",
        },
        "56": {
            "bez": "Wirkenergie L2 QI+QII+QIII+QIV",
            "unit": "kWh",
            "alt_bez": "L2 Wirken. QI+QII+QIII+QIV",
        },
        "57": {"bez": "Wirkenergie L2 QI", "unit": "kWh", "alt_bez": "L2 Wirken. QI"},
        "58": {"bez": "Wirkenergie L2 QII", "unit": "kWh", "alt_bez": "L2 Wirken. QII"},
        "59": {
            "bez": "Wirkenergie L2 QIII",
            "unit": "kWh",
            "alt_bez": "L2 Wirken. QIII",
        },
        "60": {"bez": "Wirkenergie L2 QIV", "unit": "kWh", "alt_bez": "L2 Wirken. QIV"},
        "61": {"bez": "Wirkenergie L3 (+)", "unit": "kWh", "alt_bez": "L3 Bezug"},
        "62": {"bez": "Wirkenergie L3 (-)", "unit": "kWh", "alt_bez": "L3 Lieferung"},
        "63": {
            "bez": "Blindenergie L3 (+)",
            "unit": "kvarh",
            "alt_bez": "L3 Blinden. Bezug",
        },
        "64": {
            "bez": "Blindenergie L3 (-)",
            "unit": "kvarh",
            "alt_bez": "L3 Blinden. Lieferung",
        },
        "65": {
            "bez": "Blindenergie L3 QI",
            "unit": "kvarh",
            "alt_bez": "L3 Blinden. QI",
        },
        "66": {
            "bez": "Blindenergie L3 QII",
            "unit": "kvarh",
            "alt_bez": "L3 Blinden. QII",
        },
        "67": {
            "bez": "Blindenergie L3 QIII",
            "unit": "kvarh",
            "alt_bez": "L3 Blinden. QIII",
        },
        "68": {
            "bez": "Blindenergie L3 QIV",
            "unit": "kvarh",
            "alt_bez": "L3 Blinden. QIV",
        },
        "69": {
            "bez": "Scheinenergie L3 (+)",
            "unit": "kVA",
            "alt_bez": "L3 Scheinen. Bezug",
        },
        "70": {
            "bez": "Scheinenergie L3 (-)",
            "unit": "kVA",
            "alt_bez": "L3 Scheinen. Lieferung",
        },
        "71": {"bez": "I L3", "unit": "A", "alt_bez": "L3 Strom"},
        "72": {"bez": "U PH-N L3", "unit": "V", "alt_bez": "L3 Spannung"},
        "73": {"bez": "Leistungsfaktor L3", "unit": "-", "alt_bez": "L3 P-Faktor"},
        "74": {"bez": "Frequenz L3", "unit": "Hz", "alt_bez": "L3 Frequenz"},
        "75": {
            "bez": "Wirkenergie L3 QI+QII+QIII+QIV",
            "unit": "kWh",
            "alt_bez": "L3 Wirken. QI+QII+QIII+QIV",
        },
        "76": {
            "bez": "Wirkenergie L3 QI+QII+QIII+QIV",
            "unit": "kWh",
            "alt_bez": "L3 Wirken. QI+QII+QIII+QIV",
        },
        "77": {"bez": "Wirkenergie L3 QI", "unit": "kWh", "alt_bez": "L3 Wirken. QI"},
        "78": {"bez": "Wirkenergie L3 QII", "unit": "kWh", "alt_bez": "L3 Wirken. QII"},
        "79": {
            "bez": "Wirkenergie L3 QIII",
            "unit": "kWh",
            "alt_bez": "L3 Wirken. QIII",
        },
        "80": {"bez": "Wirkenergie L3 QIV", "unit": "kWh", "alt_bez": "L3 Wirken. QIV"},
        "81": {"bez": "Phasenwinkel", "unit": "-", "alt_bez": "Phasenwinkel"},
        "82": {
            "bez": "Einheitslose Mengen (z.B. Impulse)",
            "unit": "-",
            "alt_bez": "Einheitslose Mengen",
        },
        "91": {"bez": "I Neutralleiter", "unit": "A", "alt_bez": "N Strom"},
        "92": {"bez": "U Neutralleiter", "unit": "V", "alt_bez": "N Spannung"},
    },
    "messart": {
        "0": {
            "bez": "Mittelwert Abrechnungsperiode (seit letztem Reset)",
            "alt_bez": "Mittel",
        },
        "1": {"bez": "Kumulativ Minimum 1", "alt_bez": "min"},
        "2": {"bez": "Kumulativ Maximum 1", "alt_bez": "max"},
        "3": {"bez": "Minimum 1", "alt_bez": "min"},
        "4": {"bez": "Aktueller Mittelwert 1", "alt_bez": "Mittel"},
        "5": {"bez": "Letzter Mittelwert 1", "alt_bez": "Mittel"},
        "6": {"bez": "Maximum 1", "alt_bez": "max"},
        "7": {"bez": "Momentanwert", "alt_bez": "Momentanwert"},
        "8": {"bez": "Zeit Integral 1 - Zählerstand", "alt_bez": "Zählerstand"},
        "9": {"bez": "Zeit Integral 2 - Verbrauch / Vorschub", "alt_bez": "Verbrauch"},
        "10": {"bez": "Zeit Integral 3", "alt_bez": "Integral"},
        "11": {"bez": "Kumulativ Minimum 2", "alt_bez": "min"},
        "12": {"bez": "Kumulativ Maximum 2", "alt_bez": "max"},
        "13": {"bez": "Minimum 2", "alt_bez": "min"},
        "14": {"bez": "Aktueller Mittelwert 2", "alt_bez": "Mittel"},
        "15": {"bez": "Letzter Mittelwert 2", "alt_bez": "Mittel"},
        "16": {"bez": "Maximum 2", "alt_bez": "max"},
        "17": {"bez": "Momentanwert 2", "alt_bez": "Momentanwert"},
        "18": {"bez": "Zeit Integral 2 1 - Zählerstand", "alt_bez": "Zählerstand"},
        "19": {
            "bez": "Zeit Integral 2 2 - Verbrauch / Vorschub",
            "alt_bez": "Verbrauch",
        },
        "20": {"bez": "Zeit Integral 3 2", "alt_bez": "Integral"},
        "21": {"bez": "Kumulativ Minimum 3", "alt_bez": "min"},
        "22": {"bez": "Kumulativ Maximum 3", "alt_bez": "max"},
        "23": {"bez": "Minimum 3", "alt_bez": "min"},
        "24": {"bez": "Aktueller Mittelwert 3", "alt_bez": "Mittel"},
        "25": {"bez": "Letzter Mittelwert 3", "alt_bez": "Mittel"},
        "26": {"bez": "Maximum 3", "alt_bez": "max"},
        "27": {"bez": "Aktueller Mittelwert 5", "alt_bez": "Mittel"},
        "28": {"bez": "Aktueller Mittelwert 6", "alt_bez": "Mittel"},
        "29": {
            "bez": "Zeit Integral 5 - Lastprofil Aufzeichnungsperiode 1",
            "alt_bez": "Lastprofil",
        },
        "30": {
            "bez": "Zeit Integral 6 - Lastprofil Aufzeichnungsperiode 2",
            "alt_bez": "Lastprofil",
        },
        "31": {"bez": "Untere Grenzwertschwelle", "alt_bez": "Grenzwertschwelle u"},
        "32": {
            "bez": "Unterer Grenzwert Ereigniszähler",
            "alt_bez": "Grenzwert Zähler u",
        },
        "33": {"bez": "Unterer Grenzwert Dauer", "alt_bez": "Grenzwert Dauer u"},
        "34": {"bez": "Unterer Grenzwert Größe", "alt_bez": "Grenzwert Größe u"},
        "35": {"bez": "Oberer Grenzwertschwelle", "alt_bez": "Grenzwertschwelle o"},
        "36": {
            "bez": "Oberer Grenzwert Ereigniszähler",
            "alt_bez": "Grenzwert Zähler o",
        },
        "37": {"bez": "Oberer Grenzwert Dauer", "alt_bez": "Grenzwert Dauer o"},
        "38": {"bez": "Oberer Grenzwert Größe", "alt_bez": "Grenzwert Größe o"},
        "58": {
            "bez": "Zeit Integral 4 - Test Zeit Integral",
            "alt_bez": "Test Zeit Integral",
        },
        "131": {"bez": "Schichtwert", "alt_bez": "Schichtwert"},
        "132": {"bez": "Tageswert", "alt_bez": "Tageswert"},
        "133": {"bez": "Wochenwert", "alt_bez": "Wochenwert"},
        "134": {"bez": "Monatswert", "alt_bez": "Monatswert"},
        "135": {"bez": "Quartalswert", "alt_bez": "Quartalswert"},
        "136": {"bez": "Jahreswert", "alt_bez": "Jahreswert"},
    },
}


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
