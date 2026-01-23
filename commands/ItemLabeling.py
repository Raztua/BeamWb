# ItemLabeling.py
import FreeCAD as App
import FreeCADGui as Gui
import os

def get_icon_path(icon_name):
    """Get absolute path to an icon"""
    WORKBENCH_DIR = os.path.dirname(os.path.dirname(__file__))
    ICON_DIR = os.path.join(WORKBENCH_DIR, "icons")
    return os.path.join(ICON_DIR, icon_name)

class ItemLabelingCommand:
    """Command to label nodes and beams"""

    def GetResources(self):
        return {
            'Pixmap': get_icon_path("labeling_icon.svg"),  # You'll need to create this icon
            'MenuText': "Item Labeling",
            'ToolTip': "Add labels to nodes and beams with various information",
            'Accel': "L, L"
        }

    def Activated(self):
        """Execute when the command is clicked"""
        from ui.dialog_ItemLabeling import show_item_labeling
        show_item_labeling()

    def IsActive(self):
        """Determine if the command should be active"""
        return App.ActiveDocument is not None

# Only register the command if we're running in FreeCAD
if App.GuiUp:
    Gui.addCommand('ItemLabeling', ItemLabelingCommand())