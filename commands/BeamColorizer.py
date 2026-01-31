# BeamColorizer.py
import FreeCAD as App
import FreeCADGui as Gui
import os

def get_icon_path(icon_name):
    """Get absolute path to an icon"""
    WORKBENCH_DIR = os.path.dirname(os.path.dirname(__file__))
    ICON_DIR = os.path.join(WORKBENCH_DIR, "icons")
    return os.path.join(ICON_DIR, icon_name)

class BeamColorizerCommand:
    """Command to color beams based on properties"""

    def GetResources(self):
        return {
            'Pixmap': get_icon_path("beam_colorizer_icon.svg"),  # You can create this icon later
            'MenuText': "Beam Colorizer",
            'ToolTip': "Automatically color beams based on their properties",
            'Accel': "C, B"
        }

    def Activated(self):
        """Execute when the command is clicked"""
        from ui.dialog_BeamColorizer import show_beam_colorizer
        show_beam_colorizer()
 

    def IsActive(self):
        """Determine if the command should be active"""
        return App.ActiveDocument is not None

# Only register the command if we're running in FreeCAD
if App.GuiUp:
    Gui.addCommand('BeamColorizer', BeamColorizerCommand())