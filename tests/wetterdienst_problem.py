"""Rumprobieren"""

# ruff: noqa: E722, PD011, PERF203
# pylint: disable=W0702,W0621
# sourcery skip: avoid-global-variables, do-not-use-bare-except, name-type-suffix


import datetime as dt

from wetterdienst import Settings
from wetterdienst.provider.dwd.observation import DwdObservationRequest

WETTERDIENST_SETTINGS = Settings(
    ts_shape="long",
    ts_si_units=False,
    ts_skip_empty=True,
    ts_skip_threshold=0.90,
    ts_skip_criteria="min",
    ts_dropna=True,
    ignore_env=True,
)

start: dt.datetime = dt.datetime(2022, 1, 1, 0, 0)
end: dt.datetime = dt.datetime(2022, 12, 31, 23, 59)
lat_lon: tuple[float, float] = 53.0980433, 8.7747248
selected_resolution: str = "hourly"

problematic_parameters: list[str] = [
    "cloud_cover_total_index",
    "temperature_soil_mean_100",
    "visibility_range_index",
    "water_equivalent_snow_depth",
    "water_equivalent_snow_depth_excelled",
    "wind_direction_gust_max",
    "wind_force_beaufort",
    "wind_gust_max_last_3h",
    "wind_gust_max_last_6h",
    "wind_speed_min",
    "wind_speed_rolling_mean_max",
]


for selected_parameter in problematic_parameters:
    print(f"trying parameter '{selected_parameter}'...")

    request = DwdObservationRequest(
        parameter=selected_parameter,
        resolution=selected_resolution,
        start_date=start,
        end_date=end,
        settings=WETTERDIENST_SETTINGS,
    )

    try:
        filtered = request.filter_by_rank(latlon=lat_lon, rank=1)
        values = next(filtered.values.query())
        print(f"'{selected_parameter}' works.\n")
    except:
        print(f"'!!! {selected_parameter}' throws error !!!\n")
