

import wx
import wx.lib
import wx.grid
import pcbnew
import ntpath
import sys, os.path, inspect
from sets import Set

oldpath = sys.path
# inspect.stack()[0][1] is the full path to the current file.
sys.path.insert(0, os.path.dirname(inspect.stack()[0][1]))
import DialogUtils
sys.path = oldpath

class SimpleDialog(DialogUtils.BaseDialog):
    def __init__(self):
        super(SimpleDialog, self).__init__("simple dialog")

        text = wx.StaticText(self, wx.ID_ANY, u"Select the Input File",
                             wx.DefaultPosition, wx.DefaultSize, 0)
        text.Wrap(-1)

        # scrolltest = DialogUtils.ScrolledPicker(self)
        # for i in range(10):
        #     scrolltest.Add(wx.TextCtrl(parent=scrolltest, value='here' + str(i)));
        # self.AddLabeled(item=scrolltest, label="scrolled", proportion=1, border=2)

        # # https://wxpython.org/Phoenix/docs/html/wx.Sizer.html#wx.Sizer.Add
        # # https://wxpython.org/Phoenix/docs/html/wx.Sizer.html#wx-sizer
        # self.Add(item=text, proportion=0, flag=wx.ALL, border=5)

        # self.file_picker = DialogUtils.FilePicker(self, "/home/mmccoo/kicad/kicad_mmccoo/simpledialog/simpledialog.py")
        # self.Add(item=self.file_picker, proportion=0, flag=wx.ALL, border=5)

        # self.file_picker2 = DialogUtils.FilePicker(self, "/home/mmccoo/kicad/kicad_mmccoo/simpledialog/simpledialog.py")
        # self.AddLabeled(item=self.file_picker2, label="this is the label",
        #                 proportion=0, flag=wx.ALL, border=2)


        # self.basic_layer = DialogUtils.BasicLayerPicker(self)
        # self.AddLabeled(item=self.basic_layer, label="basic label", border=2)

        # self.basic_layer2 = DialogUtils.BasicLayerPicker(self)
        # self.Add(item=self.basic_layer2, flag=wx.EXPAND)

        # self.nets = DialogUtils.NetPicker(self, singleton=False)
        # self.AddLabeled(item=self.nets,
        #                 label="all nets",
        #                 proportion=1,
        #                 flag=wx.EXPAND|wx.ALL,
        #                 border=2)

        # self.mods = DialogUtils.ModulePicker(self, singleton=False)
        # self.AddLabeled(item=self.mods,
        #                 label="all mods",
        #                 proportion=1,
        #                 flag=wx.EXPAND|wx.ALL,
        #                 border=2)


        # self.all_layer = DialogUtils.AllLayerPicker(self)
        # self.AddLabeled(item=self.all_layer,
        #                 label="all layers",
        #                 proportion=1,
        #                 flag=wx.EXPAND|wx.ALL,
        #                 border=2)


        self.IncSize(height=10)

#dlg = SimpleDialog()
dlg = DialogUtils.FootprintDialog()
res = dlg.ShowModal()

print("lib {} footprint {}".format(dlg.libpicker.value, dlg.modpicker.value))

print("nets {}".format(dlg.nets.value))
print("mods {}".format(dlg.mods.value))
#print("file {}".format(dlg.file_picker.filename))
#print("basic layer {}".format(dlg.basic_layer.value))
if res == wx.ID_OK:
    print("ok")
else:
    print("cancel")
