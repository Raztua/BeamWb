import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtGui, QtCore
from pivy import coin
import os

# Constants
WORKBENCH_DIR = os.path.dirname(os.path.dirname(__file__))
ICON_DIR = os.path.join(WORKBENCH_DIR, "icons")
MEMBER_RELEASE_ICON_PATH = os.path.join(ICON_DIR, "member_release_icon.svg")
MEMBER_RELEASE_GROUP_ICON_PATH = os.path.join(ICON_DIR, "member_release_group_icon.svg")


class MemberReleaseFeature:
    def __init__(self, obj):
        obj.Proxy = self
        self.Object=obj
        self.Type = "MemberRelease"

        # Add properties
        obj.addProperty("App::PropertyString", "Type", "Base", "Member release type").Type = "MemberRelease"

        # Release properties for start and end
        obj.addProperty("App::PropertyBool", "Start_Dx", "Start Release", "Release - Displacement along X at start").Start_Dx = False
        obj.addProperty("App::PropertyBool", "Start_Dy", "Start Release", "Release - Displacement along Y at start").Start_Dy = False
        obj.addProperty("App::PropertyBool", "Start_Dz", "Start Release", "Release - Displacement along Z at start").Start_Dz = False
        obj.addProperty("App::PropertyBool", "Start_Rx", "Start Release", "Release - Rotation about X at start").Start_Rx = False
        obj.addProperty("App::PropertyBool", "Start_Ry", "Start Release", "Release - Rotation about Y at start").Start_Ry = False
        obj.addProperty("App::PropertyBool", "Start_Rz", "Start Release", "Release - Rotation about Z at start").Start_Rz = False

        obj.addProperty("App::PropertyBool", "End_Dx", "End Release", "Release - Displacement along X at end").End_Dx = False
        obj.addProperty("App::PropertyBool", "End_Dy", "End Release", "Release - Displacement along Y at end").End_Dy = False
        obj.addProperty("App::PropertyBool", "End_Dz", "End Release", "Release - Displacement along Z at end").End_Dz = False
        obj.addProperty("App::PropertyBool", "End_Rx", "End Release", "Release - Rotation about X at end").End_Rx = False
        obj.addProperty("App::PropertyBool", "End_Ry", "End Release", "Release - Rotation about Y at end").End_Ry = False
        obj.addProperty("App::PropertyBool", "End_Rz", "End Release", "Release - Rotation about Z at end").End_Rz = False

        # Visual properties
        obj.addProperty("App::PropertyColor", "Color", "Display", "Member release color").Color = (0.0, 0.33, 1.0)
        obj.addProperty("App::PropertyFloat", "Scale", "Display", "Member release scale").Scale = 1.0

        # Set the initial label
        obj.Label = "MemberRelease"

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

        if prop in ["Start_Dx", "Start_Dy", "Start_Dz", "Start_Rx", "Start_Ry", "Start_Rz",
                   "End_Dx", "End_Dy", "End_Dz", "End_Rx", "End_Ry", "End_Rz", 
                   "Color", "Scale"]:
            self.execute(obj)

    def get_start_release(self):
        """Return start release as a tuple (Dx, Dy, Dz, Rx, Ry, Rz)"""
        return (self.Object.Start_Dx, self.Object.Start_Dy, self.Object.Start_Dz, 
                self.Object.Start_Rx, self.Object.Start_Ry, self.Object.Start_Rz)

    def get_end_release(self):
        """Return end release as a tuple (Dx, Dy, Dz, Rx, Ry, Rz)"""
        return (self.Object.End_Dx, self.Object.End_Dy, self.Object.End_Dz, 
                self.Object.End_Rx, self.Object.End_Ry, self.Object.End_Rz)

    def get_release_description(self):
        """Get a human-readable description of the releases"""
        start_releases = []
        end_releases = []
        
        releases_names = ["Dx", "Dy", "Dz", "Rx", "Ry", "Rz"]
        
        start = self.get_start_release()
        end = self.get_end_release()
        
        for i, name in enumerate(releases_names):
            if start[i]:
                start_releases.append(f"S{name}")
            if end[i]:
                end_releases.append(f"E{name}")
                
        description = "Releases: "
        if start_releases:
            description += "Start[" + ",".join(start_releases) + "] "
        if end_releases:
            description += "End[" + ",".join(end_releases) + "]"
            
        return description.strip()

    def dumps(self):
        return None

    def loads(self, state):
        return None


