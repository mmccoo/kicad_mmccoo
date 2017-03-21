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

# this script is to reproduce a bug (I think it's a bug) in the zone addition APIs
# if you don't call newoutline.CloseLastContour() after calls to
# newoutline.AppendCorner, saving to file will yield a file that won't load.
    

import pcbnew

board = pcbnew.GetBoard()

# generate a name->layer table so we can lookup layer numbers by name.
layertable = {}
numlayers = pcbnew.LAYER_ID_COUNT
for i in range(numlayers):
    layertable[board.GetLayerName(i)] = i


nets = board.GetNetsByName()
randomnet = None
for netpair in nets.items():
    if (len(str(netpair[0])) != 0):
        randomnet = netpair[1]
        break

layer = layertable["B.Cu"]

    
newarea = board.InsertArea(net.GetNet(), 0, layer,
                           pcbnew.FromMM(10), pcbnew.FromMM(10),
                           pcbnew.CPolyLine.DIAGONAL_EDGE)

newoutline = newarea.Outline()
newoutline.AppendCorner(pcbnew.FromMM(10), pcbnew.FromMM(20));
newoutline.AppendCorner(pcbnew.FromMM(20), pcbnew.FromMM(20));
newoutline.AppendCorner(pcbnew.FromMM(20), pcbnew.FromMM(10));


# this next line shouldn't really be necessary but without it, saving to
# file will yield a file that won't load.
# newoutline.CloseLastContour()

newoutline.Hatch()


# Error loading board.
# IO_ERROR: Expecting 'net, layer, tstamp, hatch, priority, connect_pads, min_thickness, fill, polygon, filled_polygon, or fill_segments' in input/source
# '/bubba/electronicsDS/kicad/leddriver2/bug.kicad_pcb'
# line 2947, offset 4

# from dsnlexer.cpp : Expecting() line:369

    
print("done")
