# commands/AnalysisCommand.py
import FreeCAD as App
import FreeCADGui as Gui
import os


def get_icon_path(icon_name):
    """Get absolute path to an icon"""
    WORKBENCH_DIR = os.path.dirname(os.path.dirname(__file__))
    ICON_DIR = os.path.join(WORKBENCH_DIR, "icons")
    return os.path.join(ICON_DIR, icon_name)


class AnalysisCommand:
    """Command to setup and run analysis"""

    def GetResources(self):
        return {
            'Pixmap': get_icon_path("solver_icon.svg"),
            'MenuText': 'Run Analysis',
            'ToolTip': 'Setup and run structural analysis',
            'Accel': 'F5'
        }

    def Activated(self):
        """Run when command is clicked"""
        from ui.dialog_AnalysisSetup import show_analysis_setup
        show_analysis_setup()

    def IsActive(self):
        """Determine if command should be active"""
        if not (hasattr(App.ActiveDocument, "Analysis")):
            return False
        return App.ActiveDocument is not None


# Only register the command if we're running in FreeCAD
if App.GuiUp:
    Gui.addCommand('AnalysisCommand', AnalysisCommand())