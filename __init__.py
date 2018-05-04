# this file is here to make the external plugins of this repo available from the pcbnew menu.

import pcbnew

print("initializing mmccoo_kicad")

import gen_border
import dxf_stuff
import place_by_sch
import instantiate_footprint
import toggle_visibility
import ratnest
import utils

print("done adding mmccoo_kicad")
