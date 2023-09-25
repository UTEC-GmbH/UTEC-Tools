"""Testing DWDParam"""

# ruff: noqa: PLR2004

import datetime as dt

import polars as pl

from modules import classes_data as cld
from modules import constants as cont

DISCOVER: dict = cld.DwdObservationRequest.discover()
ALL_PAR_DIC: dict = {
    par_name: {
        "available_resolutions": {
            res for res, par_dic in DISCOVER.items() if par_name in par_dic
        },
        "unit": " "
        + next(dic[par_name]["origin"] for dic in DISCOVER.values() if par_name in dic),
    }
    for par_name in {
        par
        for sublist in [list(dic.keys()) for dic in DISCOVER.values()]
        for par in sublist
    }
}


class TestDWDParamAirTemp:
    """Tests for DWDParam"""

    location = cld.Location("Bremen", 53.0758196, 8.8071646)
    time_span = cld.TimeSpan(
        dt.datetime(2017, 1, 1, 0, 0), dt.datetime(2019, 12, 31, 23, 59)
    )
    par = cld.DWDParam("temperature_air_mean_200", location, time_span)

    def test_init_with_valid_parameters(self) -> None:
        """Initialize DWDParam object with valid parameters"""
        par: cld.DWDParam = self.par
        assert par.name_en == "temperature_air_mean_200"
        assert par.name_de == "Lufttemperatur in 2 m Höhe"
        assert par.location == self.location
        assert par.time_span == self.time_span
        assert par.unit == " °C"
        assert par.available_resolutions == {
            "annual",
            "daily",
            "hourly",
            "minute_10",
            "monthly",
            "subdaily",
        }
        assert isinstance(par.resolutions, cld.DWDResolutions)

    def test_get_data_available_resolutions(self) -> None:
        """Get data for available resolutions"""

        par: cld.DWDParam = self.par
        par.fill_resolutions()

        assert len(par.resolutions.res_with_data()) == 4
        assert [res.name_en for res in par.resolutions.res_with_data()] == [
            "minute_10",
            "hourly",
            "daily",
            "monthly",
        ]

        for res in par.resolutions.res_with_data():
            assert isinstance(res.data, pl.DataFrame)
            assert isinstance(res.all_stations, pl.DataFrame)
            assert isinstance(res.closest_station, cld.DWDStation)
            assert res.no_data is None
            assert res.closest_station.name == "Bremen"
            assert res.closest_station.state == "Bremen"
            assert res.closest_station.station_id == "00691"
            assert res.data.height in [157543, 26280, 1095, 36]
            assert res.closest_station.distance < cont.DWD_QUERY_DISTANCE_LIMIT

        for res in [
            res
            for res in par.resolutions.res_without_data()
            if res.name_en in par.available_resolutions
        ]:
            assert isinstance(res.no_data, str)
            assert isinstance(res.data, pl.DataFrame)
            assert isinstance(res.closest_station, cld.DWDStation)
            assert res.data.height == 0
            assert res.closest_station.name == "unbekannt"
            assert res.closest_station.state == "unbekannt"
            assert res.closest_station.station_id == "unbekannt"


class TestDWDParamHumidity:
    """Tests for DWDParam"""

    location = cld.Location("Bremen", 53.0758196, 8.8071646)
    time_span = cld.TimeSpan(
        dt.datetime(2017, 1, 1, 0, 0), dt.datetime(2019, 12, 31, 23, 59)
    )
    par = cld.DWDParam("humidity", location, time_span)

    def test_init_with_valid_parameters(self) -> None:
        """Initialize DWDParam object with valid parameters"""
        par: cld.DWDParam = self.par
        assert par.name_en == "humidity"
        assert par.name_de == "Relative Luftfeuchte"
        assert par.location == self.location
        assert par.time_span == self.time_span
        assert par.unit == " pct"
        assert par.available_resolutions == {
            "daily",
            "hourly",
            "minute_10",
            "subdaily",
        }
        assert isinstance(par.resolutions, cld.DWDResolutions)

    def test_get_data_available_resolutions(self) -> None:
        """Get data for available resolutions"""

        par: cld.DWDParam = self.par
        par.fill_resolutions()

        assert len(par.resolutions.res_with_data()) == 4
        assert [res.name_en for res in par.resolutions.res_with_data()] == [
            "minute_10",
            "hourly",
            "daily",
        ]

        for res in par.resolutions.res_with_data():
            assert isinstance(res.data, pl.DataFrame)
            assert isinstance(res.all_stations, pl.DataFrame)
            assert isinstance(res.closest_station, cld.DWDStation)
            assert res.no_data is None
            assert res.closest_station.name == "Bremen"
            assert res.closest_station.state == "Bremen"
            assert res.closest_station.station_id == "00691"
            assert res.data.height in [157533, 26280, 1095]
            assert res.closest_station.distance < cont.DWD_QUERY_DISTANCE_LIMIT

        for res in [
            res
            for res in par.resolutions.res_without_data()
            if res.name_en in par.available_resolutions
        ]:
            assert isinstance(res.no_data, str)
            assert isinstance(res.data, pl.DataFrame)
            assert isinstance(res.closest_station, cld.DWDStation)
            assert res.data.height == 0
            assert res.closest_station.name == "unbekannt"
            assert res.closest_station.state == "unbekannt"
            assert res.closest_station.station_id == "unbekannt"


