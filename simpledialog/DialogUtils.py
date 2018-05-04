
import pcbnew
import wx
import ntpath
import pdb
import os
from sets import Set

from ..save_config import save_config


# seems like this class shouldn't be necessary. It just creates a basic dialog with
# ok and cancel buttons. Very common. Surely, there is already such a class.
# This class gives a basic dialog with ok and cancel buttons.
class BaseDialog(wx.Dialog):
    def __init__(self, dialogname):
        pcbnew_frame = \
            filter(lambda w: w.GetTitle().startswith('Pcbnew'), wx.GetTopLevelWindows())[0]

        wx.Dialog.__init__(self, pcbnew_frame,
                           id=wx.ID_ANY,
                           title=dialogname,
                           pos=wx.DefaultPosition)

        self.ok_cbs = []

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.main_sizer)


        # add ok and cancel buttons.
        sizer_ok_cancel = wx.BoxSizer(wx.HORIZONTAL)
        self.main_sizer.Add(item=sizer_ok_cancel, proportion=0, flag=wx.EXPAND)

        ok_button = wx.Button(self, wx.ID_OK, u"OK", wx.DefaultPosition, wx.DefaultSize, 0)
        ok_button.SetDefault()
        sizer_ok_cancel.Add(item=ok_button, proportion=1) #, flag=wx.ALL, border=5)
        ok_button.Bind(wx.EVT_BUTTON, self.OnOK)

        cancel_button = wx.Button(self, wx.ID_CANCEL, u"Cancel", wx.DefaultPosition, wx.DefaultSize, 0)
        sizer_ok_cancel.Add(cancel_button, 1) #, wx.ALL, 5)


        self.ok_cancel_sizer_index = 0
        #self.Layout()
        self.Centre(wx.BOTH)

    # when the user clicks ok, we want to save stuff like directories used....
    def OnOK(self, event):
        for cb in self.ok_cbs:
            cb()
        event.Skip()

    # wx.EXPAND is important for scrolled children.
    def Add(self, item, proportion=0, flag=wx.EXPAND|wx.ALL, border=0, origitem=None):
        self.main_sizer.Insert(item=item,
                               before=self.ok_cancel_sizer_index,
                               flag = flag,
                               proportion=proportion,
                               border=border)

        self.ok_cancel_sizer_index = self.ok_cancel_sizer_index+1
        self.main_sizer.Layout()
        self.Layout()

        ok_cb = getattr(item, "OnOKCB", None)
        if(not ok_cb):
            ok_cb = getattr(origitem, "OnOKCB", None)
        if (callable(ok_cb)):
            self.ok_cbs.append(ok_cb)

    # wx.EXPAND is important for scrolled children.
    def AddLabeled(self, item, label, proportion=0, flag=wx.EXPAND|wx.ALL, border=0):
        # Add() above assumes wx.StaticBoxSizer is used. Remember that if deciding
        # not to use StaticBox here.
        static = wx.StaticBox(self, wx.ID_ANY, label)
        staticsizer = wx.StaticBoxSizer(static, wx.VERTICAL)
        # the default color is very lite on my linux system.
        # https://stackoverflow.com/a/21112377/23630
        static.SetBackgroundColour((150, 150, 150))

        item.Reparent(static)
        # do I really want to pass these arguments to both adds?
        staticsizer.Add(item, proportion=proportion, flag=flag, border=border)

        self.Add(staticsizer, proportion=proportion, flag=flag, border=border, origitem=item)

    def IncSize(self, width=0, height=0):
        # need a little extra size for the scrolled layers list.
        # based on this hint:
        # https://groups.google.com/forum/#!topic/wxpython-users/7zUmbnA3rGk
        fontsz = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT).GetPixelSize()
        size = self.GetSizer().CalcMin()
        size.height += fontsz.y*height
        size.width += fontsz.x*width
        self.SetClientSize(size)


