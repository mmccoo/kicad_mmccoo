
import xml.etree.ElementTree as ET
import re



# paths are explained here:
# https://www.w3schools.com/graphics/svg_path.asp
# sample (the letter a):
# m is move to
# q is a quadatric bezier curve
# z is close path
# d = m 161.0332,166.95004
# q -4.35547,0 -6.03515,0.9961 -1.67969,0.99609 -1.67969,3.39844 0,1.91406
#   1.25,3.04687 1.26953,1.11328 3.4375,1.11328 2.98828,0 4.78516,-2.10937
# 1.8164,-2.12891 1.8164,-5.64453 l 0,-0.80079 -3.57422,0 z m
# 7.16797,-1.48437 0,12.48047 -3.59375,0 0,-3.32031 q -1.23047,1.99218
# -3.0664,2.94921 -1.83594,0.9375 -4.49219,0.9375 -3.35938,0
# -5.35156,-1.875 -1.97266,-1.89453 -1.97266,-5.05859 0,-3.69141
# 2.46094,-5.56641 2.48047,-1.875 7.38281,-1.875 l 5.03906,0
# 0,-0.35156 q 0,-2.48047 -1.64062,-3.82812 -1.6211,-1.36719
# -4.57032,-1.36719 -1.875,0 -3.65234,0.44922 -1.77734,0.44922
# -3.41797,1.34765 l 0,-3.32031 q 1.97266,-0.76172 3.82813,-1.13281
# 1.85547,-0.39063 3.61328,-0.39063 4.74609,0 7.08984,2.46094
# 2.34375,2.46094 2.34375,7.46094 z

# but that has bezier curvers which kicad doesn't support
# do as described here to get segments
# http://www.inkscapeforum.com/viewtopic.php?t=4308

# the same a (though choppy) looks like this:
# <path
#  d="m 161.0332,166.95004 -2.84283,0.1445 -3.19232,0.8516
#  -0.41993,0.84961 -0.41992,0.84961 -0.41992,0.84961 -0.41992,0.84961
#  0.43815,1.90148 0.81185,1.14539 1.71875,0.55664 1.71875,0.55664
#  2.39258,-1.05468 2.39258,-1.05469 0.9082,-2.82226 0.9082,-2.82227
#  0,-0.4004 0,-0.40039 -1.78711,0 z
#  m 7.16797,-1.48437 0,6.24023
#  0,6.24024 -1.79688,0 -1.79687,0 0,-1.66016 0,-1.66015
#  -1.5332,1.4746 -1.5332,1.47461 -2.2461,0.46875 -2.24609,0.46875
#  -2.67578,-0.9375 -2.67578,-0.9375 -1.2647,-1.89966
#  -0.70796,-3.15893 0.61523,-1.39161 0.61524,-1.3916 0.61523,-1.3916
#  0.61524,-1.3916 3.89847,-1.40586 3.48434,-0.46914 2.51953,0
#  2.51953,0 0,-0.17578 0,-0.17578 0.0804,-1.64462 -1.72101,-2.1835
#  -2.28516,-0.6836 -2.28516,-0.68359 -1.82617,0.22461
#  -1.82617,0.22461 -1.70899,0.67382 -1.70898,0.67383 0,-1.66016
#  0,-1.66015 1.91406,-0.56641 1.91407,-0.5664 1.80664,-0.19532
#  1.80664,-0.19531 1.88598,0.30761 1.88599,0.30762 1.65893,0.92285
#  1.65894,0.92286 2.48728,4.46222 z"

class SVGShape:
    def __init__(self, bound, holes):
        self.bound = bound
        self.holes = holes
        