class TestDWDParamAllParameters:
    """Tests for DWDParam"""

    location = cld.Location("Bremen", 53.0758196, 8.8071646)
    time_span = cld.TimeSpan(
        dt.datetime(2017, 1, 1, 0, 0), dt.datetime(2019, 12, 31, 23, 59)
    )

    def test_all_parameters(self) -> None:
        """Stuff that should work with every parameter"""
        for par_name in [
            par
            for par in sorted(ALL_PAR_DIC.keys())
            if par
            not in [
                # "cloud_cover_layer1",
                # "cloud_cover_layer2",
                # "cloud_cover_layer3",
                # "cloud_cover_layer4",
                # "cloud_cover_total",
                "cloud_cover_total_index",
                # "cloud_density",
                # "cloud_height_layer1",
                # "cloud_height_layer2",
                # "cloud_height_layer3",
                # "cloud_height_layer4",
                # "cloud_type_layer1",
                # "cloud_type_layer2",
                # "cloud_type_layer3",
                # "cloud_type_layer4",
                # "count_weather_type_dew",
                # "count_weather_type_fog",
                # "count_weather_type_glaze",
                # "count_weather_type_hail",
                # "count_weather_type_ripe",
                # "count_weather_type_sleet",
                # "count_weather_type_storm_stormier_wind",
                # "count_weather_type_storm_strong_wind",
                # "count_weather_type_thunder",
                # "humidity",
                # "humidity_absolute",
                # "precipitation_duration",
                # "precipitation_form",
                # "precipitation_height",
                # "precipitation_height_droplet",
                # "precipitation_height_max",
                # "precipitation_height_rocker",
                # "precipitation_index",
                # "pressure_air_sea_level",
                # "pressure_air_site",
                # "pressure_vapor",
                # "radiation_global",
                # "radiation_sky_long_wave",
                # "radiation_sky_short_wave_diffuse",
                # "snow_depth",
                # "snow_depth_excelled",
                # "snow_depth_new",
                # "sun_zenith_angle",
                # "sunshine_duration",
                # "temperature_air_max_005",
                # "temperature_air_max_200",
                # "temperature_air_max_200_mean",
                # "temperature_air_mean_005",
                # "temperature_air_mean_200",
                # "temperature_air_min_005",
                # "temperature_air_min_200",
                # "temperature_air_min_200_mean",
                # "temperature_dew_point_mean_200",
                "temperature_soil_mean_002",
                "temperature_soil_mean_005",
                "temperature_soil_mean_010",
                "temperature_soil_mean_020",
                "temperature_soil_mean_050",
                "temperature_soil_mean_100",
                "temperature_wet_mean_200",
                "visibility_range",
                "visibility_range_index",
                "water_equivalent_snow_depth",
                "water_equivalent_snow_depth_excelled",
                "weather",
                # "wind_direction",
                # "wind_direction_gust_max",
                # "wind_force_beaufort",
                # "wind_gust_max",
                "wind_gust_max_last_3h",
                "wind_gust_max_last_6h",
                # "wind_speed",
                # "wind_speed_min",
                # "wind_speed_rolling_mean_max",
            ]
        ]:
            par = cld.DWDParam(par_name, self.location, self.time_span)
            par.fill_resolutions()

            assert par.name_en == par_name
            assert par.name_de == cont.DWD_TRANSLATION.get(par_name, "unbekannt")
            assert par.location == self.location
            assert par.time_span == self.time_span
            assert par.unit == ALL_PAR_DIC[par_name]["unit"]
            assert (
                par.available_resolutions
                == ALL_PAR_DIC[par_name]["available_resolutions"]
            )
            assert isinstance(par.resolutions, cld.DWDResolutions)

            for res in [
                getattr(par.resolutions, res)
                for res in par.resolutions.__dataclass_fields__
            ]:
                self.test_resolutions(res, par)

    def test_resolutions(self, res: cld.DWDResData, par: cld.DWDParam) -> None:
        """Test resolutions"""
        assert isinstance(res, cld.DWDResData)

        if res in par.resolutions.res_without_data():
            assert isinstance(res.no_data, str)
        else:
            assert isinstance(res.data, pl.DataFrame)
            assert isinstance(res.all_stations, pl.DataFrame)
            assert isinstance(res.closest_station, cld.DWDStation)
            assert res.no_data is None
            assert res.data.height > 0
            assert res.closest_station.station_id != "unbekannt"
            assert res.closest_station.name != "unbekannt"
            assert res.closest_station.state != "unbekannt"
            assert res.closest_station.distance < cont.DWD_QUERY_DISTANCE_LIMIT
