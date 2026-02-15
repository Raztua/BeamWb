import FreeCAD as App
from FreeCAD import Units
import FreeCADGui as Gui
from draftobjects.point import Point
import os
from PySide import QtGui, QtCore
import textwrap

# --- LOCAL IMPORT OF PRETTYTABLE (as provided by user) ---
# NOTE: In a real FreeCAD environment, ensure this path is correct.
try:
    # Assuming 'prettytable.py' is a local module
    from prettytable.prettytable import PrettyTable, HRuleStyle, VRuleStyle, TableStyle
except ImportError:
    App.Console.PrintError("PrettyTable not found. Ensure prettytable.py is available in the Python path.\n")
    PrettyTable = None
    HRuleStyle = None
    VRuleStyle = None
    TableStyle = None
# --------------------------------------------------------

# Constants
WORKBENCH_DIR = os.path.dirname(os.path.dirname(__file__))
ICON_DIR = os.path.join(WORKBENCH_DIR, "icons")
NODE_ICON_PATH = os.path.join(ICON_DIR, "beam_node.svg")
NODE_GROUP_ICON_PATH = os.path.join(ICON_DIR, "beam_node_group.svg")
NODE_GROUP_RESULTS_ICON_PATH = os.path.join(ICON_DIR, "beam_node_results.svg")


class NodeFeature(Point):
    def __init__(self, obj, x=0, y=0, z=0, PointSize=5, PointColor=(1.0, 0.0, 0.0)):
        super(NodeFeature, self).__init__(obj)
        self.Object = obj
        obj.addProperty("App::PropertyString", "Type", "Base", "Group Type", 4).Type = "NodeFeature"
        obj.addProperty("App::PropertyString", "Comment", "Base", "Comment",4)
        obj.addProperty("App::PropertyFloat", "PointSize", "UserPoint", "Custom radius", 4)
        obj.addProperty("App::PropertyColor", "PointColor", "UserPoint", "Custom color", 4)

        # Add text annotation properties
        obj.addProperty("App::PropertyStringList", "Texts", "Annotations", "List of text annotations")
        obj.addProperty("App::PropertyVector", "TextOffsets", "Annotations", "List of text offset vectors")
        obj.addProperty("App::PropertyFloat", "TextSize", "Annotations", "Text size").TextSize = 10.0
        obj.addProperty("App::PropertyColor", "TextColor", "Annotations", "Text color").TextColor = (0.0, 0.0, 0.0)

        obj.X = x
        obj.Y = y
        obj.Z = z
        obj.TextOffsets=App.Vector(0,0,-10)
        obj.PointSize = PointSize
        obj.PointColor = PointColor

        # Placeholder properties for Boundary Conditions (for listing purpose)
        obj.addProperty("App::PropertyBool", "IsFixed", "Boundary", "Is the node fixed (all DOFs)?").IsFixed = False
        obj.addProperty("App::PropertyString", "BCInfo", "Boundary",
                        "Detailed Boundary Condition information").BCInfo = "None"

    def add_text(self, text):
        """Add a text annotation to the node"""
        if not hasattr(self,'Object'):
            return
        obj = self.Object
        obj.Texts += [text]

        self.update_visualization(obj)

    def remove_text(self, index):
        """Remove a text annotation by index"""
        obj = self.Object

        if index < 0 or index >= len(obj.Texts):
            raise IndexError("Invalid text index")

        obj.Texts = obj.Texts[:index] + obj.Texts[index + 1:]

        self.update_visualization(obj)

    def clear_texts(self):
        """Remove all text annotations"""
        if hasattr(self,"Object"):
            obj = self.Object
            obj.Texts = []
            self.update_visualization(obj)

    def onChanged(self, obj, prop):
        """Handle property changes - MUST call parent class!"""
        # Call parent class onChanged first to handle property change tracking
        super(NodeFeature, self).onChanged(obj, prop)

        # Handle text-related property changes
        if prop in ["Texts", "TextOffsets", "TextSize", "TextColor"]:
            self.update_visualization(obj)

    def update_visualization(self, obj):
        """Trigger view provider update"""

        if hasattr(obj, 'ViewObject') and obj.ViewObject is not None:
            if hasattr(obj.ViewObject, 'Proxy') and obj.ViewObject.Proxy is not None:
                obj.ViewObject.Proxy.update_text_visualization(obj)


