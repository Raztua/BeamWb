import FreeCAD as App
import FreeCADGui as Gui
import os
#from ui.dialog import show_beam_creator
# Use absolute path for FreeCAD's Mod directory
def get_icon_path(icon_name):
    """Get absolute path to an icon"""
    WORKBENCH_DIR = os.path.dirname(os.path.dirname(__file__))
    ICON_DIR = os.path.join(WORKBENCH_DIR, "icons")
    return os.path.join(ICON_DIR, icon_name)

class CreateAnalysisGroupCommand:
    """Command to create beams between nodes"""
    
    def GetResources(self):
        return {
            'Pixmap': get_icon_path("Analysis_group_icon.svg"),
            'MenuText': "Create Analysis Container",
            'ToolTip': "Creates a analysis container"
        }
    
    def Activated(self):
        """Execute when the command is clicked"""
        from features.AnalysisGroup import get_analysis_group
        get_analysis_group()
    
    def IsActive(self):
        """Determine if the command should be active"""
        if App.ActiveDocument is None:
            return False
        if hasattr(App.ActiveDocument, "AnalysisGroup") :
            return False
        return True

# Only register the command if we're running in FreeCAD
if App.GuiUp:
    Gui.addCommand('CreateAnalysisGroup', CreateAnalysisGroupCommand())