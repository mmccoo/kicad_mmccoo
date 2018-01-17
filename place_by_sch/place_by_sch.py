

import pcbnew
import os.path
import re


def PlaceBySch():
    board = pcbnew.GetBoard()

    board_path = board.GetFileName()
    sch_path = board_path.replace(".kicad_pcb", ".sch")

    if (not os.path.isfile(sch_path)):
        raise ValueError("file {} doesn't exist".format(sch_path))

    # some documentation on eeschema file format
    # https://en.wikibooks.org/wiki/Kicad/file_formats#Schematic_Files_Format
    # schematic files are written here:
    # eeschema/sch_legacy_plugin.cpp
    # rotation is given here:
    # TRANSFORM transform = aComponent->GetTransform();
    #    m_out->Print( 0, "\t%-4d %-4d %-4d %-4d\n",
    #                  transform.x1, transform.y1, transform.x2, transform.y2 );

    # $Comp
    # L Device:LED D49
    # U 1 1 5A3B7115
    # P 6650 1500
    # F 0 "D49" H 6641 1716 50  0000 C CNN
    # F 1 "LED" H 6641 1625 50  0000 C CNN
    # F 2 "Miles:LED_5730" H 6650 1500 50  0001 C CNN
    # F 3 "~" H 6650 1500 50  0001 C CNN
    # 	1    6650 1500
    # 	1    0    0    -1  
    # $EndComp

    newcomp_p = re.compile('\$Comp')
    endcomp_p = re.compile('\$EndComp')
    comp_label_p = re.compile('L (\S+) (\S+)')
    trans_p = re.compile('\t([\-0-9]+)\s+([\-0-9]+)\s+([\-0-9]+)\s+([\-0-9]+)')
    footprint_p = re.compile('F 2 "(\S+)" [VH] (\d+) (\d+)')

    c1 = '$Comp'
    l1 = 'L Device:LED D49'
    t0   = '	1    0    0    -1'
    t180 = '	-1   0    0    1'
    t180f = '	-1   0    0    -1' # this is flipped horizontally
    tM90 = '	0    1    1    0'
    t90  = '	0    -1   -1   0'
    orientations = {
        str(trans_p.match(t0).groups()): 0,
        str(trans_p.match(t180).groups()): 180,
        str(trans_p.match(t180f).groups()): 180,
        str(trans_p.match(tM90).groups()): -90,
        str(trans_p.match(t90).groups()): 90
    }

    def parse_eeschema(filename):
        retval = {}
        with open(filename) as f:
            incomp = False
            curcomp = "";
            x = -1
            y = -1
            orient = 0;
            for line in f:
                bc = newcomp_p.match(line)
                ec = endcomp_p.match(line)
                l = comp_label_p.match(line)
                t = trans_p.match(line)
                fp = footprint_p.match(line)
                if (bc):
                    incomp = True
                    #print("new comp")
                elif (ec):
                    incomp = False
                    retval[curcomp] = [x, y, orient]
                    x = -1
                    y = -1
                    curcomp = ""
                    orient = 0;
                    #print("end comp")

                if (not incomp):
                    continue

                if (l):
                    curcomp = l.groups()[1];
                    #print("l {} {}".format(l.groups()[0], l.groups()[1]))
                elif (t):
                    orient = orientations[str(t.groups())]
                    #print("orient {}".format(orient))
                elif (fp):
                    x = int(fp.groups()[1])
                    y = int(fp.groups()[2])
                    #print("location {} {}".format(x,y))

        return retval;


    locs = parse_eeschema(sch_path)

    for mod in board.GetModules():
        ref = mod.GetReference()

        if (ref not in locs):
            print("couldn't get loc info for {}".format(ref))
            continue

        # eeschema stores stuff in 1000ths of an inch.
        # pcbnew stores in 10e-6mm
        # 1000ths inch * inch/1000ths inch * 25.4mm/inch * 10e6
        # oldvalue * 25.4 / 10e4
        newx = locs[ref][0] * 25.4 * 1000.0
        newy = locs[ref][1] * 25.4 * 1000.0
        mod.SetPosition(pcbnew.wxPoint(int(newx), int(newy)))
        mod.SetOrientation(locs[ref][2]*10)
        print("placing {} at {},{}".format(ref, newx, newy))


    pcbnew.Refresh();
