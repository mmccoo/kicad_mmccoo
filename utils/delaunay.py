



import pcbnew
import numpy as np
import numpy
from scipy.spatial import Delaunay
#import matplotlib.pyplot as plt
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import minimum_spanning_tree
from sets import Set
import pdb


if (0):
    pts = []
    for mod in board.GetModules():
        for pad in mod.Pads():
            pts.append(tuple(pad.GetCenter()))

    pts = np.array(pts)

    tri = Delaunay(pts)

    if (0):
        plt.triplot(pts[:,0], pts[:,1], tri.simplices.copy())
        plt.plot(pts[:,0], pts[:,1], 'o')
        plt.show()



def draw_seg(board, p1, p2, layer):
    seg = pcbnew.DRAWSEGMENT(board)
    seg.SetShape(pcbnew.S_SEGMENT)
    seg.SetLayer(layer)

    seg.SetStart(pcbnew.wxPoint(*p1))
    seg.SetEnd(pcbnew.wxPoint(*p2))
    board.Add(seg)

def draw_triangulation(board, layer, pts):
    tri = Delaunay(np.array(pts))
    for simp in tri.simplices:
        (a,b,c) = simp
        draw_seg(board, pts[a], pts[b], layer)
        draw_seg(board, pts[b], pts[c], layer)
        draw_seg(board, pts[c], pts[a], layer)




def GenMSTRoutes(nets, mods, layername):
    board = pcbnew.GetBoard()

    # force that nets and mods are sets.
    nets = Set(nets)
    mods = Set(mods)

    # generate a name->layer table so we can lookup layer numbers by name.
    layertable = {}
    numlayers = pcbnew.PCB_LAYER_ID_COUNT
    for i in range(numlayers):
        layertable[pcbnew.GetBoard().GetLayerName(i)] = i

    layer = layertable[layername]

    netpts = {}
    for mod in board.GetModules():
        if (mod.GetReference() not in mods):
            continue

        for pad in mod.Pads():
            if (pad.GetLayerName() != layername):
                continue
            netname = pad.GetNet().GetNetname()
            if (netname not in nets):
                continue

            if (netname not in netpts):
                netpts[netname] = []
            netpts[netname].append(tuple(pad.GetCenter()))

    for via in board.GetTracks():
        if not pcbnew.VIA.ClassOf(via):
            continue
        if (via.BottomLayer() != layer) and (via.TopLayer() != layer):
            continue
        netname = via.GetNet().GetNetname()
        if (netname not in nets):
            continue

        if (netname not in netpts):
            netpts[netname] = []
        netpts[netname].append(tuple(via.GetPosition()))


    nettable = board.GetNetsByName()
    for netname in netpts:
        if (netname not in nets):
            continue

        pts = netpts[netname]
        matrix = np.zeros(shape=[len(pts),len(pts)])

        tri = Delaunay(np.array(pts))
        for simp in tri.simplices:
            (a,b,c) = simp
            matrix[a][b] = numpy.hypot(*numpy.subtract(pts[a], pts[b]))
            matrix[b][c] = numpy.hypot(*numpy.subtract(pts[b], pts[c]))
            matrix[c][a] = numpy.hypot(*numpy.subtract(pts[c], pts[a]))

        X = csr_matrix(matrix)
        Tcsr = minimum_spanning_tree(X)

        net = nettable[netname]
        nc = net.GetNetClass()
        #print("for net {}".format(net.GetNetname()))

        # info about iterating the results:
        # https://stackoverflow.com/a/4319087/23630
        rows,cols = Tcsr.nonzero()
        for row,col in zip(rows,cols):
            #print("   {} - {}".format(pts[row], pts[col]))
            newtrack = pcbnew.TRACK(board)
            # need to add before SetNet will work, so just doing it first
            board.Add(newtrack)
            newtrack.SetNet(net)
            newtrack.SetStart(pcbnew.wxPoint(*pts[row]))
            newtrack.SetEnd(pcbnew.wxPoint(*pts[col]))
            newtrack.SetWidth(nc.GetTrackWidth())
            newtrack.SetLayer(layer)




#pcbnew.Refresh()
