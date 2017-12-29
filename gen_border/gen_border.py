# Copyright [2017] [Miles McCoo]

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# this script is a basic svg generator for pcbnew.
# the point of the script is more as a teaching tool
# there are a number of ways in which is is deficient.


import pcbnew

def mymin(a,b):
    if (a == None):
        return b
    if (b == None):
        return a
    if (a<b):
        return a
    return b

def mymax(a,b):
    if (a == None):
        return b
    if (b == None):
        return a
    if (a>b):
        return a
    return b


class BBox:
    def __init__(self, xl=None, yl=None, xh=None, yh=None):
        self.xl = xl
        self.xh = xh
        self.yl = yl
        self.yh = yh

    def __str__(self):
        return "({},{} {},{})".format(self.xl, self.yl, self.xh, self.yh)
        
    def addPoint(self, pt):
        self.xl = mymin(self.xl, pt.x)
        self.xh = mymax(self.xh, pt.x)
        self.yl = mymin(self.yl, pt.y)
        self.yh = mymax(self.yh, pt.y)

    def addPointBloatXY(self, pt, x, y):
        self.xl = mymin(self.xl, pt.x-x)
        self.xh = mymax(self.xh, pt.x+x)
        self.yl = mymin(self.yl, pt.y-y)
        self.yh = mymax(self.yh, pt.y+y)
        


