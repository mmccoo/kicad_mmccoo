import numpy as np
import math

def polar(pt, ang, dist):
    return (pt[0] + dist*np.cos(ang),
            pt[1] + dist*np.sin(ang))

# 2pi is 360 degrees
# pi is 180
# pi/2 is 90
# pi/4 is 45
#print(polar((10,10), np.pi/2, 20))

def angle(pt1, pt2):
    return math.atan2(pt2[1]-pt1[1], pt2[0]-pt1[0])

#print(angle((10,10), (10,20))/np.pi)

# bulge is described here :
# http://www.lee-mac.com/bulgeconversion.html
# which used the function: polar described here:
# http://www.afralisp.net/autolisp/tutorials/calculating-polar-points.php
# 2*pi is 360 degrees


# the function and text below is a translation of this:
# http://www.lee-mac.com/bulgeconversion.html
# ;; Bulge to Arc  -  Lee Mac
# ;; p1 - start vertex
# ;; p2 - end vertex
# ;; b  - bulge
# ;; Returns: (<center> <start angle> <end angle> <radius>)

# (defun LM:Bulge->Arc ( p1 p2 b / a c r )
#     (setq a (* 2 (atan b))
#           r (/ (distance p1 p2) 2 (sin a))
#           c (polar p1 (+ (- (/ pi 2) a) (angle p1 p2)) r)
#     )
#     (if (minusp b)
#         (list c (angle c p2) (angle c p1) (abs r))
#         (list c (angle c p1) (angle c p2) (abs r))
#     )
# )
def bulge2arc(p1, p2, bulge):
    a = 2*np.arctan(bulge)
    r = math.hypot(p2[0]-p1[0], p2[1]-p1[1]) / 2.0 / np.sin(a)
    c = polar(p1, np.pi/2.0-a + angle(p1, p2), r)

    # in the code I stole above, the start and end angles are reversed
    # if bulge is negative. Even from reading the comments on that page,
    # I don't see why that is done.
    # later edit. The page also has this line:
    # "The returned bulge value may be positive or negative, depending
    # upon whether the arc passing through the three points traces a clockwise
    # or counter-clockwise path."
    # negative indicates clockwise.
    # so if going from point A->B at 90 degrees to -90 degress with bulge -1, we pass through 0
    # if going from -90 to 90 also with bulge -1, we don't pass through 0.
    #if (bulge<0):
    #    return (c, np.rad2deg(angle(c, p2)), np.rad2deg(angle(c, p1)), np.absolute(r))
    #else:
    a1 = np.rad2deg(angle(c, p1))
    a2 = np.rad2deg(angle(c, p2))
    # if clockwise (bulge<0) and the angles go from negative to positive, we
    # don't cross 0 degress.
    if (a1<0) and (a2>0) and (bulge<0):
        a1 = a1+360.0
    # if counterclockwise (bulge>0) and the angles go from positive to negative
    # we also don't cross 0 degrees
    if (a1>0) and (a2<0) and (bulge>0):
        a2 = a2+360.0
    return (c, a1, a2, np.absolute(r))

#print(bulge2arc((0,10), (10,0), .5))
