import FreeCAD as App
import FreeCADGui as Gui
import os
# Use absolute path for FreeCAD's Mod directory
def get_icon_path(icon_name):
    """Get absolute path to an icon"""
    WORKBENCH_DIR = os.path.dirname(os.path.dirname(__file__))
    ICON_DIR = os.path.join(WORKBENCH_DIR, "icons")
    return os.path.join(ICON_DIR, icon_name)

class CreateBoundaryConditionCommand:
    """Command to create boundary conditions"""

    def GetResources(self):
        return {
            'Pixmap': get_icon_path("boundary_condition_icon.svg"),
            'MenuText': "Create Boundary Condition",
            'ToolTip': "Create boundary conditions for nodes",
            'Accel': "B, C"
        }

    def Activated(self):
        """Run when command is clicked"""
        from ui.dialog import show_bc_creator
        show_bc_creator()

    def IsActive(self):
        """Determine if command should be active"""
        if not(hasattr(App.ActiveDocument, "Analysis")) :
            return False
        return App.ActiveDocument is not None


# Add command to FreeCAD
Gui.addCommand('CreateBoundaryCondition', CreateBoundaryConditionCommand())
