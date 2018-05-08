
import dxfgrabber
import numpy as np
import sys, os.path, inspect
import re
import pcbnew
import bulge
import pcbpoint

from sets import Set
import pdb

# how close together to points need to be to each other to be considered
# connected?
thresh = 0.01
# when breaking and arc into segments, what's the max seg length we want.
arc_line_length = 5.0

# I mostly depend on pcbpoint to deal with scaling issues. For radius below,
# still need to scale.
# the internal coorinate space of pcbnew is 10E-6 mm. (a millionth of a mm)
# the coordinate 121550000 corresponds to 121.550000
SCALE = 1000000.0



class graphic_actions:
    def __init__(self, print_unhandled=False):
        self.print_unhandled = print_unhandled

    def line_action(self, start, end):
        if (self.print_unhandled):
            print("line: {} {}".format(start, end))

    def circle_action(self, center, radius):
        if (self.print_unhandled):
            print("circle center: {} radius: {}".format(center, radius))

    def arc_action(self, center, radius, start_angle, end_angle):
        if (self.print_unhandled):
            print("arc center: {} radius {} angles: {} {}".format(center, radius, start_angle, end_angle))

    def poly_action(self, points):
        if (self.print_unhandled):
            print("poly: {}".format(points))

    # here is some helper stuff
    # dxf arcs are different from pcbnew arcs
    # dxf arcs have a center point, radius and start/stop angles
    # pcbnew arcs have a center pointer, radius, and a start point,
    # angle (counter clockwise)
    def dxfarc2pcbarc(self, center, radius, start_angle, end_angle):
        # need negative angles because pcbnew flips over x axis
        start_angle, end_angle = (min(start_angle, end_angle), max(start_angle, end_angle))
        return (center,
                start_angle-end_angle,
                # location of start of arc
                center.polar(radius, start_angle))


class segment_actions(graphic_actions):
    def __init__(self, board, layer, print_unhandled=False):
        graphic_actions.__init__(self, print_unhandled)

        self.board = board
        self.layer = layer

    def make_basic_seg(self):
        seg = pcbnew.DRAWSEGMENT(self.board)
        seg.SetLayer(self.layer)
        seg.SetShape(pcbnew.S_SEGMENT)
        self.board.Add(seg)
        return seg

    def line_action(self, start, end):
        seg = self.make_basic_seg()
        seg.SetShape(pcbnew.S_SEGMENT)
        seg.SetStart(pcbpoint.pcbpoint(start).wxpoint())
        seg.SetEnd(pcbpoint.pcbpoint(end).wxpoint())

    def circle_action(self, center, radius):
        seg = self.make_basic_seg()
        seg.SetShape(pcbnew.S_CIRCLE)
        seg.SetCenter(pcbpoint.pcbpoint(center).wxpoint())
        # kicad has a goofy way of specifying circles. instead
        # of a radius, you give a point on the circle. The radius
        # can be computed from there.
        seg.SetEnd((pcbpoint.pcbpoint(center)+
                    pcbpoint.pcbpoint(radius, 0)).wxpoint()
        )

    def arc_action(self, center, radius, start_angle, end_angle):
        # dxf arcs are different from pcbnew arcs
        # dxf arcs have a center point, radius and start/stop angles
        # pcbnew arcs have a center pointer, radius, and a start point,
        # angle (counter clockwise)
        seg = self.make_basic_seg()

        center, angle, arcstart = self.dxfarc2pcbarc(pcbpoint.pcbpoint(center),
                                                     radius,
                                                     start_angle,
                                                     end_angle)
        seg.SetShape(pcbnew.S_ARC)
        seg.SetCenter(pcbpoint.pcbpoint(center).wxpoint())
        # negative angle since y goes the wrong way.
        seg.SetAngle(angle*10)
        seg.SetArcStart(pcbpoint.pcbpoint(arcstart).wxpoint())

    def poly_action(self, points):
        seg = self.make_basic_seg()
        seg.SetShape(pcbnew.S_POLYGON)

        sps = seg.GetPolyShape()
        o = sps.NewOutline()
        for pt in points:
            ppt = pcbpoint.pcbpoint(pt).wxpoint()
            sps.Append(ppt.x, ppt.y)

class zone_actions(graphic_actions):
    def __init__(self, board, net, layer, print_unhandled=False):
        graphic_actions.__init__(self, print_unhandled)
        self.board = board
        self.net = net
        self.layer = layer

    # poly is the only thing that really makes sense in
    # the zone context
    def poly_action(self, points):
        pcbpt = pcbpoint.pcbpoint(points[0]).wxpoint()
        zone_container = self.board.InsertArea(self.net.GetNet(), 0, self.layer,
                                               pcbpt.x, pcbpt.y,
                                               pcbnew.CPolyLine.DIAGONAL_EDGE)
        shape_poly_set = zone_container.Outline()
        shapeid = 0
        for pt in points[1:]:
            pcbpt = pcbpoint.pcbpoint(pt).wxpoint()
            shape_poly_set.Append(pcbpt.x, pcbpt.y)

        zone_container.Hatch()


