
import sys,inspect,os
oldpath = sys.path
# inspect.stack()[0][1] is the full path to the current file.
sys.path.insert(0, os.path.dirname(inspect.stack()[0][1]))
import bulge
import pcbpoint
sys.path = oldpath

from dxf_utils import traverse_dxf
from dxf_utils import traverse_graphics
from dxf_utils import segment_actions
from dxf_utils import mounting_actions
from dxf_utils import orient_actions
from dxf_utils import zone_actions


import pcbnew
import re


#graphic_actions has callback to just print what's there
#traverse_dxf("/bubba/electronicsDS/fusion/powerrails.dxf", graphic_actions(True))

# segment actions has callbacks to create graphic polys
board = pcbnew.GetBoard()
# generate a name->layer table so we can lookup layer numbers by name.
layertable = {}
numlayers = pcbnew.PCB_LAYER_ID_COUNT
for i in range(numlayers):
    layertable[pcbnew.GetBoard().GetLayerName(i)] = i

shape_table = {}
for s in filter(lambda s: re.match("S_.*", s), dir(pcbnew)):
    shape_table[getattr(pcbnew, s)] = s


    
#traverse_dxf("/bubba/electronicsDS/fusion/powerrails.dxf",
#             segment_actions(board, layertable['Eco1.User']))
#traverse_dxf("/bubba/electronicsDS/fusion/powerrails.dxf",
#             graphic_actions(True),
#             merge_polys=True)


if (0):
    traverse_dxf("/bubba/electronicsDS/fusion/leds_projection.dxf",
                 segment_actions(board, layertable['Cmts.User']),
                 merge_polys=True,
                 break_curves=True)


if (0):
    if (1):
        traverse_graphics(board, 'Cmts.User',
                 orient_actions(board, "LED_5730"),
                 merge_polys=True,
                 break_curves=True)
    else:
        traverse_dxf("/bubba/electronicsDS/fusion/leds_projection.dxf",
                     orient_actions(board, "LED_5730"),
                     merge_polys=True,
                     break_curves=True)



    



powerlayer = layertable["B.Cu"]
# find a power net to add the zone to.
powernet = None
nets = board.GetNetsByName()
for name in ["+12V", "+5V", "GND"]:
    if (nets.has_key(name)):
        powernet = nets[name]

if (0):
    traverse_dxf("/bubba/electronicsDS/fusion/powerrails.dxf",
                 zone_actions(board, powernet, layertable["B.Cu"]),
                 merge_polys=True,
                 break_curves=True
    )

if (0):
    traverse_dxf("/bubba/electronicsDS/fusion/cross_rails.dxf",
                 zone_actions(board, powernet, layertable["F.Cu"]),
                 merge_polys=True,
                 break_curves=True
    )

if (0):
    traverse_dxf("/bubba/electronicsDS/fusion/powerrails.dxf",
                 segment_actions(board, layertable['Eco1.User']),
                 merge_polys=True,
                 break_curves=True
    )

    
if (0):
    traverse_dxf("/bubba/electronicsDS/fusion/boundary.dxf",
                 segment_actions(board, layertable['Edge.Cuts']),
                 merge_polys=False,
                 break_curves=True)

footprint_lib = '/home/mmccoo/kicad/kicad-footprints/MountingHole.pretty'
testpad_lib   = '/home/mmccoo/kicad/kicad-footprints/TestPoint.pretty/'
footprint_mapping = {
    "3.0": (footprint_lib, "MountingHole_3.2mm_M3")
}

if (1):
    traverse_dxf("/bubba/electronicsDS/fusion/mountingholes.dxf",
                 mounting_actions(board,
                                  footprint_mapping,
                                  clearance=pcbnew.Millimeter2iu(1)
                 ))

if (1):
    traverse_dxf("/bubba/electronicsDS/fusion/mountingholes.dxf",
                 mounting_actions(board, 
                                  {"2.5": (testpad_lib,   "TestPoint_Pad_D2.5mm")},
                                  flip=True))
    traverse_dxf("/bubba/electronicsDS/fusion/mountingholes.dxf",
                 mounting_actions(board,
                                  {"2.5": (testpad_lib,   "TestPoint_Pad_D2.5mm")}))
    

if (0):
    traverse_graphics(board, "B.SilkS",
                      segment_actions(board, layertable['Cmts.User']),
                      merge_polys=True,
                      break_curves=True)


if (0):
    traverse_dxf("/bubba/electronicsDS/fusion/powerrails.dxf",
                 segment_actions(board, layertable['B.SilkS']),
                 merge_polys=False,
                 break_curves=True
    )

if (0):
    traverse_dxf("/bubba/electronicsDS/fusion/solder_mask.dxf",
                 segment_actions(board, layertable['F.Mask']),
                 merge_polys=True,
                 break_curves=True
    )
    traverse_dxf("/bubba/electronicsDS/fusion/solder_mask.dxf",
                 segment_actions(board, layertable['B.Mask']),
                 merge_polys=True,
                 break_curves=True
    )

    
pcbnew.Refresh()

