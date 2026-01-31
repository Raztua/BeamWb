from types import NoneType
import FreeCAD as App
import FreeCADGui as Gui
from features.section_definitions import get_section_points
import os
import math

# Constants
WORKBENCH_DIR = os.path.dirname(os.path.dirname(__file__))
ICON_DIR = os.path.join(WORKBENCH_DIR, "icons")
BEAM_GROUP_ICON_PATH = os.path.join(ICON_DIR, "beam_group_icon.svg")
BEAM_ICON_PATH = os.path.join(ICON_DIR, "beam_icon.svg")


class BeamFeature:
    def __init__(self, obj):
        self.node = None
        obj.Proxy = self

        # Node properties
        obj.addProperty("App::PropertyLink", "StartNode", "Beam", "Start node object").StartNode = None
        obj.addProperty("App::PropertyLink", "EndNode", "Beam", "End node object").EndNode = None
        obj.addProperty("App::PropertyVector", "StartNodeDisp", "Results",
                        "start node displacement", 4).StartNodeDisp = App.Vector(0, 0, 1000)
        obj.addProperty("App::PropertyVector", "EndNodeDisp", "Results",
                        "start node displacement", 4).EndNodeDisp = App.Vector(0, 0, -500)
        # Local coordinate system properties without offset
        obj.addProperty("App::PropertyFloat", "section_rotation", "Beam",
                        "section rotation(in deg)").section_rotation=0.0
        obj.addProperty("App::PropertyVector", "Local_X", "Beam", "Local X-axis (beam direction)",
                        4).Local_X = App.Vector(0, 0, 1)
        obj.addProperty("App::PropertyVector", "Local_Y", "Beam", "Local Y-axis", 4).Local_Y = App.Vector(1, 0, 0)
        obj.addProperty("App::PropertyVector", "Local_Z", "Beam", "Local Z-axis", 4).Local_Z = App.Vector(0, 1, 0)

        # Offset properties
        obj.addProperty("App::PropertyBool", "OffsetAxis", "Offset", "Local axis system for offset").OffsetAxis = True
        obj.addProperty("App::PropertyVector", "StartOffset", "Offset",
                        "Offset at start node").StartOffset = App.Vector(0, 0, 0)
        obj.addProperty("App::PropertyVector", "EndOffset", "Offset",
                        "Offset at end node").EndOffset = App.Vector(0, 0, 0)

        # Section properties
        obj.addProperty("App::PropertyLink", "Section", "Section", "Cross-section from library")
        obj.addProperty("App::PropertyFloat", "angle", "Section", "section rotation (deg)", 1).angle = 0.0

        # Visual properties
        #obj.addProperty("App::PropertyColor", "FlangeColor", "Appearance", "Color of flanges", 4).FlangeColor = (
        # 0.2, 0.5, 0.8)
        #obj.addProperty("App::PropertyColor", "WebColor", "Appearance", "Color of web", 4).WebColor = (0.4, 0.7, 1.0)

        # Read-only properties
        obj.addProperty("App::PropertyFloat", "Length", "Base", "Length of beam", 1).Length = 0.0
        obj.addProperty("App::PropertyVector", "StartPos", "Base", "Start position (hidden)",
                        4).StartPos = App.Vector(0, 0, 0)
        obj.addProperty("App::PropertyVector", "EndPos", "Base", "End position (hidden)", 4).EndPos = App.Vector(0,                                                                                                          0)
        obj.addProperty("App::PropertyVector", "StartPosWithOffset", "Base",
                        "Start position with offset (hidden)", 4).StartPosWithOffset = App.Vector(0, 0, 0)
        obj.addProperty("App::PropertyVector", "EndPosWithOffset", "Base",
                        "End position with offset (hidden)", 4).EndPosWithOffset = App.Vector(0, 0, 0)

        obj.addProperty("App::PropertyString", "Type", "Base", "Group Type",4).Type = "BeamFeature"

        self.execute(obj)

    def validate_nodes(self, obj):
        """Validate that nodes exist and are proper node objects"""
        valid = True
        if not obj.StartNode or not hasattr(obj.StartNode, "Proxy"):
            App.Console.PrintWarning("Beam: Invalid start node\n")
            valid = False
        if not obj.EndNode or not hasattr(obj.EndNode, "Proxy"):
            App.Console.PrintWarning("Beam: Invalid end node\n")
            valid = False
        return valid

    def update_visualization(self, obj):
        """Trigger view provider update instead of direct manipulation"""
        if hasattr(obj, 'ViewObject') and obj.ViewObject is not None:
            if hasattr(obj.ViewObject, 'Proxy') and obj.ViewObject.Proxy is not None:
                if hasattr(obj.ViewObject.Proxy, 'updateVisualization'):
                    obj.ViewObject.Proxy.updateVisualization(obj)

    def get_show_sections(self, obj):
        """Get ShowSections property from parent group"""
        if obj.InList and hasattr(obj.InList[0], "ShowSections"):
            return obj.InList[0].ShowSections
        return True

    def calculate_local_axes(self,obj, beam_dir):
        """Calculate the local coordinate system with consistent orientation"""
        if beam_dir.Length < 1e-6:
            # Handle zero-length beam case
            return App.Vector(1, 0, 0), App.Vector(0, 1, 0), App.Vector(0, 0, 1)

        local_x = beam_dir.normalize()

        # Default up vector is global Z
        up_vector = App.Vector(0, 0, 1)

        # If beam is nearly vertical, use global X as reference instead
        if abs(local_x.dot(up_vector)) > 0.999:
            up_vector = App.Vector(-1, 0, 0)

        # Calculate local Y as perpendicular to beam direction and up vector
        local_y = up_vector.cross(local_x).normalize()

        # Calculate Z as X cross Y to ensure right-handed system
        local_z = local_x.cross(local_y).normalize()

        # Apply section rotation around local X-axis
        if obj.section_rotation != 0.0:
            rotation_angle = math.radians(obj.section_rotation)
            rot = App.Rotation(local_x, obj.section_rotation)
            local_y = rot.multVec(local_y)
            local_z = rot.multVec(local_z)
        return local_x, local_y, local_z

    def calculate_positions(self, obj):
        """Calculate all position-related properties"""
        if not self.validate_nodes(obj):
            return

        # Get base positions
        start_pos = App.Vector(obj.StartNode.X, obj.StartNode.Y, obj.StartNode.Z)
        end_pos = App.Vector(obj.EndNode.X, obj.EndNode.Y, obj.EndNode.Z)

        # Calculate beam direction and length prior offset application
        beam_dir = end_pos - start_pos
        obj.Length = beam_dir.Length

        # Calculate local coordinate system (including section rotation)
        try:
            local_x, local_y, local_z = self.calculate_local_axes(obj,beam_dir)
            obj.Local_X = local_x
            obj.Local_Y = local_y
            obj.Local_Z = local_z
        except Exception as e:
            App.Console.PrintWarning(f"Error calculating local axes: {str(e)}\n")
            obj.Local_X = App.Vector(1, 0, 0)
            obj.Local_Y = App.Vector(0, 1, 0)
            obj.Local_Z = App.Vector(0, 0, 1)

        # Create rotation matrix for offset transformation (using rotated axes)
        rot = App.Matrix()
        rot.A11, rot.A12, rot.A13 = obj.Local_X.x, obj.Local_Y.x, obj.Local_Z.x
        rot.A21, rot.A22, rot.A23 = obj.Local_X.y, obj.Local_Y.y, obj.Local_Z.y
        rot.A31, rot.A32, rot.A33 = obj.Local_X.z, obj.Local_Y.z, obj.Local_Z.z

        # Apply offsets in the correct coordinate system
        if obj.OffsetAxis:
            # Transform offsets from local to global coordinates
            start_offset_global = rot.multVec(obj.StartOffset)
            end_offset_global = rot.multVec(obj.EndOffset)
        else:
            # Use offsets directly in global coordinates
            start_offset_global = obj.StartOffset
            end_offset_global = obj.EndOffset

        # Calculate and store positions with offsets
        obj.StartPosWithOffset = start_pos + start_offset_global
        obj.EndPosWithOffset = end_pos + end_offset_global

        # Calculate beam direction and length after application of offset
        beam_dir_offset = obj.EndPosWithOffset - obj.StartPosWithOffset
        obj.Length = beam_dir_offset.Length  # Update length with offset

        # Recalculate local axes based on offset direction if needed
        if obj.OffsetAxis:
            try:
                local_x_offset, local_y_offset, local_z_offset = self.calculate_local_axes(obj,beam_dir_offset)
                obj.Local_X = local_x_offset
                obj.Local_Y = local_y_offset
                obj.Local_Z = local_z_offset
            except Exception as e:
                App.Console.PrintWarning(f"Error recalculating local axes with offset: {str(e)}\n")

    def execute(self, obj):
        if 'Restore' in obj.State:
            return  # or do some special thing
        if obj.StartNode is None or obj.EndNode is None:
            return
        if hasattr(obj,"Type") and obj.Type=="BeamFeature":
            self.calculate_positions(obj)
            self.update_visualization(obj)
    def onChanged(self, obj, prop):
        if prop in ["StartNode", "EndNode", "StartOffset", "EndOffset", "OffsetAxis",
                    "SectionType", "Width", "Height", "Thickness", "SectionRotation", "section_rotation"]:
            self.execute(obj)

    def dumps(self):
        return None

    def loads(self, state):
        return None


