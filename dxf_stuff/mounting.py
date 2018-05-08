import wx
import wx.lib
import wx.grid
import pcbnew
import ntpath
import pdb
import sys, os.path, inspect
from sets import Set

from ..save_config import save_config
from ..simpledialog import DialogUtils

# oldpath = sys.path
# # inspect.stack()[0][1] is the full path to the current file.
# sys.path.insert(0, os.path.dirname(inspect.stack()[0][1]))
# import DialogUtils
# import save_config
# sys.path = oldpath


class MountingDialog(DialogUtils.BaseDialog):
    def __init__(self, configname=None):
        super(MountingDialog, self).__init__("mounting hole dialog", onok=self.OnOKCB)

        homedir = os.path.expanduser("~")
        self.file_picker = DialogUtils.FilePicker(self, homedir,
                                                  wildcard="DXF files (.dxf)|*.dxf",
                                                  configname="mountingdialog")
        self.AddLabeled(item=self.file_picker, label="DXF file",
                        proportion=0, flag=wx.EXPAND|wx.ALL, border=2)

        self.grid = wx.Panel(self)
        self.gridSizer = wx.FlexGridSizer(cols=4, hgap=5, vgap=0)
        self.grid.SetSizer(self.gridSizer)

        self.configname = configname

        self.therows = {}

        self.mappings = []
        if self.configname != None:
            self.mappings = save_config.GetConfigComplex(self.configname, [])

        for size in self.mappings:
            lib,foot = self.mappings[size]
            self.AddOption(size, lib, foot)

        self.AddLabeled(self.grid, "diameter to footprint mappings",
                        proportion=1,
                        flag=wx.EXPAND|wx.ALL,
                        border=0)


        w = wx.Window(self)
        s = wx.BoxSizer(wx.HORIZONTAL)
        w.SetSizer(s)

        self.flip = wx.CheckBox(w, label="Flip to backside")
        s.Add(self.flip)

        self.add = wx.Button(w, label="Add Row")
        self.add.Bind(wx.EVT_BUTTON, self.OnAdd)
        s.Add(self.add, proportion=1)


        self.Add(w, flag=wx.EXPAND|wx.ALL, border=0)


        #self.IncSize(width=25, height=10)
        self.Fit()

    def AddOption(self, size, lib, foot):

        s = wx.SpinCtrlDouble(self.grid, value=str(size), inc=0.1)
        self.gridSizer.Add(s)

        print("lib {} foot {}".format(lib, foot))
        l = wx.StaticText(self.grid, label=lib)
        self.gridSizer.Add(l, proportion=1)

        f = wx.StaticText(self.grid, label=foot)
        self.gridSizer.Add(f, proportion=1)

        b = wx.Button(self.grid, label="remove")
        self.gridSizer.Add(b)
        b.Bind(wx.EVT_BUTTON, self.OnRemove)

        self.therows[b.GetId()] = (s,l,f,b)

    def OnAdd(self, event):
        dlg = DialogUtils.FootprintDialog()
        res = dlg.ShowModal()
        if (res != wx.ID_OK):
            return

        self.AddOption(1, dlg.libpicker.value, dlg.modpicker.value)
        self.Fit()


    def OnRemove(self, event):
        id = event.EventObject.GetId()
        wins = self.therows[id]
        del self.therows[id]
        wins[0].Destroy()
        wins[1].Destroy()
        wins[2].Destroy()
        wins[3].Destroy()

        self.Fit()

    def SetValue(self):
        self.value = {}
        for id in self.therows:
            row = self.therows[id]
            size = row[0].GetValue()
            lib  = row[1].GetLabel()
            foot = row[2].GetLabel()
            self.value[str(size)] = (lib, foot)

    def OnOKCB(self):
        self.SetValue()
        if (self.configname != None):
            save_config.SaveConfigComplex(self.configname, self.value)



# dlg = MountingDialog(configname = "mountingmap")
# res = dlg.ShowModal()

# print("lib {} footprint {}".format(dlg.value))

# print("nets {}".format(dlg.nets.value))
# print("mods {}".format(dlg.mods.value))
# #print("file {}".format(dlg.file_picker.filename))
# #print("basic layer {}".format(dlg.basic_layer.value))
# if res == wx.ID_OK:
#     print("ok")
# else:
#     print("cancel")