class mounting_actions(graphic_actions):

    def __init__(self, board, footprint_mapping,
                 flip=False,
                 clearance=None,
                 print_unhandled=False):
        graphic_actions.__init__(self, print_unhandled)

        self.footprint_mapping = footprint_mapping
        self.board = board
        self.flip = flip
        self.clearance = clearance

    def circle_action(self, center, radius):
        d = str(radius*2)
        if d not in self.footprint_mapping:
                print("diameter {} not found in footprint mapping".format(d))
                return
        fp = self.footprint_mapping[d]
        mod = pcbnew.InstantiateFootprint(fp[0], fp[1])
        mod.SetPosition(pcbpoint.pcbpoint(center).wxpoint())
        if (self.flip):
            mod.Flip(pcbpoint.pcbpoint(center).wxpoint())
        if (self.clearance != None):
            for pad in mod.Pads():
                pad.SetLocalClearance(self.clearance)
        self.board.Add(mod)


# http://www.ariel.com.au/a/python-point-int-poly.html
# determine if a point is inside a given polygon or not
# Polygon is a list of (x,y) pairs.
def point_inside_polygon(x,y,poly):

    n = len(poly)
    inside =False

    p1x,p1y = poly[0]
    for i in range(n+1):
        p2x,p2y = poly[i % n]
        if y > min(p1y,p2y):
            if y <= max(p1y,p2y):
                if x <= max(p1x,p2x):
                    if p1y != p2y:
                        xinters = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x,p1y = p2x,p2y

    return inside


def longest_angle_for_polygon(poly):
    prevpt = poly[-1]
    length = None
    retval = None
    for pt in poly:
        d = prevpt.distance(pt)
        if (length and (length>d)):
            prevpt = pt
            continue
        length = d
        retval = prevpt.angle(pt)
        prevpt = pt
    return retval


def center_for_polygon(poly):
    # based on this:
    # https://en.wikipedia.org/wiki/Centroid#Centroid_of_a_polygon

    prev = poly[-1]
    x = 0.0
    y = 0.0
    area = 0.0
    for cur in poly:
        x = x + (prev.x+cur.x)*(prev.x*cur.y - cur.x*prev.y)
        y = y + (prev.y+cur.y)*(prev.x*cur.y - cur.x*prev.y)
        area = area + prev.x*cur.y - cur.x*prev.y
        prev = cur

    area =  area/2.0

    x = x/6.0/area
    y = y/6.0/area

    return pcbpoint.pcbpoint(x,y,noscale=True)

class orient_actions(graphic_actions):
    def __init__(self, board, modnames, print_unhandled=False):
        graphic_actions.__init__(self, print_unhandled)
        self.board = board
        self.modnames = Set(modnames)

    # I only care about poly because I want directionality (which a cirle doesn't have)
    # and I want to check for enclosing (which doesn't make sense for line, arc
    def poly_action(self, points):
        for mod in self.board.GetModules():
            #modname = mod.GetFPID().GetLibItemName().c_str()
            #if (modname != "LED_5730"):
            #    continue
            modname = mod.GetReference()
            if (modname not in self.modnames):
                continue
            pos = pcbpoint.pcbpoint(mod.GetPosition())
            inside = point_inside_polygon(pos.x, pos.y, points)
            if (not inside):
                continue
            angle = longest_angle_for_polygon(points)
            if (angle>0):
                angle = angle - 180.0
            mod.SetOrientation(angle*10)
            mod.SetPosition(center_for_polygon(points).wxpoint())

class myarc:
    def __init__(self, center, radius, start_angle, end_angle):
        self.center = center = pcbpoint.pcbpoint(center)
        self.radius = radius
        self.start_angle = start_angle
        self.end_angle = end_angle

        self.start_point = center.polar(radius, start_angle)
        self.end_point   = center.polar(radius, end_angle)
        self.other = Set()

    def reverse(self):
        self.start_angle, self.end_angle = (self.end_angle, self.start_angle)
        self.start_point, self.end_point = (self.end_point, self.start_point)

    def __str__(self):
        return "arc c{} r{} {},{} {},{}".format(self.center, self.radius, self.start_angle, self.end_angle, self.start_point, self.end_point)

