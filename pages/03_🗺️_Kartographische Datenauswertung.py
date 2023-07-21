# sourcery skip: avoid-global-variables
"""Show stuff on a map"""


import fastkml as fk
import polars as pl
import streamlit as st

from modules import classes_data as cld
from modules import constants as cont
from modules import excel_import as ex_i
from modules import fig_formatting as fig_format
from modules import general_functions as gf
from modules import map as mp
from modules import setup_stuff as set_stuff
from modules import streamlit_functions as sf
from modules import user_authentication as uauth

# setup stuff
gf.log_new_run()
set_stuff.page_header_setup(page=cont.ST_PAGES.maps.short)

if uauth.authentication(sf.s_get("page")):
    locations: pl.DataFrame = ex_i.general_excel_import(
        file="tests/sample_data/888 PV-Potenzial py.xlsx", worksheet="Leistungen"
    )
    # markers: list[fk.kml.Placemark] = mp.get_all_placemarkers_from_kmz_or_kml()
    # locations: list[cld.Location] = mp.list_or_df_of_locations_from_markers(markers)
    st.plotly_chart(
        mp.main_map(locations, zoom=12),
        use_container_width=True,
        theme=cont.ST_PLOTLY_THEME,
        config=fig_format.plotly_config(height=1600, title_edit=False),
    )
