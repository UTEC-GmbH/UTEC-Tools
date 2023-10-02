"""Show stuff on maps"""

import os
from pathlib import Path
from zipfile import ZipFile

import fastkml as fk
import numpy as np
import plotly.graph_objects as go
import polars as pl
import pygeoif
from loguru import logger

from modules import classes_data as cld
from modules import classes_errors as cle
from modules import fig_formatting as fig_format
from modules import general_functions as gf
from modules import streamlit_functions as sf


def get_all_placemarkers_from_kmz_or_kml(
    file: str | None = None,
) -> list[fk.kml.Placemark]:
    """Get placemarkers data from a kmz-file"""
    file_in: str = file or "tests\\sample_data\\888 Standorte Gebäude.kmz"

    document: list = load_kmx_file(file_in)

    markers: list[fk.kml.Placemark] = []
    for feature in document:
        if isinstance(feature, fk.kml.Placemark):
            markers.append(feature)
        if isinstance(feature, fk.kml.Folder):
            markers.extend(
                feat
                for feat in list(feature.features())
                if isinstance(feat, fk.kml.Placemark)
            )
        if isinstance(feature, fk.kml.Document):
            for feat in list(feature.features()):
                if isinstance(feat, fk.kml.Placemark):
                    markers.append(feat)
                if isinstance(feat, fk.kml.Folder):
                    markers.extend(
                        feat_2
                        for feat_2 in list(feat.features())
                        if isinstance(feat_2, fk.kml.Placemark)
                    )
    if markers:
        logger.success(f"{len(markers)} placemarkers imported")
    else:
        logger.critical("No placemarkers found!")
        raise cle.NotFoundError(entry="placemarkers", where="file")
    return markers


def load_kmx_file(file: str) -> list:
    """Load a kmz or kml file"""

    if file.endswith(".kmz"):
        with ZipFile(file, "r") as kmz, kmz.open("doc.kml", "r") as kml:
            kml_string: bytes | str = kml.read()
    elif file.endswith(".kml"):
        kml_string = Path(file).read_text()
    else:
        raise FileNotFoundError

    k_cl = fk.kml.KML()
    k_cl.from_string(kml_string)

    return list(k_cl.features())


def list_or_df_of_locations_from_markers(
    markers: list[fk.kml.Placemark], *, as_df: bool = False
) -> list[cld.Location] | pl.DataFrame:
    """Get a list of coordinates from a list of kml-Placemarkers
    (only if the marker is a point)
    """
    if as_df:
        return pl.DataFrame(
            {
                "name": marker.name,
                "latitude": marker.geometry.y,
                "longitude": marker.geometry.x,
            }
            for marker in markers
            if isinstance(marker.geometry, pygeoif.geometry.Point)
        )
    return [
        cld.Location(
            name=marker.name, latitude=marker.geometry.y, longitude=marker.geometry.x
        )
        for marker in markers
        if isinstance(marker.geometry, pygeoif.geometry.Point)
    ]


# @gf.func_timer
# def geo_locate(address: str = "Bremen") -> geopy.Location:
#     """Retrieve the geographical coordinates (longitude and latitude)
#     of a given address using the Nominatim geocoding service.

#     Args:
#         - address (str): The address for which the coordinates are to be retrieved.

#     Returns:
#         - geopy.Location: The location object containing
#             the latitude and longitude of the provided address.
#     """

#     logger.info(f"Getting coordinates of '{address}'")

#     user_agent_secret: str | None = os.environ.get("GEO_USER_AGENT")
#     if user_agent_secret is None:
#         raise cle.NotFoundError(entry="GEO_USER_AGENT", where="Secrets")

#     geolocator: Nominatim = Nominatim(user_agent=user_agent_secret)

#     return geolocator.geocode(address)  # type: ignore


