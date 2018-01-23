
import dxfgrabber
import numpy as np
import sys, os.path, inspect
import re
import pcbnew
oldpath = sys.path
# inspect.stack()[0][1] is the full path to the current file.
sys.path.insert(0, os.path.dirname(inspect.stack()[0][1]))
import bulge
import pcbpoint
sys.path = oldpath

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
        seg = pcbnew.DRAWSEGMENT(board)
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

    def __init__(self, board, footprint_mapping, print_unhandled=False):
        graphic_actions.__init__(self, print_unhandled)

        self.footprint_mapping = footprint_mapping
        self.board = board
        
    def circle_action(self, center, radius):
        d = str(radius*2)
        if d not in self.footprint_mapping:
                raise ValueError("diameter {} not found in footprint mapping".format(d))
        fp = self.footprint_mapping[d]
        io = pcbnew.PCB_IO()
        mod = io.FootprintLoad(fp[0], fp[1])
        mod.SetPosition(pcbpoint.pcbpoint(center).wxpoint())
        self.board.Add(mod)
    
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
    start_angle, end_angle = (np.deg2rad(start_angle), np.deg2rad(end_angle))

    # the circumference of a cirle is 2*pi*radius
    circ = np.abs(end_angle-start_angle)*radius
    num_segs = int(np.ceil(circ/arc_line_length))
    incr_angle = (end_angle-start_angle)/num_segs

    for i in range(num_segs+1):
        angle = start_angle + incr_angle*i
        retpts.append(center.polar(radius, np.rad2deg(angle)))
    
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
                actions.line_action(e.start, e.end)
            
        elif(e.dxftype == "CIRCLE"):
            actions.circle_action(e.center, e.radius)
            
        elif(e.dxftype == "ARC"):
            if (merge_polys):
                merge_elts.append(myarc(e.center, e.radius, e.start_angle, e.end_angle))
                continue

            if (not break_curves):
                actions.arc_action(e.center, e.radius, e.start_angle, e.end_angle)
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
                                        d.GetArcAngleStart()/10.0,
                                        (d.GetArcAngleStart()+d.GetAngle())/10.0))
                continue

            if (not break_curves):
                pdb.set_trace()
                # negative angles because kicad's y axis goes down.
                actions.arc_action(d.GetCenter(),
                                   d.GetRadius()/SCALE,                                   
                                   -d.GetArcAngleStart()/10.0,
                                   -(d.GetArcAngleStart()+d.GetAngle())/10.0)
                continue

            pts = break_curve(d.GetCenter(),
                              d.GetRadius()/SCALE,
                              d.GetArcAngleStart()/10.0,
                              (d.GetArcAngleStart()+d.GetAngle())/10.0)
            prevpt = pts.pop(0)
            for pt in pts:
                actions.line_action(prevpt, pt)
                prevpt = pt

        elif (d.GetShape() == pcbnew.S_POLYGON):
            pts = d.GetPolyPoints()
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
    traverse_dxf("/bubba/electronicsDS/fusion/powerrails.dxf",
                 segment_actions(board, layertable['Eco1.User']),
                 merge_polys=True,
                 break_curves=True
    )


powerlayer = layertable["B.Cu"]
# find a power net to add the zone to.
powernet = None
nets = board.GetNetsByName()
for name in ["+12V", "+5V", "GND"]:
    if (nets.has_key(name)):
        powernet = nets[name]

if (0):
    traverse_dxf("/bubba/electronicsDS/fusion/powerrails.dxf",
                 zone_actions(board, powernet, powerlayer),
                 merge_polys=True,
                 break_curves=True
    )


footprint_lib = '/home/mmccoo/kicad/kicad-footprints/MountingHole.pretty'

footprint_mapping = {
    "3.0": (footprint_lib, "MountingHole_3.2mm_M3")
    }

if (0):
    traverse_dxf("/bubba/electronicsDS/fusion/mountingholes.dxf",
                 mounting_actions(board, footprint_mapping))


if (0):
    traverse_dxf("/bubba/electronicsDS/fusion/leds_projection.dxf",
                 segment_actions(board, layertable['Cmts.User']),
                 merge_polys=True,
                 break_curves=True)


traverse_graphics(board, "B.SilkS",
                  segment_actions(board, layertable['Cmts.User']),
                  merge_polys=False,
                  break_curves=False)

pcbnew.Refresh()

