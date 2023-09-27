"""Rumprobieren"""

# ruff: noqa: E722, PD011, PERF203, T201, BLE001
# pylint: disable=W0702,W0621,W0718
# sourcery skip: avoid-global-variables, do-not-use-bare-except,
# sourcery skip: name-type-suffix, flag-print


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
]


for selected_parameter in problematic_parameters:
    availabel_resolutions: set[str] = {
        res
        for res, par_dic in DwdObservationRequest.discover().items()
        if selected_parameter in par_dic
    }
    print(f"\n'{selected_parameter}' | '{availabel_resolutions}'...")

    for res in availabel_resolutions:
        try:
            request = DwdObservationRequest(
                parameter=selected_parameter,
                resolution=res,
                start_date=start,
                end_date=end,
                settings=WETTERDIENST_SETTINGS,
            )
            filtered = request.filter_by_rank(latlon=lat_lon, rank=1)
            values = next(filtered.values.query())
            print(f"Resolution: '{res}': 👍 No Error 👍")

        except Exception as error:
            print(f"Resolution: '{res}': 🐞 ERROR: '{error}' 🐞")
