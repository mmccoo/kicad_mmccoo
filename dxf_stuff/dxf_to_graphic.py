

# http://pythonhosted.org/dxfgrabber/#dxfgrabber

import pcbnew
import dxfgrabber
import re
import sys, os.path, inspect
import numpy as np

oldpath = sys.path
# inspect.stack()[0][1] is the full path to the current file.
sys.path.insert(0, os.path.dirname(inspect.stack()[0][1]))
import bulge
import pcbpoint
sys.path = oldpath


# the internal coorinate space of pcbnew is 10E-6 mm. (a millionth of a mm)
# the coordinate 121550000 corresponds to 121.550000 
SCALE = 1000000.0
    


type_table = {}
for t in filter(lambda t: re.match("PCB_.*_T", t), dir(pcbnew)):
    type_table[getattr(pcbnew, t)] = t

shape_table = {}
for s in filter(lambda s: re.match("S_.*", s), dir(pcbnew)):
    shape_table[getattr(pcbnew, s)] = s

# generate a name->layer table so we can lookup layer numbers by name.
layertable = {}
numlayers = pcbnew.PCB_LAYER_ID_COUNT
for i in range(numlayers):
    layertable[pcbnew.GetBoard().GetLayerName(i)] = i

    
def print_current_graphics():    
    # to get information about current graphics
    for d in board.GetDrawings():
        if (d.Type() == pcbnew.PCB_LINE_T):
            # this type is DRAWSEGMENT in pcbnew/class_drawsegment.h
            # the different shape types are defined in class_board_item.h enum STROKE_T
            print("line shape {}".format(shape_table[d.GetShape()]))



# this is sample code for adding a polygon. The downside of polygons is they are filled.
# bummer
# the internal coorinate space of pcbnew is 10E-6 mm. (a millionth of a mm)
# the coordinate 121550000 corresponds to 121.550000 
# SCALE = 1000000.0
# seg = pcbnew.DRAWSEGMENT(board)
# seg.SetLayer(44)
# seg.SetShape(pcbnew.S_POLYGON)
# sps = seg.GetPolyShape()

# o = sps.NewOutline()
# sps.Append(int(10.0*SCALE),int(10.0*SCALE), o)
# sps.Append(int(10.0*SCALE),int(20.0*SCALE), o)
# sps.Append(int(20.0*SCALE),int(20.0*SCALE), o)
# sps.Append(int(20.0*SCALE),int(10.0*SCALE), o)
# board.Add(seg)



        
def dxfarc2pcbarc(board, layer, center, radius, startangle, endangle):
    # dxf arcs are different from pcbnew arcs
    # dxf arcs have a center point, radius and start/stop angles
    # pcbnew arcs have a center pointer, radius, and a start point, angle (counter clockwise)

    seg = pcbnew.DRAWSEGMENT(board)
    seg.SetLayer(layer)
    seg.SetShape(pcbnew.S_ARC)
    seg.SetCenter(center.wxpoint())
    # need negative angles because pcbnew flips over x axis
    sa, ea = (min(-startangle, -endangle), max(-startangle, -endangle))
    
    seg.SetArcStart((center + pcbpoint.pcbpoint(radius*np.cos(np.deg2rad(startangle)),
                                                radius*np.sin(np.deg2rad(startangle)))).wxpoint())
    # y axis is flipped, so negative angles
    seg.SetAngle((-endangle+startangle)*10)
    board.Add(seg)