class MemberReleaseViewProvider:
    def __init__(self, vobj):
        vobj.Proxy = self
        self.ViewObject = vobj
        self.Object = vobj.Object
        self.default = None
        if not hasattr(self, "ViewObject"):
            self.ViewObject = vobj
        if not hasattr(self, "Object"):
            self.Object = vobj.Object

        vobj.addProperty("App::PropertyPercent", "Transparency", "Display",
                         "Transparency level").Transparency = 0

        # Visual elements - we'll create the nodes but NOT add them to scene
        if not hasattr(self, "start_release_node"):
            self.start_release_node = None
        if not hasattr(self, "end_release_node"):
            self.end_release_node = None


    def attach(self, vobj):
        # Store reference to view object
        if not hasattr(self, "ViewObject"):
            self.ViewObject = vobj
        # Store reference to object
        if not hasattr(self, "Object"):
            self.Object = vobj.Object
        from pivy import coin
        self.default = coin.SoGroup()
        vobj.addDisplayMode(self.default, "Default")

        # Create the visualization nodes but don't add them to any scene
        self.updateVisualization(self.Object)

    def doubleClicked(self, vobj):
        """Handle double-click event"""
        try:
            from ui.dialog_MemberReleaseCreator import show_member_release_modifier
            # Pass the object for editing
            show_member_release_modifier([vobj.Object])
            return True
        except Exception as e:
            App.Console.PrintError(f"Error opening member release modifier: {str(e)}\n")
            return False

    def setupContextMenu(self, vobj, menu):
        """Add custom context menu item"""
        from PySide import QtGui, QtCore
        action = QtGui.QAction("Modify Member Release", menu)
        action.triggered.connect(lambda: self.onModifyRelease(vobj.Object))
        menu.addAction(action)

    def onModifyRelease(self, release_obj):
        """Handle context menu action"""
        try:
            from ui.dialog_MemberReleaseCreator import show_member_release_modifier
            show_member_release_modifier([release_obj])
        except Exception as e:
            App.Console.PrintError(f"Error opening member release modifier: {str(e)}\n")

    def updateData(self, obj, prop):
        pass

    def updateVisualization(self, obj):
        """Update the member release visualization nodes"""
        if not obj:
            return

        # Get member release properties
        start_release = (obj.Start_Dx, obj.Start_Dy, obj.Start_Dz, obj.Start_Rx, obj.Start_Ry, obj.Start_Rz)
        end_release = (obj.End_Dx, obj.End_Dy, obj.End_Dz, obj.End_Rx, obj.End_Ry, obj.End_Rz)
        color = obj.Color[0:3] if hasattr(obj, "Color") else (0.0, 0.33, 1.0)
        scale = obj.Scale if hasattr(obj, "Scale") else 1.0

        # Create visualization nodes for start and end releases
        self.start_release_node = self._create_release_node(start_release, color, scale, is_start=True)
        self.end_release_node = self._create_release_node(end_release, color, scale, is_start=False)

    def _create_release_node(self, release, color, scale, is_start=True):
        """Create a visualization node for a release (start or end)"""
        from pivy import coin
        
        # Create separator for this release
        release_sep = coin.SoSeparator()
        release_sep.setName(f"{'Start' if is_start else 'End'}Release")
        
        # Create material
        material = coin.SoMaterial()
        material.diffuseColor = color
        release_sep.addChild(material)
        
        # Create release symbol based on fixity
        symbol = self._create_release_symbol(release, scale, is_start)
        if symbol:
            release_sep.addChild(symbol)
            
        return release_sep

    def _create_release_symbol(self, release, scale, is_start):
        """Create visual symbol representing the release type"""
        from pivy import coin
        
        # Count the number of releases
        release_count = sum(release)
        
        if release_count == 0:
            # No releases - show fixed symbol (cube)
            cube = coin.SoCube()
            cube.width = 3.0 * scale
            cube.height = 3.0 * scale
            cube.depth = 3.0 * scale
            return cube
            
        else:
            # Has releases - show spring-like symbol
            spring_sep = coin.SoSeparator()
            
            # Create a spring shape using helix or multiple circles
            for i in range(3):
                transform = coin.SoTransform()
                transform.translation.setValue(0, 0, i * 2 * scale)
                
                # Create circle for spring coil
                circle = coin.SoSphere()
                circle.radius = 1.5 * scale
                
                coil_sep = coin.SoSeparator()
                coil_sep.addChild(transform)
                coil_sep.addChild(circle)
                spring_sep.addChild(coil_sep)
            
            return spring_sep

    def get_start_release_node(self):
        """Get the start release visualization node"""
        return self.start_release_node

    def get_end_release_node(self):
        """Get the end release visualization node"""
        return self.end_release_node

    def getDisplayModes(self, obj):
        return ["Default"]

    def getDefaultDisplayMode(self):
        return "Default"

    def setDisplayMode(self, mode):
        return mode

    def getIcon(self):
        return MEMBER_RELEASE_ICON_PATH

    def onChanged(self, vobj, prop):
        if prop in ["Color", "Scale", "Transparency"]:
            self.updateVisualization(vobj.Object)


    def dumps(self):
        return None

    def loads(self, state):
        return None

    def canDragObjects(self):
        return False

    def canDropObjects(self):
        return False

