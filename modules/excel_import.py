"""Import und Download von Excel-Dateien"""

import io
import re
from typing import Literal, NamedTuple

import polars as pl
from loguru import logger

from modules import classes as cl
from modules import general_functions as gf
from modules import constants as cont
from modules import setup_logger as slog


@gf.func_timer
def import_prefab_excel(
    file: io.BytesIO | str,
) -> tuple[pl.DataFrame, cl.MetaData]:
    """Import and download Excel files.

    Args:
    - file (io.BytesIO | str): BytesIO object or string
        representing the Excel file to import.

    Returns:
    - tuple[pl.DataFrame, MetaData]: A tuple containing the imported DataFrame
        and metadata extracted from the Excel file.

    Example files for testing:
    - file = "example_files/Auswertung Stromlastgang - einzelnes Jahr.xlsx"
    - file = "example_files/Stromlastgang - mehrere Jahre.xlsx"
    - file = "example_files/Wärmelastgang - mehrere Jahre.xlsx"

    Example test run:
    file = "example_files/Auswertung Stromlastgang - einzelnes Jahr.xlsx"
    df, meta = import_prefab_excel(file)
    """

    mark_index: str = cont.ExcelMarkers.index
    mark_units: str = cont.ExcelMarkers.units

    df: pl.DataFrame = get_df_from_excel(file)

    # remove empty rows and columns and rename columns
    df = remove_empty(df)
    df = rename_columns(df, mark_index)

    # extract units
    meta: cl.MetaData = meta_units(df, mark_index, mark_units)

    # clean up DataFrame
    df = clean_up_df(df, mark_index)

    # meta data if obis code in column title
    df, meta = meta_from_obis(df, meta)

    # Weitere Metadaten
    meta = temporal_metadata(df, mark_index, meta)
    meta = set_y_axis_for_lines(meta)
    meta = meta_number_format(df, meta)

    # 15min und kWh
    df, meta = convert_15min_kwh_to_kw(df, meta)

    logger.info(meta.__dict__)
    slog.log_df(df)
    logger.success("Excel-Datei importiert.")

    return df, meta


def get_df_from_excel(file: io.BytesIO | str) -> pl.DataFrame:
    """Excel Import via csv-conversion"""

    sheet: str = "Daten"
    xlsx_options: dict[str, str | bool] = {
        "skip_empty_lines": True,
        "skip_trailing_columns": True,
        "dateformat": "%d.%m.%Y %T",
    }
    csv_options: dict[str, bool] = {"has_header": False, "try_parse_dates": False}

    return pl.read_excel(
        file,
        sheet_name=sheet,
        xlsx2csv_options=xlsx_options,
        read_csv_options=csv_options,
    )


def remove_empty(df: pl.DataFrame, **kwargs) -> pl.DataFrame:
    """Remove empty rows and / or columns

    Args:
        - df (pl.DataFrame): DataFrame to edit
        - row (bool): Optional keyword argument.
            Set to False if empty rows should not be removed
        - col (bool): Optional keyword argument.
            Set to False if empty columns should not be removed

    Returns:
        - pl.DataFrame: DataFrame without empty rows / columns
    """

    row: bool = kwargs.get("row") or True
    col: bool = kwargs.get("col") or True

    # remove rows where all values are 'null'
    if row:
        df = df.filter(~pl.all(pl.all().is_null()))  # pylint: disable=E1130

    # remove columns where all values are 'null'
    if col:
        df = df[[col.name for col in df if col.null_count() != df.height]]

    return df


def rename_columns(df: pl.DataFrame, mark_index: str) -> pl.DataFrame:
    """Rename the columns of the DataFrame"""

    # find index marker
    ind_col: str = [col for col in df.columns if mark_index in df.get_column(col)][0]
    logger.info(f"Index-marker found in column '{ind_col}'")

    # rename columns
    cols: tuple = df.row(by_predicate=pl.col(ind_col) == mark_index)
    df.columns = list(cols)

    return df


