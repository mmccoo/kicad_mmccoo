# this file is here to make the external plugins of this repo available from the pcbnew menu.

import pcbnew

print("initializing mmccoo_kicad")

import gen_border
from . import dxf_stuff
from . import place_by_sch
from . import instantiate_footprint
from . import toggle_visibility

print("done adding mmccoo_kicad")
