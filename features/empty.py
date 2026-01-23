from types import NoneType
import FreeCAD as App
import FreeCADGui as Gui
from features.section_definitions import get_section_points
import os
import math

# Constants
WORKBENCH_DIR = os.path.dirname(os.path.dirname(__file__))
ICON_DIR = os.path.join(WORKBENCH_DIR, "icons")

BEAM_GROUP_ICON_PATH = os.path.join(ICON_DIR, "beam_group_icon.svg")

BEAM_ICON_PATH = os.path.join(ICON_DIR, "beam_icon.svg")


class EmptyFeature:
    def __init__(self, obj):
        self.node = None
        obj.Proxy = self

        # add properties
        obj.addProperty("App::PropertyString", "propertyName", "group", "comment").propertyName = "string"
        self.execute(obj)

    def execute(self, obj):
        if hasattr(obj,"Type") and obj.Type=="BeamFeature":
            #self.do_something(obj)
            self.update_visualization(obj)
    def onChanged(self, obj, prop):
        if 'Restore' in obj.State:
            return
        if prop in ["propertyName"]:
            self.execute(obj)

    def update_visualization(self, obj):
        """Trigger view provider update instead of direct manipulation"""
        if hasattr(obj, 'ViewObject') and obj.ViewObject is not None:
            if hasattr(obj.ViewObject, 'Proxy') and obj.ViewObject.Proxy is not None:
                if hasattr(obj.ViewObject.Proxy, 'updateVisualization'):
                    obj.ViewObject.Proxy.updateVisualization(obj)
    def dumps(self):
        return None

    def loads(self, state):
        return None

class EmptyViewProvider():
    def __init__(self, vobj):
        vobj.Proxy = self
        self.Object = vobj.Object
        self.ViewObject=vobj
        self.display_node1 = None
        self.display_node2 = None

    def attach(self, vobj):
        if not (hasattr(vobj, "ViewProperty")):
            vobj.addProperty("App::PropertyString", "ViewProperty", "group", "comment")
        if not (hasattr(vobj, "LineColor")):
            vobj.addProperty("App::PropertyColor", "LineColor", "Appearance", "Line color")
        # Store reference to view object
        if not (hasattr(self, "ViewObject")):
            self.ViewObject = vobj
        # Store reference to object
        if not (hasattr(self, "Object")):
            self.Object = vobj.Object

        # Set defaults
        vobj.ViewProperty = "0.2"

        #import Coin
        from pivy import coin
        # Create display mode nodes
        self.display_node1 = coin.SoGroup()
        self.display_node1.setName("display_node1")

        self.display_node2 = coin.SoGroup()
        self.display_node2.setName("display_node2")

        # Add display modes to view object
        vobj.addDisplayMode(self.display_node1, "display_node1")
        vobj.addDisplayMode(self.display_node2, "display_node2")

        self.updateVisualization(self.Object)

    #To si if updateData is usefull, as it is already in emptyfeature
    def updateData(self, obj, prop):
        if prop in ["ViewProperty"]:
            self.updateVisualization(obj)

    def updateVisualization(self, obj):
        """Update all display modes based on current beam data"""
        if not hasattr(self,"Object"):
            return

        if hasattr(self, "display_node1"):
            # Clear existing nodes
            self.display_node1.removeAllChildren()
        if hasattr(self, "display_node1"):
            # Clear existing nodes
            self.display_node2.removeAllChildren()
        #find how to change
        self.display_node1_func(obj)
        self.display_node2_func(obj)

    def display_node1_func(self, obj):
        """Create simple line representation"""
        from pivy import coin
        #verticle position
        start_pos = App.Vector(0,0,1)
        end_pos = App.Vector(1,0,1)
        coords = coin.SoCoordinate3()
        coords.setName("display_node1 - coordinate")
        coords.point.setValues(0, 2, [start_pos, end_pos])
        line = coin.SoLineSet()
        line.setName("display_node1 - lineset")
        line.numVertices.setValue(2)

        # Add line style for better visibility
        line_style = coin.SoDrawStyle()
        line_style.setName("display_node1 - linestyle")
        line_style.lineWidth = 2

        # Material for display_node1 mode
        material = coin.SoMaterial()
        material.diffuseColor = self.Object.ViewObject.LineColor[0:3]
        #material.diffuseColor = App.Vector(0, 0, 1)
        self.display_node1.addChild(material)
        self.display_node1.addChild(line_style)
        self.display_node1.addChild(coords)
        self.display_node1.addChild(line)

    def display_node2_func(self, obj):
        """Create simple line representation"""
        from pivy import coin
        #verticle position
        start_pos = App.Vector(0,0,1)
        end_pos = App.Vector(0,1,1)

        coords = coin.SoCoordinate3()
        coords.setName("display_node 2 - coordinate")
        coords.point.setValues(0, 2, [start_pos, end_pos])
        line = coin.SoLineSet()
        line.setName("display_node1 - lineset")
        line.numVertices.setValue(2)

        # Add line style for better visibility
        line_style = coin.SoDrawStyle()
        line_style.setName("display_node1 - linestyle")
        line_style.lineWidth = 2

        # Material for display_node1 mode
        material = coin.SoMaterial()
        material.diffuseColor = self.Object.ViewObject.LineColor[0:3]
        self.display_node2.addChild(material)
        self.display_node2.addChild(line_style)
        self.display_node2.addChild(coords)
        self.display_node2.addChild(line)

    def onChanged(self, vobj, prop):
        if not  hasattr(self,"display_node1") or not hasattr(self,"display_node2"):
            return
        if prop in ["ShapeColor","LineColor","Transparency"] and hasattr(self,"Object"):
            self.updateVisualization(self.Object)

    def getDisplayModes(self, obj):
        return ["display_node1", "display_node2"]

    def getDefaultDisplayMode(self):
        return "display_node1"

    def setDisplayMode(self, mode):
        return mode

    def getIcon(self):
        return BEAM_ICON_PATH

    def dumps(self):
        return None

    def loads(self, state):
        return None

def create_empty():
    empty_element = App.ActiveDocument.addObject("App::FeaturePython", "empty")
    EmptyFeature(empty_element)
    # Attach the view provider
    EmptyViewProvider(empty_element.ViewObject)

#to use from freecad:
from features.empty import create_empty
create_empty()