def meta_units(df: pl.DataFrame, mark_index: str, mark_units: str) -> cl.MetaData:
    """Get units for dataclass"""

    units: dict[str, str] = (
        df.filter(pl.col(mark_index) == mark_units)
        .select([col for col in df.columns if col != mark_index])
        .row(0, named=True)
    )

    # leerzeichen vor Einheit
    units = {line: f" {unit.strip()}" for line, unit in units.items()}

    meta: cl.MetaData = cl.MetaData(
        units=cl.MetaUnits(
            all_units=list(units.values()),
            set_units=gf.sort_list_by_occurance(list(units.values())),
        ),
        lines=[
            cl.MetaLine(name=line, orig_tit=line, tit=line, unit=unit)
            for line, unit in units.items()
        ],
    )

    return meta


def meta_number_format(df: pl.DataFrame, meta: cl.MetaData) -> cl.MetaData:
    """Define Number Formats for Excel-Export"""

    # cut-off for decimal places
    decimal_0: int = 1000
    decimal_1: int = 100
    decimal_2: int = 10

    quantiles: pl.DataFrame = df.quantile(0.95)

    for line in meta.lines:
        if line.name in df.columns:
            line_quant = quantiles.get_column(line.name).item()
            if any(isinstance(line_quant, number) for number in [int, float]):
                if abs(line_quant) >= decimal_0:
                    line.excel_number_format = f'#.##0"{line.unit}"'
                if abs(line_quant) >= decimal_1:
                    line.excel_number_format = f'#.##0,0"{line.unit}"'
                if abs(line_quant) >= decimal_2:
                    line.excel_number_format = f'#.##0,00"{line.unit}"'
                else:
                    line.excel_number_format = f'#.##0,000"{line.unit}"'

    return meta


def meta_units_update(meta: cl.MetaData) -> cl.MetaData:
    """Update units with all units from metadata"""

    all_units: list[str] = [str(line.unit) for line in meta.lines]
    meta.units.all_units = all_units
    meta.units.set_units = gf.sort_list_by_occurance(all_units)

    return meta


def set_y_axis_for_lines(meta: cl.MetaData) -> cl.MetaData:
    """Y-Achsen der Linien"""

    for line in meta.lines:
        if line.unit not in meta.units.set_units:
            continue
        index_unit: int = meta.units.set_units.index(line.unit)
        if index_unit > 0:
            meta.get_line_by_name(line.name).y_axis = f"y{index_unit + 1}"
        logger.info(f"{line.name}: Y-Achse '{meta.get_line_by_name(line.name).y_axis}'")

    return meta


def clean_up_df(df: pl.DataFrame, mark_index: str) -> pl.DataFrame:
    """Clean up the DataFrame and adjust the data types"""

    ind_row: int = (
        df.with_row_count().filter(pl.col(mark_index) == mark_index).row(0)[0]
    )
    df = df.slice(ind_row + 1)
    df = df.select(
        [pl.col(mark_index).str.strptime(pl.Datetime, "%d.%m.%Y %T")]
        + [pl.col(col).cast(pl.Float32) for col in df.columns if col != mark_index]
    )

    df = clean_up_daylight_savings(df, mark_index).df_clean

    # copy index in separate column to preserve if index is changed (multi year)
    df = df.with_columns(pl.col(mark_index).alias(cont.ORIGINAL_INDEX_COL))

    return df


class CleanUpDLS(NamedTuple):
    """Named Tuple for return value of following function"""

    df_clean: pl.DataFrame
    df_deleted: pl.DataFrame