def GenerateBoarder():
    print("running generate boarder")
    
    board = pcbnew.GetBoard()

    padshapes = {
        pcbnew.PAD_SHAPE_CIRCLE:  "PAD_SHAPE_CIRCLE",
        pcbnew.PAD_SHAPE_OVAL:    "PAD_SHAPE_OVAL",
        pcbnew.PAD_SHAPE_RECT:    "PAD_SHAPE_RECT",
        pcbnew.PAD_SHAPE_TRAPEZOID: "PAD_SHAPE_TRAPEZOID"    
    }
    # new in the most recent kicad code
    if hasattr(pcbnew, 'PAD_SHAPE_ROUNDRECT'):
        padshapes[pcbnew.PAD_SHAPE_ROUNDRECT] = "PAD_SHAPE_ROUNDRECT",

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

    boardbbox = BBox();

    print("getting tracks")
    alltracks = board.GetTracks() 
    for track in alltracks:
        # print("{}->{}".format(track.GetStart(), track.GetEnd()))
        # print("{},{}->{},{} width {} layer {}".format(track.GetStart().x/SCALE, track.GetStart().y/SCALE,
        #                                               track.GetEnd().x/SCALE,   track.GetEnd().y/SCALE,
        #                                               track.GetWidth()/SCALE,
        #                                               track.GetLayer())          
        # )
        boardbbox.addPoint(track.GetStart())
        boardbbox.addPoint(track.GetEnd())

    print("getting pads")
    allpads = board.GetPads()
    for pad in allpads:
        #print("pad {} {}".format(pad.GetParent().GetReference(), pad.GetPadName()))
        if (pad.GetShape() == pcbnew.PAD_SHAPE_RECT):        
            if ((pad.GetOrientationDegrees()==270) | (pad.GetOrientationDegrees()==90)):
                boardbbox.addPointBloatXY(pad.GetPosition(), pad.GetSize().y/2, pad.GetSize().x/2)
            else:
                boardbbox.addPointBloatXY(pad.GetPosition(), pad.GetSize().x/2, pad.GetSize().y/2)
        elif (pad.GetShape() == pcbnew.PAD_SHAPE_CIRCLE):
            boardbbox.addPointBloatXY(pad.GetPosition(), pad.GetSize().x/2, pad.GetSize().y/2)

        elif (pad.GetShape() == pcbnew.PAD_SHAPE_OVAL):
            boardbbox.addPointBloatXY(pad.GetPosition(), pad.GetSize().x/2, pad.GetSize().y/2)
        else:
            print("unknown pad shape {}({})".format(pad.GetShape(), padshapes[pad.GetShape()]))


    for mod in board.GetModules():
        #print("for mod {}".format(mod.GetReference()))
        #print("bbox is {}".format(str(boardbbox)))
        for gi in mod.GraphicalItems():
            bbox = gi.GetBoundingBox()
            boardbbox.addPointBloatXY(bbox.Centre(), bbox.GetWidth()/2, bbox.GetHeight()/2)




    for d in board.GetDrawings():
        #print("{}".format(str(d)))
        #print("on layer {} {} {}".format(d.GetLayerName(),
        #                                 str(d.GetStart()),
        #                                 str(d.GetEnd())))
        if (d.GetLayerName() == 'Edge.Cuts'):
            board.Remove(d)


    edgecut = layertable['Edge.Cuts']

    seg1 = pcbnew.DRAWSEGMENT(board)
    board.Add(seg1)
    seg1.SetStart(pcbnew.wxPoint(boardbbox.xl, boardbbox.yl))
    seg1.SetEnd(  pcbnew.wxPoint(boardbbox.xl, boardbbox.yh))
    seg1.SetLayer(edgecut)

    seg1 = pcbnew.DRAWSEGMENT(board)
    board.Add(seg1)
    seg1.SetStart(pcbnew.wxPoint(boardbbox.xl, boardbbox.yh))
    seg1.SetEnd(  pcbnew.wxPoint(boardbbox.xh, boardbbox.yh))
    seg1.SetLayer(edgecut)

    seg1 = pcbnew.DRAWSEGMENT(board)
    board.Add(seg1)
    seg1.SetStart(pcbnew.wxPoint(boardbbox.xh, boardbbox.yh))
    seg1.SetEnd(  pcbnew.wxPoint(boardbbox.xh, boardbbox.yl))
    seg1.SetLayer(edgecut)

    seg1 = pcbnew.DRAWSEGMENT(board)
    board.Add(seg1)
    seg1.SetStart(pcbnew.wxPoint(boardbbox.xh, boardbbox.yl))
    seg1.SetEnd(  pcbnew.wxPoint(boardbbox.xl, boardbbox.yl))
    seg1.SetLayer(edgecut)


    # from PolyLine.h
    # //
    # // A polyline contains one or more contours, where each contour
    # // is defined by a list of corners and side-styles
    # // There may be multiple contours in a polyline.
    # // The last contour may be open or closed, any others must be closed.
    # // All of the corners and side-styles are concatenated into 2 arrays,
    # // separated by setting the end_contour flag of the last corner of
    # // each contour.
    # //
    # // When used for copper (or technical layers) areas, the first contour is the outer edge
    # // of the area, subsequent ones are "holes" in the copper.

    nets = board.GetNetsByName()

    powernets = []
    for name in ["+12V", "+5V"]:
        if (nets.has_key(name)):
            powernets.append((name, "B.Cu"))
            break

    for name in ["GND"]:
        if (nets.has_key(name)):
            powernets.append((name, "F.Cu"))
            break


    for netname,layername in (powernets):
        net = nets.find(netname).value()[1]
        layer = layertable[layername]
        newarea = board.InsertArea(net.GetNet(), 0, layer, boardbbox.xl, boardbbox.yl, pcbnew.CPolyLine.DIAGONAL_EDGE)

        newoutline = newarea.Outline()

        # if you get a crash here, it's because you're on an older version of pcbnew.
        # the data structs for polygons has changed a little. The old struct has a
        # method called AppendCorner. Now it's just Append. Also, the call to CloseLastContour,
        # commented below used to be needed to avoid a corrupt output file.
        newoutline.Append(boardbbox.xl, boardbbox.yh);
        newoutline.Append(boardbbox.xh, boardbbox.yh);
        newoutline.Append(boardbbox.xh, boardbbox.yl);
        # this next line shouldn't really be necessary but without it, saving to
        # file will yield a file that won't load.
        # newoutline.CloseLastContour()

        # don't know why this is necessary. When calling InsertArea above, DIAGONAL_EDGE was passed
        # If you save/restore, the zone will come back hatched.
        # before then, the zone boundary will just be a line.
        # Omit this if you are using pcbnew.CPolyLine.NO_HATCH
        newarea.Hatch()


    # In the future, this build connectivity call will not be neccessary.
    # I have submitted a patch to include this in the code for Refresh.
    # You'll know you needed it if pcbnew crashes without it.
    board.BuildConnectivity()

    pcbnew.Refresh()
    print("done")
