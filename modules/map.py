"""Show stuff on maps"""

import os
from pathlib import Path
from zipfile import ZipFile

import fastkml as fk
import geopy
import numpy as np
import plotly.graph_objects as go
import polars as pl
import pygeoif
from geopy.geocoders import Nominatim
from loguru import logger

from modules import classes_data as cld
from modules import classes_errors as cle
from modules import excel_import as exi
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


def geo_locate(address: str = "Bremen") -> geopy.Location:
    """Geographische daten (Längengrad, Breitengrad) aus eingegebener Adresse"""

    user_agent_secret: str | None = os.environ.get("GEO_USER_AGENT") or "lasinludwig"
    if user_agent_secret is None:
        raise cle.NotFoundError(entry="GEO_USER_AGENT", where="Secrets")

    geolocator: Nominatim = Nominatim(user_agent=user_agent_secret)
    location: geopy.Location = geolocator.geocode(address)  # type: ignore

    sf.s_set("geo_location", location)

    return location


def get_hover_template_from_kwargs(given_kwargs: dict) -> str:
    """Get a hover template from given kwargs"""

    hovertemplate: str = "<b>%{text}</b>"

    if "ref_size" in given_kwargs and "ref_size_unit" in given_kwargs:
        hovertemplate = (
            f"{hovertemplate}<br>"
            f"{given_kwargs.get('ref_size')}: "
            "%{marker.size:,.1f}"
            f" {str(given_kwargs.get('ref_size_unit')).strip()}"
        )

    if "ref_col" in given_kwargs and "ref_col_unit" in given_kwargs:
        hovertemplate = (
            f"{hovertemplate}<br>"
            f"{given_kwargs.get('ref_col')}: "
            "%{marker.color:,.1f}"
            f" {str(given_kwargs.get('ref_col_unit')).strip()}"
        )

    return f"{hovertemplate}<extra></extra>"


def get_zoom_level_from_locations(
    locations: list[cld.Location] | pl.DataFrame, **kwargs
) -> float:
    """Get the Zoom level to fit all points
    (Based on: https://stackoverflow.com/questions/63787612/plotly-automatic-zooming-for-mapbox-maps)
    """

    deg_to_km = 111  # constant to convert decimal degrees to kilometers
    factor = 14  # initial factor to manipulate

    if isinstance(locations, pl.DataFrame):
        latitudes: list[float] = list(locations[kwargs.get("col_lat") or "Breitengrad"])
        longitudes: list[float] = list(locations[kwargs.get("col_lon") or "Längengrad"])

    elif all(
        [isinstance(locations, list)]
        + [isinstance(location, cld.Location) for location in locations]
    ):
        latitudes = [loc.latitude for loc in locations]
        longitudes = [loc.longitude for loc in locations]

    else:
        raise ValueError

    max_lat: float = max(latitudes)
    min_lat: float = min(latitudes)
    max_lon: float = max(longitudes)
    min_lon: float = min(longitudes)
    max_bound: float = max(abs(max_lat - min_lat), abs(max_lon - min_lon)) * deg_to_km

    return factor - np.log(max_bound)


def main_map_scatter(
    locations: list[cld.Location] | pl.DataFrame, **kwargs
) -> go.Figure:
    """Karte

    kwargs:
        - col_name (str): Spaltenüberschrift für Bezeichnung (Name) des Datenpunkts
        - col_lat (str): Spaltenüberschrift für Breitengrad
        - col_lon (str): Spaltenüberschrift für Längengrad
        - col_size (str): Spaltenüberschrift für Punktgröße
        - col_col (str): Spaltenüberschrift für Punktfarbe

        - ref_size (str): Bezugsgröße für Punktgröße (z.B. "Leistung")
        - ref_size_unit (str): Einheit der Bezugsgröße für Punktgröße (z.B. "kWp")
        - ref_col (str): Bezugsgröße für Punktfarbe (z.B. "spezifische Leistung")
        - ref_col_unit (str): Einheit der Bezugsgröße für Punktfarbe (z.B. "kWh/kWp")

        - title (str): Titel des Karte
        - height (int): Größe der Karte in px
        - zoom (int): Zoomfaktor beim ersten Anzeigen der Karte

    DataFrame and Figure from Example File:
        df=exi.general_excel_import(file="example_map/Punkte_Längengrad_Breitengrad.xlsx")
        fig = main_map_scatter(
            locations=df,
            ref_size="Leistung",
            ref_size_unit="kWp",
            ref_col="spezifisch",
            ref_col_unit="kWh/kWp",
            title=(
                "PV-Potenzial Fischereihafen"
                '<i><span style="font-size: 12px;">'
                " (Punktgröße referenziert Leistungspotenzial)</span></i>"
            )
        )

    Show Fig in VSCode (interactive window):
        fig.show(renderer="notebook_connected")

    """

    standard_size: float = 4

    if isinstance(locations, pl.DataFrame):
        latitudes: list[float] = list(locations[kwargs.get("col_lat") or "Breitengrad"])
        longitudes: list[float] = list(locations[kwargs.get("col_lon") or "Längengrad"])
        names: list[str] = list(locations[kwargs.get("col_name") or "Name"])
        sizes: list[float] = list(locations[kwargs.get("col_size") or "Punktgröße"])
        colours: list[float] = list(locations[kwargs.get("col_col") or "Punktfarbe"])
    elif all(
        [isinstance(locations, list)]
        + [isinstance(location, cld.Location) for location in locations]
    ):
        latitudes = [loc.latitude for loc in locations]
        longitudes = [loc.longitude for loc in locations]
        names = [loc.name or "" for loc in locations]
        sizes = [loc.attr_size or standard_size for loc in locations]
        colours = [loc.attr_colour or standard_size for loc in locations]
    else:
        raise ValueError

    fig: go.Figure = go.Figure(
        data=go.Scattermapbox(
            lat=latitudes,
            lon=longitudes,
            text=names,
            mode="markers",
            marker={
                "size": sizes,
                "sizemin": standard_size,
                "sizeref": max(sizes) / 50,
                "color": colours,
                "colorscale": "Portland",  # Blackbody,Bluered,Blues,Cividis,Earth,
                #   Electric,Greens,Greys,Hot,Jet,Picnic,Portland,
                #   Rainbow,RdBu,Reds,Viridis,YlGnBu,YlOrRd
                "colorbar": {
                    "title": (
                        f"{str(kwargs.get('ref_col')).replace(' ', '<br>')}<br> ----- "
                        if kwargs.get("ref_col")
                        else None
                    ),
                    "bgcolor": "rgba(255,255,255,0.5)",
                    "ticksuffix": (
                        f" {str(kwargs.get('ref_col_unit')).strip()}"
                        if kwargs.get("ref_col_unit")
                        else None
                    ),
                    "x": 0,
                },
                "opacity": 0.8,
                "reversescale": False,
                # "cmax": 400,
                # "cmin": 0,
            },
            hovertemplate=get_hover_template_from_kwargs(kwargs),
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