def clean_up_daylight_savings(df: pl.DataFrame, mark_index: str) -> CleanUpDLS:
    """Zeitumstellung

    Bei der Zeitumstellung auf Sommerzeit wird die Uhr eine Stunde vor gestellt,
    sodass in der Zeitreihe eine Stunde fehlt. Falls das DataFrame diese Stunde
    enthält (z.B. mit nullen in der Stunde), werden diese Zeilen gelöscht.

    Bei der Zeitumstellung auf Winterzeit wird die Uhr eine Sunde zurück gestellt.
    Dadurch gibt es die Stunde doppelt in der Zeitreihe. Das erste Auftreten der
    doppelten Stunde wird gelöscht.

    Args:
        - df (DataFrame): DataFrame to edit

    Returns:
        - dict[str, pd.DataFrame]:
            - "df_clean": edited DataFrame
            - "df_deleted": deleted data
    """

    # Sommerzeitumstellung: letzter Sonntag im Maerz - von 2h auf 3h
    month: int = 3  # Monat = 3 -> März
    day: int = 31 - 7  # letzte Woche (Tag > 31-7)
    weekday: int = 6  # Wochentag = 6 -> Sonntag
    hour: int = 2  # Stunde 2 wird ausgelassen

    date_col: pl.Series = df.get_column(mark_index)
    summer: pl.Series = df.filter(
        (date_col.dt.month() == month)
        & (date_col.dt.day() > day)
        & (date_col.dt.weekday() == weekday)
        & (date_col.dt.hour() == hour)
    ).get_column(mark_index)

    # Winterzeitumstellung: doppelte Stunde -> Duplikate löschen

    df_clean: pl.DataFrame = df.filter(~pl.col(mark_index).is_in(summer)).unique(
        subset=mark_index, keep="first", maintain_order=True
    )
    df_deleted: pl.DataFrame = df.filter(
        pl.col(mark_index).is_in(summer) | pl.col(mark_index).is_duplicated()
    ).unique(subset=mark_index, keep="last", maintain_order=True)

    if df_deleted.height > 0:
        logger.warning("Data deleted due to daylight savings.")
        logger.log(slog.log_lvl().data_frame.name, df_deleted)
    else:
        logger.info("No data deleted due to daylight savings")

    return CleanUpDLS(df_clean=df_clean, df_deleted=df_deleted)


def temporal_metadata(
    df: pl.DataFrame, mark_index: str, meta: cl.MetaData
) -> cl.MetaData:
    """Get information about the time index."""

    if not df.get_column(mark_index).is_temporal():
        logger.error("Kein Zeitindex gefunden!!!")
        return meta

    viertel: int = 15
    std: int = 60

    meta.datetime = True
    meta.years = df.get_column(mark_index).dt.year().unique().sort().to_list()

    meta.td_mean = int(
        df.select(pl.col(mark_index).diff().dt.minutes().drop_nulls().mean()).item()
    )

    if meta.td_mean == viertel:
        meta.td_interval = "15min"
        logger.info("Index mit zeitlicher Auflösung von 15 Minuten erkannt.")
    elif meta.td_mean == std:
        meta.td_interval = "h"
        logger.info("Index mit zeitlicher Auflösung von 1 Stunde erkannt.")
    else:
        logger.debug(f"Mittlere zeitliche Auflösung des df: {meta.td_mean} Minuten")

    return meta


def meta_from_obis(
    df: pl.DataFrame, meta: cl.MetaData
) -> tuple[pl.DataFrame, cl.MetaData]:
    """Update meta data and column name if there is an obis code in a column title.

    If there's an OBIS-code (e.g. 1-1:1.29.0), the following meta data is edited:
    - obis -> instance of ObisElecgtrical class
    - unit -> only if not given in Excel-File
    - tite -> "alternative name (code)"

    Args:
        - df (DataFrame): DataFrame to edit
        - meta (MetaData): MetaData dataclass

    Returns:
        - df (DataFrame): updated DataFrame
        - meta (MetaData): updated MetaData dataclass
    """

    for line in meta.lines:
        name: str = line.name

        # check if there is an OBIS-code in the column title
        if match := re.search(cont.ObisElectrical.pattern, name):
            line.obis = cont.ObisElectrical(match[0])
            line.name = line.obis.name
            line.tit = line.obis.name
            line.unit = line.unit or line.obis.unit

            df = df.rename({name: line.obis.name})

    return df, meta_units_update(meta)


