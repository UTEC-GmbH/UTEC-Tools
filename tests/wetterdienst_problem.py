# sourcery skip: avoid-global-variables
"""Rumprobieren"""

from datetime import datetime as dt

import polars as pl
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

par_1: str = "temperature_air_mean_200"
par_2: str = "radiation_global"

res: str = "hourly"
start: dt = dt(2022, 1, 1, 0, 0)
end: dt = dt(2022, 12, 31, 23, 59)

latlon_bremen: tuple[float, float] = 53.0980433, 8.7747248

# request for temperature
request_1: DwdObservationRequest = DwdObservationRequest(
    parameter=par_1,
    resolution=res,
    start_date=start,
    end_date=end,
    settings=WETTERDIENST_SETTINGS,
)

# request for radiation
request_2: DwdObservationRequest = DwdObservationRequest(
    parameter=par_2,
    resolution=res,
    start_date=start,
    end_date=end,
    settings=WETTERDIENST_SETTINGS,
)

# get a DataFrame with all stations that have data with the given constraints
# (here: 502 stations for "temperature" and 42 stations for "radiation")
stations_with_data_1: pl.DataFrame = request_1.filter_by_distance(latlon_bremen, 500).df
stations_with_data_2: pl.DataFrame = request_2.filter_by_distance(latlon_bremen, 500).df

# get the station-id of the closest station that has data (here: "00691" for both)
closest_station_id_1: str = stations_with_data_1.row(0, named=True)["station_id"]
closest_station_id_2: str = stations_with_data_2.row(0, named=True)["station_id"]

# get the actual weather data from the closest station
# -> "temperature" works as expected, "radiation" raises TypeError:
# TypeError: argument 'length': 'Expr' object cannot be interpreted as an integer
values_1: pl.DataFrame = (
    request_1.filter_by_station_id(closest_station_id_1).values.all().df  # noqa: PD011
)
values_2: pl.DataFrame = (
    request_2.filter_by_station_id(closest_station_id_2).values.all().df  # noqa: PD011
)