class NodeViewProvider:
    """View provider for NodeFeature to handle double-click events and text visualization"""

    def __init__(self, vobj):
        vobj.Proxy = self
        self.Object = vobj.Object
        # self.text_separator = None
        self.text_nodes = []

    def attach(self, vobj):
        self.Object = vobj.Object
        from pivy import coin
        self.text_separator = coin.SoSeparator()
        vobj.RootNode.addChild(self.text_separator)

        # Initialize text visualization
        self.update_text_visualization(vobj.Object)

    def updateData(self, obj, prop):
        """Handle data changes including text updates"""

    def update_text_visualization(self, obj):
        """Update text annotations visualization"""
        from pivy import coin

        # Clear existing text nodes
        self.text_separator.removeAllChildren()

        if not hasattr(obj, "Texts") or not obj.Texts:
            return
        text=obj.Texts
        #for i, (text, offset) in enumerate(zip(obj.Texts, obj.TextOffsets)):
            # Create text transform
        transform = coin.SoTransform()
        text_pos = obj.TextOffsets
        transform.translation.setValue(text_pos.x, text_pos.y, text_pos.z)

        # Create text node
        text_node = coin.SoText2()

        text_node.string.setValues(text)
        text_node.justification = coin.SoText2.CENTER

        # Set font size
        font = coin.SoFont()
        font.size = getattr(obj, "TextSize", 10.0)

        # Set text color - use different color for reaction data
        material = coin.SoMaterial()
        material.diffuseColor=obj.TextColor[0:3]

        # Create separator for this text
        text_sep = coin.SoSeparator()
        text_sep.addChild(transform)
        text_sep.addChild(material)
        text_sep.addChild(font)
        text_sep.addChild(text_node)

        self.text_separator.addChild(text_sep)

    def doubleClicked(self, vobj):
        """Handle double-click event"""
        try:
            # Import and show the node modifier dialog
            from ui.dialog_NodeModifier import show_node_modifier
            # Pass the node object to pre-select it
            show_node_modifier([vobj.Object])
            return True
        except Exception as e:
            App.Console.PrintError(f"Error opening node modifier: {str(e)}\n")
            return False

    def setupContextMenu(self, vobj, menu):
        """Add custom context menu item"""
        from PySide import QtGui, QtCore
        action = QtGui.QAction("Modify Node Properties", menu)
        action.triggered.connect(lambda: self.onModifyNode(vobj.Object))
        menu.addAction(action)

    def onModifyNode(self, node_obj):
        """Handle context menu action"""
        try:
            from ui.dialog_NodeModifier import show_node_modifier
            show_node_modifier([node_obj])
        except Exception as e:
            App.Console.PrintError(f"Error opening node modifier: {str(e)}\n")

    def updateData(self, obj, prop):
        """Handle data changes"""
        pass

    def onChanged(self, vobj, prop):
        """Handle view provider changes"""
        pass

    def getIcon(self):
        """Return the icon for this node"""
        return NODE_ICON_PATH

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None


class ResultNode(NodeFeature):
    def __init__(self, obj, base_node=None):
        super(ResultNode, self).__init__(obj)
        obj.Type = "ResultNode"
        obj.addProperty("App::PropertyLink", "BaseNode", "Base", "Original node")
        obj.addProperty("App::PropertyVectorDistance", "Displacement", "Results", "Node displacement (mm)")
        obj.addProperty("App::PropertyLength", "DisplacementMagnitude", "Results", "Displacement magnitude")
        obj.addProperty("App::PropertyLength", "Base_X", "Base", "original position", 4)
        obj.addProperty("App::PropertyLength", "Base_Y", "Base", "original position", 4)
        obj.addProperty("App::PropertyLength", "Base_Z", "Base", "original position", 4)

        if base_node:
            obj.X = base_node.X
            obj.Y = base_node.Y
            obj.Z = base_node.Z
            obj.Base_X = base_node.X
            obj.Base_Y = base_node.Y
            obj.Base_Z = base_node.Z
            obj.BaseNode = base_node
            obj.PointSize = base_node.PointSize * 1.2  # Slightly larger than original
            obj.PointColor = (0.0, 1.0, 0.0)  # Green for results
            obj.Displacement = App.Vector(0, 0, 0)
            obj.DisplacementMagnitude = 0.0


    def set_displacement(self, displacement, max_disp=1.0):
        """Update the node's displacement and visual representation"""
        self.Object.Displacement = displacement
        self.Object.DisplacementMagnitude = displacement.Length
        self.Object.X = self.Object.Base_X.getValueAs("mm") +  self.Object.Displacement[0] / (0.5 * max_disp)
        self.Object.Y = self.Object.Base_Y.getValueAs("mm") + self.Object.Displacement[1] / (0.5 * max_disp)
        self.Object.Z = self.Object.Base_Z.getValueAs("mm") + self.Object.Displacement[2] / (0.5 * max_disp)

