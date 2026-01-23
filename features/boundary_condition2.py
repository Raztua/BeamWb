import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtGui, QtCore
from pivy import coin
from shapes.BaseShape import BoxShape, PyramidShape
import os

# Constants
WORKBENCH_DIR = os.path.dirname(os.path.dirname(__file__))
ICON_DIR = os.path.join(WORKBENCH_DIR, "icons")
BOUNDARY_CONDITION_ICON_PATH = os.path.join(ICON_DIR, "boundary_condition_icon.svg")
BOUNDARY_GROUP_ICON_PATH = os.path.join(ICON_DIR, "boundary_group_icon.svg")


class BoundaryConditionFeature:
    def __init__(self, obj):
        obj.Proxy = self
        self.Type = "BoundaryCondition"

        # Add properties
        obj.addProperty("App::PropertyString", "Type", "Base", "Boundary condition type").Type = "BoundaryCondition"
        obj.addProperty("App::PropertyLinkList", "Nodes", "Boundary", "Nodes with this boundary condition")

        # Fixity properties
        obj.addProperty("App::PropertyBool", "Dx", "Fixity", "Fixity - Displacement along X").Dx = False
        obj.addProperty("App::PropertyBool", "Dy", "Fixity", "Fixity - Displacement along Y").Dy = False
        obj.addProperty("App::PropertyBool", "Dz", "Fixity", "Fixity - Displacement along Z").Dz = False
        obj.addProperty("App::PropertyBool", "Rx", "Fixity", "Fixity - Rotation about X").Rx = False
        obj.addProperty("App::PropertyBool", "Ry", "Fixity", "Fixity - Rotation about Y").Ry = False
        obj.addProperty("App::PropertyBool", "Rz", "Fixity", "Fixity - Rotation about Z").Rz = False

        # Visual properties
        obj.addProperty("App::PropertyColor", "Color", "Display", "Boundary condition color").Color = (1.0, 0.0, 0.0)
        obj.addProperty("App::PropertyFloat", "Scale", "Display", "Boundary condition scale").Scale = 1.0

        self.execute(obj)

    def execute(self, obj):
        """Called on recompute"""
        if 'Restore' in obj.State:
            return

        # Update visualization if needed
        if hasattr(obj, 'ViewObject') and obj.ViewObject is not None:
            if hasattr(obj.ViewObject, 'Proxy') and obj.ViewObject.Proxy is not None:
                obj.ViewObject.Proxy.updateVisualization(obj)

    def onChanged(self, obj, prop):
        """Handle property changes"""
        if 'Restore' in obj.State:
            return

        if prop in ["Dx", "Dy", "Dz", "Rx", "Ry", "Rz", "Color", "Scale", "Nodes"]:
            self.execute(obj)

    def getFixity(self):
        """Return fixity as a tuple (Dx, Dy, Dz, Rx, Ry, Rz)"""
        return (self.Dx, self.Dy, self.Dz, self.Rx, self.Ry, self.Rz)

    def dumps(self):
        return None

    def loads(self, state):
        return None


