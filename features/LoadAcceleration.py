import FreeCAD as App
from pivy import coin
import os
from features.FEMVisualization import FEMVisualization

# Constants
WORKBENCH_DIR = os.path.dirname(os.path.dirname(__file__))
ICON_DIR = os.path.join(WORKBENCH_DIR, "icons")
ACCCELERATION_LOAD_ICON_PATH = os.path.join(ICON_DIR, "acceleration_load_icon.svg")

class AccelerationLoad:
    def __init__(self, obj):
        obj.Proxy = self
        obj.addProperty("App::PropertyString", "Type", "Base", "Load Type").Type = "AccelerationLoad"
        
        obj.addProperty("App::PropertyVector", "LinearAcceleration", "Load", "Linear acceleration (g)")
        #not used yet
        obj.addProperty("App::PropertyVector", "AngularAcceleration", "Load", "Angular acceleration (rad/s²)",4)
        obj.addProperty("App::PropertyVector", "Center", "Load", "Rotation center",4)
        obj.addProperty("App::PropertyLinkList", "Beams", "Base", "Applied Beams (empty for whole model)")

        # Default values
        obj.Center = App.Vector(0, 0, 0)
        obj.LinearAcceleration = App.Vector(0, 0, 0)
        obj.AngularAcceleration = App.Vector(0, 0, 0)

        self.execute(obj)

    def execute(self, obj):
        """Called on recompute"""
        if 'Restore' in obj.State:
            return
        if hasattr(obj, "Type") and obj.Type == "AccelerationLoad":
            self.update_visualization(obj)

    def onChanged(self, obj, prop):
        """Called when properties change"""
        if 'Restore' in obj.State:
            return
        if prop in ["Center", "LinearAcceleration", "AngularAcceleration", "Beams"]:
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


class AccelerationLoadViewProvider:
    def __init__(self, vobj):
        from pivy import coin
        vobj.Proxy = self
        self.Object = vobj.Object
        self.ViewObject=vobj
        vobj.addProperty("App::PropertyColor", "AccelerationLinearColor", "Style",
                         "Color for all nodes in this group").AccelerationLinearColor = (1.0, 0.0, 0.0)
        vobj.addProperty("App::PropertyColor", "AccelerationAngularColor", "Style",
                         "Color for all nodes in this group").AccelerationAngularColor = (1.0, 0.0, 0.0)
        vobj.addProperty("App::PropertyFloat", "AccelerationLoadScale", "Style",
                         "Scale factor for all nodes in this group").AccelerationLoadScale = 1.0

    def attach(self, vobj):
        from pivy import coin
        # Store reference to view object
        if not (hasattr(self, "ViewObject")):
            self.ViewObject = vobj
        # Store reference to object
        if not (hasattr(self, "Object")):
            self.Object = vobj.Object
        self.Object = vobj.Object
        self.default_node = coin.SoGroup()
        self.default_node.setName("Acceleration Load Default node")
        vobj.addDisplayMode(self.default_node, "Default")


    def updateData(self, obj, prop):
        """Update visualization when data changes"""
        if prop in ["Center", "LinearAcceleration", "AngularAcceleration"]:
            self.updateVisualization(obj)

    def updateVisualization(self, obj):
        """Update the visualization"""
        from pivy import coin
        # Clear existing visualization
        if not hasattr(self, "Object") or not self.Object:
            return
        if not hasattr(self, "ViewObject") or not self.ViewObject:
            return
        if not hasattr(self, "default_node"):
                return
        self.default_node.removeAllChildren()

        # Linear acceleration visualization
        if hasattr(obj, "LinearAcceleration") and obj.LinearAcceleration.Length > 1e-6:
            linear_node = coin.SoSeparator()
            linear_node.setName("Acceleration Load - Linear load Separator")
            arrow = FEMVisualization.create_force_arrow(
                obj.LinearAcceleration,
                obj.Center,
                scale=self.ViewObject.AccelerationLoadScale,
                color=self.ViewObject.AccelerationLinearColor[0:3]
            )
            #add one separator, maybe not useful ->add complexity
            linear_node.addChild(arrow)
            self.default_node.addChild(linear_node)

    def getIcon(self):
        return ACCCELERATION_LOAD_ICON_PATH

    def onChanged(self, vobj, prop):
        if not hasattr(self,"Type"):
            return
        if not self.Type=='AccelerationLoad':
            return
        if prop in ["AccelerationLinearColor", "AccelerationAngularColor","AccelerationLoadScale"] and hasattr(self,"Object"):
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
        from ui.dialog_AccelerationLoad import show_acceleration_load_creator
        show_acceleration_load_creator(acceleration_load_to_modify=vobj.Object)
        return True
        
    def canDragObjects(self):
        return False

    def canDropObjects(self):
        return False
