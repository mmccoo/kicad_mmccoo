

import pcbnew
import re
import math
import numpy

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

def distpts(a,b):   
    return numpy.sqrt((a[0]-b[0])**2+(a[1]-b[1])**2)

def anglepts(a,b):
    return math.degrees(math.atan2(b[1]-a[1], b[0]-a[0]))

def longest_angle_for_polygon(poly):
    prevpt = poly[-1]
    length = None
    retval = None
    for pt in poly:
        d = distpts(prevpt, pt)
        if (length and (length>d)):
            prevpt = pt
            continue
        length = d
        retval = anglepts(prevpt, pt)
        prevpt = pt
    return retval

    
board = pcbnew.GetBoard()

type_table = {}
for t in filter(lambda t: re.match("PCB_.*_T", t), dir(pcbnew)):
    type_table[getattr(pcbnew, t)] = t
shape_table = {}
for s in filter(lambda s: re.match("S_.*", s), dir(pcbnew)):
    shape_table[getattr(pcbnew, s)] = s

#for d in board.GetDrawings():
#        print("type {} {} {}".format(type_table[d.Type()],
#                                  shape_table[d.GetShape()],
#                                  d.GetLayerName()))
for mod in board.GetModules():
    # this should be exposed better.
    modname = mod.GetFPID().GetLibItemName().c_str()
    if (modname != "LED_5730"):
        continue
    pos = mod.GetPosition()
    #print("mod {}".format(mod.GetReference()))
    for d in board.GetDrawings():
        if (d.GetLayerName() != 'Cmts.User'):
            continue
        bbox = d.GetBoundingBox()
        # this is just a rough check. the bbox can be much bigger then
        # the polygon is wraps around.
        if (not bbox.Contains(pos)):
            continue
        pts = [(pt.x, pt.y) for pt in d.GetPolyPoints()]
        inside = point_inside_polygon(pos.x, pos.y, pts)
        if (not inside):
            continue
        # negative angle because y goes down.
        angle = -longest_angle_for_polygon(pts)
        mod.SetOrientation(angle*10)
        mod.SetPosition(d.GetCenter())
        print("mod {} d {} {} {} {}".format(mod.GetReference(),
                                            bbox.GetPosition(),
                                            bbox.GetWidth(),
                                            bbox.GetHeight(),
                                            angle                                            
        ))
pcbnew.Refresh()
    
