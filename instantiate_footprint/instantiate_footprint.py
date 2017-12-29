import pcbnew

def GetRectCorners(rect):
    return [pcbnew.wxPoint(rect.Centre().x-rect.GetWidth()/2, rect.Centre().y-rect.GetHeight()/2),
            pcbnew.wxPoint(rect.Centre().x-rect.GetWidth()/2, rect.Centre().y+rect.GetHeight()/2),
            pcbnew.wxPoint(rect.Centre().x+rect.GetWidth()/2, rect.Centre().y+rect.GetHeight()/2),
            pcbnew.wxPoint(rect.Centre().x+rect.GetWidth()/2, rect.Centre().y-rect.GetHeight()/2)]

# GetBoundingBox includes the text stuff.
def GetModBBox(mod):
    modbox = None
    for pad in mod.Pads():
        #print("pad on layer {}".format(pad.GetLayerName()))
        if (modbox == None):
            modbox = pad.GetBoundingBox()
        else:
            modbox.Merge(pad.GetBoundingBox())
    for gi in mod.GraphicalItems():
        #print("pad gi on layer {}".format(gi.GetLayerName()));
        if (modbox == None):
            modbox = gi.GetBoundingBox()
        else:
            modbox.Merge(gi.GetBoundingBox())
    
    return modbox

def AddMountingHoles():
    footprint_lib = '/home/mmccoo/kicad/kicad-footprints/MountingHole.pretty'

    board = pcbnew.GetBoard()

    # the internal coorinate space of pcbnew is 10E-6 mm. (a millionth of a mm)
    # the coordinate 121550000 corresponds to 121.550000 

    SCALE = 1000000.0

    rect = None
    for d in board.GetDrawings():
        if (d.GetLayerName() != "Edge.Cuts"):
            continue
        if (rect == None):
            rect = d.GetBoundingBox()
        else:
            rect.Merge(d.GetBoundingBox())
        #print("{}".format(str(d)))
        #print("on layer {} {} {}".format(d.GetLayerName(),
        #                                 str(d.GetStart()),
        #                                 str(d.GetEnd())))


    print("bbox of boundary is centered at {}. Width: {}, Height {}".format(rect.Centre(),
                                                                            rect.GetWidth(),
                                                                            rect.GetHeight()))
    print("left {} {} {} {}".format(rect.GetLeft(),
                                    rect.GetBottom(),
                                    rect.GetRight(),
                                    rect.GetTop()))





    io = pcbnew.PCB_IO()
    board = pcbnew.GetBoard()

    mod = io.FootprintLoad(footprint_lib, "MountingHole_3.2mm_M3")

    # what I really want to do is inflating by a negative amount,
    # but that function takes a xwCoord, which I don't know how
    # to create given the current python interface.
    # in this case we want to compute where the mounting
    # holes should go.
    # I am reducing with the full width/height of the module because
    # adjusting width/height of the rect needs both sides
    modbox = GetModBBox(mod);
    rect.SetWidth(rect.GetWidth()   - modbox.GetWidth())
    rect.SetHeight(rect.GetHeight() + modbox.GetHeight())
    rect.SetX(rect.GetX() + modbox.GetWidth()/2)
    rect.SetY(rect.GetY() - modbox.GetHeight()/2)
    print("new bbox of boundary is centered at {}. Width: {}, Height {}".format(rect.Centre(),
                                                                                rect.GetWidth(),
                                                                                rect.GetHeight()))
    print("left {} {} {} {}".format(rect.GetLeft(),
                                    rect.GetBottom(),
                                    rect.GetRight(),
                                    rect.GetTop()))

    # this is here for testing on an empty design
    # for mod in board.GetModules():
    #    board.Remove(mod)

    for point in GetRectCorners(rect):
        # this looks like a redundant call given the similar call above.
        # this call basically instantiates a new one. We don't want to add it twice.
        mod = io.FootprintLoad(footprint_lib, "MountingHole_3.2mm_M3")
        print("location {}".format(point))
        modbox = GetModBBox(mod)

        point.x = point.x - modbox.Centre().x + mod.GetPosition().x
        point.y = point.y - modbox.Centre().y + mod.GetPosition().y
        mod.SetPosition(point)
        print("mod pos {}, {}".format(point, modbox.Centre()))
        print("x {} y {}".format(point.x - modbox.Centre().x,
                                 point.y - modbox.Centre().y))

        board.Add(mod)











    # In the future, this build connectivity call will not be neccessary.
    # I have submitted a patch to include this in the code for Refresh.
    # You'll know you needed it if pcbnew crashes without it.
    board.BuildConnectivity()

    pcbnew.Refresh()
    print("done")
