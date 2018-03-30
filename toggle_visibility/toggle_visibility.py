

import pcbnew

def ToggleVisibility():
    b = pcbnew.GetBoard()

    for mod in b.GetModules():
        r = mod.Reference()
        if (r.IsSelected()):
            r.SetVisible(not r.IsVisible())

        v = mod.Value()
        if (v.IsSelected()):
            v.SetVisible(not v.IsVisible())
