
import pcbnew
import wx
import os
import sys
import inspect
import pdb

import dxf_utils
from ..simpledialog import DialogUtils

import os.path

from dxf_utils import zone_actions
from dxf_utils import segment_actions
from dxf_utils import orient_actions
from dxf_utils import mounting_actions
from dxf_utils import traverse_dxf
from dxf_utils import traverse_graphics
import mounting

class DXFZoneDialog(DialogUtils.BaseDialog):
    def __init__(self):
        super(DXFZoneDialog, self).__init__("DXF Dialog")

        homedir = os.path.expanduser("~")
        self.file_picker = DialogUtils.FilePicker(self, homedir,
                                                  wildcard="DXF files (.dxf)|*.dxf",
                                                  configname="DXFZonedialog")
        self.AddLabeled(item=self.file_picker, label="DXF file",
                        proportion=0, flag=wx.ALL, border=2)

        self.basic_layer = DialogUtils.BasicLayerPicker(self, layers=['F.Cu', 'B.Cu'])
        self.AddLabeled(item=self.basic_layer, label="Target layer", border=2)

        self.net = DialogUtils.NetPicker(self)
        self.AddLabeled(item=self.net,
                        label="Target Net",
                        proportion=1,
                        flag=wx.EXPAND|wx.ALL,
                        border=2)

        # make the dialog a little taller than minimum to give the layer and net
        # lists a bit more space.
        self.IncSize(height=5)

class DXFZonePlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Convert a DXF to a zone"
        self.category = "A descriptive category name"
        self.description = "This plugin reads a dxf file and converts it to a zone"

    def Run(self):
        dlg = DXFZoneDialog()
        res = dlg.ShowModal()

        if res == wx.ID_OK:
            print("ok")
            if (dlg.net.value == None):
                warndlg = wx.MessageDialog(self, "no net was selected", "Error", wx.OK | wx.ICON_WARNING)
                warndlg.ShowModal()
                warndlg.Destroy()
                return

            net = dlg.net.GetValuePtr()

            traverse_dxf(dlg.file_picker.value,
                         zone_actions(pcbnew.GetBoard(),
                                      net,
                                      dlg.basic_layer.valueint),
                         merge_polys=True,
                         break_curves=True
            )
            #pcbnew.Refresh()
        else:
            print("cancel")

DXFZonePlugin().register()

class DXFGraphicDialog(DialogUtils.BaseDialog):
    def __init__(self):
        super(DXFGraphicDialog, self).__init__("DXF Dialog")

        homedir = os.path.expanduser("~")
        self.file_picker = DialogUtils.FilePicker(self, homedir,
                                                  wildcard="DXF files (.dxf)|*.dxf",
                                                  configname="DXFGraphicdialog")
        self.AddLabeled(item=self.file_picker, label="DXF file",
                        proportion=0, flag=wx.ALL, border=2)

        self.basic_layer = DialogUtils.BasicLayerPicker(self)
        self.AddLabeled(item=self.basic_layer, label="Target layer", border=2)



class DXFGraphicPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Convert a DXF to a graphic (Edge.Cuts, User.Cmts,...)"
        self.category = "A descriptive category name"
        self.description = "This plugin reads a dxf file and converts it to a zone"

    def Run(self):
        dlg = DXFGraphicDialog()
        res = dlg.ShowModal()

        print("dxf file {}".format(dlg.file_picker.value))
        print("layer {}".format(dlg.basic_layer.value))

        if res == wx.ID_OK:
            print("ok")
            traverse_dxf(dlg.file_picker.value,
                 segment_actions(pcbnew.GetBoard(), dlg.basic_layer.valueint),
                 merge_polys=False,
                 break_curves=True)

        else:
            print("cancel")

DXFGraphicPlugin().register()

class OrientToGraphicDialog(DialogUtils.BaseDialog):
    def __init__(self):
        super(OrientToGraphicDialog, self).__init__("Orient to Graphic")

        self.basic_layer = DialogUtils.BasicLayerPicker(self, layers=['Cmts.User', 'Eco1.User', 'Eco2.User'])
        self.AddLabeled(item=self.basic_layer, label="Target layer", border=2)

        self.mods = DialogUtils.ModulePicker(self, singleton=False)
        self.AddLabeled(item=self.mods,
                        label="all mods",
                        proportion=1,
                        flag=wx.EXPAND|wx.ALL,
                        border=2)

class OrientToGraphicPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Orient the selected modules to underlying graphics"
        self.category = "A descriptive category name"
        self.description = "This plugin moves/orients selected modules to align with graphic"

    def Run(self):
        dlg = OrientToGraphicDialog()
        res = dlg.ShowModal()

        print("layer {}".format(dlg.basic_layer.value))
        print("mods  {}".format(dlg.mods.value))

        traverse_graphics(pcbnew.GetBoard(), dlg.basic_layer.value,
                 orient_actions(pcbnew.GetBoard(), dlg.mods.value),
                 merge_polys=True,
                 break_curves=True)


OrientToGraphicPlugin().register()

class DXFToMountingPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "DXF circles to modules"
        self.category = "A descriptive category name"
        self.description = "This plugin places a module for each circle in a DXF"

    def Run(self):
        dlg = mounting.MountingDialog(configname = "mountingmap")
        res = dlg.ShowModal()

        if res != wx.ID_OK:
            return


        traverse_dxf(dlg.file_picker.value,
                     mounting_actions(pcbnew.GetBoard(),
                                      dlg.value,
                                      flip=dlg.flip.GetValue()))



DXFToMountingPlugin().register()
