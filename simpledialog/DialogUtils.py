
import pcbnew
import wx
import ntpath
import pdb

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

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.main_sizer)

        
        # add ok and cancel buttons.
        sizer_ok_cancel = wx.BoxSizer(wx.HORIZONTAL)
        self.main_sizer.Add(item=sizer_ok_cancel, proportion=0, flag=wx.EXPAND)

        ok_button = wx.Button(self, wx.ID_OK, u"OK", wx.DefaultPosition, wx.DefaultSize, 0)
        ok_button.SetDefault()
        sizer_ok_cancel.Add(item=ok_button, proportion=1) #, flag=wx.ALL, border=5)

        cancel_button = wx.Button(self, wx.ID_CANCEL, u"Cancel", wx.DefaultPosition, wx.DefaultSize, 0)
        sizer_ok_cancel.Add(cancel_button, 1) #, wx.ALL, 5)


        self.ok_cancel_sizer_index = 0    
        #self.Layout()
        self.Centre(wx.BOTH)


    # wx.EXPAND is important for scrolled children.
    def Add(self, item, proportion=0, flag=wx.EXPAND|wx.ALL, border=0):
        self.main_sizer.Insert(item=item,
                               before=self.ok_cancel_sizer_index,
                               flag = flag,
                               proportion=proportion,
                               border=border)

        self.ok_cancel_sizer_index = self.ok_cancel_sizer_index+1
        self.main_sizer.Layout()
        self.Layout()

    # wx.EXPAND is important for scrolled children.
    def AddLabeled(self, item, label, proportion=0, flag=wx.EXPAND|wx.ALL, border=0):
        static = wx.StaticBox(self, wx.ID_ANY, label)
        staticsizer = wx.StaticBoxSizer(static, wx.VERTICAL)
        # the default color is very lite on my linux system.
        # https://stackoverflow.com/a/21112377/23630
        static.SetBackgroundColour((150, 150, 150))
        
        item.Reparent(static)
        # do I really want to pass these arguments to both adds?
        staticsizer.Add(item, proportion=proportion, flag=flag, border=border)

        # it's important to add the correrct thing to sizer. when using staticboxsizer,
        # the sizer takes over. The static box is secondary. This is different from normal
        # window/sizer relationships. We add the sizer, not the staticbox
        self.Add(staticsizer, proportion=proportion, flag=flag, border=border)

    def IncHeight(self, h):
        # need a little extra size for the scrolled layers list.
        # based on this hint:
        # https://groups.google.com/forum/#!topic/wxpython-users/7zUmbnA3rGk
        fontsz = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT).GetPixelSize()
        size = self.GetSizer().CalcMin()
        size.height += fontsz.y*h
        self.SetClientSize(size)


class ScrolledPicker(wx.ScrolledWindow):
    def __init__(self, parent, rows = 4, cols=1):
        wx.ScrolledWindow.__init__(self, parent, wx.ID_ANY)
        
        fontsz = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT).GetPixelSize()
        self.SetScrollRate(fontsz.x, fontsz.y)

        self.scrollsizer = wx.GridSizer(rows=rows, cols=cols, hgap=5, vgap=5)
        self.SetSizer(self.scrollsizer)

    def Add(self, w):
        self.scrollsizer.Add(w)


class FilePicker(wx.Window):
    def __init__(self, parent, value, wildcard=None):
        wx.Window.__init__(self, parent)

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
        print("on button")
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

class BasicLayerPicker(wx.Window):
    def __init__(self, parent, layers=None, rows=2):
        wx.Window.__init__(self, parent, wx.ID_ANY)

        if (layers == None):
            layers = ['F.Cu', 'F.Silks','Edge.Cuts', 'F.Mask',
                      'B.Cu', 'B.SilkS','Cmts.User', 'B.Mask']

        sizer = wx.GridSizer(rows=rows, cols=len(layers)/rows)#, hgap=5, vgap=5)
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
    def __init__(self, parent):
        numlayers = pcbnew.PCB_LAYER_ID_COUNT

        ScrolledPicker.__init__(self, parent, rows=numlayers/4+1, cols=4)

        layertable = {}

        for i in range(numlayers):
            layername = pcbnew.GetBoard().GetLayerName(i)
            layertable[layername] = i
            if (i==0):
                rb = wx.RadioButton(self,
                                    label=layername,
                                    style=wx.RB_GROUP)
                self.value = layername
            else:
                rb = wx.RadioButton(self,
                                    label=layername)
            rb.Bind(wx.EVT_RADIOBUTTON, self.OnButton)
            self.Add(rb)

    def OnButton(self, event):
        self.value = event.EventObject.GetLabel()

        
class NetPicker(ScrolledPicker):
    def __init__(self, parent):
        self.board = pcbnew.GetBoard()
        nets = [str(net) for net in self.board.GetNetsByName().keys() if (str(net) != "")]
        nets.sort()
        

        ScrolledPicker.__init__(self, parent, rows=len(nets)/4+1, cols=4)

        for net in nets:
            if (net == nets[0]):
                rb = wx.RadioButton(self,
                                    label=net,
                                    style=wx.RB_GROUP)
                self.value = net
                self.valueptr = self.board.GetNetsByName()[net]
            else:
                rb = wx.RadioButton(self,
                                    label=net)
            rb.Bind(wx.EVT_RADIOBUTTON, self.OnButton)
            self.Add(rb)

    def OnButton(self, event):
        self.value = event.EventObject.GetLabel()
        self.valueptr = self.board.GetNetsByName()[self.value]
     
        
