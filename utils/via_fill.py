
import pcbnew

import pdb

import numpy as np
import math
from sets import Set

showplot = False
if showplot:
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()

from shapely.ops import polygonize
from shapely.geometry import Polygon
from shapely.geometry import MultiPolygon
from shapely.geometry import CAP_STYLE, JOIN_STYLE
from shapely.ops import cascaded_union
from shapely.geometry import box
from shapely.geometry import LineString
from shapely.geometry import Point

# this shouldn't be a global. it will be populated by viafill()
layertable = {}

def iterable(a):
    try:
        (x for x in a)
        return True
    except TypeError:
        return False



def draw_poly(board, polys, layer):
    # sometimes shapely returns a poly sometimes a multi.
    if not iterable(polys):
        polys = [polys]

    for poly in polys:
        if (not getattr(poly, "exterior", None)):
            print("got line? " + str(poly))
            continue


        seg = pcbnew.DRAWSEGMENT(board)
        seg.SetLayer(layer)
        seg.SetShape(pcbnew.S_SEGMENT)
        board.Add(seg)

        seg.SetShape(pcbnew.S_POLYGON)

        sps = seg.GetPolyShape()

        o = sps.NewOutline()

        # shapely polygons start and end with the same coord
        # so skip the first
        print("ext {}".format(len(list(poly.exterior.coords)[1:])))
        for pt in list(poly.exterior.coords)[1:]:
            sps.Append(int(pt[0]), int(pt[1]), o)

        for hole in poly.interiors:
            h = sps.NewHole()
            print("  hole {}".format(len(list(hole.coords)[1:])))
            for pt in list(hole.coords)[1:]:
                sps.Append(int(pt[0]), int(pt[1]), o, h)


def coordsFromPolySet(ps):
    str = ps.Format()
    lines = str.split('\n')
    numpts = int(lines[2])
    pts = [[int(n) for n in x.split(" ")] for x in lines[3:-2]] # -1 because of the extra two \n
    return pts

def plot_poly(polys):
    for poly in polys:
        if (not getattr(poly, "exterior", None)):
            print("got line?")
            continue
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
def add_via_at_pt(board, net, pt, viadiameter):
    x,y = pt
    for xother,yother in added:
        if np.hypot(x-xother, y-yother) < viadiameter:
            #print("{},{} and {},{} have distance of {}".format(x,y,xother,yother,np.hypot(x-xother, y-yother)))
            return
    if showplot:
        ax.add_artist(plt.Circle((x,y), viadiameter/2))
    create_via(board, net, (x,y))
    added.append((x,y))

# this fun takes a bunch of lines and converts to a boundary with holes
# seems like there'd be a standard way to do this. I haven't found it.
def LinesToPolyHoles(lines):
    # get all of the polys, both outer and holes
    # if there are holes, you'll get them double:
    # once as themselves and again as holes in a boundary
    polys = list(polygonize(lines))

    # merge to get just the outer
    bounds =  cascaded_union(polys)

    if not iterable(bounds):
        bounds = [bounds]

    retval = []
    for bound in bounds:
        for poly in polys:
            if Polygon(poly.exterior).almost_equals(bound):
                retval.append(poly)

    return retval


