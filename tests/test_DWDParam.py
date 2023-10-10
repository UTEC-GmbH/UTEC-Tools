"""Testing DWDParam"""

# ruff: noqa: PLR2004

import datetime as dt

import polars as pl
import pytest

from modules import classes_data as cld
from modules import constants as cont

LOCATION = cld.Location("Bremen").fill_using_geopy()
TIME_SPAN = cld.TimeSpan(
    dt.datetime(2017, 1, 1, 0, 0), dt.datetime(2019, 12, 31, 23, 59)
)

PARS_TO_TEST: set[str] = cont.DWD_GOOD_PARAMS  # set(DWD_ALL_PAR_DIC)
BAD_PARS: set[str] = set(cont.DWD_PROBLEMATIC_PARAMS)

PARS_TO_TEST_CLOUD: set[str] = {par for par in PARS_TO_TEST if "cloud" in par}
PARS_TO_TEST_COUNT: set[str] = {par for par in PARS_TO_TEST if "count" in par}
PARS_TO_TEST_TEMP: set[str] = {par for par in PARS_TO_TEST if "temperature" in par}
PARS_TO_TEST_HUM_PRE: set[str] = {
    par
    for par in PARS_TO_TEST
    if any(var in par for var in ["humidity", "precipitation"])
}
PARS_TO_TEST_PRES_RAD: set[str] = {
    par for par in PARS_TO_TEST if any(var in par for var in ["pressure", "radiation"])
}
PARS_TO_TEST_SNOW_SUN: set[str] = {
    par for par in PARS_TO_TEST if any(var in par for var in ["snow", "sun"])
}
PARS_TO_TEST_REST: set[str] = {
    par
    for par in PARS_TO_TEST
    if par
    not in (
        *PARS_TO_TEST_CLOUD,
        *PARS_TO_TEST_COUNT,
        *PARS_TO_TEST_TEMP,
        *PARS_TO_TEST_HUM_PRE,
        *PARS_TO_TEST_PRES_RAD,
        *PARS_TO_TEST_SNOW_SUN,
    )
}


def general_assumptions_param(par: cld.DWDParam, par_name: str) -> None:
    """Test parameter"""
    assert par.name_en == par_name
    assert par.name_de == cont.DWD_PARAM_TRANSLATION.get(par_name, par.name_en)
    assert par.location == LOCATION
    assert par.time_span == TIME_SPAN
    assert par.unit == cont.DWD_ALL_PAR_DIC[par_name]["unit"]
    assert (
        par.available_resolutions
        == cont.DWD_ALL_PAR_DIC[par_name]["available_resolutions"]
    )
    assert isinstance(par.resolutions, cld.DWDResolutions)


def general_assumptions_res_with_data(res: cld.DWDResData) -> None:
    """Test resolution with data"""
    default_station = cld.DWDStation()
    assert isinstance(res.data, pl.DataFrame)
    assert isinstance(res.all_stations, pl.DataFrame)
    assert isinstance(res.closest_station, cld.DWDStation)
    assert res.no_data is None
    assert res.data.height > 0
    assert res.closest_station.station_id != default_station.station_id
    assert res.closest_station.name != default_station.name
    assert res.closest_station.state != default_station.state
    assert res.closest_station.distance < cont.DWD_QUERY_DISTANCE_LIMIT


class TestDWDParamAirTemp:
    """Tests for DWDParam"""

    location: cld.Location = LOCATION
    time_span: cld.TimeSpan = TIME_SPAN

    par = cld.DWDParam("temperature_air_mean_200", location, time_span)

    def test_init_with_valid_parameters(self) -> None:
        """Initialize DWDParam object with valid parameters"""
        par: cld.DWDParam = self.par
        if par.name_en in cont.DWD_PROBLEMATIC_PARAMS:
            return

        assert par.name_en == "temperature_air_mean_200"
        assert par.name_de == "Lufttemperatur"
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
        par.fill_all_resolutions()

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

    location: cld.Location = LOCATION
    time_span: cld.TimeSpan = TIME_SPAN
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
        if par.name_en in cont.DWD_PROBLEMATIC_PARAMS:
            return

        par.fill_all_resolutions()

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


class TestBadPars:
    """Testing the problematic parameters"""

    @pytest.mark.parametrize("par_name", BAD_PARS)
    def test_bad(self, par_name: str) -> None:
        """Tests for parameters in group"""
        self.run_tests(par_name)

    def run_tests(self, par_name: str) -> None:
        """Run Test"""

        par = cld.DWDParam(par_name, LOCATION, TIME_SPAN)
        par.fill_all_resolutions()

        general_assumptions_param(par, par_name)

        for res in (
            getattr(par.resolutions, res)
            for res in par.resolutions.__dataclass_fields__
        ):
            assert isinstance(res, cld.DWDResData)

            if res in par.resolutions.res_with_data():
                general_assumptions_res_with_data(res)
            else:
                assert isinstance(res.no_data, str)


class TestInGroups:
    """Testing multiple parameters at a time in groups"""

    @pytest.mark.parametrize("par_name", PARS_TO_TEST_CLOUD)
    def test_cloud(self, par_name: str) -> None:
        """Tests for parameters in group"""
        self.run_tests(par_name)

    @pytest.mark.parametrize("par_name", PARS_TO_TEST_COUNT)
    def test_count(self, par_name: str) -> None:
        """Tests for parameters in group"""
        self.run_tests(par_name)

    @pytest.mark.parametrize("par_name", PARS_TO_TEST_TEMP)
    def test_temperature(self, par_name: str) -> None:
        """Tests for parameters in group"""
        self.run_tests(par_name)

    @pytest.mark.parametrize("par_name", PARS_TO_TEST_HUM_PRE)
    def test_humiditiy_presipitation(self, par_name: str) -> None:
        """Tests for parameters in group"""
        self.run_tests(par_name)

    @pytest.mark.parametrize("par_name", PARS_TO_TEST_PRES_RAD)
    def test_pressure_radiation(self, par_name: str) -> None:
        """Tests for parameters in group"""
        self.run_tests(par_name)

    @pytest.mark.parametrize("par_name", PARS_TO_TEST_SNOW_SUN)
    def test_snow_sunshine(self, par_name: str) -> None:
        """Tests for parameters in group"""
        self.run_tests(par_name)

    @pytest.mark.parametrize("par_name", PARS_TO_TEST_REST)
    def test_rest(self, par_name: str) -> None:
        """Tests for parameters in group"""
        self.run_tests(par_name)

    def run_tests(self, par_name: str) -> None:
        """Run Test"""

        par = cld.DWDParam(par_name, LOCATION, TIME_SPAN)
        par.fill_all_resolutions()

        general_assumptions_param(par, par_name)

        for res in (
            getattr(par.resolutions, res)
            for res in par.resolutions.__dataclass_fields__
        ):
            assert isinstance(res, cld.DWDResData)

            if res in par.resolutions.res_with_data():
                general_assumptions_res_with_data(res)
            else:
                assert isinstance(res.no_data, str)
