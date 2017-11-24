import pdb
import pcbnew

board = pcbnew.GetBoard()

# the internal coorinate space of pcbnew is 10E-6 mm. (a millionth of a mm)
# the coordinate 121550000 corresponds to 121.550000 

SCALE = 1000000


if hasattr(pcbnew, "LAYER_ID_COUNT"):
    pcbnew.PCB_LAYER_ID_COUNT = pcbnew.LAYER_ID_COUNT

def coordsFromPolySet(ps):
    str = ps.Format()
    lines = str.split('\n')
    numpts = int(lines[2])
    pts = [[int(n) for n in x.split(" ")] for x in lines[3:-2]] # -1 because of the extra two \n
    return pts

def padsForNet(net):
    retval = []
    for pad in board.GetPads():
        # first get the netinfo, then get the netcode (int)
        if pad.GetNet().GetNet() == net:
            retval.append(pad)

    #for pad in retval:
    #    print("pad {} connected to {}".format(pad.GetName(), board.GetNetsByNetcode()[net].GetNetname()));
    return retval

from collections import defaultdict
class SheetInstance:

    # "static" helper functions
    @staticmethod
    def GetSheetChildId(child):
        global depth_of_array
        path = child.GetPath().split('/')
        path.pop(0) # pop the empty head
        # the path will be missing if you have modules added
        # directly in pcbnew, not imported from eeschema netlist.
        if (len(path) == 0):
            return (None, None)
        # if there are multiple sheet heirarchies, where's the replication?
        # does the top cell contain an arrayed child? or is the child of top
        # arrayed.
        # if you have a sheet heirarchy like this: /58DED9F1/58F8C609/58F8CB4E
        # 58F8CB4E is the lowest child thing/package (ie not a sheet)
        # 58DED9F1 is the top child
        # 58F8C609 is the instance in the middle.
        sheetid = "/".join(path[0:-1])
        childid = "/".join(path[-1:])
        return (sheetid, childid)

    @staticmethod
    def GetNetCanonical(net):
        pads = []
        for pad in padsForNet(net.GetNet()):
            sheetid, childid = SheetInstance.GetSheetChildId(pad.GetParent())
            pads.append((childid, pad.GetPadName()))
        pads.sort()

        cname = "_".join([i[0]+":"+i[1] for i in pads])
        #print("for net {} pads {}".format(net.GetNetname(), cname))
        return cname

    @staticmethod
    def NetIsSheetInternal(net):
        commonsheet = None
        #print("for net " + net.GetNetname())
        for pad in padsForNet(net.GetNet()):
            mod = pad.GetParent()
            sheetid, childid = SheetInstance.GetSheetChildId(mod)
            #print("  sheet {} child {} {}:{}".format(sheetid, str(childid), mod.GetReference(), pad.GetPadName()))
            if (childid == None):
                return None
            if commonsheet == None:
                commonsheet = sheetid
            if commonsheet != sheetid:
                return None
        return commonsheet
    
    @staticmethod
    def RegisterModulesAndNets(board):
        SheetInstance.__sheetinstances = {}
        SheetInstance.__child2sheetinstance = defaultdict(lambda: list())
        for child in board.GetModules():
            sheetid, childid = SheetInstance.GetSheetChildId(child)
            if (sheetid not in SheetInstance.__sheetinstances):
                SheetInstance.__sheetinstances[sheetid] = SheetInstance(sheetid)

            si = SheetInstance.__sheetinstances[sheetid]
            si.addChild(child)
            SheetInstance.__child2sheetinstance[childid].append(si)
        for net in board.GetNetsByNetcode().values():
            common = SheetInstance.NetIsSheetInternal(net)
            if common == None:
                continue
            si = SheetInstance.__sheetinstances[common]
            si.addInternalNet(net)
            
    @staticmethod
    def GetSheetInstanceForModule(child):
        return SheetInstance.__sheetinstances[SheetInstance.GetSheetChildId(child)[0]]

    @staticmethod
    def GetSheetInstances(child):
        sheetid, childid = SheetInstance.GetSheetChildId(child)
        return SheetInstance.__child2sheetinstance[childid]
        
    # methods
    def __init__(self, id):
        self.id = id
        self.children = {}
        self.internalnets = {}

    def __str__(self):
        retval = "sheet id is :" + self.id + " {"
        retval += ", ".join([m.GetReference() for m in self.children.values()])
        retval += "} internalnets: {"
        retval += ", ".join([n.GetNetname() for n in self.internalnets.values()])
        return retval
        
    def addChild(self, child):
        sheetid,childid = SheetInstance.GetSheetChildId(child)
        if (childid == None):
            return
        self.children[childid] = child

    def addInternalNet(self, net):
        cannon = SheetInstance.GetNetCanonical(net)
        self.internalnets[cannon] = net
        
    def getChildById(self, id):
        return self.children[id]

    def getChildCorrespondingToModule(self, child):
        sheetid, childid = SheetInstance.GetSheetChildId(child)        
        if (childid not in self.children):
            print("missing child {} others {}".format(mod.GetReference(),
                                                      ", ".join([m.GetReference()+" "+id+" "+m.GetPath() for id,m in self.children.items()])))
        return self.children[childid]

    def getChildren(self):
        return self.children.values()



    
SheetInstance.RegisterModulesAndNets(board)


# this trick came from here: http://stackoverflow.com/a/2669158
import re
tokenize = re.compile(r'(\d+)|(\D+)').findall
def natural_sortkey(string):          
    return tuple(int(num) if num else alpha for num, alpha in tokenize(string))

