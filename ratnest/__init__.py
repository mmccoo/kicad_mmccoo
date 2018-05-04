
print("adding ratnest plugin")

import pcbnew
from . import ratnest

class RatNestPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Toggle Power Ratnest"
        self.category = "A descriptive category name"
        self.description = "This plugin turns off display of power ratsnest"

    def Run(self):
        # The entry function of the plugin that is executed on user action
        ratnest.TogglePowerRatnest()


RatNestPlugin().register() # Instantiate and register to Pcbnew

print("done adding ratnest")