def convert_15min_kwh_to_kw(
    df: pl.DataFrame, meta: cl.MetaData
) -> tuple[pl.DataFrame, cl.MetaData]:
    """Falls die Daten als 15-Minuten-Daten vorliegen,
    wird geprüft ob es sich um Verbrauchsdaten handelt.
    Falls dem so ist, werden sie mit 4 multipliziert um
    Leistungsdaten zu erhalten.

    Die Leistungsdaten werden in neue Spalten im
    DataFrame geschrieben.


    Args:
        - df (pl.DataFrame): Der zu untersuchende DataFrame
        - meta (MetaData): Metadaten

    Returns:
        - tuple[pd.DataFrame, MetaData]: Aktualisierte df und Metadaten
    """

    if meta.td_interval not in ["15min"]:
        logger.debug("Skipped 'convert_15min_kwh_to_kw'")
        return df, meta

    suffixes: list[str] = cont.ARBEIT_LEISTUNG.get_all_suffixes()

    for col in meta.get_all_line_names():
        unit: str = (meta.get_line_by_name(col).unit or "").strip()
        suffix_not_in_col_name: bool = all(suffix not in col for suffix in suffixes)
        unit_is_leistung_or_arbeit: bool = unit in (
            cont.ARBEIT_LEISTUNG.arbeit.possible_units
            + cont.ARBEIT_LEISTUNG.leistung.possible_units
        )
        if suffix_not_in_col_name and unit_is_leistung_or_arbeit:
            originla_type: Literal["Arbeit", "Leistung"] = (
                "Arbeit"
                if unit in cont.ARBEIT_LEISTUNG.arbeit.possible_units
                else "Leistung"
            )
            df, meta = insert_column_arbeit_leistung(originla_type, df, meta, col)
            df, meta = rename_column_arbeit_leistung(originla_type, df, meta, col)

            logger.success(f"Arbeit und Leistung für Spalte '{col}' aufgeteilt")

    return df, meta_units_update(meta)


def rename_column_arbeit_leistung(
    original_data_type: Literal["Arbeit", "Leistung"],
    df: pl.DataFrame,
    meta: cl.MetaData,
    col: str,
) -> tuple[pl.DataFrame, cl.MetaData]:
    """Wenn Daten als Arbeit oder Leistung in 15-Minuten-Auflösung
    vorliegen, wird die Originalspalte umbenannt (mit Suffix "Arbeit" oder "Leistung")
    und in den Metadaten ein Eintrag für den neuen Spaltennamen eingefügt.


    Args:
        - original_data_type (Literal['Arbeit', 'Leistung']):
            Sind die Daten "Arbeit" oder "Leistung"
        - df (DataFrame): DataFrame für neue Spalte
        - meta (MetaData): Metadaten
        - col (str): Name der (Original-) Spalte
    """
    new_name: str = f"{col}{cont.ARBEIT_LEISTUNG.get_suffix(original_data_type)}"
    df = df.rename({col: new_name})
    old_line: cl.MetaLine = meta.get_line_by_name(col)
    new_line: cl.MetaLine = cl.MetaLine(**vars(old_line))
    new_line.name = new_name
    new_line.tit = new_name
    meta.lines += [new_line]

    logger.info(f"Spalte '{col}' umbenannt in '{new_name}'")

    return df, meta


def insert_column_arbeit_leistung(
    original_data: Literal["Arbeit", "Leistung"],
    df: pl.DataFrame,
    meta: cl.MetaData,
    col: str,
) -> tuple[pl.DataFrame, cl.MetaData]:
    """Wenn Daten als Arbeit oder Leistung in 15-Minuten-Auflösung
    vorliegen, wird eine neue Spalte mit dem jeweils andern Typ eingefügt.


    Args:
        - original_data (Literal['Arbeit', 'Leistung']):
            Sind die Daten "Arbeit" oder "Leistung"
        - df (DataFrame): DataFrame für neue Spalte
        - meta (MetaData): Metadaten
        - col (str): Name der (Original-) Spalte
    """
    new_col_type: str = "Arbeit" if original_data == "Leistung" else "Leistung"
    new_col_name: str = f"{col}{cont.ARBEIT_LEISTUNG.get_suffix(new_col_type)}"
    old_line: cl.MetaLine = meta.get_line_by_name(col)
    new_line: cl.MetaLine = cl.MetaLine(**vars(old_line))
    new_line.name = new_col_name
    new_line.tit = new_col_name
    meta.lines += [new_line]

    if original_data == "Arbeit":
        df = df.with_columns((pl.col(col) * 4).alias(new_col_name))
        old_unit: str = old_line.unit or " kWh"
        new_unit: str = old_unit[:-1]
    else:
        df = df.with_columns((pl.col(col) / 4).alias(new_col_name))
        old_unit = old_line.unit or " kW"
        new_unit: str = f"{old_unit}h"

    meta.change_line_attribute(new_col_name, "unit", new_unit)
    logger.info(f"Spalte '{new_col_name}' mit Einheit '{new_unit}' eingefügt")

    return df, meta
