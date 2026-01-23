# features/AnalysisGroup.py
import FreeCAD as App
import FreeCADGui as Gui
import os
from features.nodes import make_nodes_group
from features.beams import make_beams_group
from features.sections import make_section_group
from features.boundary_condition import make_boundary_condition_group
from features.LoadIDManager import make_loads_group
from features.LoadCombination import make_load_combination_group
from features.Solver import make_solver
from features.material import make_material_group
from features.member_releases import make_member_release_group
# Constants
WORKBENCH_DIR = os.path.dirname(os.path.dirname(__file__))
ICON_DIR = os.path.join(WORKBENCH_DIR, "icons")
ANALYSIS_GROUP_ICON_PATH = os.path.join(ICON_DIR, "analysis_group_icon.svg")


class AnalysisGroup:
    def __init__(self, obj):
        obj.Proxy = self
        obj.addProperty("App::PropertyString", "Type", "Base", "Group Type").Type = "AnalysisGroup"
        obj.addProperty("App::PropertyString", "Description", "Base", "Analysis description")
        #create the groups
        make_nodes_group()
        make_boundary_condition_group()
        make_material_group()
        make_section_group()
        make_beams_group()
        make_member_release_group()
        make_loads_group()
        make_load_combination_group()
        make_solver()

        self.execute(obj)

    def execute(self, obj):
        """Called on recompute - collect all analysis items"""
        return

    def onChanged(self, obj, prop):
        """Handle property changes"""
        return

    def dumps(self):
        return None

    def loads(self, state):
        return None


class AnalysisGroupViewProvider:
    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        return ANALYSIS_GROUP_ICON_PATH

    def attach(self, vobj):
        self.Object = vobj.Object

    def updateData(self, obj, prop):
        pass

    def onChanged(self, vobj, prop):
        pass

    def getDisplayModes(self, obj):
        return ["Default"]

    def getDefaultDisplayMode(self):
        return "Default"

    def dumps(self):
        return None

    def loads(self, state):
        return None

    def canDragObjects(self):
        return False

    def canDropObjects(self):
        return False



def make_analysis_group():
    """Create a new analysis group that automatically collects all analysis items"""
    doc = App.ActiveDocument
    if not doc:
        App.Console.PrintError("No active document found\n")
        return None
    # Check if Analysis group already exists
    if hasattr(doc, "Analysis"):
        Analysis_group = doc.Analysis
    else:
        # Create new Analysis group
        analysis_group = doc.addObject("App::DocumentObjectGroupPython", "Analysis")
        AnalysisGroup(analysis_group)
        analysis_group.Label = "Analysis"
        if App.GuiUp:
            analysis_group.ViewObject.Proxy = AnalysisGroupViewProvider(analysis_group.ViewObject)
    App.ActiveDocument.recompute()

# Also add this function to your existing beams.py file to integrate with the beam creation system
def get_analysis_group():
    """Get existing analysis group or create a new one"""
    doc = App.ActiveDocument
    if not doc:
        return None

    # Look for existing analysis group
    for obj in doc.Objects:
        if hasattr(obj, "Type") and obj.Type == "AnalysisGroup":
            return obj

    # Create new one if none exists
    return make_analysis_group()