

# sudo apt install wxglade for gui builder
# https://wiki.wxpython.org/AnotherTutorial
import wx 

class SimpleGui(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, title="this is the title")
        self.panel = wx.Panel(self) 
        label = wx.StaticText(self.panel, label = "Hello World")
        button = wx.Button(self.panel, label="Button label", id=1)
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(label,  proportion=0)
        box.Add(button, proportion=1)
        self.panel.SetSizer(box)
        self.Bind(wx.EVT_BUTTON, self.OnPress, id=1)

    def OnPress(self, event):
        print("in OnPress")

        
# this class is necessary to ensure proper timing of widget creation only after wx.App is ready.
class SimpleApp(wx.App):
    def OnInit(self):
        sg = SimpleGui(None)
        sg.Show(True)
        return True

# if you try to create wx.App twice, pcbnew will crash.
# I don't know all of the implications of this but I'm
# guessing that if you want two GUI'd script to coexist,
# they'll have to share one wx.App
if ('simpleapp' not in locals()):
    simpleapp = SimpleApp()
else:
    simpleapp.OnInit()
# you don't want app.MainLoop. Kicad already has a loop running.
# if you use the print command in your callbacks, the output won't
# show up in python scripting window, but it will print to
# xterm where you invoked kicad.
