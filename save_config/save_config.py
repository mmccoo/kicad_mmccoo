

import pcbnew
import xml.etree.ElementTree as ET
import xml.dom.minidom as MD
import os
import os.path
import pdb
import re


def GetConfigPath():
    configpath = pcbnew.GetKicadConfigPath()
    return configpath + "/kicad_mmccoo.xml"

def GetConfigTree():

    path = GetConfigPath()
    if os.path.isfile(path):
        tree = ET.parse(path)
        root = tree.getroot()
        return tree

    root = ET.fromstring("<kicad_mmccoo/>")
    return root

def GetHierElement(root, path):
    elt = root
    for name in path.split('/'):
        sub = elt.find(name)
        if (not sub):
            sub = ET.SubElement(elt, name)

        elt = sub


def SaveConfig(name, value):
    tree = GetConfigTree()

    root = tree.getroot()
    child  = root.find(name)

    if (child == None):
        child = ET.SubElement(root, name)

    child.text = value

    rough_string = ET.tostring(root, 'utf-8')

    reparsed = MD.parseString(rough_string)
    pretty = reparsed.toprettyxml(indent="  ")

    # remove empty lines. Got it from here:
    # https://stackoverflow.com/a/1140966/23630
    pretty = os.linesep.join([s for s in pretty.splitlines() if s and not s.isspace()])

    path = GetConfigPath()
    with open(path, "w") as text_file:
        text_file.write(pretty)


def GetConfig(name, default=None):
    tree = GetConfigTree()

    child = tree.find(name)
    if (child == None):
        return default
    return child.text;


if __name__ == "__main__":
    print(GetConfig("test1"))
    SaveConfig("test2", "this is the string")
    print(GetConfig("test2"))
    SaveConfig("test2.path", "this is the other string")
    print(GetConfig("test2.path"))
