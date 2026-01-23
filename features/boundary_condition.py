import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtGui, QtCore
from pivy import coin
from shapes.BaseShape import BoxShape, PyramidShape
import os

# Import PrettyTable (assuming same setup as nodes.py)
try:
    from prettytable import PrettyTable, HRuleStyle, VRuleStyle, TableStyle
except ImportError:
    App.Console.PrintError("PrettyTable not found.\n")
    PrettyTable = None
    TableStyle = None

# Constants
WORKBENCH_DIR = os.path.dirname(os.path.dirname(__file__))
ICON_DIR = os.path.join(WORKBENCH_DIR, "icons")
BOUNDARY_CONDITION_ICON_PATH = os.path.join(ICON_DIR, "boundary_condition_icon.svg")
BOUNDARY_GROUP_ICON_PATH = os.path.join(ICON_DIR, "boundary_group_icon.svg")


class BoundaryConditionFeature:
    def __init__(self, obj):
        obj.Proxy = self
        self.Type = "BoundaryCondition"
        self.Object = obj
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
        obj.addProperty("App::PropertyColor", "Color", "Display", "Boundary condition color").Color = (0.33, 1.0, 0.0)
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
        if not (hasattr(self, "ViewObject")):
            self.ViewObject = vobj
        if not (hasattr(self, "Object")):
            self.Object = vobj.Object
        vobj.addProperty("App::PropertyPercent", "Transparency", "Display",
                         "Transparency level").Transparency = 50

        # Visual elements
        if not (hasattr(self, "root_node")):
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

        # Initial visualization
        self.updateVisualization(self.Object)

    def doubleClicked(self, vobj):
        """Handle double-click event"""

        # Import and show the boundary condition modifier dialog
        from ui.dialog_BoundaryConditionCreator import show_boundary_condition_creator
        # Pass the boundary condition object to pre-select it
        show_boundary_condition_creator(boundary_condition=vobj.Object)
        return True

    def onModifyBoundaryCondition(self, bc_obj):
        """Handle context menu action"""

        from ui.dialog_BoundaryConditionCreator import show_boundary_condition_creator
        show_boundary_condition_creator(boundary_condition=bc_obj)

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
        color = obj.Color[0:3] if hasattr(obj, "Color") else (0.33, 1.0, 0.0)
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
        node_x = getattr(node, "X", 0).Value
        node_y = getattr(node, "Y", 0).Value
        node_z = getattr(node, "Z", 0).Value

        # Create transform to position at node
        transform = coin.SoTransform()
        transform.translation.setValue(node_x, node_y, node_z)
        transform.scaleFactor.setValue(scale, scale, scale)

        # Create shape based on fixity
        if sum(fixity) == 6:  # Fully fixed
            shape = BoxShape(length=60.0, depth=60.0, height=30.0)
        elif sum(fixity) > 0:  # Partially fixed
            shape = PyramidShape(length_base=90.0, height=60.0)
        else:  # No fixity
            shape = BoxShape(length=60.0, depth=60.0, height=30.0)

        # Create separator for this node
        node_separator = coin.SoSeparator()
        node_separator.addChild(transform)
        node_separator.addChild(shape.get_separator())
        node_separator.setName = "Boundary condition"
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

    def canDragObjects(self):
        return False

    def canDropObjects(self):
        return False


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

    def canDragObjects(self):
        return False

    def canDropObjects(self):
        return False

    # --- CONTEXT MENU IMPLEMENTATION ---
    def setupContextMenu(self, vobj, menu):
        """Adds a context menu item to list all Boundary Conditions."""

        if PrettyTable is None:
            App.Console.PrintWarning("PrettyTable not available for BC listing.\n")
            return

        action = QtGui.QAction("List Boundary Conditions in Report View", menu)
        action.triggered.connect(lambda: self.onListBCs(vobj.Object))
        menu.addAction(action)

    def onListBCs(self, bc_group):
        """Collects Boundary Condition data and prints it to the FreeCAD report view."""

        if PrettyTable is None:
            App.Console.PrintError("Cannot list Boundary Conditions: PrettyTable module is missing.\n")
            return

        # --- 1. SETUP AND COLLECT DATA ---

        # Initialize PrettyTable
        table = PrettyTable()
        table.field_names = [
            "Name", "Type", "Nodes Count",
            "Dx", "Dy", "Dz",
            "Rx", "Ry", "Rz", "Color"
        ]
        table.align["Name"] = "l"
        table.set_style(TableStyle.SINGLE_BORDER)

        # Iterate over all objects in the group
        for obj in bc_group.Group:
            if hasattr(obj, "Type") and obj.Type == "BoundaryCondition":

                # Retrieve fixity properties
                fixity = {
                    'Dx': getattr(obj, 'Dx', False),
                    'Dy': getattr(obj, 'Dy', False),
                    'Dz': getattr(obj, 'Dz', False),
                    'Rx': getattr(obj, 'Rx', False),
                    'Ry': getattr(obj, 'Ry', False),
                    'Rz': getattr(obj, 'Rz', False),
                }

                # Convert Boolean fixity to simple text representation (X or ' ')
                fixity_display = {k: "X" if v else " " for k, v in fixity.items()}

                # Format color tuple for display
                color_tuple = getattr(obj, 'Color', (0.33, 1.0, 0.0))
                # Ensure color tuple has at least 3 elements before formatting
                if len(color_tuple) >= 3:
                    color_str = f"R:{color_tuple[0]:.2f} G:{color_tuple[1]:.2f} B:{color_tuple[2]:.2f}"
                else:
                    color_str = "N/A"

                # Add row to the table
                table.add_row([
                    obj.Label,
                    obj.Type,
                    len(getattr(obj, 'Nodes', [])),
                    fixity_display['Dx'],
                    fixity_display['Dy'],
                    fixity_display['Dz'],
                    fixity_display['Rx'],
                    fixity_display['Ry'],
                    fixity_display['Rz'],
                    color_str
                ])

        # --- 2. CONCATENATE AND PRINT OUTPUT (SINGLE CALL) ---

        header_string = "\n--- Boundary Condition List ---\n"
        table_string = table.get_string()
        final_output = header_string + table_string + "\n"

        App.Console.PrintMessage(final_output)
    # --- END CONTEXT MENU IMPLEMENTATION ---


def make_boundary_condition_group():
    """Create or get the BoundaryConditions group"""
    doc = App.ActiveDocument
    if not doc:
        return None

    if hasattr(doc, "BoundaryConditions"):
        bc_group = doc.BoundaryConditions
    else:
        bc_group = doc.addObject("App::DocumentObjectGroupPython", "BoundaryConditions")
        BoundaryConditionGroup(bc_group)
        bc_group.Label = "BoundaryConditions"
        from features.AnalysisGroup import get_analysis_group
        analysis_group = get_analysis_group()
        if analysis_group and bc_group not in analysis_group.Group:
            analysis_group.addObject(bc_group)
        if App.GuiUp:
            bc_group.ViewObject.Proxy = BoundaryConditionGroupViewProvider(bc_group.ViewObject)
        App.ActiveDocument.recompute()
    return bc_group


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
        App.ActiveDocument.recompute()
        return obj

    except Exception as e:
        App.Console.PrintError(f"Error creating boundary condition: {str(e)}\n")
        return None