class ScrolledPicker(wx.Window):
    def __init__(self, parent, singleton=True, cols=1):
        wx.Window.__init__(self, parent, wx.ID_ANY)

        self.singleton = singleton

        self.boxes = []

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)


        self.buttonwin = wx.Window(self)
        self.buttonsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.buttonwin.SetSizer(self.buttonsizer)
        self.sizer.Add(self.buttonwin)

        if (not singleton):
            self.value = Set()

            self.selectall = wx.Button(self.buttonwin, label="select all");
            self.selectall.Bind(wx.EVT_BUTTON, self.OnSelectAllNone)
            self.buttonsizer.Add(self.selectall)

            self.selectnone = wx.Button(self.buttonwin, label="select none");
            self.selectnone.Bind(wx.EVT_BUTTON, self.OnSelectAllNone)
            self.buttonsizer.Add(self.selectnone)

        self.scrolled = wx.ScrolledWindow(self, wx.ID_ANY)
        self.sizer.Add(self.scrolled, proportion=1, flag=wx.EXPAND|wx.ALL)

        fontsz = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT).GetPixelSize()
        self.scrolled.SetScrollRate(fontsz.x, fontsz.y)

        self.scrollsizer = wx.GridSizer(cols=cols, hgap=5, vgap=5)
        self.scrolled.SetSizer(self.scrollsizer)

    def Add(self, w):
        w.Reparent(self.scrolled)
        self.scrollsizer.Add(w)
        if (isinstance(w, wx.CheckBox) or isinstance(w, wx.RadioButton)):
            self.boxes.append(w)

    def AddSelector(self, name, binding=None):
        if (binding == None):
            binding = self.OnButton

        if (not self.singleton):
            rb = wx.CheckBox(self, label=name)
            rb.Bind(wx.EVT_CHECKBOX, binding)
        elif (len(self.boxes) == 0):
            # boxes gets updated in Add
            rb = wx.RadioButton(self.scrolled, label=name, style=wx.RB_GROUP)
            rb.Bind(wx.EVT_RADIOBUTTON, binding)
            self.SendSelectorEvent(rb)
        else:
            rb = wx.RadioButton(self.scrolled, label=name)
            rb.Bind(wx.EVT_RADIOBUTTON, binding)

        self.Add(rb)

    def OnButton(self, event):
        value = event.EventObject.GetLabel()

        if (self.singleton):
            self.value = value
        else:
            if (event.EventObject.IsChecked()):
                self.value.add(value)
            else:
                self.value.remove(value)


    def SendSelectorEvent(self, box):
        if (isinstance(box, wx.CheckBox)):
            # I have the feeling that this is the wrong way to trigger
            # an event.
            newevent = wx.CommandEvent(wx.EVT_CHECKBOX.evtType[0])
            newevent.SetEventObject(box)
            wx.PostEvent(box, newevent)

        if (isinstance(box, wx.RadioButton)):
            newevent = wx.CommandEvent(wx.EVT_RADIOBUTTON.evtType[0])
            newevent.SetEventObject(box)
            wx.PostEvent(box, newevent)


    def Clear(self):
        #self.scrollsizer.Clear()
        self.scrolled.DestroyChildren()
        self.boxes = []

    def OnSelectAllNone(self, event):
        newvalue = True
        if (event.EventObject == self.selectnone):
            newvalue = False

        for box in self.boxes:
            box.SetValue(newvalue)
            self.SendSelectorEvent(box)

