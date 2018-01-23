
import pcbnew
import pdb
import math

# kicad, like many programs uses a coordinate space where y=0 at the top and increases
# down. This is the reverse of what I was taught in high school math class.
# dxf file use the "normal" euclidean space.
# also, need to set the x,y origin to some place within the pcbnew canvas.



class pcbpoint:
    origin = (50,150)
    # the internal coorinate space of pcbnew is 10E-6 mm. (a millionth of a mm)
    # the coordinate 121550000 corresponds to 121.550000 
    SCALE = 1000000.0
    
    def __init__(self, x=0.0, y=0.0, noscale=False):
        if (noscale):
            scale = 1
        else:
            scale = self.SCALE

        if (isinstance(x, pcbpoint)):
            self.x = x.x
            self.y = x.y
        elif (isinstance(x, pcbnew.wxPoint)):
            # later, when I get a wxpoint, I'll put the origin back
            self.x = x.x-self.origin[0]
            self.y = self.origin[1]-x.y
        elif (type(x) == tuple):
            self.x = int(scale*x[0])
            self.y = int(scale*x[1])
        elif (type(x) == list):
            pdb.set_trace()
        else:
            self.x = int(scale*x)
            self.y = int(scale*y)

            
    def wxpoint(self):
        # y is minus because y increases going down the canvase
        return pcbnew.wxPoint(self.origin[0]+self.x,
                              self.origin[1]-self.y)

    def polar(self, radius, angle):
        return pcbpoint(self.x + self.SCALE*radius*math.cos(math.radians(angle)),
                        self.y + self.SCALE*radius*math.sin(math.radians(angle)),
                        noscale=True
        )
        
    def __add__(self, other):
        return pcbpoint(self.x+other.x, self.y+other.y, noscale=True)

    def __str__(self):
        return "({},{})".format(self.x, self.y)

    def distance(self, other):
        return math.sqrt(float(self.x-other.x)**2+float(self.y-other.y)**2)
    
# p1 = pcbpoint(10,10)
# print("double {}".format(p1+p1))
# print("double {}".format((p1+p1).wxpoint()))

# pt = (42,77)
# p2 = pcbpoint(pt)
# print("double {}".format(p1+p2))
# print("double {}".format((p1+p2).wxpoint()))
