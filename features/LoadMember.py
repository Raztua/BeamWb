# MemberLoad.py
import FreeCAD as App
from PySide import QtGui, QtCore
import os
from features.FEMVisualization import FEMVisualization
import math

# Constants
WORKBENCH_DIR = os.path.dirname(os.path.dirname(__file__))
ICON_DIR = os.path.join(WORKBENCH_DIR, "icons")
MEMBER_LOAD_ICON_PATH = os.path.join(ICON_DIR, "beam_member_load.svg")


class MemberLoad:
    def __init__(self, obj):
        self.flagInit = True
        try:
            obj.Proxy = self
            obj.addProperty("App::PropertyString", "Type", "Base", "Load Type").Type = "MemberLoad"
            obj.addProperty("App::PropertyString", "Comment", "Base", "Comment", 4)
            obj.addProperty("App::PropertyLinkList", "Beams", "Base", "Applied Beams")
            obj.addProperty("App::PropertyVector", "StartForce", "Load", "Start Force vector (N)")
            obj.addProperty("App::PropertyVector", "EndForce", "Load", "End Force vector (N)")
            obj.addProperty("App::PropertyVector", "StartMoment", "Load", "Start Moment vector (Nm)")
            obj.addProperty("App::PropertyVector", "EndMoment", "Load", "End Moment vector (Nm)")
            obj.addProperty("App::PropertyFloat", "StartPosition", "Load", "Start position (0-1)").StartPosition = 0.0
            obj.addProperty("App::PropertyFloat", "EndPosition", "Load", "End position (0-1)").EndPosition = 1.0
            obj.addProperty("App::PropertyBool", "LocalCS", "Load", "Use local coordinate system").LocalCS = True

            # Initialize properties
            obj.StartForce = App.Vector(0, 0, 0)
            obj.EndForce = App.Vector(0, 0, 0)
            obj.StartMoment = App.Vector(0, 0, 0)
            obj.EndMoment = App.Vector(0, 0, 0)

            self.execute(obj)
        except Exception as e:
            App.Console.PrintError(f"Failed to initialize Memberload: {str(e)}\n")

    def execute(self, obj):
        """Called on recompute"""
        if 'Restore' in obj.State:
            return
        if hasattr(obj, "Type") and obj.Type == "MemberLoad":
            self.update_visualization(obj)

    def onChanged(self, obj, prop):
        """Called when properties change"""
        if 'Restore' in obj.State:
            return
        if not hasattr(self,"flagInit"):
            return
        if self.flagInit:
            return
        if prop in ["Beams", "StartForce", "EndForce", "StartMoment", "EndMoment",
                    "StartPosition", "EndPosition", "LocalCS"]:
            self.execute(obj)

    def update_visualization(self, obj):
        """Trigger view provider update"""
        if hasattr(obj, 'ViewObject') and obj.ViewObject is not None:
            if hasattr(obj.ViewObject, 'Proxy') and obj.ViewObject.Proxy is not None:
                if hasattr(obj.ViewObject.Proxy, 'updateVisualization'):
                    obj.ViewObject.Proxy.updateVisualization(obj)

    def dumps(self):
        return None

    def loads(self, state):
        return None


class MemberLoadViewProvider:
    def __init__(self, vobj):
        vobj.Proxy = self
        self.Object = vobj.Object
        self.ViewObject = vobj
        if not (hasattr(vobj, "MemberLoadColor")):
            vobj.addProperty("App::PropertyColor", "MemberLoadColor", "Style",
                             "Color for all nodes in this group").MemberLoadColor = (1.0, 0.0, 0.0)
            vobj.addProperty("App::PropertyColor", "MemberMomentColor", "Style",
                             "Color for all nodes in this group").MemberMomentColor = (1.0, 0.0, 0.0)
            vobj.addProperty("App::PropertyFloat", "MemberLoadScale", "Style",
                             "Scale factor for all nodes in this group").MemberLoadScale = 1.0
            vobj.addProperty("App::PropertyBool", "ShowLoads", "Display",
                             "Show loads visualization").ShowLoads = True

    def attach(self, vobj):
        from pivy import coin
        self.Object = vobj.Object
        if not (hasattr(vobj, "MemberLoadColor")):
            vobj.addProperty("App::PropertyColor", "MemberLoadColor", "Style",
                             "Color for all nodes in this group").MemberLoadColor = (1.0, 0.0, 0.0)
            vobj.addProperty("App::PropertyColor", "MemberMomentColor", "Style",
                             "Color for all nodes in this group").MemberMomentColor = (1.0, 0.0, 0.0)
            vobj.addProperty("App::PropertyFloat", "MemberLoadScale", "Style",
                             "Scale factor for all nodes in this group").MemberLoadScale = 1.0
            vobj.addProperty("App::PropertyBool", "ShowLoads", "Display",
                             "Show loads visualization").ShowLoads = True
        self.default_node = coin.SoSeparator()
        self.default_node.setName("Default")
        vobj.addDisplayMode(self.default_node, "Default")

    def updateData(self, obj, prop):
        """Called when object data changes"""
        if prop in ["Beams", "StartForce", "EndForce", "StartMoment", "EndMoment",
                    "StartPosition", "EndPosition", "LocalCS"]:
            self.updateVisualization(obj)

    def updateVisualization(self, obj):
        """Create visualization for member loads"""
        from pivy import coin

        if not hasattr(self, "Object") or not self.Object:
            return
        if not hasattr(self, "ViewObject") or not self.ViewObject:
            return
        if not hasattr(self.ViewObject, "ShowLoads"):
            return
        if not hasattr(self, "default_node"):
            return

        self.default_node.removeAllChildren()

        if self.ViewObject.ShowLoads == False:
            return
        if not hasattr(obj, "Beams") or not isinstance(obj.Beams, (list, tuple)):
            return

        load_color = self.ViewObject.MemberLoadColor[0:3]  # Red for forces
        moment_color = self.ViewObject.MemberMomentColor[0:3]  # Blue for moments
        load_scale = self.ViewObject.MemberLoadScale

        for beam in obj.Beams:
            if not hasattr(beam, "Proxy"):
                continue
            beams_sep=FEMVisualization.create_member_load(beam,obj,load_scale,load_color,moment_color)
            self.default_node.addChild(beams_sep)


    def getIcon(self):
        return MEMBER_LOAD_ICON_PATH

    def onChanged(self, vobj, prop):
        if not hasattr(self, "Object"):
            return
        if prop in ["MemberLoadColor", "MemberMomentColor","MemberLoadScale"]:
            self.updateVisualization(self.Object)

    def getDisplayModes(self, obj):
        return ["Default"]

    def getDefaultDisplayMode(self):
        return "Default"

    def setDisplayMode(self, mode):
        return mode

    def dumps(self):
        return None

    def loads(self, state):
        return None
        
    def doubleClicked(self, vobj):
        """Handle double-click event"""
        from ui.dialog_MemberLoad import show_member_load_creator
        show_member_load_creator(member_load_to_modify=vobj.Object)
        return True
    def canDragObjects(self):
        return False

    def canDropObjects(self):
        return False



