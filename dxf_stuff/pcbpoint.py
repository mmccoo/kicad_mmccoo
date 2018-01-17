
import pcbnew

# kicad, like many programs uses a coordinate space where y=0 at the top and increases
# down. This is the reverse of what I was taught in high school math class.
# dxf file use the "normal" euclidean space.
# also, need to set the x,y origin to some place within the pcbnew canvas.



class pcbpoint:
    origin = (50,150)
    # the internal coorinate space of pcbnew is 10E-6 mm. (a millionth of a mm)
    # the coordinate 121550000 corresponds to 121.550000 
    SCALE = 1000000.0
    
    def __init__(self, x=0.0, y=0.0):
        if (type(x) == tuple):
            self.x = x[0]
            self.y = x[1]
        else:
            self.x = x
            self.y = y

    def wxpoint(self):
        # y is minus because y increases going down the canvase
        return pcbnew.wxPoint(int(self.SCALE*(self.origin[0]+self.x)),
                              int(self.SCALE*(self.origin[1]-self.y)))

    def __add__(self, other):
        return pcbpoint(self.x+other.x, self.y+other.y)

    def __str__(self):
        return "({},{})".format(self.x, self.y)
    
# p1 = pcbpoint(10,10)
# print("double {}".format(p1+p1))
# print("double {}".format((p1+p1).wxpoint()))

# pt = (42,77)
# p2 = pcbpoint(pt)
# print("double {}".format(p1+p2))
# print("double {}".format((p1+p2).wxpoint()))
