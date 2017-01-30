# Copyright [2017] [Miles McCoo]

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# this file is some basic examples of doing scripting in pcbnew's python
# interface.



import pcbnew

# most queries start with a board
board = pcbnew.GetBoard()

######
# NETS
######

# what to know all of the nets in your board?
# nets can be looked up in two ways:
#  by name
#  by netcode - a unique integer identifier for you net.

# returns a dictionary netcode:netinfo_item
netcodes = board.GetNetsByNetcode()

# list off all of the nets in the board.
for netcode, net in netcodes.items():
    print("netcode {}, name {}".format(netcode, net.GetNetname()))


# here's another way of doing the same thing.
print("here's the other way to do it")
nets = board.GetNetsByName()
for netname, net in nets.items():
    print("method2 netcode {}, name{}".format(net.GetNet(), netname))


# maybe you just want a single net
# the find method returns an iterator to all matching nets.
# the value of an iterator is a tuple: name, netinfo
clknet = nets.find("/clk").value()[1]
clkclass = clknet.GetNetClass()

print("net {} is on netclass {}".format(clknet.GetNetname(),
                                        clkclass))

#####################
# physical dimensions
#####################

# coordinate space of kicad_pcb is in mm. At the beginning of
# https://en.wikibooks.org/wiki/Kicad/file_formats#Board_File_Format
# "All physical units are in mils (1/1000th inch) unless otherwise noted."
# then later in historical notes, it says,
# As of 2013, the PCBnew application creates ".kicad_pcb" files that begin with
# "(kicad_pcb (version 3)". All distances are in millimeters. 

# the internal coorinate space of pcbnew is 10E-6 mm. (a millionth of a mm)
# the coordinate 121550000 corresponds to 121.550000 

SCALE = 1000000.0

boardbbox = board.ComputeBoundingBox()
boardxl = boardbbox.GetX()
boardyl = boardbbox.GetY()
boardwidth = boardbbox.GetWidth()
boardheight = boardbbox.GetHeight()

print("this board is at position {},{} {} wide and {} high".format(boardxl,
                                                                   boardyl,
                                                                   boardwidth,
                                                                   boardheight))

# each of your placed modules can be found with its reference name
# the module connection points are pad, of course.


padshapes = {
    pcbnew.PAD_SHAPE_CIRCLE:  "PAD_SHAPE_CIRCLE",
    pcbnew.PAD_SHAPE_OVAL:    "PAD_SHAPE_OVAL",
    pcbnew.PAD_SHAPE_RECT:    "PAD_SHAPE_RECT",
    pcbnew.PAD_SHAPE_TRAPEZOID: "PAD_SHAPE_TRAPEZOID"    
}
# new in the most recent kicad code
if hasattr(pcbnew, 'PAD_SHAPE_ROUNDRECT'):
    padshapes[pcbnew.PAD_SHAPE_ROUNDRECT] = "PAD_SHAPE_ROUNDRECT",


modref = "U1"
mod = board.FindModuleByReference(modref)
for pad in mod.Pads():
    print("pad {}({}) on {}({}) at {},{} shape {} size {},{}"
          .format(pad.GetPadName(),
                  pad.GetNet().GetNetname(),
                  mod.GetReference(),
                  mod.GetValue(),
                  pad.GetPosition().x, pad.GetPosition().y,
                  padshapes[pad.GetShape()],
                  pad.GetSize().x, pad.GetSize().y
          ))

########
# layers
########

layertable = {}

numlayers = pcbnew.LAYER_ID_COUNT
for i in range(numlayers):
    layertable[i] = board.GetLayerName(i)
    print("{} {}".format(i, board.GetLayerName(i)))



########
# tracks
########

# clk net was defined above as was SCALE
clktracks = board.TracksInNet(clknet.GetNet())
for track in clktracks:
    print("{},{}->{},{} width {} layer {}".format(track.GetStart().x/SCALE,
                                                  track.GetStart().y/SCALE,
                                                  track.GetEnd().x/SCALE,
                                                  track.GetEnd().y/SCALE,
                                                  track.GetWidth()/SCALE,
                                                  layertable[track.GetLayer()]))          
    
 
