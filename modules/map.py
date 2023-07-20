"""Show stuff on maps"""

import os
from pathlib import Path
from zipfile import ZipFile

import fastkml as fk
import geopy
import plotly.graph_objects as go
import polars as pl
import pygeoif
from geopy.geocoders import Nominatim
from loguru import logger

from modules import classes_data as cld
from modules import classes_errors as cle
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


def main_map(locations: list[cld.Location], **kwargs) -> go.Figure:
    """Karte"""
    # hov_temp: str = "%{text}<br><i>(Wetterstation)</i><extra></extra>"

    fig: go.Figure = go.Figure(
        data=go.Scattermapbox(
            lat=[loc.latitude for loc in locations],
            lon=[loc.longitude for loc in locations],
            text=[loc.name for loc in locations],
            mode="markers",
            marker={
                "size": 4,
                "color": "blue",
                # "colorscale": "Portland",  # Blackbody,Bluered,Blues,Cividis,Earth,
                #   Electric,Greens,Greys,Hot,Jet,Picnic,Portland,
                #   Rainbow,RdBu,Reds,Viridis,YlGnBu,YlOrRd
                # "colorbar": {
                #     "title": "Entfernung<br>DWD-Station<br>Adresse<br> ----- ",
                #     "bgcolor": "rgba(255,255,255,0.5)",
                #     "ticksuffix": " km",
                #     "x": 0,
                # },
                # "opacity": 0.5,
                # "reversescale": True,
                # "cmax": 400,
                # "cmin": 0,
            },
            # hovertemplate=hov_temp,
        )
    )

    return fig.update_layout(
        title=kwargs.get("title"),
        autosize=True,
        showlegend=False,
        font_family="Arial",
        separators=",.",
        margin={"l": 5, "r": 5, "t": 30, "b": 5},
        mapbox={
            "accesstoken": os.getenv("MAPBOX_TOKEN"),
            "zoom": kwargs.get("zoom") or 3,
            "center": {
                "lat": 53.519,
                "lon": 8.579,
            },
        },
    )