def create_result_node(base_node):
    """Create a ResultNode from a base NodeFeature"""
    doc = App.ActiveDocument
    if not doc or not base_node:
        return None
    try:
        result_node = doc.addObject("Part::FeaturePython", "ResultNode")
        ResultNode(result_node, base_node)
        if App.GuiUp:
            # Use our custom view provider for result nodes as well
            result_node.ViewObject.Proxy = NodeViewProvider(result_node.ViewObject)
            result_node.ViewObject.Transparency = 30
        return result_node
    except Exception as e:
        App.Console.PrintError(f"Error creating result node: {str(e)}\n")
        return None


class NodeGroup:
    def __init__(self, obj):
        obj.Proxy = self
        obj.addProperty("App::PropertyString", "Type", "Base", "Group Type", 4).Type = "NodesGroup"

    def execute(self, obj):
        """Required execution method"""
        pass

    def onChanged(self, obj, prop):
        pass

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None

    def getDisplayModes(self, obj):
        return ["Default"]

    def getDefaultDisplayMode(self):
        return "Default"


class NodeGroupViewProvider:
    def __init__(self, vobj):
        vobj.Proxy = self
        vobj.addProperty("App::PropertyColor", "NodeColor", "Style", "Color for all nodes in this group").NodeColor = (
            2.0, 0.0, 0.0)
        vobj.addProperty("App::PropertyFloat", "NodeScale", "Style",
                         "Scale factor for all nodes in this group").NodeScale = 5.0

    def getIcon(self):
        return NODE_GROUP_ICON_PATH

    def attach(self, vobj):
        self.Object = vobj.Object

    def updateData(self, vobj, prop):
        pass

    def onChanged(self, vobj, prop):
        if prop in ["NodeColor", "NodeScale"]:
            # Update all nodes in this group when color or scale changes
            for child in vobj.Object.Group:
                if hasattr(child, "Proxy") and hasattr(vobj.Object, "Proxy"):
                    child.ViewObject.PointColor = vobj.NodeColor
                    child.ViewObject.PointSize = vobj.NodeScale
                    child.Proxy.execute(child)

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

    def setupContextMenu(self, vobj, menu):
        """Adds a context menu item to list all nodes."""

        # Check if PrettyTable is available
        if PrettyTable is None:
            App.Console.PrintWarning("PrettyTable not available for node listing.\n")
            return

        action = QtGui.QAction("List Nodes in Report View", menu)
        action.triggered.connect(lambda: self.onListNodes(vobj.Object))
        menu.addAction(action)

    def onListNodes(self, node_group):
        """Collects node data and prints it to the FreeCAD report view using PrettyTable."""

        if PrettyTable is None:
            App.Console.PrintError("Cannot list nodes: PrettyTable module is missing.\n")
            return

        # Initialize PrettyTable
        table = PrettyTable()
        table.field_names = ["Name", "X (m)", "Y (m)", "Z (m)", "Bound. Cond."]
        table.align["Name"] = "l"
        table.align["X (m)"] = "r"
        table.align["Y (m)"] = "r"
        table.align["Z (m)"] = "r"
        table.align["Boundary Condition"] = "l"
        table.set_style(TableStyle.SINGLE_BORDER)

        header_string = "\n--- Node List ---\n"
        # Iterate over all objects in the node group
        for obj in node_group.Group:
            if hasattr(obj, "Type") and obj.Type == "NodeFeature":
                # Get coordinates in meters and extract the float value using .Value
                try:
                    x_m = Units.Quantity(obj.X).getValueAs('m').Value
                    y_m = Units.Quantity(obj.Y).getValueAs('m').Value
                    z_m = Units.Quantity(obj.Z).getValueAs('m').Value
                except Exception:
                    # Fallback if Units are not easily convertible
                    x_m = getattr(obj, 'X', 0.0)
                    y_m = getattr(obj, 'Y', 0.0)
                    z_m = getattr(obj, 'Z', 0.0)

                # Format coordinates to 4 decimal places
                x_str = f"{x_m:.4f}"
                y_str = f"{y_m:.4f}"
                z_str = f"{z_m:.4f}"

                # Determine Boundary Condition (BC) information
                boundary_condition = "N/A"

                if hasattr(obj, "IsFixed") and obj.IsFixed:
                    boundary_condition = "Fixed (All DOFs)"
                elif hasattr(obj, "BCInfo") and obj.BCInfo != "None":
                    boundary_condition = obj.BCInfo
                elif hasattr(obj, "Texts") and obj.Texts:
                    # Display annotations if they contain BC information
                    boundary_condition = "; ".join(obj.Texts)

                # Add row to the table
                table.add_row([obj.Label, x_str, y_str, z_str, boundary_condition])

        table_string = table.get_string()

        final_output = header_string + table_string + "\n"

        App.Console.PrintMessage(final_output)

