"""App Entry Point"""

import streamlit as st

from modules import constants as cont
from modules import general_functions as gf
from modules import setup_logger as slog
from modules import setup_stuff
from modules import streamlit_functions as sf

# logger setup and logging run
if sf.s_not_in("logger_setup"):
    slog.logger_setup()
gf.log_new_run()


# general page config (Favicon, etc.)
st.set_page_config(
    page_title="UTEC Online Tools",
    page_icon="logo/UTEC_logo.png",
    layout="wide",
)

if sf.s_not_in("initial_setup"):
    setup_stuff.general_setup()

st.navigation(
    {
        section: [
            st.Page(
                page=page.file,
                title=page.title,
                icon=page.icon,
                default=page.short == "login",
            )
            for page in cont.ST_PAGES.__dict__.values()
            if page.nav_section == section
        ]
        for section in cont.ST_PAGES.get_all_nav_sections()
    }
).run()
