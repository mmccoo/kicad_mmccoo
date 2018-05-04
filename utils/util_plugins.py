

import pcbnew
import wx
from ..simpledialog import DialogUtils
import groundvias
import delaunay
import via_fill


class GroundViasDialog(DialogUtils.BaseDialog):
    def __init__(self):
        super(GroundViasDialog, self).__init__("Ground vias dialog")


        self.nets = DialogUtils.NetPicker(self, singleton=False)
        self.AddLabeled(item=self.nets,
                        label="Target Net",
                        proportion=1,
                        flag=wx.EXPAND|wx.ALL,
                        border=2)

        self.mods = DialogUtils.ModulePicker(self, singleton=False)
        self.AddLabeled(item=self.mods,
                        label="all mods",
                        proportion=1,
                        flag=wx.EXPAND|wx.ALL,
                        border=2)


        # make the dialog a little taller than minimum to give the layer and net
        # lists a bit more space.
        self.IncSize(width=50, height=10)


class GroundViasPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Drop a via on module pads of net"
        self.category = "A descriptive category name"
        self.description = "This plugin finds all pads on selected nets and drops a via"

    def Run(self):
        dlg = GroundViasDialog()
        res = dlg.ShowModal()

        groundvias.GroundVias(dlg.nets.value, dlg.mods.value)

GroundViasPlugin().register()


class MSTRoutesDialog(DialogUtils.BaseDialog):
    def __init__(self):
        super(MSTRoutesDialog, self).__init__("MST Routes dialog")

        self.basic_layer = DialogUtils.BasicLayerPicker(self, layers=['F.Cu', 'B.Cu'])
        self.AddLabeled(item=self.basic_layer, label="target layer", border=2)

        self.nets = DialogUtils.NetPicker(self, singleton=False)
        self.AddLabeled(item=self.nets,
                        label="Target Nets",
                        proportion=1,
                        flag=wx.EXPAND|wx.ALL,
                        border=2)

        self.mods = DialogUtils.ModulePicker(self, singleton=False)
        self.AddLabeled(item=self.mods,
                        label="all mods",
                        proportion=1,
                        flag=wx.EXPAND|wx.ALL,
                        border=2)

        # make the dialog a little taller than minimum to give the layer and net
        # lists a bit more space.
        self.IncSize(width=50, height=10)

class MSTRoutesPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Generate Minimum Spanning Tree route"
        self.category = "A descriptive category name"
        self.description = "This plugin computes an MST for selected nets/modules and generates a route from that"

    def Run(self):
        dlg = MSTRoutesDialog()
        res = dlg.ShowModal()

        delaunay.GenMSTRoutes(dlg.nets.value, dlg.mods.value, dlg.basic_layer.value)

MSTRoutesPlugin().register()


class ViaFillDialog(DialogUtils.BaseDialog):
    def __init__(self):
        super(ViaFillDialog, self).__init__("Via Fill dialog")

        self.nets = DialogUtils.NetPicker(self, singleton=False)
        self.AddLabeled(item=self.nets,
                        label="Target Nets",
                        proportion=1,
                        flag=wx.EXPAND|wx.ALL,
                        border=2)

class ViaFillPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Fill vias"
        self.category = "A descriptive category name"
        self.description = "This plugin tries to place many vias between zones of a net."

    def Run(self):
        dlg = ViaFillDialog()
        res = dlg.ShowModal()

        via_fill.ViaFill(dlg.nets.value)


ViaFillPlugin().register()
