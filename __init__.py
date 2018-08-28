# this file is here to make the external plugins of this repo available from the pcbnew menu.
# to make these plugins available in your kicad, you'll need to have then be available here:
# ~/ubuntu/.kicad_plugins/
#in other worked ~/ubuntu/.kicad_plugins/kicad_mmccooo

# for these particular plugins, you'll need dxfgrabber, numpy, scipy, shapely.
# note that kicad is still on python 2.7.
# sudo python2.7 -m ensurepip --default-pip
#  or
# sudo apt install python-pip


# sudo pip2 install --upgrade pip
# sudo pip2 install dxfgrabber
# sudo pip2 install numpy
# sudo pip2 install scipy
# sudo pip2 install shapely

import pcbnew

print("initializing mmccoo_kicad")

import gen_border
import dxf_stuff
import place_by_sch
import instantiate_footprint
import toggle_visibility
import ratnest
import utils
import svg2border
print("done adding mmccoo_kicad")