def dxf_to_graphic(board, layer, filepath, singlepoly=False):

    dxf = dxfgrabber.readfile(filepath)

    layer_count = len(dxf.layers) # collection of layer definitions
    block_definition_count = len(dxf.blocks) #  dict like collection of block definitions
    entity_count = len(dxf.entities) # list like collection of entities
    print("layers: {}".format(layer_count))
    print("blocks: {}".format(block_definition_count))
    print("entities:{}".format(entity_count))

    
    for e in dxf.entities.get_entities():
        
        if (e.dxftype == "LINE"):
            seg = pcbnew.DRAWSEGMENT(board)
            seg.SetLayer(layer)
            seg.SetShape(pcbnew.S_SEGMENT)
            seg.SetStart(pcbpoint.pcbpoint(e.start).wxpoint())
            seg.SetEnd(pcbpoint.pcbpoint(e.end).wxpoint())
            board.Add(seg)
        
        if (e.dxftype == "CIRCLE"):
            print("center {} radius {}".format(e.center, e.radius))
            
        if (e.dxftype == "ARC"):
            # dxf arcs are different from pcbnew arcs
            # dxf arcs have a center point, radius and start/stop angles
            # pcbnew arcs have a center pointer, radius, and a start point,
            # angle (counter clockwise)

            dxfarc2pcbarc(board, layer,
                          pcbpoint.pcbpoint(e.center),
                          e.radius, e.start_angle, e.end_angle)

        if (e.dxftype == "LWPOLYLINE"):
            if (singlepoly):
                seg = pcbnew.DRAWSEGMENT(board)
                seg.SetLayer(layer)
                seg.SetShape(pcbnew.S_POLYGON)
                board.Add(seg)
                sps = seg.GetPolyShape()

                o = sps.NewOutline()

                for pt in e.points:
                    ppt = pcbpoint.pcbpoint(pt).wxpoint()
                    sps.Append(ppt.x, ppt.y)

            else:

                prevpt = e.points[-1]
                curbulge = e.bulge[-1]
                for pt, nextbulge in zip(e.points, e.bulge):
                    # y is minus because y increases going down the canvase
                    if (curbulge == 0.0):
                        seg = pcbnew.DRAWSEGMENT(board)
                        seg.SetLayer(layer)
                        seg.SetShape(pcbnew.S_SEGMENT)
                        seg.SetStart(pcbpoint.pcbpoint(prevpt).wxpoint())
                        seg.SetEnd(pcbpoint.pcbpoint(pt).wxpoint())
                        board.Add(seg)
                    else:
                        center, startangle, endangle, radius = bulge.bulge2arc(prevpt, pt, curbulge)

                        dxfarc2pcbarc(board, layer,
                                      pcbpoint.pcbpoint(center),
                                      radius, startangle, endangle)

                    prevpt = pt
                    curbulge = nextbulge




    pcbnew.Refresh()

def dxf_to_mountholes(board,footprint_mapping, filepath):
    dxf = dxfgrabber.readfile(filepath)

    io = pcbnew.PCB_IO()
    for e in dxf.entities.get_entities():
        
        if (e.dxftype == "CIRCLE"):
            print("center {} radius {}".format(e.center, e.radius))
            d = str(e.radius*2)
            if d not in footprint_mapping:
                raise ValueError("diameter {} not found in footprint mapping".format(d))
            fp = footprint_mapping[d]
            mod = io.FootprintLoad(fp[0], fp[1])
            mod.SetPosition(pcbpoint.pcbpoint(e.center).wxpoint())
            board.Add(mod)
    pcbnew.Refresh()

            
board = pcbnew.GetBoard()

dxf_to_graphic(board, layertable['Cmts.User'],
               "/bubba/electronicsDS/fusion/leds_projection.dxf", True)

dxf_to_graphic(board, layertable['Edge.Cuts'],
               "/bubba/electronicsDS/fusion/boundary_polyline.dxf")

footprint_lib = '/home/mmccoo/kicad/kicad-footprints/MountingHole.pretty'

footprint_mapping = {
    "3.0": (footprint_lib, "MountingHole_3.2mm_M3")
    }
dxf_to_mountholes(board, footprint_mapping, "/bubba/electronicsDS/fusion/mountingholes.dxf")


dxf_to_graphic(board, layertable['Eco1.User'],
               "/bubba/electronicsDS/fusion/powerrails.dxf")

#traverse_dxf("/bubba/electronicsDS/fusion/powerrails.dxf", graphic_actions)
