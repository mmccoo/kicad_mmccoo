

import pcbnew
import wx
import wx.aui


# get the path of this script. Will need it to load the png later.
import inspect
import os
filename = inspect.getframeinfo(inspect.currentframe()).filename
path = os.path.dirname(os.path.abspath(filename))
print("running {} from {}".format(filename, path))


def findPcbnewWindow():
    windows = wx.GetTopLevelWindows()
    pcbnew = [w for w in windows if w.GetTitle()[0:6] == "Pcbnew"]
    if len(pcbnew) != 1:
        raise Exception("Cannot find pcbnew window from title matching!")
    return pcbnew[0]

pcbwin = findPcbnewWindow()


# 6038 is the value that H_TOOLBAR from kicad/include/id.h happens to get.
# other interesting values include:
# 6041 is AUX_TOOLBAR. That's the second row of stuff in the pcbnew gui.
#    it contains things like track width, via size, grid
# 6039 is V_TOOLBAR, the right commands window. zoom to selection, highlight net.
# 6040 is OPT_TOOLBAR, the left commands window. disable drc, hide grid, display polar

# kicad/include/id.h has been added to pcbnew's interface. If you get the error
# that ID_H_TOOLBAR doesn't exist, it's probably because you need to update your
# version of kicad.
top_tb = pcbwin.FindWindowById(pcbnew.ID_H_TOOLBAR)



# let's look at what top level frames/windows we have. These include the
#
#children = {}
#for subwin in pcbwin.Children:
#    id = subwin.GetId()
#    children[id] = subwin
#    print("subwin {} {} {}".format(subwin.GetLabel(), subwin.GetClassName(), subwin.GetId()))

# for idx in range(top_tb.GetToolCount()):
#     tbi = top_tb.FindToolByIndex(idx)
#     #print("toolbar item {}".format(tbi.GetShortHelp()))



def MyButtonsCallback(event):
    # when called as a callback, the output of this print
    # will appear in your xterm or wherever you invoked pcbnew.
    print("got a click on my new button {}".format(str(event)))





# Plan for three sizes of bitmaps:
# SMALL - for menus         - 16 x 16
# MID   - for toolbars      - 26 x 26
# BIG   - for program icons - 48 x 48
# bitmaps_png/CMakeLists.txt

bm = wx.Bitmap(path + '/hello.png', wx.BITMAP_TYPE_PNG)


itemid = wx.NewId()
top_tb.AddTool(itemid, "mybutton", bm, "this is my button", wx.ITEM_NORMAL)
top_tb.Bind(wx.EVT_TOOL, MyButtonsCallback, id=itemid)
top_tb.Realize()