# in this class, I have a bunch of places where a helper method modifies the
# class. I don't really like the way I did that. It's not good coding. 
class SVGPath:
    def get_float(self):
        m = re.match("(-?[0-9]+(\.[0-9]*)?([eE]\-?[0-9]+)?)", self.d)
        if (not m):
            raise ValueError("expecting number, got {}".format(self.d))

        self.d = self.d[len(m.group(1)):].lstrip(" \t\n,")
        return float(m.group(1))

    def get_cmd(self, default):
        if (re.match("[lLmMzZ]", self.d[0])):
            retval = self.d[0]
            self.d = self.d[1:].lstrip(" \t\n,")
            return retval

        return default

    def get_pt(self):
        return (self.get_float(), self.get_float())
    
    def pt_add(self, a, b):
        return (a[0]+b[0], a[1]+b[1])
    
    def transform_pt(self, pt):
        if not self.trans:
            return pt

        # svg matrix transforms are described here:
        # quoting from here:
        # https://developer.mozilla.org/en-US/docs/Web/SVG/Attribute/transform
        # matrix(<a> <b> <c> <d> <e> <f>)
        #    This transform definition specifies a transformation in the form of
        #    a transformation matrix of six values.
        #    matrix(a,b,c,d,e,f) is equivalent to applying the transformation matrix
        #    ( a        c       e
        #      b        d       f
        #      0        0       1 )
        #   which maps coordinates from a previous coordinate system into a
        #   new coordinate system by the following matrix equalities:
        #    (xnewCoordSys ) =  ( a c e)  ( xprevCoordSys ) = ( axprevCoordSys+cyprevCoordSys+e )  
        #     ynewCoordSys        b d f     yprevCoordSys       bxprevCoordSys+dyprevCoordSys+f 
        #           1             0 0 1     1 )                 1  

        newx = self.trans[0] * pt[0] + self.trans[2] * pt[1] + self.trans[4]
        newy = self.trans[1] * pt[0] + self.trans[3] * pt[1] + self.trans[5]

        return (newx, newy)

    def append_pt(self, pt):
        self.curpoly.append(self.transform_pt(pt))

    def parse_path_string(self, d, trans):
        self.trans = trans

        self.polys = []
        self.curpoly = None

        firstloc = None
        curloc = None
        curcmd = None
        
        self.d = d.lstrip(" \t\n,")

        while self.d:
            # get_cmd returns passed argument as fallback
            cmd = self.get_cmd(curcmd)
                
            if (cmd == 'M'):
                curloc = self.get_pt()
                if (not firstloc):
                    firstloc = curloc
                if (not self.curpoly):
                    self.curpoly = []
                    self.polys.append(self.curpoly)
                self.append_pt(curloc)
                curcmd = 'L'

            elif (cmd == 'm'):
                pt = self.get_pt()
                if (curloc):
                    curloc = self.pt_add(curloc, pt)
                else:
                    # the first m of a path is treated as absolute
                    curloc = pt
                if (not firstloc):
                    firstloc = curloc
                if (not self.curpoly):
                    self.curpoly = []
                    self.polys.append(self.curpoly)
                self.append_pt(curloc)
                curcmd = 'l'

            elif (cmd == 'l'):
                pt = self.get_pt()
                curloc = self.pt_add(curloc, pt)
                self.append_pt(curloc)
                curcmd = 'l'
                
            elif (cmd == 'L'):
                curloc = self.get_pt()
                self.append_pt(curloc)
                curcmd = 'L'

            elif (cmd == 'z') or (cmd == 'Z'):
                self.append_pt(firstloc)
                self.curpoly = None
                curloc = firstloc
                firstloc = None

    # http://www.ariel.com.au/a/python-point-int-poly.html
    # determine if a point is inside a given polygon or not
    # Polygon is a list of (x,y) pairs.
    @staticmethod
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

    def group_by_bound_and_holes(self):
        # inkscape gives me a path by first listing the boundaries and then the holes.
        # I want to know a boundary and its holes, then another boundary,...
        # this function will reorder the polys that way.

        bounds = []
        holes = []
        for poly in self.polys:
            if not poly_is_hole(poly):
                bounds.append(poly)
            else:
                holes.append(poly)

        # a lookup table keyed off the boundary index.
        # the values are lists of holes
        bound_holes = {}
        for bi, bound in enumerate(bounds):
            for hi, hole in enumerate(holes):
                # pass x and y of the first point of hole.
                if SVGPath.point_inside_polygon(hole[0][0], hole[0][1], bound):
                    if bi not in bound_holes:
                        bound_holes[bi] = []
                    bound_holes[bi].append(hole)

        retshapes = []
        for bi, bound in enumerate(bounds):
            if (bi in bound_holes):
                retshapes.append(SVGShape(bound, bound_holes[bi]))
            else:
                retshapes.append(SVGShape(bound, []))

        return retshapes
            
    def __init__(self, d, trans):
        self.origd = d

        self.parse_path_string(d,trans)

        
# this site was helpful in debugging
# http://www.bluebit.gr/matrix-calculator/multiply.aspx
def multiply_transforms(a, b):
    # this assumes a and b are represented with these indexes
    # 0    2   4            <- these are indexes of a and b
    # 1    3   5
    # "0" "0" "1"           <- these always have the value 0 0 1
    retval = [
        a[0]*b[0]+a[2]*b[1],  # 0
        a[1]*b[0]+a[3]*b[1],  # 1
        a[0]*b[2]+a[2]*b[3],  # 2
        a[1]*b[2]+a[3]*b[3],  # 3
        a[0]*b[4]+a[2]*b[5]+a[4],  # 4
        a[1]*b[4]+a[3]*b[5]+a[5]   # 5
        ]
    return retval

    
