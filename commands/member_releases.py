import FreeCAD as App
import FreeCADGui as Gui
import os

# Use absolute path for FreeCAD's Mod directory
def get_icon_path(icon_name):
    """Get absolute path to an icon"""
    WORKBENCH_DIR = os.path.dirname(os.path.dirname(__file__))
    ICON_DIR = os.path.join(WORKBENCH_DIR, "icons")
    return os.path.join(ICON_DIR, icon_name)

class CreateMemberReleaseCommand:
    """Command to create member end releases"""

    def GetResources(self):
        return {
            'Pixmap': get_icon_path("member_release_icon.svg"),
            'MenuText': "Create Member Release",
            'ToolTip': "Create member end release definitions",
            'Accel': "M, R"
        }

    def Activated(self):
        """Run when command is clicked"""
        from ui.dialog_MemberReleaseCreator import show_member_release_modifier
        show_member_release_modifier()

    def IsActive(self):
        """Determine if command should be active"""
        if not hasattr(App.ActiveDocument, "Analysis"):
            return False
        return App.ActiveDocument is not None


# Add command to FreeCAD
Gui.addCommand('CreateMemberRelease', CreateMemberReleaseCommand())