def build_hover_template() -> str:
    """Generate a hover template from the text input fields in the sidebar

    This function retrieves the values of several input fields from the sidebar and
    uses them to build a hover template string.
    The hover template defines the content and formatting of the hover tooltip
    that appears when hovering over data points on the plot.

    Returns:
        - str: The hover template string.
    """

    ref_size: str = sf.s_get("ti_ref_size") or ""
    ref_size_unit: str = sf.s_get("ti_ref_size_unit") or ""
    ref_col: str = sf.s_get("ti_ref_col") or ""
    ref_col_unit: str = sf.s_get("ti_ref_col_unit") or ""

    hover_parts: list[str] = ["<b>%{text}</b>"]

    if ref_size != "":
        hover_parts.append(f"<br>{ref_size.strip()}")
        if not sf.s_get("all_same_size"):
            hover_parts.extend((": ", "%{marker.size:,.1f}"))
    if ref_size_unit != "":
        if not ref_size:
            hover_parts.append("<br>")
            if not sf.s_get("all_same_size"):
                hover_parts.append("%{marker.size:,.1f}")
        hover_parts.append(f" {ref_size_unit.strip()}")

    if ref_col != "":
        hover_parts.append(f"<br>{ref_col.strip()}")
        if not sf.s_get("all_same_colour"):
            hover_parts.extend((": ", "%{marker.color:,.1f}"))
    if ref_col_unit != "":
        if not ref_col:
            hover_parts.append("<br>")
            if not sf.s_get("all_same_colour"):
                hover_parts.append("%{marker.color:,.1f}")
        hover_parts.append(f" {ref_col_unit.strip()}")

    hovertemplate: str = "".join(hover_parts)

    return f"{hovertemplate}<extra></extra>"


def get_zoom_level_from_locations(locations: list[cld.Location]) -> float:
    """Get the Zoom level to fit all points
    (Based on: https://stackoverflow.com/questions/63787612/plotly-automatic-zooming-for-mapbox-maps)
    """

    deg_to_km = 111  # constant to convert decimal degrees to kilometers
    factor = 14  # initial factor to manipulate

    if not all(
        [isinstance(locations, list)]
        + [isinstance(location, cld.Location) for location in locations]
    ):
        raise ValueError

    latitudes: list[float] = [
        loc.latitude for loc in locations if isinstance(loc.latitude, float)
    ]
    longitudes: list[float] = [
        loc.longitude for loc in locations if isinstance(loc.longitude, float)
    ]

    max_lat: float = max(latitudes)
    min_lat: float = min(latitudes)
    max_lon: float = max(longitudes)
    min_lon: float = min(longitudes)
    max_bound: float = max(abs(max_lat - min_lat), abs(max_lon - min_lon)) * deg_to_km

    return factor - np.log(max_bound)


@gf.func_timer
def create_list_of_locations_from_df(df: pl.DataFrame) -> list[cld.Location]:
    """From a DataFrame with the correct columns, create a list of locations"""

    col_nam: str = "Name"
    col_lat: str = "Breitengrad"
    col_lon: str = "Längengrad"
    col_adr: str = "Adresse"
    col_siz: str = "Punktgröße"
    col_col: str = "Punktfarbe"

    if all(col in df.columns for col in [col_lat, col_lon]):
        locations: list[cld.Location] = [
            cld.Location(
                name=row[col_nam],
                latitude=row[col_lat],
                longitude=row[col_lon],
                attr_size=row[col_siz] if col_siz in df.columns else None,
                attr_colour=row[col_col] if col_col in df.columns else None,
            )
            for row in df.iter_rows(named=True)
        ]

    elif "Adresse" in df.columns:
        locations = [
            cld.Location(
                name=row[col_nam],
                address=row[col_adr],
                attr_size=row[col_siz] if col_siz in df.columns else None,
                attr_colour=row[col_col] if col_col in df.columns else None,
            ).fill_using_geopy()
            for row in df.iter_rows(named=True)
        ]
    else:
        raise cle.WrongColumnNamesError(None)

    return locations


