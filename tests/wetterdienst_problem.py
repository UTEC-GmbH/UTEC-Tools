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

# selected_parameter: str = "radiation_global"
selected_parameter: str = "temperature_air_mean_200"

res: str = "hourly"
start: dt = dt(2022, 1, 1, 0, 0)
end: dt = dt(2022, 12, 31, 23, 59)

lat_lon: tuple[float, float] = 53.0980433, 8.7747248

request: DwdObservationRequest = DwdObservationRequest(
    parameter=selected_parameter,
    resolution=res,
    start_date=start,
    end_date=end,
    settings=WETTERDIENST_SETTINGS,
)

all_stations_by_distance = request.filter_by_rank(lat_lon, 1)

all_stations_by_distance_df = all_stations_by_distance.df

values = all_stations_by_distance.values.all()  # noqa: PD011

stations_with_data = values.df_stations
weather_data = values.df