class myline:
    def __init__(self, start_point, end_point):
        self.start_point = pcbpoint.pcbpoint(start_point)
        self.end_point   = pcbpoint.pcbpoint(end_point)
        self.other = Set()

    def reverse(self):
        self.start_point, self.end_point = (self.end_point, self.start_point)

    def __str__(self):
        return "line {} {}".format(self.start_point, self.end_point)


def mydist(o1, o2):
    return min(o1.start_point.distance(o2.start_point),
               o1.start_point.distance(o2.end_point),
               o1.end_point.distance(o2.start_point),
               o1.end_point.distance(o2.end_point))


# it is possible for two polygons to meet at a point. This implementation
# will destroy those. worry about it later.
def remove_non_duals(e):
    if (len(e.other) == 2):
        return

    # if I have three lines joining in one spot. this doesn't deal
    # with the properly. I try to mitigate that by beginning with
    # lines that connect at only one edge first.
    others = e.other
    e.other = Set()
    for other in others:
        other.other.remove(e)
        remove_non_duals(other)

def merge_arcs_and_lines(elts):


    # yes, this is a O(n^2) algorithm. scanline would be better
    # this is quicker to implement
    for e1 in elts:
        for e2 in elts:
            if (e1==e2):
                continue
            if mydist(e1, e2)<thresh:
                e1.other.add(e2)
                e2.other.add(e1)

    # this needs some work. if I have a line that connects to a poly,
    # I want to first lose that line and only then break triple connections.
    for e in elts:
        if (len(e.other) == 1):
            remove_non_duals(e)

    for e in elts:
        remove_non_duals(e)


    merged = []
    for e in elts:
        if (len(e.other) != 2):
            continue

        members = [e]
        # after this pop, the e.other set will have one member
        other = e.other.pop()

        other.other.remove(e)

        while (other):
            if (other == e):
                break

            nextelt = other.other.pop()
            nextelt.other.remove(other)

            members.append(other)

            other = nextelt

        if (len(members) < 2):
            raise ValueError("There should be at least two members in this merged poly")

        prev = members[-1]
        # here, I'm about to reorder the point order of the member lines/arcs. I
        # want to end_point to match the next member.
        if ((members[0].start_point.distance(prev.end_point) > thresh) and
            (members[0].end_point.distance(prev.end_point) > thresh)):
            prev.reverse()

        for m in members:
            if (m.start_point.distance(prev.end_point) > thresh):
                m.reverse()
            if (m.start_point.distance(prev.end_point) > thresh):
                raise ValueError("expecting the start and end to match here {} {}".format(prev, m))

            prev = m

        merged.append(members)

    return merged

def break_curve(center, radius, start_angle, end_angle):
    retpts = []

    center = pcbpoint.pcbpoint(center)

    # in this file, I generally use degrees (kicad uses degrees),
    # in this function, radians more convenient.
    start_radians, end_radians = (np.deg2rad(start_angle), np.deg2rad(end_angle))

    # the circumference of a cirle is 2*pi*radius
    circ = np.abs(end_radians-start_radians)*radius

    num_segs = int(np.max((np.ceil(circ/arc_line_length),
                           np.ceil(np.abs(end_angle-start_angle)/15.0))))
    incr_radians = (end_radians-start_radians)/num_segs

    for i in range(num_segs+1):
        radians = start_radians + incr_radians*i
        retpts.append(center.polar(radius, np.rad2deg(radians)))

    return retpts

# unlike the other functions where I just pass generic attributes, (center, radius...)
# since bulge is specific to dxf polylines, I'm just passing the polyline
def break_bulges(e):
    retpts = []

    prevpt = e.points[-1]
    curbulge = e.bulge[-1]
    for pt, nextbulge in zip(e.points, e.bulge):
        if (curbulge == 0.0):
            retpts.append(pt)
            prevpt = pt
            curbulge = nextbulge
            continue

        # dxf arcs are different from pcbnew arcs
        # dxf arcs have a center point, radius and start/stop angles
        # pcbnew arcs have a center pointer, radius, and a start point, angle (counter clockwise)

        # the angles are negative because pcbnew coodinates are flipped over the x axis
        center, start_angle, end_angle, radius = bulge.bulge2arc(prevpt, pt, curbulge)

        arcpts = break_curve(center, radius, start_angle, end_angle)
        # remove the first point because we don't want repeats in this poly
        arcpts.pop(0)
        retpts.extend(arcpts)

        prevpt = pt
        curbulge = nextbulge

    return retpts