class BeamViewProvider:
    def __init__(self, obj):
        obj.Proxy = self
        print("Creating BeamViewProvider")
        self.node = {}

    def attach(self, vobj):
        print("Attaching view provider")
        #self.Default= coin.SoGroup()
        #self.node = coin.SoSeparator()
        #vobj.addDisplayMode(self.Default, "Default")
        from pivy import coin
        # Create display mode nodes

        self.shaded_node = coin.SoSeparator()
        self.shaded_node.setName("Shaded")

        self.line_node = coin.SoSeparator()
        self.line_node.setName("Line")

        # Add display modes to view object
        vobj.addDisplayMode(self.shaded_node, "Shaded")
        vobj.addDisplayMode(self.line_node, "Line")

        # Store reference to view object
        self.ViewObject = vobj

    def updateData(self, obj, prop):
        if prop in ["StartNode", "EndNode", "StartOffset", "EndOffset", "OffsetAxis",
                    "Section", "Local_X", "Local_Y", "Local_Z","StartNodeDisp","EndNodeDisp"]:
            print("updatedata")
            self.updateVisualization(obj)

    def updateVisualization(self, obj):
        """Update all display modes based on current beam data"""
        if not obj.StartNode or not obj.EndNode:
            return

        # Clear existing nodes
        self.shaded_node.removeAllChildren()
        self.line_node.removeAllChildren()

        # Get beam data
        show_sections = obj.Proxy.get_show_sections(obj)
        start_pos = obj.StartPosWithOffset
        end_pos = obj.EndPosWithOffset

        # Create rotation matrix
        rot = App.Matrix(
            obj.Local_X.x, obj.Local_X.y, obj.Local_X.z, 0,
            obj.Local_Y.x, obj.Local_Y.y, obj.Local_Y.z, 0,
            obj.Local_Z.x, obj.Local_Z.y, obj.Local_Z.z, 0,
            start_pos[0], start_pos[1], start_pos[2], 1
        )

        # Update Line mode (simple line)
        self.createLineMode(start_pos, end_pos)

        # Update Wireframe and Shaded modes
        if obj.Section and hasattr(obj.Section, "Proxy") and show_sections:
            self.createSectionModes(obj, obj.Section, start_pos, end_pos, rot)
        else:
            # Fallback to line for both modes
            #self.createLineMode(start_pos, end_pos, self.wireframe_node)
            self.createLineMode(start_pos, end_pos, self.shaded_node)

    def createLineMode(self, start_pos, end_pos, target_node=None):
        """Create simple line representation"""
        from pivy import coin

        if target_node is None:
            target_node = self.line_node

        coords = coin.SoCoordinate3()
        coords.point.setValues(0, 2, [start_pos, end_pos])
        line = coin.SoLineSet()
        line.numVertices.setValue(2)

        # Add line style for better visibility
        line_style = coin.SoDrawStyle()
        line_style.lineWidth = 2

        target_node.addChild(line_style)
        target_node.addChild(coords)
        target_node.addChild(line)

    def createSectionModes(self, obj, section, start_pos, end_pos, rot):
        """Create 3D section representation for wireframe and shaded modes"""
        from pivy import coin

        beam_length = obj.Length

        # Create transform
        transform = coin.SoTransform()
        transform.setMatrix(coin.SbMatrix(
            rot.A11, rot.A12, rot.A13, rot.A14,
            rot.A21, rot.A22, rot.A23, rot.A24,
            rot.A31, rot.A32, rot.A33, rot.A34,
            rot.A41, rot.A42, rot.A43, rot.A44))

        # Get section parameters
        params = {prop: getattr(section, prop).Value for prop in section.PropertiesList
                  if hasattr(getattr(section, prop), 'Value')}

        # Get points and faces for this section type
        points, faces = get_section_points(section.ProfileType, beam_length, params)
        # Create coordinates
        coords = coin.SoCoordinate3()
        coords.point.setValues(0, len(points), points)

        # Create shaded mode
        shaded_sep = coin.SoSeparator()
        shaded_sep.addChild(transform)

        # Material for shaded mode
        material = coin.SoMaterial()
        material.diffuseColor.setValue(0.2,0.2,0.2)
        #material.specularColor.setValue(0.2, 0.2, 0.2)
        #material.shininess = 0.3
        shaded_sep.addChild(material)

        # Shaded style
        shaded_style = coin.SoDrawStyle()
        shaded_style.style = coin.SoDrawStyle.FILLED
        shaded_sep.addChild(shaded_style)
        shaded_sep.addChild(coords)

        if faces:
            face_set = coin.SoIndexedFaceSet()
            indices = []
            for face in faces:
                indices.extend(face)
              # indices.append(-1)  # Face separator
            face_set.coordIndex.setValues(0, len(indices), indices)
            shaded_sep.addChild(face_set)

        self.shaded_node.addChild(shaded_sep)
    def onChanged(self, vobj, prop):
        pass

    def getDisplayModes(self, obj):
        return ["Line", "Shaded"]

    def getDefaultDisplayMode(self):
        return "Shaded"

    def setDisplayMode(self, mode):
        return mode

    def getIcon(self):
        return BEAM_ICON_PATH

    def dumps(self):
        return None

    def loads(self, state):
        return None


