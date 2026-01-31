# nodes.py (command part)
import FreeCAD as App
import FreeCADGui as Gui
import os


# Get the workbench directory
WORKBENCH_DIR = os.path.dirname(os.path.dirname(__file__))
ICON_DIR = os.path.join(WORKBENCH_DIR, "icons")
NODE_ICON_PATH = os.path.join(ICON_DIR, "node_icon.svg")

class ManageNodesCommand:
    """Command to manage nodes using task panel"""

    def GetResources(self):
        return {
            'Pixmap': os.path.join(ICON_DIR, "node_manager_icon.svg"),
            'MenuText': "Manage Nodes",
            'ToolTip': "Create and manage structural nodes",
            'Accel': "N, M"
        }

    def Activated(self):
        """Run when command is clicked"""
        from ui.dialog_NodeManager import show_node_manager
        show_node_manager()

    def IsActive(self):
        """Determine if command should be active"""
        if not (hasattr(App.ActiveDocument, "Analysis")):
            return False
        return App.ActiveDocument is not None

class CreateNodeCommand:
    """Command to create nodes by entering coordinates"""

    def GetResources(self):
        return {
            'Pixmap': os.path.join(ICON_DIR, "node_create_icon.svg"),
            'MenuText': "Create Node",
            'ToolTip': "Create nodes by entering coordinates",
            'Accel': "N, C"
        }

    def Activated(self):
        """Run when command is clicked"""
        from ui.dialog_NodeCreator import show_node_creator
        show_node_creator()

    def IsActive(self):
        """Determine if command should be active"""
        return App.ActiveDocument is not None


class ModifyNodeCommand:
    """Command to modify existing nodes"""

    def GetResources(self):
        return {
            'Pixmap': os.path.join(ICON_DIR, "node_modify_icon.svg"),
            'MenuText': "Modify Nodes",
            'ToolTip': "Modify selected nodes",
            'Accel': "N, M"
        }

    def Activated(self):
        """Run when command is clicked"""
        from ui.dialog_NodeModifier import show_node_modifier
        show_node_modifier()

    def IsActive(self):
        """Determine if command should be active"""
        return App.ActiveDocument is not None


class OffsetNodeCommand:
    """Command to create offset nodes"""

    def GetResources(self):
        return {
            'Pixmap': os.path.join(ICON_DIR, "node_offset_icon.svg"),
            'MenuText': "Offset Nodes",
            'ToolTip': "Create nodes offset from selected nodes",
            'Accel': "N, O"
        }

    def Activated(self):
        """Run when command is clicked"""
        from ui.dialog_NodeOffset import show_node_offset
        show_node_offset()

    def IsActive(self):
        """Determine if command should be active"""
        return App.ActiveDocument is not None


# Add commands to FreeCAD
Gui.addCommand('CreateNode', CreateNodeCommand())
Gui.addCommand('ModifyNode', ModifyNodeCommand())
Gui.addCommand('OffsetNode', OffsetNodeCommand())
Gui.addCommand('ManageNodes', ManageNodesCommand())