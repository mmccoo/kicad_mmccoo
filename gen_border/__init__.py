
print("adding genborderplugin")

import pcbnew
from . import gen_border

class GenBorderPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Generate Border"
        self.category = "A descriptive category name"
        self.description = "This plugin shrinks a rectangular boarder around the stuff in your design"

    def Run(self):
        # The entry function of the plugin that is executed on user action
        gen_border.GenerateBoarder()


GenBorderPlugin().register() # Instantiate and register to Pcbnew

print("done adding genborderplugin")
