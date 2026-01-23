# commands/results_viewer.py
import FreeCAD as App
import FreeCADGui as Gui
import os


def get_icon_path(icon_name):
    """Get absolute path to an icon"""
    WORKBENCH_DIR = os.path.dirname(os.path.dirname(__file__))
    ICON_DIR = os.path.join(WORKBENCH_DIR, "icons")
    return os.path.join(ICON_DIR, icon_name)


class ResultsViewerCommand:
    """Command to show the results viewer dialog"""

    def GetResources(self):
        return {
            'Pixmap': get_icon_path("results_icon.svg"),  # You'll need to add this SVG
            'MenuText': "Results Viewer",
            'ToolTip': "View and control analysis results",
            'Accel': "R, V"
        }

    def Activated(self):
        """Run when command is clicked"""
        from ui.dialog_ResultsViewer import show_results_viewer
        show_results_viewer()

    def IsActive(self):
        """Determine if command should be active"""
        return App.ActiveDocument is not None


# Add command to FreeCAD
Gui.addCommand('ResultsViewer', ResultsViewerCommand())