class FilePicker(wx.Window):
    def __init__(self, parent, value=None, wildcard=None, configname=None):
        wx.Window.__init__(self, parent)

        self.configname = configname
        if (value == None):
            value = os.path.expanduser("~")

        if (self.configname != None):
            value = save_config.GetConfig(self.configname + ".path", value)

        self.value = value
        self.wildcard = wildcard

        sizer =  wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(sizer)

        self.selectedfile = wx.TextCtrl(parent=self,
                                        id=wx.ID_ANY,
                                        value=self.value,
                                        size=(490,25))
        self.selectedfile.Bind(wx.EVT_TEXT, self.OnText)
        sizer.Add(self.selectedfile, proportion=1)

        self.browse = wx.Button(self, label="browse");
        self.browse.Bind(wx.EVT_BUTTON, self.OnButton)

        sizer.Add(self.browse, proportion=0)

    def OnText(self, event):
        self.value = self.selectedfile.GetValue()


    def OnButton(self, event):
        fileDialog = wx.FileDialog(self, "open xyz",
                                   defaultDir=ntpath.dirname(self.value),
                                   defaultFile=ntpath.basename(self.value),
                                   style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if (self.wildcard != None):
            fileDialog.SetWildcard(self.wildcard)
        if fileDialog.ShowModal() == wx.ID_CANCEL:
            return
        self.value = fileDialog.GetPath()
        self.selectedfile.SetValue(self.value)

    def OnOKCB(self):
        if (self.configname != None):
            save_config.SaveConfig(self.configname + ".path", self.value)



class BasicLayerPicker(wx.Window):
    def __init__(self, parent, layers=None, cols=4):
        wx.Window.__init__(self, parent, wx.ID_ANY)

        if (layers == None):
            layers = ['F.Cu', 'F.Silks','Edge.Cuts', 'F.Mask',
                      'B.Cu', 'B.SilkS','Cmts.User', 'B.Mask']

        sizer = wx.GridSizer(cols=cols)#, hgap=5, vgap=5)
        self.SetSizer(sizer)

        board = pcbnew.GetBoard()
        self.layertable = {}
        numlayers = pcbnew.PCB_LAYER_ID_COUNT
        for i in range(numlayers):
            self.layertable[board.GetLayerName(i)] = i

        for layername in layers:
            if (layername not in self.layertable):
                ValueError("layer {} doesn't exist".format(layername))

            if (layername == layers[0]):
                rb = wx.RadioButton(self, label=layername, style=wx.RB_GROUP)
                self.value = layername
                self.valueint = self.layertable[layername]
            else:
                rb = wx.RadioButton(self, label=layername)
            rb.Bind(wx.EVT_RADIOBUTTON, self.OnButton)
            sizer.Add(rb)

    def OnButton(self, event):
        self.value = event.EventObject.GetLabel()
        self.valueint = self.layertable[self.value]

# when adding an instance of this class to a sizer, it's really important
# to pass the flag=wx.EXPAND
class AllLayerPicker(ScrolledPicker):
    def __init__(self, parent, singleton=True):
        numlayers = pcbnew.PCB_LAYER_ID_COUNT

        ScrolledPicker.__init__(self, parent, singleton=singleton, cols=4)

        for i in range(numlayers):
            layername = pcbnew.GetBoard().GetLayerName(i)
            self.AddSelector(layername)



class ModulePicker(ScrolledPicker):
    def __init__(self, parent, singleton=True):
        ScrolledPicker.__init__(self, parent, singleton=singleton, cols=4)

        if (not self.singleton):
            self.value = Set()

        self.board = pcbnew.GetBoard()
        modnames = [mod.GetReference() for mod in self.board.GetModules()]
        modnames.sort()

        for mod in modnames:
            self.AddSelector(mod)


class NetPicker(ScrolledPicker):
    def __init__(self, parent, singleton=True):
        ScrolledPicker.__init__(self, parent, singleton=singleton, cols=4)

        self.board = pcbnew.GetBoard()
        nets = [str(net) for net in self.board.GetNetsByName().keys() if (str(net) != "")]
        nets.sort()

        for net in nets:
            self.AddSelector(net)

    def GetValuePtr(self):
        nbn = self.board.GetNetsByName()
        if (self.singleton):
            return nbn[self.value]

        retval = []
        for net in self.value:
            retval.append(nbn[net])

        return retval

class FootprintDialog(BaseDialog):
    def __init__(self):
        super(FootprintDialog, self).__init__("simple dialog")

        # GetLogicalLibs gives wxStrings
        libnames = [str(s) for s in pcbnew.GetLogicalLibs()]

        self.libpicker = ScrolledPicker(self, cols=4)

        for lib in libnames:
            if (lib == libnames[0]):
                rb = wx.RadioButton(self.libpicker,
                                    label=lib,
                                    style=wx.RB_GROUP)
                self.lib = lib
            else:
                rb = wx.RadioButton(self.libpicker,
                                    label=lib)
            rb.Bind(wx.EVT_RADIOBUTTON, self.OnLibButton)
            self.libpicker.Add(rb)

        self.AddLabeled(item=self.libpicker,
                        label="Select a Library:",
                        proportion=1,
                        flag=wx.EXPAND|wx.ALL,
                        border=2)

        # this is to force the dialog to be wide enough to show all the libraries
        libx, liby = self.libpicker.scrollsizer.ComputeFittingWindowSize(self)
        self.SetMinSize(wx.Size(libx, -1))

        self.modpicker = ScrolledPicker(self, cols=2)
        self.AddLabeled(item=self.modpicker,
                        label="Select a Module:",
                        proportion=1,
                        flag=wx.EXPAND|wx.ALL,
                        border=2)
        self.SetLib()


        self.IncSize(25,15)


    def OnLibButton(self, event):
        self.lib = event.EventObject.GetLabel()
        self.SetLib();

    def OnModButton(self, event):
        self.value = (self.lib, event.EventObject.GetLabel())

    def SetLib(self):
        self.modpicker.Clear()

        mods = pcbnew.FootprintsInLib(self.lib)
        for mod in mods:
            if (mod == mods[0]):
                rb = wx.RadioButton(self.modpicker,
                                    label=mod,
                                    style=wx.RB_GROUP)
                self.value = (self.lib, mod)
            else:
                rb = wx.RadioButton(self.modpicker,
                                    label=mod)
            rb.Bind(wx.EVT_RADIOBUTTON, self.OnModButton)
            self.modpicker.Add(rb)


        self.Layout()