def ViaFill(nets):

    nets = Set(nets)

    board = pcbnew.GetBoard()

    global layertable
    layertable = {}
    numlayers = pcbnew.PCB_LAYER_ID_COUNT
    for i in range(numlayers):
        layertable[pcbnew.GetBoard().GetLayerName(i)] = i

    #https://matplotlib.org/tutorials/introductory/usage.html#sphx-glr-tutorials-introductory-usage-py

    # here I get all of the obstacles.
    # I avoid module footprints
    mods = []
    for mod in board.GetModules():
        lines = []
        for edge in mod.GraphicalItemsList():
            if type(edge) != pcbnew.EDGE_MODULE:
                continue

            if edge.GetShapeStr() == 'Circle':
                mods.append(Point(edge.GetPosition()).buffer(edge.GetRadius()))
            else:
                lines.append(LineString([edge.GetStart(), edge.GetEnd()]))

        # polygonize returns a generator. the polygons needs to be extracted from that.
        if (len(lines)):
            mods.extend(polygonize(lines))


    #lines.append(((x1,y1),(x2,y2)))
    #modpolys = MultiPolygon(polygonize(lines)).buffer(pcbnew.Millimeter2iu(.6),
    #                        cap_style=CAP_STYLE.square)

    #for poly in modpolys:
    #    points = list(poly.exterior.coords)
    #    x,y = zip(*points)
    #    #plt.plot(x,y)

    tracks = []
    for track in board.GetTracks():
        # getTracks actually returns both vias and wires. Since
        # I'm trying to fill vias on a two layer board, it doesn't
        # matter if the object is a via or wire.
        # It actually could matter if it's a wire on the same net as the
        # fill area, but I don't care at the moment.
        tracks.append(LineString([track.GetStart(), track.GetEnd()]).
                      buffer(track.GetWidth()/2+pcbnew.Millimeter2iu(.2),
                             cap_style=CAP_STYLE.square))

    bounds = []
    for d in board.GetDrawings():
        if d.GetLayerName() != "Edge.Cuts":
            continue
        if (d.GetShape() == pcbnew.S_CIRCLE):
            c = Point(d.GetPosition()).buffer(d.GetRadius())
            bounds.append(c)
        else:
            bounds.append(LineString([d.GetStart(), d.GetEnd()]))


    for netname in nets:
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

        netclass = net.GetNetClass()
        viadiameter = netclass.GetViaDiameter()

        obstacles = cascaded_union(mods + tracks).buffer(viadiameter/2,
                                                         cap_style=CAP_STYLE.flat,
                                                         join_style=JOIN_STYLE.mitre)
        #draw_poly(board, obstacles, layertable['Eco1.User'])


        # cascaded_union takes a list of polys and merges/unions them together
        overlaps = cascaded_union(bzonepolygons).intersection(cascaded_union(tzonepolygons)).buffer(-viadiameter/2)

        # unlike the other polys in this function, the boundary can have holes.
        boundspoly = MultiPolygon(LinesToPolyHoles(bounds)).buffer(-viadiameter/2)

        overlapsinbound = overlaps.intersection(cascaded_union(boundspoly))

        viaspots = list(overlapsinbound.difference(obstacles))
        #draw_poly(board, viaspots, layertable['Eco1.User'])


        # this gives list of polygons where vias can be placed.
        # I got some unexpected behavior from shrinking. there's a self intersecting poly
        # in there I think.
        # viaspots above used to be called diff
        #viaspots = diff.buffer(-viadiameter/2, join_style=JOIN_STYLE.mitre)
        #draw_poly(board, viaspots, layertable['Eco1.User'])

        # if buffer can return only one polygon that's what it will do.
        # otherwise it gives a list of polys


        for spot in viaspots:
            if spot.is_empty:
                continue
            coords = list(spot.exterior.coords)
            prevpt = coords[-2]
            pt = coords[-1]
            for nextpt in coords:
                angle = math.degrees(math.atan2(nextpt[1]-pt[1],nextpt[0]-pt[0])-
                                     math.atan2(pt[1]-prevpt[1],pt[0]-prevpt[0]))


                length=np.hypot(pt[0]-prevpt[0], pt[1]-prevpt[1])

                # I don't really want to maximize vias.
                numvias = int(length/(viadiameter+pcbnew.Millimeter2iu(5)))+1

                if (numvias == 1):
                    x = (prevpt[0]+pt[0])/2
                    y = (prevpt[1]+pt[1])/2
                    add_via_at_pt(board, net, (x,y), viadiameter)
                    prevpt = pt
                    pt = nextpt
                    continue

                xincr = (pt[0]-prevpt[0])/(numvias-1)
                yincr = (pt[1]-prevpt[1])/(numvias-1)
                for i in range(numvias):
                    x = prevpt[0] + i*xincr
                    y = prevpt[1] + i*yincr
                    add_via_at_pt(board, net, (x,y), viadiameter)

                prevpt = pt
                pt = nextpt


    #plot_poly(viaspots)

    if showplot:
        plt.show()


#pcbnew.Refresh()
