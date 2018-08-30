

import pcbnew
import wx
import pdb

import inspect

import sys, os.path
import parse_svg_path

from ..simpledialog import DialogUtils

# I know, this code should really be merged into the dxf stuff. The same command could read
# svg and dxf and then use the callback actions classes.
# The two features were written at two different times,... whatever,
# Just don't feel like it at the moment. ;)


class SVG2ZoneDialog(DialogUtils.BaseDialog):
    def __init__(self):
        super(SVG2ZoneDialog, self).__init__("SVG Dialog")

        homedir = os.path.expanduser("~")
        self.file_picker = DialogUtils.FilePicker(self, homedir,
                                                  wildcard="SVG files (.svg)|*.svg",
                                                  configname="SVG2ZoneDialog")
        self.AddLabeled(item=self.file_picker, label="SVG file",
                        proportion=0, flag=wx.ALL, border=2)

        self.basic_layer = DialogUtils.BasicLayerPicker(self, layers=['F.Cu', 'B.Cu'])
        self.AddLabeled(item=self.basic_layer, label="Target layer", border=2)

        self.net = DialogUtils.NetPicker(self)
        self.AddLabeled(item=self.net,
                        label="Target Net",
                        proportion=1,
                        flag=wx.EXPAND|wx.ALL,
                        border=2)



        # make the dialog a little taller than minimum to give the layer list a bit more space.
        # self.IncSize(height=5)


class SVG2ZonePlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Convert an SVG to a zone...)"
        self.category = "A descriptive category name"
        self.description = "This plugin reads a svg file and converts it to a graphic"

    def Run(self):
        dlg = SVG2ZoneDialog()
        res = dlg.ShowModal()

        if res == wx.ID_OK:
            print("ok")

            if (dlg.net.value == None):
                warndlg = wx.MessageDialog(self, "no net was selected", "Error", wx.OK | wx.ICON_WARNING)
                warndlg.ShowModal()
                warndlg.Destroy()
                return

            # do it.
            SVG2Zone(dlg.file_picker.value,
                     pcbnew.GetBoard(),
                     dlg.basic_layer.valueint,
                     dlg.net.GetValuePtr())
        else:
            print("cancel")


class SVG2GraphicDialog(DialogUtils.BaseDialog):
    def __init__(self):
        super(SVG2GraphicDialog, self).__init__("SVG Dialog")

        homedir = os.path.expanduser("~")
        self.file_picker = DialogUtils.FilePicker(self, homedir,
                                                  wildcard="SVG files (.svg)|*.svg",
                                                  configname="SVG2GraphicDialog")
        self.AddLabeled(item=self.file_picker, label="SVG file",
                        proportion=0, flag=wx.ALL, border=2)

        self.basic_layer = DialogUtils.BasicLayerPicker(self, layers=['F.SilkS', 'Eco1.User','Dwgs.User','Edge.Cuts',
                                                                      'B.Silks', 'Eco2.User','Cmts.User'])
        self.AddLabeled(item=self.basic_layer, label="Target layer", border=2)


        # make the dialog a little taller than minimum to give the layer list a bit more space.
        # self.IncSize(height=5)


class SVG2GraphicPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Convert an SVG to a graphic (Silk, EdgeCuts,...)"
        self.category = "A descriptive category name"
        self.description = "This plugin reads a svg file and converts it to a graphic"

    def Run(self):
        dlg = SVG2GraphicDialog()
        res = dlg.ShowModal()

        if res == wx.ID_OK:
            print("ok")

            # do it.
            SVG2Graphic(dlg.file_picker.value,
                     pcbnew.GetBoard(),
                     dlg.basic_layer.valueint)
        else:
            print("cancel")


SVG2ZonePlugin().register()
SVG2GraphicPlugin().register()


def SVG2Zone(filename, board, layer, net):

    # the internal coorinate space of pcbnew is 10E-6 mm. (a millionth of a mm)
    # the coordinate 121550000 corresponds to 121.550000
    SCALE = 1000000.0


    # here I load from drawing.svg in the current directory. You'll want to change that path.
    paths = parse_svg_path.parse_svg_path(filename)
    if not paths:
        raise ValueError('wasnt able to read any paths from file')


    # things are a little tricky below, because the first boundary has its first
    # point passed into the creation of the new area. subsequent bounds are not
    # done that way.
    zone_container = None
    shape_poly_set = None

    for path in paths:
        for shape in path.group_by_bound_and_holes():
            shapeid = None
            if not shape_poly_set:
                # the call to GetNet() gets the netcode, an integer.
                zone_container = board.InsertArea(net.GetNet(), 0, layer,
                                                  int(shape.bound[0][0]*SCALE),
                                                  int(shape.bound[0][1]*SCALE),
                                                  pcbnew.CPolyLine.DIAGONAL_EDGE)
                shape_poly_set = zone_container.Outline()
                shapeid = 0
            else:
                shapeid = shape_poly_set.NewOutline()
                shape_poly_set.Append(int(shape.bound[0][0]*SCALE),
                                      int(shape.bound[0][1]*SCALE),
                                      shapeid)

            for pt in shape.bound[1:]:
                shape_poly_set.Append(int(pt[0]*SCALE), int(pt[1]*SCALE))

            for hole in shape.holes:
                hi = shape_poly_set.NewHole()
                # -1 to the third arg maintains the default behavior of
                # using the last outline.
                for pt in hole:
                    shape_poly_set.Append(int(pt[0]*SCALE), int(pt[1]*SCALE), -1, hi)

            zone_container.Hatch()


def make_line(board, start, end, layer):

    start = pcbnew.wxPoint(pcbnew.Millimeter2iu(start[0]), pcbnew.Millimeter2iu(start[1]))
    end   = pcbnew.wxPoint(pcbnew.Millimeter2iu(end[0]),   pcbnew.Millimeter2iu(end[1]))
    if (start == end):
        return
    seg = pcbnew.DRAWSEGMENT(board)
    seg.SetLayer(layer)
    seg.SetShape(pcbnew.S_SEGMENT)
    seg.SetStart(start)
    seg.SetEnd(end)
    board.Add(seg)


def SVG2Graphic(filename, board, layer):
    # the internal coorinate space of pcbnew is 10E-6 mm. (a millionth of a mm)
    # the coordinate 121550000 corresponds to 121.550000
    SCALE = 1000000.0


    # here I load from drawing.svg in the current directory. You'll want to change that path.
    paths = parse_svg_path.parse_svg_path(filename)
    if not paths:
        raise ValueError('wasnt able to read any paths from file')

    for path in paths:
        for shape in path.group_by_bound_and_holes():

            lastPt = shape.bound[0]
            for pt in shape.bound[1:]:
                # I'm getting repeated points from the svg. haven't investigated why.
                if (pt == lastPt):
                    continue
                make_line(board, lastPt, pt, layer)
                lastPt = pt


            for hole in shape.holes:
                lastPt = hole[0]
                for pt in hole[1:]:
                    if (pt == lastPt):
                        continue;
                    make_line(board, lastPt, pt, layer)
                    lastPt = pt



# this stuff is done for you by the plugin mechanicm.
# # In the future, this build connectivity call will not be neccessary.
# # I have submitted a patch to include this in the code for Refresh.
# # You'll know you needed it if pcbnew crashes without it.
# board.BuildConnectivity()

# pcbnew.Refresh()
print("done")
