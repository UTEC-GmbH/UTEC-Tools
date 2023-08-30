# sourcery skip: avoid-global-variables, do-not-use-bare-except
# ruff: noqa: PD011
"""Rumprobieren"""


from datetime import datetime as dt
from typing import Any

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

discover: dict = DwdObservationRequest.discover()
all_parameters: dict[str, dict[str, Any]] = {}
for res, params in discover.items():
    for param in params:
        if not all_parameters.get(param):
            all_parameters[param] = {
                "name": param,
                "available_resolutions": [res],
                "unit": f" {discover[res][param].get('origin')}",
            }
        else:
            all_parameters[param]["available_resolutions"].append(res)

# selected_parameter: str = "radiation_global"
selected_parameter: str = "temperature_air_mean_200"

selected_res: str = "hourly"
start: dt = dt(2022, 1, 1, 0, 0)
end: dt = dt(2022, 12, 31, 23, 59)

lat_lon: tuple[float, float] = 53.0980433, 8.7747248

query = next(
    DwdObservationRequest(
        parameter=selected_parameter,
        resolution=selected_res,
        start_date=start,
        end_date=end,
        settings=WETTERDIENST_SETTINGS,
    )
    .filter_by_rank(lat_lon, 1)
    .values.query()
)

for param, par_dic in all_parameters.items():
    res_options: list[str] = par_dic["available_resolutions"]
    for res in res_options:
        try:
            query = next(
                DwdObservationRequest(
                    parameter=param,
                    resolution=res,
                    start_date=start,
                    end_date=end,
                    settings=WETTERDIENST_SETTINGS,
                )
                .filter_by_rank(lat_lon, 1)
                .values.query()
            )
        except:
            print(f"No values found for '{res}' resolution")
            res_options.remove(res)
