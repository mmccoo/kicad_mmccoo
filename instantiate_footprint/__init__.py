
import pcbnew

from . import instantiate_footprint


class AddMountingHolesPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Add Mounting Holes"
        self.category = "A descriptive category name"
        self.description = "This plugin adds mounting holes above the top and bottom of your design"

    def Run(self):
        # The entry function of the plugin that is executed on user action
        instantiate_footprint.AddMountingHoles()


AddMountingHolesPlugin().register() # Instantiate and register to Pcbnew