def replicate_sheet_trackst(fromnet, tonet, offset):
    board = tonet.GetParent()
    # remove tonet's old routing
    for track in board.TracksInNet(tonet.GetNet()):
        board.Remove(track)

    for track in board.TracksInNet(fromnet.GetNet()):
        if track.GetClass() == "VIA":
            # cloning is an easier way, but I want to ensure I
            # can create a Via from scratch
            #newvia = track.Clone()

            oldvia = board.GetViaByPosition(track.GetPosition())
            newvia = pcbnew.VIA(board)
            # need to add before SetNet will work, so just doing it first
            board.Add(newvia)
            toplayer=-1
            bottomlayer=pcbnew.PCB_LAYER_ID_COUNT
            for l in range(pcbnew.PCB_LAYER_ID_COUNT):
                if not track.IsOnLayer(l):
                    continue
                toplayer = max(toplayer, l)
                bottomlayer = min(bottomlayer, l)
            newvia.SetLayerPair(toplayer, bottomlayer)
            newvia.SetPosition(pcbnew.wxPoint(track.GetPosition().x+offset[0],
                                              track.GetPosition().y+offset[1]))
            newvia.SetViaType(oldvia.GetViaType())
            newvia.SetWidth(oldvia.GetWidth())
            newvia.SetNet(tonet)
        else:
            newtrack = pcbnew.TRACK(board)
            # need to add before SetNet will work, so just doing it first
            board.Add(newtrack)
            newtrack.SetStart(pcbnew.wxPoint(track.GetStart().x+offset[0],
                                             track.GetStart().y+offset[1]))
            newtrack.SetEnd(pcbnew.wxPoint(track.GetEnd().x+offset[0],
                                           track.GetEnd().y+offset[1]))
            newtrack.SetWidth(track.GetWidth())
            newtrack.SetLayer(track.GetLayer())

            newtrack.SetNet(tonet)

    fromzones = []
    tozones = []

    for zoneid in range(board.GetAreaCount()):
        zone = board.GetArea(zoneid)
        if (zone.GetNet().GetNetname() == fromnet.GetNetname()):
            fromzones.append(zone)
            continue;
        if (zone.GetNet().GetNetname() == tonet.GetNetname()):
            tozones.append(zone)
            continue;
    for zone in tozones:
        board.Remove(zone)

    for zone in fromzones:
        coords = coordsFromPolySet(zone.Outline())
        #pdb.set_trace()
        newzone = board.InsertArea(tonet.GetNet(), 0, zone.GetLayer(),
                                   coords[0][0]+int(offset[0]), coords[0][1]+int(offset[1]),
                                   pcbnew.CPolyLine.DIAGONAL_EDGE)
        newoutline = newzone.Outline()
        for pt in coords[1:]:
            newoutline.Append(pt[0]+offset[0], pt[1]+offset[1])
        newzone.Hatch()


def place_instances(mainref, pitch):
    
    pitch = (pitch[0] * SCALE, pitch[1] * SCALE)
    
    pivotmod = board.FindModuleByReference(mainref)

    sheetinstance = SheetInstance.GetSheetInstanceForModule(pivotmod)
    #peers = instances[pivotsheet]

    #print("getting for {}".format(pivotmod.GetReference()))
    arrayedsheets = sorted(SheetInstance.GetSheetInstances(pivotmod),
                           key = lambda elt: natural_sortkey(elt.getChildCorrespondingToModule(pivotmod).GetReference()))
    #replicasheets = sorted(children[pivotinstance], key=lambda elt: natural_sortkey(elt[2]))

    
    print("children of the same instance as {}: {}".format(mainref,
                                                           ",".join([m.GetReference() for m in sheetinstance.getChildren()])))
    
    basepositions = {}
    for mod in sheetinstance.getChildren():
        sheetid, childid = SheetInstance.GetSheetChildId(mod)
        basepositions[childid] = (mod.GetPosition().x,
                                  mod.GetPosition().y,
                                  mod.GetOrientation(),
                                  mod.IsFlipped())  

    print("basepositions {}".format(str(basepositions)))

    instnum = -1
    for i, si in enumerate(arrayedsheets):
        if (si.getChildCorrespondingToModule(pivotmod).GetReference() == mainref):
            instnum = i
            break

    print("{} is in index {}".format(mainref, instnum))

    # we start with index=-instnum because we want the pivot module to stay where it is.
    for idx, si in enumerate(arrayedsheets, start=-instnum):
        #print("placing instance {} {}".format(idx, si.id))
        if idx == 0:
            continue

        #first move the modules
        for peer in si.getChildren():            
            sheetid, childid = SheetInstance.GetSheetChildId(peer)
            newposition = basepositions[childid]
            newposition = (int(newposition[0] + idx*pitch[0]),
                           int(newposition[1] + idx*pitch[1]))
            #print("moving peer {} to {},{}".format(peer.GetReference(), newposition[0], newposition[1]))
            if (peer.IsFlipped() != basepositions[childid][3]):
                peer.Flip(peer.GetPosition())

            peer.SetPosition(pcbnew.wxPoint(*newposition))
            peer.SetOrientation(basepositions[childid][2])

        #copy the nets
        for fromnetid, fromnet in sheetinstance.internalnets.items():
            if fromnetid not in si.internalnets:
                #print("{} is missing from {}\n".format(fromnetid, ", ".join(si.internalnets.keys())))
                print("{} is missing\n".format(fromnetid))
                continue
        
            tonet = si.internalnets[fromnetid]
            print("copying net {} to {}".format(fromnet.GetNetname(), tonet.GetNetname()))
            replicate_sheet_trackst(fromnet, tonet, (idx*pitch[0],idx*pitch[1]))


            
#place_instances("U7", (0, -45))
#place_instances("U71", (0, -45))

place_instances("Q1", (6.5, 0))
place_instances("Q5", (6.5, 0))

board.BuildConnectivity()

pcbnew.Refresh();