class BoundaryConditionViewProvider:
    def __init__(self, vobj):
        vobj.Proxy = self
        self.Object = vobj.Object
        self.ViewObject = vobj

        # Visual elements
        self.root_node = None
        self.fixity_nodes = {}

    def attach(self, vobj):
        # Store reference to view object
        if not (hasattr(self, "ViewObject")):
            self.ViewObject = vobj
        # Store reference to object
        if not (hasattr(self, "Object")):
            self.Object = vobj.Object

        # Set up the root node
        self.root_node = coin.SoGroup()
        self.root_node.setName("Rootnode")
        vobj.addDisplayMode(self.root_node, "Standard")

        #if not hasattr(vobj, "Transparency"):
        #    vobj.addProperty("App::PropertyPercent", "Transparency", "Display", "Transparency")
        #    vobj.Transparency = 0

        # Initial visualization
        self.updateVisualization(self.Object)

    def updateVisualization(self, obj):
        """Update the boundary condition visualization"""
        if not self.root_node:
            return

        # Clear existing nodes
        self.root_node.removeAllChildren()

        if not obj or not hasattr(obj, "Nodes") or not obj.Nodes:
            return
        # Get boundary condition properties
        fixity = (obj.Dx, obj.Dy, obj.Dz, obj.Rx, obj.Ry, obj.Rz)
        color = obj.Color[0:3] if hasattr(obj, "Color") else (1.0, 0.0, 0.0)
        scale = obj.Scale if hasattr(obj, "Scale") else 1.0

        # Create material
        material = coin.SoMaterial()
        material.diffuseColor = color

        # Add material to root
        self.root_node.addChild(material)

        # Create visual representation for each node
        for node in obj.Nodes:
            if hasattr(node, "X") and hasattr(node, "Y") and hasattr(node, "Z"):
                self._create_node_fixity_visualization(node, fixity, scale)

    def _create_node_fixity_visualization(self, node, fixity, scale):
        """Create visual representation of fixity at a node"""
        # Get node position
        node_x = getattr(node, "X", 0)
        node_y = getattr(node, "Y", 0)
        node_z = getattr(node, "Z", 0)

        # Create transform to position at node
        transform = coin.SoTransform()
        transform.translation.setValue(node_x, node_y, node_z)
        transform.scaleFactor.setValue(scale, scale, scale)

        # Create shape based on fixity
        if sum(fixity) == 6:  # Fully fixed
            shape = BoxShape(length=1.0, depth=1.0, height=0.5)
        elif sum(fixity) > 0:  # Partially fixed
            shape = PyramidShape(length_base=1.5, height=1.0)
        else:  # No fixity
            shape = BoxShape(length=0.8, depth=0.8, height=0.3)

        # Create separator for this node
        node_separator = coin.SoSeparator()
        node_separator.addChild(transform)
        node_separator.addChild(shape.get_separator())
        node_separator.setName="Boundary condition"
        # Add to root
        self.root_node.addChild(node_separator)

    def getDisplayModes(self, obj):
        return ["Standard"]

    def getDefaultDisplayMode(self):
        return "Standard"

    def setDisplayMode(self, mode):
        return mode

    def getIcon(self):
        return BOUNDARY_CONDITION_ICON_PATH

    def onChanged(self, vobj, prop):
        if prop in ["LineColor", "PointSize", "Transparency"]:
            self.updateVisualization(vobj.Object)

    def dumps(self):
        return None

    def loads(self, state):
        return None


class BoundaryConditionGroup:
    def __init__(self, obj):
        obj.Proxy = self
        obj.addProperty("App::PropertyString", "Type", "Base", "Group Type", 4).Type = "BoundaryConditionGroup"

    def onChanged(self, obj, prop):
        pass

    def getDisplayModes(self, obj):
        return ["Default"]

    def getDefaultDisplayMode(self):
        return "Default"


class BoundaryConditionGroupViewProvider:
    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        return BOUNDARY_GROUP_ICON_PATH

    def attach(self, vobj):
        self.Object = vobj.Object

    def updateData(self, vobj, prop):
        pass

    def onChanged(self, vobj, prop):
        pass

    def getDisplayModes(self, vobj):
        return ["Default"]

    def getDefaultDisplayMode(self):
        return "Default"

    def dumps(self):
        return None

    def loads(self, state):
        return None


def make_boundary_condition_group():
    """Create or get the BoundaryConditions group"""
    doc = App.ActiveDocument
    if not doc:
        return None

    if not hasattr(doc, "BoundaryConditions"):
        group = doc.addObject("App::DocumentObjectGroupPython", "BoundaryConditions")
        BoundaryConditionGroup(group)
        group.Label = "Boundary Conditions"
        if App.GuiUp:
            group.ViewObject.Proxy = BoundaryConditionGroupViewProvider(group.ViewObject)
    return doc.BoundaryConditions


def create_boundary_condition(nodes=None, fixity=None):
    """Create a boundary condition object"""
    doc = App.ActiveDocument
    if not doc:
        App.Console.PrintError("No active document found\n")
        return None

    try:
        group = make_boundary_condition_group()
        if not group:
            App.Console.PrintError("Failed to create boundary condition group\n")
            return None

        # Create boundary condition object
        obj = doc.addObject("App::FeaturePython", "BoundaryCondition")
        BoundaryConditionFeature(obj)

        if App.GuiUp:
            obj.ViewObject.Proxy = BoundaryConditionViewProvider(obj.ViewObject)

        # Set properties
        if nodes:
            obj.Nodes = nodes

        # Set default fixity if provided
        if fixity:
            obj.Dx, obj.Dy, obj.Dz, obj.Rx, obj.Ry, obj.Rz = fixity
        else:
            # Default: fixed in all directions
            obj.Dx = obj.Dy = obj.Dz = obj.Rx = obj.Ry = obj.Rz = True

        obj.Label = "BoundaryCondition"
        group.addObject(obj)
        return obj

    except Exception as e:
        App.Console.PrintError(f"Error creating boundary condition: {str(e)}\n")
        return None