class MemberReleaseGroup:
    def __init__(self, obj):
        obj.Proxy = self
        obj.addProperty("App::PropertyString", "Type", "Base", "Group Type", 4).Type = "MemberReleaseGroup"

    def onChanged(self, obj, prop):
        pass

    def getDisplayModes(self, obj):
        return ["Default"]

    def getDefaultDisplayMode(self):
        return "Default"


class MemberReleaseGroupViewProvider:
    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        return MEMBER_RELEASE_GROUP_ICON_PATH

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

def make_member_release_group():
    """Create or get the MemberReleases group"""
    doc = App.ActiveDocument
    if not doc:
        return None

    if hasattr(doc, "MemberReleases"):
        mr_group = doc.MemberReleases
    else:
        mr_group = doc.addObject("App::DocumentObjectGroupPython", "MemberReleases")
        MemberReleaseGroup(mr_group)
        mr_group.Label = "MemberReleases"
        
        from features.AnalysisGroup import get_analysis_group
        analysis_group = get_analysis_group()
        if analysis_group and mr_group not in analysis_group.Group:
            analysis_group.addObject(mr_group)
            
        if App.GuiUp:
            mr_group.ViewObject.Proxy = MemberReleaseGroupViewProvider(mr_group.ViewObject)
        
    return mr_group


def create_member_release(start_release=None, end_release=None, label=None):
    """Create a member release object"""
    doc = App.ActiveDocument
    if not doc:
        App.Console.PrintError("No active document found\n")
        return None

    try:
        group = make_member_release_group()
        if not group:
            App.Console.PrintError("Failed to create member release group\n")
            return None

        # Create member release object
        obj = doc.addObject("App::FeaturePython", "MemberRelease")
        MemberReleaseFeature(obj)

        if App.GuiUp:
            obj.ViewObject.Proxy = MemberReleaseViewProvider(obj.ViewObject)

        # Set default releases if provided
        if start_release:
            obj.Start_Dx, obj.Start_Dy, obj.Start_Dz, obj.Start_Rx, obj.Start_Ry, obj.Start_Rz = start_release
        
        if end_release:
            obj.End_Dx, obj.End_Dy, obj.End_Dz, obj.End_Rx, obj.End_Ry, obj.End_Rz = end_release

        # Set label
        if label:
            obj.Label = label
        else:
            # Generate descriptive label
            desc = obj.Proxy.get_release_description()
            obj.Label = f"MemberRelease_{desc.replace(' ', '_')}"

        group.addObject(obj)
        App.ActiveDocument.recompute()
        return obj

    except Exception as e:
        App.Console.PrintError(f"Error creating member release: {str(e)}\n")
        return None


def create_common_release_types():
    """Create common member release types"""
    common_releases = [
        # Fully fixed (no releases)
        ("Fixed", [False]*6, [False]*6),
        # Hinged both ends
        ("Hinged_Both", [False, False, False, True, True, True], [False, False, False, True, True, True]),
        # Hinged start only
        ("Hinged_Start", [False, False, False, True, True, True], [False]*6),
        # Hinged end only  
        ("Hinged_End", [False]*6, [False, False, False, True, True, True]),
        # Roller both ends (release Dy)
        ("Roller_Both", [False, True, False, False, False, False], [False, True, False, False, False, False]),
    ]
    
    created = []
    for name, start, end in common_releases:
        release = create_member_release(start, end, name)
        if release:
            created.append(release)
    App.ActiveDocument.recompute()
    
    return created