# svg files can have multiple levels of transformation.
# find and combine them.
def combine_path_transforms(curtrans, curnode, parent_map):
    if ('transform' in curnode.attrib):
        trans = None
        mo = re.search("matrix\((.*)\)", curnode.attrib['transform'])
        if (mo):
            trans = [float(x) for x in mo.group(1).split(',')]

        mo = re.search("translate\((.*)\)", curnode.attrib['transform'])
        # quoting again from https://developer.mozilla.org/en-US/docs/Web/SVG/Attribute/transform
        # translate(<x> [<y>])
        #     This transform definition specifies a translation by x and y.
        #     This is equivalent to matrix(1 0 0 1 x y).
        #     If y is not provided, it is assumed to be zero.
        if (mo):
            trans = (1, 0, 0, 1) + tuple([float(x) for x in mo.group(1).split(',')])
            if len(trans) == 5:
                trans = trans + (0)
            
        if not trans:
            raise ValueError('wasnt able to match transform')

        if (curtrans):
            # need to multiply trans
            print("need to multiple {} and {}".format(trans, curtrans))
            curtrans = multiply_transforms(trans, curtrans)
        else:
            print("have trans {}".format(trans))
            curtrans = trans

            
    if (curnode not in parent_map):
        return curtrans

    return combine_path_transforms(curtrans, parent_map[curnode], parent_map)

def get_mm_from_dimension(val):
    mo = re.match("([0-9\.\-]+)(mm|cm|m|in|ft)", val)
    if (not mo):
        raise ValueError("expecting number with mm,cm,m,in, or ft dimension, got '{}'".format(val))

    num = float(mo.group(1))
    dim = mo.group(2)

    # number to multiply by to get mm
    multiplier = {
        "mm": 1.0,
        "cm": 10.0,
        "m":  1000.0,
        "in": 25.4,
        "ft": 25.4*12
    }
    if (dim not in multiplier):
        raise ValueError("this shouldn't happen. expecing a dimension of mm,cm,m,in or ft. Got {}".format(dim))

    return num*multiplier[dim]

    

    


def parse_svg_path(filepath):
    tree = ET.parse(filepath)
    root = tree.getroot()

    # width="100mm"
    # height="100mm"
    # viewBox="0 0 354.33071 354.33071"
    width  = get_mm_from_dimension(root.attrib['width'])
    height = get_mm_from_dimension(root.attrib['height'])
    box    = [float(x) for x in root.attrib['viewBox'].split(" ")]

    # throughout path parsing, various transformations need to be applied
    # these are embedded in the path as well as parent groups.
    # the last transformation is into the target coordinate system,
    # based a projection of viewbox into 0->width and 0->height
    # xfinal = (x-xl_viewbox)/(xh_viewbox-xl_viewbox)*width
    # so we have a stretch factor of 1/(xh-xl)*width and an offset of xl*width

    # as with the rest of the transformations, I reference here:
    # https://developer.mozilla.org/en-US/docs/Web/SVG/Attribute/transform
    # this page is also helpful:
    # https://en.wikipedia.org/wiki/Transformation_matrix
    (xl, yl, xh, yh) = tuple(box)

    # a c e   1.0/(xh-xl)*width  0                   xl*width
    # b d f   0                  1.0/(yh-yl)*height  yl*height
    # 0 0 1
    coordtrans = (1.0/(xh-xl)*width, 0,
                  0, 1.0/(yh-yl)*height,
                  xl*width, yl*height)
    print("coortrans is {}".format(coordtrans))
    # from here: https://stackoverflow.com/a/20132342/23630
    parent_map = {c:p for p in tree.iter() for c in p}

    retval = []
    for path in root.iter('{http://www.w3.org/2000/svg}path'):
        points = path.attrib['d']

        # here I pass in None as the initial transform.
        # this is because combine, combines on the way up.
        # coordtrans is the top most transform.
        # I could also have combine do the matrix stuff on the way
        # down, but it was already written when I realized I needed
        # coordtrans
        curtrans = combine_path_transforms(None, path, parent_map)
        if (curtrans):
            curtrans = multiply_transforms(coordtrans, curtrans)
        else:
            curtrans = coordtrans
        print("using transform {}".format(curtrans))
        p = SVGPath(points, curtrans)
        retval.append(p)
    return retval

def path_bbox(path):

    xl = min([min([pt[0] for pt in poly]) for poly in path.polys])
    xh = max([max([pt[0] for pt in poly]) for poly in path.polys])
    yl = min([min([pt[1] for pt in poly]) for poly in path.polys])
    yh = max([max([pt[1] for pt in poly]) for poly in path.polys])


    return (xl,yl,xh,yh)

def poly_is_hole(poly):
    # to determine if a poly is a hole or outer boundary i check for
    # clockwise or counter-clockwise.
    # As suggested here:
    # https://stackoverflow.com/a/1165943/23630
    # I take the area under the curve, and if it's positive or negative
    # I'll know bounds or hole.
    lastpt = poly[-1]
    area = 0.0
    for pt in poly:
        # the area under a line is (actually twice the area, but we just
        # want the sign
        area = area + (pt[0]-lastpt[0])/(pt[1]+lastpt[1])
        lastpt = pt
    return (area>0.0)

# paths= parse_svg_path('/home/mmccoo/kicad/kicad_mmccoo/svg2border/drawing.svg')
# for path in paths:
#     print("path")
#     for poly in path.polys:
#         print("    points {}".format(poly))
