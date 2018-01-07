

import pcbnew

import inspect

import sys, os.path
oldpath = sys.path
# inspect.stack()[0][1] is the full path to the current file.
sys.path.insert(0, os.path.dirname(inspect.stack()[0][1]))
import parse_svg_path
sys.path = oldpath



board = pcbnew.GetBoard()

nets = board.GetNetsByName()

# find a power net to add the zone to.
powernet = None
for name in ["+12V", "+5V", "GND"]:
    if (nets.has_key(name)):
        powernet = nets[name]

# generate a name->layer table so we can lookup layer numbers by name.
layertable = {}

# if you get an error saying that PCB_LAYER_ID_COUNT doesn't exist, then
# it's probably because you're on an older version of pcbnew.
# the interface has changed a little (progress) it used to be called LAYER_ID_COUNT.
# now it's called PCB_LAYER_ID_COUNT
if hasattr(pcbnew, "LAYER_ID_COUNT"):
    pcbnew.PCB_LAYER_ID_COUNT = pcbnew.LAYER_ID_COUNT


numlayers = pcbnew.PCB_LAYER_ID_COUNT
for i in range(numlayers):
    layertable[board.GetLayerName(i)] = i
    #print("{} {}".format(i, board.GetLayerName(i)))

# the internal coorinate space of pcbnew is 10E-6 mm. (a millionth of a mm)
# the coordinate 121550000 corresponds to 121.550000 
SCALE = 1000000.0
        
powerlayer = layertable["B.Cu"]

# here I load from drawing.svg in the current directory. You'll want to change that path.
paths = parse_svg_path.parse_svg_path(os.path.dirname(inspect.stack()[0][1]) + '/drawing.svg')
if not paths:
     raise ValueError('wasnt able to read any paths from file')


# things are a little tricky below, because the first boundary has its first
# point passed into the creation of the new area. subsequent bounds are not
# done that way.
zone_container = None
shape_poly_set = None
 
for path in paths:
    for shape in path.group_by_bound_and_holes():
        shapeid = None
        if not shape_poly_set: 
            # the call to GetNet() gets the netcode, an integer.
            zone_container = board.InsertArea(powernet.GetNet(), 0, powerlayer,
                                              int(shape.bound[0][0]*SCALE),
                                              int(shape.bound[0][1]*SCALE),
                                              pcbnew.CPolyLine.DIAGONAL_EDGE)
            shape_poly_set = zone_container.Outline()
            shapeid = 0
        else:
            shapeid = shape_poly_set.NewOutline()
            shape_poly_set.Append(int(shape.bound[0][0]*SCALE),
                                  int(shape.bound[0][1]*SCALE),
                                  shapeid)
            
        for pt in shape.bound[1:]:
            shape_poly_set.Append(int(pt[0]*SCALE), int(pt[1]*SCALE))

        for hole in shape.holes:
            hi = shape_poly_set.NewHole()
            # -1 to the third arg maintains the default behavior of
            # using the last outline.
            for pt in hole:
                shape_poly_set.Append(int(pt[0]*SCALE), int(pt[1]*SCALE), -1, hi)
                
        zone_container.Hatch() 
    



# In the future, this build connectivity call will not be neccessary.
# I have submitted a patch to include this in the code for Refresh.
# You'll know you needed it if pcbnew crashes without it.
board.BuildConnectivity()

pcbnew.Refresh()
print("done")