class BeamGroup:
    def __init__(self, obj):
        obj.Proxy = self
        obj.addProperty("App::PropertyString", "Type", "Base", "Group Type").Type = "BeamsGroup"
        obj.addProperty("App::PropertyBool", "ShowSections", "Display", "Show 3D sections").ShowSections = True

    def onChanged(self, obj, prop):
        if 'Restore' in obj.State:
            return  # or do some special thing
        if prop == "ShowSections":
            for beam in obj.Group:
                if hasattr(beam, "Type"):
                    beam.Proxy.execute(beam)

    def getIcon(self):
        return BEAM_ICON_PATH

class BeamGroupViewProvider:
    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        return BEAM_GROUP_ICON_PATH

#    def attach(self, vobj):
#        self.Object = vobj.Object
#    def attach(self, vobj):
#        self.standard = coin.SoGroup()

    def updateData(self, obj, prop):
        pass

    def onChanged(self, vobj, prop):
        pass

    def getDisplayModes(self, obj):
        return ["Default"]

    def getDefaultDisplayMode(self):
        return "Default"


def make_beams_group():
    """Create or get the Beams group with custom icon"""
    doc = App.ActiveDocument
    if not doc:
        return None

    if not hasattr(doc, "Beams"):
        group = doc.addObject("App::DocumentObjectGroupPython", "Beams")
        BeamGroup(group)
        group.Label = "Beams"

        # Create icon in workbench directory
        #create_beam_icon()

        # Set view provider
        group.ViewObject.Proxy = BeamGroupViewProvider(group.ViewObject)
    return doc.Beams


