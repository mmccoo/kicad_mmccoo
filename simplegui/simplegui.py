

# sudo apt install wxglade for gui builder
# https://wiki.wxpython.org/AnotherTutorial
import wx 
import pcbnew


class SimpleGui(wx.Frame):
    def __init__(self, parent, board):
        wx.Frame.__init__(self, parent, title="this is the title")
        self.panel = wx.Panel(self) 
        label = wx.StaticText(self.panel, label = "Hello World")
        button = wx.Button(self.panel, label="Button label", id=1)
        
        nets = board.GetNetsByName()
        self.netnames = []
        for netname, net in nets.items():
            if (str(netname) == ""):
                continue
            self.netnames.append(str(netname))
        
        netcb = wx.ComboBox(self.panel, choices=self.netnames)
        netcb.SetSelection(0)

        netsbox = wx.BoxSizer(wx.HORIZONTAL)
        netsbox.Add(wx.StaticText(self.panel, label="Nets:"))
        netsbox.Add(netcb, proportion=1)
        
        modules = board.GetModules()
        self.modulenames = []
        for mod in modules:
            self.modulenames.append("{}({})".format(mod.GetReference(), mod.GetValue()))
        modcb = wx.ComboBox(self.panel, choices=self.modulenames)
        modcb.SetSelection(0)

        modsbox = wx.BoxSizer(wx.HORIZONTAL)
        modsbox.Add(wx.StaticText(self.panel, label="Modules:"))
        modsbox.Add(modcb, proportion=1)
        
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(label,   proportion=0)
        box.Add(button,  proportion=0)
        box.Add(netsbox, proportion=0)
        box.Add(modsbox, proportion=0)
        
        self.panel.SetSizer(box)
        self.Bind(wx.EVT_BUTTON, self.OnPress, id=1)
        self.Bind(wx.EVT_COMBOBOX, self.OnSelectNet, id=netcb.GetId())
        self.Bind(wx.EVT_COMBOBOX, self.OnSelectMod, id=modcb.GetId())
        
    def OnPress(self, event):
        print("in OnPress")

    def OnSelectNet(self, event):
        item = event.GetSelection()
        print("Net {} was selected".format(self.netnames[item]))

    def OnSelectMod(self, event):
        item = event.GetSelection()
        print("Module {} was selected".format(self.modulenames[item]))
        
def InitSimpleGui(board):
        sg = SimpleGui(None, board)
        sg.Show(True)
        return sg


sg = InitSimpleGui(pcbnew.GetBoard())
