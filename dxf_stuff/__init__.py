import pdb

try:
    import dxfgrabber
    import numpy
    import scipy
    import shapely
except ImportError as error:

    print("unable to import needed libraries. dxf stuff won't work.")
    print(error.message)
    print("""
    # To get it to work on linux systems, you'll need something like this:
    # Make sure pip is available
    sudo python2.7 -m ensurepip --default-pip
    #  or
    sudo apt install python-pip

    # then these 
    sudo pip2 install --upgrade pip
    sudo pip2 install dxfgrabber
    sudo pip2 install numpy
    sudo pip2 install scipy
    sudo pip2 install shapely
    """)
else:
    import dxf_plugins
