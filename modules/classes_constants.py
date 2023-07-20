"""Classes and such"""

import re
from dataclasses import dataclass, field
from typing import TypedDict

from loguru import logger


@dataclass(frozen=True, kw_only=True)
class Suffixes:
    """Suffixes"""

    col_smooth: str
    col_arbeit: str
    col_leistung: str
    col_original_index: str
    fig_tit_h: str
    fig_tit_15: str
    h_line: str


@dataclass(frozen=True, kw_only=True)
class ExcelMarkers:
    """Name of Markers for Index and Units in the Excel-File"""

    index: str
    units: str


@dataclass(frozen=True, kw_only=True)
class SpecialCols:
    """Special Column Names"""

    index: str
    original_index: str
    smooth: str
    temp: str


@dataclass(frozen=True, kw_only=True)
class TimeMSec:
    """Übersetzung von Zeitbezeichnung in Millisekunden
    (z.B. für Tickstops in plotly graphs)
    """

    half_day: int
    week: int
    month: int


@dataclass(frozen=True, kw_only=True)
class TimeMin:
    """Zeiten in Minuten"""

    hour: int
    half_hour: int
    quarter_hour: int


@dataclass(frozen=True, kw_only=True)
class FigIDs:
    """Title und css-suffixes für Plotly graphen"""

    lastgang: str
    jdl: str
    mon: str
    days: str

    def list_all(self) -> list[str]:
        """List all values"""
        return [getattr(self, attr) for attr in self.__dataclass_fields__]

    def as_dic(self) -> dict:
        """Dictionary representation"""
        return {attr: getattr(self, attr) for attr in self.__dataclass_fields__}


@dataclass(frozen=True)
class SuffixUnit:
    """Für die Aufteilung in Leistung / Arbeit bei 15-Minuten-Werten"""

    suffix: str
    possible_units: list[str]


@dataclass(frozen=True, kw_only=True)
class ArbeitLeistung:
    """Arbeit und Leistung bei 15-min-Daten


    Methods:
        - get_suffix: Get the suffix by providing the type (Arbeit / Leistung)
    """

    arbeit: SuffixUnit
    leistung: SuffixUnit
    all_suffixes: list[str]

    def get_suffix(self, data_type: str) -> str:
        """Get the suffix by providing the type (Arbeit / Leistung)"""
        return getattr(self, data_type.lower()).suffix


@dataclass(frozen=True, kw_only=True)
class Exclude:
    """Column names or suffixes to exclude in order to only get the "normal" data"""

    base: list[str]
    index: list[str]
    suff_arbeit: list[str]


@dataclass(frozen=True)
class StPageProps:
    """Streamlit Page Properties"""

    short: str
    title: str
    excel_ws_name: str | None = None


@dataclass(frozen=True, kw_only=True)
class StPages:
    """Streamlit Pages"""

    login: StPageProps
    graph: StPageProps
    meteo: StPageProps
    chat: StPageProps
    maps: StPageProps

    def get_all_short(self) -> list[str]:
        """Get a list of short page descriptors"""
        return [getattr(self, attr).short for attr in self.__dataclass_fields__]

    def get_title(self, short: str) -> str:
        """Get the title by providing the short page descriptor"""
        return getattr(self, short.lower()).title


@dataclass
class MeteoParameter:
    """Properties of Meteo Codes"""

    original_name: str
    title: str
    unit: str
    category_utec: str
    default_parameter: bool
    closest_station_id: str | None = None
    distance_closest: float | None = None
    num_format: str = field(init=False)
    pandas_styler: str = field(init=False)

    def __post_init__(self) -> None:
        """Fill in fields"""
        self.num_format = f'#,##0.0" {self.unit}"'
        self.pandas_styler = "{:,.1f} " + self.unit


@dataclass
class MeteoCodes:
    """Meteo Codes from the Meteostat package"""

    temp: MeteoParameter
    dwpt: MeteoParameter
    prcp: MeteoParameter
    wdir: MeteoParameter
    wspd: MeteoParameter
    wpgt: MeteoParameter
    rhum: MeteoParameter
    pres: MeteoParameter
    snow: MeteoParameter
    tsun: MeteoParameter

    def list_utec_categories(self) -> list[str]:
        """Returns a list (set) of all used UTEC categories"""
        return list(
            {getattr(self, field).category_utec for field in self.__dataclass_fields__}
        )

    def list_all_params(self) -> list[str]:
        """Returns a list of available parameters"""
        return list(self.__dataclass_fields__)


class ObisDic(TypedDict):
    """dictionary type definition for OBIS Code dictionary"""

    medium: dict[str, str]
    messgroesse: dict
    messart: dict


@dataclass()
class ObisElectrical:
    """OBIS-Codes für elektrische Zähler.
    Raises
        - ValueError: Falls der Code nicht mit '1' anfängt,
            ist es kein Code für eletrische Zähler.
    """

    code_or_name: str
    pattern: str = r"1-\d*:\d*\.\d*"
    code: str = field(init=False)
    medium: str = "Elektrizität"
    messgroesse: str = field(init=False)
    messart: str = field(init=False)
    unit: str = field(init=False)
    name: str = field(init=False)
    name_kurz: str = field(init=False)
    name_lang: str = field(init=False)

    def as_dic(self) -> dict[str, str]:
        """Dictionary representation"""
        return {attr: getattr(self, attr) for attr in self.__dataclass_fields__}

    def __repr__(self) -> str:
        """Customize the representation to give a dictionary"""
        return "\n".join([f"{key}: '{val}'" for key, val in self.as_dic().items()])

    def __post_init__(self) -> None:
        """Check if code is valid and fill in the fields"""
        pat_match: re.Match[str] | None = re.search(self.pattern, self.code_or_name)
        if pat_match is None:
            err_msg: str = "Kein gültiger OBIS-Code für elektrische Zähler!"
            logger.critical(err_msg)
            raise ValueError(err_msg)
        self.code = pat_match[0]
        code_r: str = self.code.replace(":", "-").replace(".", "-").replace("~*", "-")
        code_l: list[str] = code_r.split("-")
        code_messgr: str = code_l[2]
        code_messart: str = code_l[3]
        dic: dict = OBIS_ELECTRICAL

        self.messgroesse = dic["messgroesse"][code_messgr]["bez"]
        self.messart = dic["messart"][code_messart]["bez"]
        self.unit = f' {dic["messgroesse"][code_messgr]["unit"]}'
        self.name = f'{dic["messgroesse"][code_messgr]["alt_bez"]} ({self.code})'
        self.name_kurz = dic["messgroesse"][code_messgr]["alt_bez"]
        self.name_lang = (
            f'{dic["messgroesse"][code_messgr]["bez"]} '
            f'[{dic["messgroesse"][code_messgr]["unit"]}] - '
            f'{dic["messart"][code_messart]["bez"]} ({self.code})'
        )


OBIS_ELECTRICAL: dict = {
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
