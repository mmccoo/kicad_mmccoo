# this file is here to make the command "external plugins" available from the pcbnew menu.

import pcbnew

from . import gen_border

class GenBorderPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Generate Border"
        self.category = "A descriptive category name"
        self.description = "This plugin shrinks a rectangular boarder around the stuff in your design"

    def Run(self):
        # The entry function of the plugin that is executed on user action
        gen_border.gen_border.GenerateBoarder()


GenBorderPlugin().register() # Instantiate and register to Pcbnew

from . import place_by_sch

class PlaceBySchPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Place By Sch"
        self.category = "A descriptive category name"
        self.description = "This plugin reads the .sch file and apply its placements to the current design"

    def Run(self):
        # The entry function of the plugin that is executed on user action
        place_by_sch.place_by_sch.PlaceBySch()


PlaceBySchPlugin().register() # Instantiate and register to Pcbnew

from . import instantiate_footprint

class AddMountingHolesPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Add Mounting Holes"
        self.category = "A descriptive category name"
        self.description = "This plugin adds mounting holes above the top and bottom of your design"

    def Run(self):
        # The entry function of the plugin that is executed on user action
        instantiate_footprint.instantiate_footprint.AddMountingHoles()


AddMountingHolesPlugin().register() # Instantiate and register to Pcbnew