def traverse_dxf(filepath, actions,
                 merge_polys=False,
                 break_curves=False):
    dxf = dxfgrabber.readfile(filepath)

    merge_elts = []
    for e in dxf.entities.get_entities():
        if (e.dxftype == "LINE"):
            if (merge_polys):
                merge_elts.append(myline(e.start, e.end))
            else:
                actions.line_action(pcbpoint.pcbpoint(e.start),
                                    pcbpoint.pcbpoint(e.end))

        elif(e.dxftype == "CIRCLE"):
            actions.circle_action(pcbpoint.pcbpoint(e.center), e.radius)

        elif(e.dxftype == "ARC"):
            if (merge_polys):
                merge_elts.append(myarc(e.center, e.radius, e.start_angle, e.end_angle))
                continue

            if (not break_curves):
                actions.arc_action(pcbpoint.pcbpoint(e.center), e.radius, e.start_angle, e.end_angle)
                continue

            pts = break_curve(e.center, e.radius, e.start_angle, e.end_angle)
            prevpt = pts.pop(0)
            for pt in pts:
                actions.line_action(prevpt, pt)
                prevpt = pt

        elif (e.dxftype == "LWPOLYLINE"):
            pts = e.points
            if (break_curves):
                pts = break_bulges(e)
            if (merge_polys):
                # if we're asking polygons to be merged, we just leave
                # existing polys as they are.
                actions.poly_action([pcbpoint.pcbpoint(p) for p in pts])
            else:
                # otherwise, I will un-merge polys
                prevpt = pcbpoint.pcbpoint(pts[-1])
                for p in pts:
                    curpt = pcbpoint.pcbpoint(p)
                    actions.line_action(prevpt, curpt)
                    prevpt = curpt


    if (not merge_polys):
        return

    merged = merge_arcs_and_lines(merge_elts)

    # at this point, if there were objects that weren't merged into something, they'll
    # be lost.

    for poly in merged:
        pts = []
        for elt in poly:
            # when talking about polys in kicad, there are no arcs.
            # so I'm just assuming that either, the arcs have been broken
            # in the code above, or that the user doesn't care about the lost
            # accuracy
            if (break_curves and isinstance(elt, myarc)):
                brokenpts = break_curve(elt.center, elt.radius, elt.start_angle, elt.end_angle)
                # pop the last point because the next elt will give that point.
                # adjacent element share a start/end point. We only want it once.
                brokenpts.pop()
                pts.extend(brokenpts)
            else:
                pts.append(elt.start_point)
        actions.poly_action(pts)


def traverse_graphics(board, layer, actions,
                      merge_polys=False,
                      break_curves=False):

    merge_elts = []
    for d in board.GetDrawings():
        if ((layer != None) and (layer != d.GetLayerName())):
            continue

        if (d.GetShape() == pcbnew.S_SEGMENT):
            if (merge_polys):
                merge_elts.append(myline(d.GetStart(), d.GetEnd()))
            else:
                actions.line_action(d.GetStart(), d.GetEnd())

        elif (d.GetShape() == pcbnew.S_CIRCLE):
            actions.circle_action(d.GetCenter(), d.GetRadius()/SCALE)

        elif(d.GetShape() == pcbnew.S_ARC):
            if (merge_polys):
                merge_elts.append(myarc(d.GetCenter(),
                                        d.GetRadius()/SCALE,
                                        -d.GetArcAngleStart()/10.0,
                                        -(d.GetArcAngleStart()+d.GetAngle())/10.0))
                continue

            if (not break_curves):
                # negative angles because kicad's y axis goes down.
                actions.arc_action(d.GetCenter(),
                                   d.GetRadius()/SCALE,
                                   -d.GetArcAngleStart()/10.0,
                                   -(d.GetArcAngleStart()+d.GetAngle())/10.0)
                continue

            pts = break_curve(d.GetCenter(),
                              d.GetRadius()/SCALE,
                              -d.GetArcAngleStart()/10.0,
                              -(d.GetArcAngleStart()+d.GetAngle())/10.0)
            prevpt = pts.pop(0)
            for pt in pts:
                actions.line_action(prevpt, pt)
                prevpt = pt

        elif (d.GetShape() == pcbnew.S_POLYGON):
            pts = [pcbpoint.pcbpoint(p) for p in d.GetPolyPoints()]
            actions.poly_action(pts)

    if (not merge_polys):
        return

    merged = merge_arcs_and_lines(merge_elts)

    # at this point, if there were objects that weren't merged into something, they'll
    # be lost.

    for poly in merged:
        pts = []
        for elt in poly:
            # when talking about polys in kicad, there are no arcs.
            # so I'm just assuming that either, the arcs have been broken
            # in the code above, or that the user doesn't care about the lost
            # accuracy
            if (break_curves and isinstance(elt, myarc)):
                brokenpts = break_curve(elt.center, elt.radius, elt.start_angle, elt.end_angle)
                # pop the last point because the next elt will give that point.
                # adjacent element share a start/end point. We only want it once.
                brokenpts.pop()
                pts.extend(brokenpts)
            else:
                pts.append(elt.start_point)
        actions.poly_action(pts)
