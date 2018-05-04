

import pcbnew

powerratsoff = True

def TogglePowerRatnest():
    b = pcbnew.GetBoard()
    c = b.GetConnectivity()

    global powerratsoff
    print("setting power visibility to {}".format(powerratsoff))
    for net in ['GND', '+6V', '-6V']:
        nc = b.GetNetcodeFromNetname(net)
        c.SetVisible(nc, powerratsoff)

    powerratsoff = not powerratsoff
