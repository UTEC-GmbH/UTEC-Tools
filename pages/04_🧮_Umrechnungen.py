# sourcery skip: avoid-global-variables
"""Convert Time Series"""

from modules import constants as cont
from modules import general_functions as gf
from modules import setup_stuff as set_stuff

# setup stuff
gf.log_new_run()
set_stuff.page_header_setup(page=cont.ST_PAGES.conv.short)