def marker_layout(locations: list[cld.Location]) -> dict:
    """Generate marker properties for a plot.

    Args:
        - locations (list[cld.Location]): A list of Location objects.

    Returns:
        - dict: A dictionary containing the properties for the markers,
            including size, color, opacity, and other settings.
    """
    # sourcery skip: move-assign
    min_size: float = 4
    max_size: float = sf.s_get("sl_marker_size") or 5
    standard_size: float = 4
    sizes: list[float | int] = [loc.attr_size or standard_size for loc in locations]
    size_ref: float = 2.0 * max(sizes) / (max_size**2)

    colours: list[float | int] = [loc.attr_colour or standard_size for loc in locations]
    ref_col: str = sf.s_get("ti_ref_col") or ""
    ref_col_unit: str = sf.s_get("ti_ref_col_unit") or ""

    all_same_size: bool = len(set(sizes)) == 1
    sf.s_set("all_same_size", all_same_size)

    all_same_colour: bool = len(set(colours)) == 1
    sf.s_set("all_same_colour", all_same_colour)

    if all_same_colour:
        colours = [sf.s_get("sl_marker_colour") or standard_size for _ in colours]
        col_scale: str | None = None
        col_bar: dict | None = None
        col_min: float | None = 1
        col_max: float | None = 100
    else:
        col_scale = sf.s_get("sb_col_scale") or "Portland"
        col_bar = {
            "title": (
                f"{ref_col.replace(' ', '<br>')}<br> ----- " if ref_col != "" else None
            ),
            "bgcolor": "rgba(255,255,255,0.5)",
            "ticksuffix": (f" {ref_col_unit.strip()}" if ref_col_unit != "" else None),
            "x": 0,
        }
        col_min = None
        col_max = None

    return {
        "allowoverlap": True,
        "size": sizes,
        "sizemode": "area",
        "sizemin": min_size,
        "sizeref": size_ref,
        "color": colours,
        "cmin": col_min,
        "cmax": col_max,
        "colorscale": col_scale,
        "colorbar": col_bar,
        "opacity": 0.8,
        "reversescale": False,
    }


def main_map_scatter(locations: list[cld.Location], **kwargs) -> go.Figure:
    """Karte

    kwargs:
        - title (str): Titel des Karte
        - height (int): Größe der Karte in px

    """

    if not all(
        [isinstance(locations, list)]
        + [isinstance(location, cld.Location) for location in locations]
    ):
        raise ValueError

    latitudes: list[float] = [
        loc.latitude for loc in locations if isinstance(loc.latitude, float)
    ]
    longitudes: list[float] = [
        loc.longitude for loc in locations if isinstance(loc.longitude, float)
    ]
    names: list[str] = [loc.name or "" for loc in locations]

    fig: go.Figure = go.Figure(
        data=go.Scattermapbox(
            lat=latitudes,
            lon=longitudes,
            text=names,
            mode="markers",
            marker=marker_layout(locations),
            hovertemplate=build_hover_template(),
            hoverlabel_align="right",
        )
    )

    return fig.update_layout(
        title=kwargs.get("title"),
        height=kwargs.get("height") or 750,
        autosize=True,
        showlegend=False,
        font_family="Arial",
        separators=",.",
        margin={"l": 5, "r": 5, "t": 30, "b": 5},
        mapbox={
            "accesstoken": os.getenv("MAPBOX_TOKEN"),
            "zoom": get_zoom_level_from_locations(locations),
            "center": {
                "lat": (max(latitudes) + min(latitudes)) / 2,
                "lon": (max(longitudes) + min(longitudes)) / 2,
            },
        },
    )


def html_exp(
    fig: go.Figure, f_pn: str = "export\\Kartografische_Datenauswertung.html"
) -> None:
    """html-Export"""

    if Path.exists(Path(f_pn)):
        Path.unlink(Path(f_pn))

    with open(f_pn, "w", encoding="utf-8") as fil:
        fil.write("<!DOCTYPE html>")
        fil.write("<title>Kartografische Datenauswertung</title>")
        fil.write("<head><style>")
        fil.write("h1{text-align: left; font-family: sans-serif;}")
        fil.write("body{width: 85%; margin-left:auto; margin-right:auto}")
        fil.write("</style></head>")
        fil.write('<body><h1><a href="https://www.utec-bremen.de/">')
        fil.write(sf.s_get("UTEC_logo") or gf.render_svg())
        fil.write("</a><br /><br />")
        fil.write("Kartografische Datenauswertung")
        fil.write("</h1><br /><hr><br /><br />")

        fil.write("<style>")
        fil.write("#map{width: 100%; margin-left:auto; margin-right:auto; }")
        fil.write("</style>")

        fil.write('<div id="map">')
        fil.write(
            fig.to_html(
                full_html=False,
                config=fig_format.plotly_config(height=1600, title_edit=False),
            )
        )

        fil.write("<br /><br /><hr><br /><br /><br /></div>")

        fil.write("</body></html>")
