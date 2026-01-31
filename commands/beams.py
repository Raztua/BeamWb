import FreeCAD as App
import FreeCADGui as Gui
import os


# Use absolute path for FreeCAD's Mod directory
def get_icon_path(icon_name):
    """Get absolute path to an icon"""
    WORKBENCH_DIR = os.path.dirname(os.path.dirname(__file__))
    ICON_DIR = os.path.join(WORKBENCH_DIR, "icons")
    return os.path.join(ICON_DIR, icon_name)

class CreateBeamCommand:
    """Command to create beams between nodes"""
    
    def GetResources(self):
        return {
            'Pixmap': get_icon_path("beam_icon.svg"),
            'MenuText': "Create Beam",
            'ToolTip': "Creates a new beam between two nodes",
            'Accel': "B, B"
        }
    
    def Activated(self):
        """Execute when the command is clicked"""
        from ui.dialog import show_beam_creator  # Local import to prevent circular imports
        show_beam_creator()
    
    def IsActive(self):
        """Determine if the command should be active"""
        if App.ActiveDocument is None:
            return False
        if not hasattr(App.ActiveDocument, "Nodes"):
            return False
        if not (hasattr(App.ActiveDocument, "Analysis")):
            return False
        if App.ActiveDocument.Nodes is None:
            return False
        if len(App.ActiveDocument.Nodes.Group) < 2:  # Need at least 2 nodes to create a beam
            return False
        return True
        
class ModifyBeamCommand:
    """Command to modify existing nodes"""

    def GetResources(self):
        return {
            'Pixmap': get_icon_path("beam_modify_icon.svg"),
            'MenuText': "Modify Beams",
            'ToolTip': "Modify selected Beams",
            'Accel': "B, M"
        }

    def Activated(self):
        """Run when command is clicked"""
        from ui.dialog_BeamModifier import show_beam_modifier
        show_beam_modifier()

    def IsActive(self):
        """Determine if command should be active"""
        return App.ActiveDocument is not None
        
        
# Only register the command if we're running in FreeCAD
if App.GuiUp:
    Gui.addCommand('CreateBeam', CreateBeamCommand())
    Gui.addCommand('ModifyBeam',ModifyBeamCommand())