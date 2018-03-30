
import pcbnew

from . import place_by_sch


class PlaceBySchPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Place By Sch"
        self.category = "A descriptive category name"
        self.description = "This plugin reads the .sch file and apply its placements to the current design"

    def Run(self):
        # The entry function of the plugin that is executed on user action
        place_by_sch.PlaceBySch()


PlaceBySchPlugin().register() # Instantiate and register to Pcbnew
