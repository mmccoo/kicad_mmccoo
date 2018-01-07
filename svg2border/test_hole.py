import pcbnew

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

# class_zone.h
zone_container = board.InsertArea(powernet.GetNet(), 0, powerlayer,
                                  int(10*SCALE), int(10*SCALE),
                                  pcbnew.CPolyLine.DIAGONAL_EDGE)

# shape_poly_set.h
# this was has been initialized with the point passed to InsertArea
shape_poly_set = zone_container.Outline()

# append actually takes 4 args. x,y, outline, hole
# outline and hole can be omitted.
# if outline is omitted, -1 is passed and the last main outline is used.
# if hole is omitted, the point is added to the main outline.
shape_poly_set.Append(int(10*SCALE), int(20*SCALE))
shape_poly_set.Append(int(20*SCALE), int(20*SCALE))
shape_poly_set.Append(int(20*SCALE), int(10*SCALE))

hole = shape_poly_set.NewHole()
# -1 to the third arg maintains the default behavior of using the last
# outline.
shape_poly_set.Append(int(12*SCALE), int(12*SCALE), -1, hole)
shape_poly_set.Append(int(12*SCALE), int(16*SCALE), -1, hole)
shape_poly_set.Append(int(16*SCALE), int(16*SCALE), -1, hole)
shape_poly_set.Append(int(16*SCALE), int(12*SCALE), -1, hole)

# don't know why this is necessary. When calling InsertArea above, DIAGONAL_EDGE was passed
# If you save/restore, the zone will come back hatched.
# before then, the zone boundary will just be a line.
# Omit this if you are using pcbnew.CPolyLine.NO_HATCH
# if you don't use hatch, you won't see any hole outlines
zone_container.Hatch()


# In the future, this build connectivity call will not be neccessary.
# I have submitted a patch to include this in the code for Refresh.
# You'll know you needed it if pcbnew crashes without it.
board.BuildConnectivity()

pcbnew.Refresh()
print("done")