def create_beam_icon():
    """Create beam icon if it doesn't exist, using workbench-specific paths"""
    if not os.path.exists(BEAM_GROUP_ICON_PATH):
        group_icon = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg width="64" height="64" viewBox="0 0 64 64">
  <line x1="10" y1="32" x2="54" y2="32" stroke="#1E90FF" stroke-width="8"/>
  <rect x="10" y="24" width="8" height="16" fill="#4682b4"/>
  <rect x="46" y="24" width="8" height="16" fill="#4682b4"/>
</svg>"""
        with open(BEAM_GROUP_ICON_PATH, 'w') as f:
            f.write(group_icon)


def create_beam(self, start_node, end_node, section):
    print('create_beam init')
    if not start_node or not end_node:
        print("Error", "Please select both start and end nodes")
        return
    print(start_node, end_node)
    if start_node == end_node:
        print("Error", "Identical nodes selected for start and end")
        return
    group = make_beams_group()
    beam = App.ActiveDocument.addObject("App::FeaturePython", "Beam")
    BeamFeature(beam)

    # Attach the view provider
    BeamViewProvider(beam.ViewObject)

    # Set properties
    beam.StartNode = start_node
    beam.EndNode = end_node
    beam.Section = section


    beam.Label = "Beam"
    group.addObject(beam)
    self.close()