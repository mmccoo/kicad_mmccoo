import inspect

import sys, os.path
oldpath = sys.path
# inspect.stack()[0][1] is the full path to the current file.
sys.path.insert(0, os.path.dirname(inspect.stack()[0][1]))
import parse_svg_path
sys.path = oldpath


paths = parse_svg_path.parse_svg_path('/home/mmccoo/kicad/kicad_mmccoo/svg2border/drawing.svg')

for path in paths:
    print("path {}".format(parse_svg_path.path_bbox(path)))
    #for poly in path.polys:
        #print("    points {}".format(poly))
        #print("        is hole {}".format(parse_svg_path.poly_is_hole(poly)))
        # print("    points 18{}".format(poly))
    for shape in path.group_by_bound_and_holes():
        print("bounds: {}".format(shape.bound))
        print("with holes:")
        for hole in shape.holes:
            print("   hole: {}".format(hole))
        
