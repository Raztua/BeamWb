# commands/CodeCheck.py
import FreeCAD as App
import FreeCADGui as Gui
import os
from ui.TaskPanel_CodeCheck import show_code_check_task_panel

def get_icon_path(icon_name):
    """Get absolute path to an icon"""
    WORKBENCH_DIR = os.path.dirname(os.path.dirname(__file__))
    ICON_DIR = os.path.join(WORKBENCH_DIR, "icons")
    return os.path.join(ICON_DIR, icon_name)

class CreateCodeCheckCommand:
    """
    Command to open the Code Check Setup Task Panel.
    """
    def GetResources(self):
        return {
            'Pixmap': get_icon_path("Codecheck_icon.svg"),
            'MenuText': "Code Check Setup",
            'ToolTip': "Setup standards and parameters for code checking"
        }

    def Activated(self):
        # Open the Setup Task Panel
        show_code_check_task_panel()

    def IsActive(self):
        """Determine if the command should be active"""
        return App.ActiveDocument is not None

if Gui.getMainWindow():
    Gui.addCommand('RunCodeCheck', CreateCodeCheckCommand())