class NodeResultGroupViewProvider(NodeGroupViewProvider):
    def __init__(self, vobj):
        super().__init__(vobj)

    def getIcon(self):
        return NODE_GROUP_RESULTS_ICON_PATH


def make_nodes_group():
    """Create or get the Nodes group with proper icon paths and add it to AnalysisGroup"""
    doc = App.ActiveDocument
    if not doc:
        App.Console.PrintError("No active document found\n")
        return None

    # Check if Nodes group already exists
    if hasattr(doc, "Nodes"):
        node_group = doc.Nodes
    else:
        # Create new Nodes group
        node_group = doc.addObject("App::DocumentObjectGroupPython", "Nodes")
        NodeGroup(node_group)
        node_group.Label = "Nodes"

        # Add the Nodes group to the AnalysisGroup if it exists
        from features.AnalysisGroup import get_analysis_group
        analysis_group = get_analysis_group()
        if analysis_group and node_group not in analysis_group.Group:
            analysis_group.addObject(node_group)

        if App.GuiUp:
            node_group.ViewObject.Proxy = NodeGroupViewProvider(node_group.ViewObject)

    return node_group


def make_result_nodes_group():
    """Create or get the Nodes group with proper icon paths and add it to AnalysisGroup"""
    doc = App.ActiveDocument
    if not doc:
        App.Console.PrintError("No active document found\n")
        return None

    # Check if Nodes group already exists
    if hasattr(doc, "Nodes_Result"):
        node_group = doc.Nodes
    else:
        # Create new Nodes group
        node_group = doc.addObject("App::DocumentObjectGroupPython", "NodesResult")
        NodeGroup(node_group)
        node_group.Label = "Nodes Results"
        if App.GuiUp:
            node_group.ViewObject.Proxy = NodeResultGroupViewProvider(node_group.ViewObject)
    App.ActiveDocument.recompute()

    return node_group


def get_all_nodes():
    """Get all nodes in the document"""
    doc = App.ActiveDocument
    if not doc:
        return []

    nodes = []
    nodes_group = doc.getObject("Nodes")
    for obj in nodes_group.Group:
        if hasattr(obj, "Type") and obj.Type == "NodeFeature":
            nodes.append(obj)
    return nodes


def update_node(node, x=None, y=None, z=None, point_size=None, point_color=None):
    """Update node properties"""
    if x is not None:
        node.X = x
    if y is not None:
        node.Y = y
    if z is not None:
        node.Z = z
    if point_size is not None:
        node.PointSize = point_size
    if point_color is not None:
        node.PointColor = point_color
    print("recompute Nodes l480")
    App.ActiveDocument.recompute()


def delete_node(node):
    """Delete a node"""
    doc = App.ActiveDocument
    if doc and hasattr(doc, "Nodes") and node in doc.Nodes.Group:
        doc.Nodes.removeObject(node)
        doc.removeObject(node.Name)
        App.ActiveDocument.recompute()


def create_node(**kwargs):
    doc = App.ActiveDocument
    if not doc:
        App.Console.PrintError("No active document found\n")
        return None

    try:
        node_props = {
            "X": kwargs.get('X', 0.0),
            "Y": kwargs.get('Y', 0.0),
            "Z": kwargs.get('Z', 0.0),
        }

        group = make_nodes_group()

        if not group:
            App.Console.PrintError("Failed to create node group\n")
            return None

        obj = doc.addObject("Part::FeaturePython", "Node")
        NodeFeature(obj)

        if App.GuiUp:
            # Use our custom view provider instead of the draft one
            obj.ViewObject.Proxy = NodeViewProvider(obj.ViewObject)
            obj.ViewObject.PointColor = group.ViewObject.NodeColor
            obj.ViewObject.PointSize = group.ViewObject.NodeScale

        for prop, value in node_props.items():
            setattr(obj, prop, value)

        group.addObject(obj)
        App.ActiveDocument.recompute()
        return obj
    except Exception as e:
        App.Console.PrintError(f"Error in create_node: {str(e)}\n")
        return None