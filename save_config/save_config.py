

import pcbnew
import numbers
import xml.etree.ElementTree as ET
import xml.dom.minidom as MD
import os
import os.path
import pdb
import re
import pprint


def GetConfigPath():
    configpath = pcbnew.GetKicadConfigPath()
    return configpath + "/kicad_mmccoo.xml"

def GetConfigTree():

    path = GetConfigPath()
    if os.path.isfile(path):
        tree = ET.parse(path)
        root = tree.getroot()
        return root

    root = ET.fromstring("<kicad_mmccoo/>")
    return root

def GetHierElement(root, path):
    elt = root
    for name in path.split('/'):
        sub = elt.find(name)
        if (not sub):
            sub = ET.SubElement(elt, name)

        elt = sub

def Save(root):
    rough_string = ET.tostring(root, 'utf-8')

    reparsed = MD.parseString(rough_string)
    pretty = reparsed.toprettyxml(indent="  ")

    # remove empty lines. Got it from here:
    # https://stackoverflow.com/a/1140966/23630
    pretty = os.linesep.join([s for s in pretty.splitlines() if s and not s.isspace()])

    path = GetConfigPath()
    with open(path, "w") as text_file:
        text_file.write(pretty)



def SaveConfig(name, value):
    root = GetConfigTree()

    child  = root.find(name)

    if (child == None):
        child = ET.SubElement(root, name)

    child.text = value

    Save(root)

def GetConfig(name, default=None):
    tree = GetConfigTree()

    child = tree.find(name)
    if (child == None):
        return default
    return child.text;

def ValueToElt(parent, value):
    if isinstance(value, dict):
        d = ET.SubElement(parent, 'dict')
        for key in value:
            sub = ValueToElt(d, value[key])
            sub.attrib['key'] = str(key)
        return d

    if isinstance(value, list):
        l = ET.SubElement(parent, 'list')
        for elt in value:
            sub = ValueToElt(l, elt)
        return l

    if isinstance(value, tuple):
        l = ET.SubElement(parent, 'tuple')
        for elt in value:
            sub = ValueToElt(l, elt)
        return l

    elif isinstance(value, basestring):
        s = ET.SubElement(parent, "string")
        s.text = value

        return s

    elif isinstance(value, numbers.Number):
        n = ET.SubElement(parent, "number")
        n.text = str(value)
        return n


    else:
        return None

def EltToValue(elt):

    if elt == None:
        return None

    if elt.tag == "list":
        retval = []
        for child in elt:
            retval.append(EltToValue(child))
        return retval

    if elt.tag == "tuple":
        retval = []
        for child in elt:
            retval.append(EltToValue(child))
        return tuple(retval)

    if elt.tag == "dict":
        retval = {}
        for child in elt:
            retval[child.attrib['key']] = EltToValue(child)
        return retval

    if elt.tag == "string":
        return elt.text

    if elt.tag == "number":
        return float(elt.text)



    return None




def SaveConfigComplex(name, value):
    root = GetConfigTree()

    child  = root.find(name)

    if (child == None):
        child = ET.SubElement(root, name)

    child.clear()
    ValueToElt(child, value)

    Save(root)

def GetConfigComplex(name, default=None):
    tree = GetConfigTree()

    child = tree.find(name)
    if (child == None):
        return default

    return EltToValue(list(child)[0])

if __name__ == "__main__":
    root = GetConfigTree()

    m = [
        { 'size': 1.2,
          'lib':  "lib1",
          'foot': "mh1.2"
        },
        { 'size': 1.3,
          'lib':  "lib1",
          'foot': "mh1.3"
        },
        { 'size': 1.4,
          'lib':  "lib1",
          'foot': "mh1.4"
        }]

    SaveConfigComplex("complex", m)
    pprint.pprint(GetConfigComplex("complex"))

    print(GetConfig("test1"))
    SaveConfig("test2", "this is the string")
    print(GetConfig("test2"))
    SaveConfig("test2.path", "this is the other string")
    print(GetConfig("test2.path"))
