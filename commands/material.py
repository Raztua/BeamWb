import FreeCAD as App
import FreeCADGui as Gui
import os

# Use absolute path for FreeCAD's Mod directory
def get_icon_path(icon_name):
    """Get absolute path to an icon"""
    WORKBENCH_DIR = os.path.dirname(os.path.dirname(__file__))
    ICON_DIR = os.path.join(WORKBENCH_DIR, "icons")
    return os.path.join(ICON_DIR, icon_name)

class CreateMaterialCommand:
    """Command to create materials"""

    def GetResources(self):
        return {
            'Pixmap': get_icon_path("material_icon.svg"),
            'MenuText': "Create Material",
            'ToolTip': "Create material properties for beams",
            'Accel': "M, A"
        }

    def Activated(self):
        """Run when command is clicked"""
        from ui.dialog_MaterialCreator import MaterialCreatorTaskPanel
        panel = MaterialCreatorTaskPanel()
        Gui.Control.showDialog(panel)

    def IsActive(self):
        """Determine if command should be active"""
        return App.ActiveDocument is not None


# Add command to FreeCAD
Gui.addCommand('CreateMaterial', CreateMaterialCommand())