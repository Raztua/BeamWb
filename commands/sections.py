import FreeCAD as App
import FreeCADGui as Gui
import os
from ui.dialog import show_section_creator

# Get the workbench directory
WORKBENCH_DIR = os.path.dirname(os.path.dirname(__file__))
ICON_DIR = os.path.join(WORKBENCH_DIR, "icons")
SECTION_ICON_PATH = os.path.join(ICON_DIR, "section_icon.svg")


class CreateSectionCommand:
    """Command to create sections"""

    def GetResources(self):
        return {
            'Pixmap': SECTION_ICON_PATH,
            'MenuText': "Create Section",
            'ToolTip': "Creates a new cross-section",
            'Accel': "S, S"
        }

    def Activated(self):
        """Run when command is clicked"""
        show_section_creator()  # Now shows task panel

    def IsActive(self):
        """Determine if command should be active"""
        if not (hasattr(App.ActiveDocument, "Analysis")):
            return False
        return App.ActiveDocument is not None


# Add command to FreeCAD
if App.GuiUp:
    Gui.addCommand('CreateSection', CreateSectionCommand())