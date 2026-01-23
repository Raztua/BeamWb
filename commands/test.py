import FreeCAD as App
import FreeCADGui as Gui
import os
from features.FEMVisualization import FEMVisualization

# Get the workbench directory
WORKBENCH_DIR = os.path.dirname(os.path.dirname(__file__))
ICON_DIR = os.path.join(WORKBENCH_DIR, "icons")
SECTION_ICON_PATH = os.path.join(ICON_DIR, "section_icon.svg")

class TestCommand:
    """Command to create sections"""
    
    def GetResources(self):
        return {
            'Pixmap': SECTION_ICON_PATH,
            'MenuText': "test",
            'ToolTip': "test function",
            'Accel': "S, S"  # Optional keyboard shortcut
        }
    
    def Activated(self):
        """Run when command is clicked"""
        from pivy import coin
        from features.LoadNodal import NodalLoad,NodalLoadViewProvider
        doc = App.ActiveDocument
        load = doc.addObject("App::FeaturePython", "NodalLoad")
        NodalLoad(load)
        load.Nodes = App.ActiveDocument.getObject("Node")
        load.Force = App.Vector(10,10,0)
        NodalLoadViewProvider(load.ViewObject)

        print("after creation")
    def IsActive(self):
        """Determine if command should be active"""
        if not (hasattr(App.ActiveDocument, "Analysis")):
            return False
        return App.ActiveDocument is not None

# Add command to FreeCAD
Gui.addCommand('TestCommand', TestCommand())