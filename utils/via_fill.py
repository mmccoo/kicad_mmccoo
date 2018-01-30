
import pcbnew

import numpy as np
import math

showplot = False
if showplot:
    import matplotlib.pyplot as plt

from shapely.ops import polygonize
from shapely.geometry import Polygon
from shapely.geometry import MultiPolygon
from shapely.geometry import CAP_STYLE, JOIN_STYLE
from shapely.ops import cascaded_union
from shapely.geometry import box
from shapely.geometry import LineString


board = pcbnew.GetBoard()
layertable = {}
numlayers = pcbnew.PCB_LAYER_ID_COUNT
for i in range(numlayers):
    layertable[pcbnew.GetBoard().GetLayerName(i)] = i

    
def coordsFromPolySet(ps):
    str = ps.Format()
    lines = str.split('\n')
    numpts = int(lines[2])
    pts = [[int(n) for n in x.split(" ")] for x in lines[3:-2]] # -1 because of the extra two \n
    return pts

def plot_poly(polys):
    for poly in polys:
        dpts = list(poly.exterior.coords)
        x,y = zip(*dpts)
        if showplot:
            plt.plot(x,y)

        for hole in poly.interiors:
            hpts = list(hole.coords)
            x,y = zip(*hpts)
            if showplot:
                plt.plot(x,y)

def create_via(board, net, pt):
    newvia = pcbnew.VIA(board)
    # need to add before SetNet will work, so just doing it first
    board.Add(newvia)
    toplayer = layertable['F.Cu']
    bottomlayer = layertable['B.Cu']

    newvia.SetNet(net)
    nc = net.GetNetClass()
    newvia.SetWidth(nc.GetViaDiameter())
    newvia.SetPosition(pcbnew.wxPoint(*pt))
    newvia.SetLayerPair(toplayer, bottomlayer)
    newvia.SetViaType(pcbnew.VIA_THROUGH)

# I don't want to update the geometries everytime I add something.
added = []
def add_via_at_pt(board, net, pt):
    x,y = pt
    for xother,yother in added:
        if np.hypot(x-xother, y-yother) < viadiameter:
            #print("{},{} and {},{} have distance of {}".format(x,y,xother,yother,np.hypot(x-xother, y-yother)))
            return
    if showplot:
        ax.add_artist(plt.Circle((x,y), viadiameter/2))
    create_via(board, net, (x,y))
    added.append((x,y))


if showplot:
    fig, ax = plt.subplots()

#https://matplotlib.org/tutorials/introductory/usage.html#sphx-glr-tutorials-introductory-usage-py

# here I get all of the obstacles.
# I avoid module footprints
lines = []
for mod in board.GetModules():
    for edge in mod.GraphicalItemsList():
        if type(edge) != pcbnew.EDGE_MODULE:
            continue
        x1, y1 = edge.GetStart()
        x2, y2 = edge.GetEnd()

        #plt.plot([x1,x2],[y1,y2])
        lines.append(((x1,y1),(x2,y2)))

modpolys = MultiPolygon(polygonize(lines)).buffer(pcbnew.Millimeter2iu(.6),
                                                  cap_style=CAP_STYLE.square)
for poly in modpolys:
    points = list(poly.exterior.coords)
    x,y = zip(*points)
    #plt.plot(x,y)

tracks = []
for track in board.GetTracks():
    # getTracks actually returns both vias and wires. Since
    # I'm trying to fill vias on a two layer board, it doesn't
    # matter of the object is a via or wire.
    # It actually could matter if it's a wire on the same net as the
    # fill area, but I don't care at the moment.
    tracks.append(LineString([track.GetStart(), track.GetEnd()]).
                  buffer(track.GetWidth()/2+pcbnew.Millimeter2iu(.6),
                         cap_style=CAP_STYLE.square))

bounds = []
for d in board.GetDrawings():
    if d.GetLayerName() != "Edge.Cuts":
        continue
    bounds.append(LineString([d.GetStart(), d.GetEnd()]).
                  buffer(pcbnew.Millimeter2iu(.6),
                         cap_style=CAP_STYLE.square))

    
obstacles = cascaded_union([modpolys] + tracks + bounds)
#multitracks = MultiPolygon(tracks)

1#if showplot:
#    plot_poly(multitracks)
    
for netname in ["GND", "+12V"]:
    if (netname not in board.GetNetsByName()):
        print("net {} not present".format(netname))
        continue
    net = board.GetNetsByName()[netname]


    tzonepolygons = []
    bzonepolygons = []
    for zone in board.Zones():
        netcode = zone.GetNet().GetNet()
        # pointer comparison doesn't work. have to compare netcodes.
        if (zone.GetNet().GetNet() != net.GetNet()):
            continue
        shape_poly_set = zone.Outline()
        zonepts = coordsFromPolySet(shape_poly_set)
        x,y = zip(*zonepts)
        polygon = Polygon(zonepts)
        if (zone.GetLayerName() == "B.Cu"):
            bzonepolygons.append(polygon)
        else:
            tzonepolygons.append(polygon)

    # cascaded_union takes a list of polys and merges/unions them together
    overlaps = cascaded_union(bzonepolygons).intersection(cascaded_union(tzonepolygons))

    plot_poly(obstacles)

    diff = overlaps.difference(obstacles)

    netclass = net.GetNetClass()
    viadiameter = netclass.GetViaDiameter()

    # this gives list of polygons where vias can be placed.
    viaspots = diff.buffer(-viadiameter/2, join_style=JOIN_STYLE.mitre)

    # if buffer can return only one polygon that's what it will do.
    # otherwise it gives a list of polys
    if type(viaspots) == Polygon:
        viaspots = [viaspots]

    for spot in viaspots:
        if spot.is_empty:
            continue
        coords = list(spot.exterior.coords)
        prevpt = coords[-2]
        pt = coords[-1]
        for nextpt in coords:
            angle = math.degrees(math.atan2(nextpt[1]-pt[1],nextpt[0]-pt[0])-
                                 math.atan2(pt[1]-prevpt[1],pt[0]-prevpt[0]))


            length=np.hypot(pt[0]-prevpt[0],
                            pt[1]-prevpt[1])
            numvias = int(length/viadiameter)+1

            if (numvias == 1):
                x = (prevpt[0]+pt[0])/2
                y = (prevpt[1]+pt[1])/2
                add_via_at_pt(board, net, (x,y))
                prevpt = pt
                pt = nextpt
                continue

            xincr = (pt[0]-prevpt[0])/(numvias-1)
            yincr = (pt[1]-prevpt[1])/(numvias-1)
            for i in range(numvias):
                x = prevpt[0] + i*xincr
                y = prevpt[1] + i*yincr
                add_via_at_pt(board, net, (x,y))

            prevpt = pt
            pt = nextpt

                
#plot_poly(viaspots)

if showplot:
    plt.show()


pcbnew.Refresh()
