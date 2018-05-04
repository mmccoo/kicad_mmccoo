import pcbnew
from sets import Set


def GroundVias(nets, modules):

    board = pcbnew.GetBoard()
    # this blog argues what I'm doing here it bad:
    # http://www.johngineer.com/blog/?p=1319
    # generate a name->layer table so we can lookup layer numbers by name.
    layertable = {}
    numlayers = pcbnew.PCB_LAYER_ID_COUNT
    for i in range(numlayers):
        layertable[pcbnew.GetBoard().GetLayerName(i)] = i

    modules = Set(modules)

    nettable = board.GetNetsByName()

    netcodes = Set()
    for name in nets:
        if (name in nettable):
            netcodes.add(nettable[name].GetNet())

    toplayer    = layertable['F.Cu']
    bottomlayer = layertable['B.Cu']

    for mod in board.GetModules():
        if (mod.GetReference() not in modules):
            continue

        for pad in mod.Pads():
            netcode = pad.GetNetCode()
            if (netcode not in netcodes):
                continue

            newvia = pcbnew.VIA(board)
            # need to add before SetNet will work, so just doing it first
            board.Add(newvia)

            net = pad.GetNet()
            newvia.SetNet(net)
            nc = net.GetNetClass()
            newvia.SetWidth(nc.GetViaDiameter())
            newvia.SetPosition(pad.GetCenter())
            newvia.SetLayerPair(toplayer, bottomlayer)
            newvia.SetViaType(pcbnew.VIA_THROUGH)

#pcbnew.Refresh()
