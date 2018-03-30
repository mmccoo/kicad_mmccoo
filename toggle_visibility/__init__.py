import pcbnew
from . import toggle_visibility

class ToggleVisibilityPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Toggle visibility of value/reference"
        self.category = "A descriptive category name"
        self.description = "This plugin toggles the visibility of any selected module values/references"

    def Run(self):
        # The entry function of the plugin that is executed on user action
        toggle_visibility.ToggleVisibility()


ToggleVisibilityPlugin().register() # Instantiate and register to Pcbnew

print("done adding toggle")
