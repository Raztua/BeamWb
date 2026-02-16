from types import NoneType
import FreeCAD as App
import FreeCADGui as Gui
from FreeCAD import Units
from features.section_definitions import get_section_points
import os
import math
from PySide import QtGui, QtCore

try:
    from prettytable.prettytable import PrettyTable, HRuleStyle, VRuleStyle, TableStyle
except ImportError:
    App.Console.PrintError("PrettyTable not found.\n")
    PrettyTable = None
    TableStyle = None

# Constants
WORKBENCH_DIR = os.path.dirname(os.path.dirname(__file__))
ICON_DIR = os.path.join(WORKBENCH_DIR, "icons")
BEAM_GROUP_ICON_PATH = os.path.join(ICON_DIR, "beam_group.svg")
BEAM_ICON_PATH = os.path.join(ICON_DIR, "beam.svg")
BEAM_GROUP_RESULTS_ICON_PATH = NODE_GROUP_RESULTS_ICON_PATH = os.path.join(ICON_DIR, "beam_node_results.svg")


class BeamFeature:
    def __init__(self, obj):
        self.node = None
        self.Object = obj
        obj.Proxy = self
        self.flagInit = True
        obj.addProperty("App::PropertyString", "Comment", "Base", "Comment",4)
        # Node properties
        obj.addProperty("App::PropertyLink", "StartNode", "Beam", "Start node object").StartNode = None
        obj.addProperty("App::PropertyLink", "EndNode", "Beam", "End node object").EndNode = None
        obj.addProperty("App::PropertyEnumeration", "MemberType", "Beam",
                        "Type of member for design").MemberType = ["normal", "compression", "tension"]
        obj.MemberType = "normal"

        # Buckling lengths
        obj.addProperty("App::PropertyLength", "BucklingLengthY", "Beam",
                        "Buckling length about local Y-axis").BucklingLengthY = 0.0
        obj.addProperty("App::PropertyLength", "BucklingLengthZ", "Beam",
                        "Buckling length about local Z-axis").BucklingLengthZ = 0.0

        # Effective lengths (for lateral torsional buckling)
        obj.addProperty("App::PropertyLength", "EffectiveLengthY", "Eurocode 3",
                        "Effective length for lateral torsional buckling Y").EffectiveLengthY = 0.0
        obj.addProperty("App::PropertyLength", "EffectiveLengthZ", "Eurocode 3",
                        "Effective length for lateral torsional buckling Z").EffectiveLengthZ = 0.0

        obj.addProperty("App::PropertyVector", "StartNodeDisp", "Results",
                        "start node displacement", 4).StartNodeDisp = App.Vector(0, 0, 1000)
        obj.addProperty("App::PropertyVector", "EndNodeDisp", "Results",
                        "start node displacement", 4).EndNodeDisp = App.Vector(0, 0, -500)
        # Material property
        obj.addProperty("App::PropertyLink", "Material", "Beam", "Material properties").Material = None

        # Local coordinate system properties without offset
        obj.addProperty("App::PropertyFloat", "section_rotation", "Beam",
                        "section rotation(in deg)").section_rotation = 0.0
        obj.addProperty("App::PropertyVector", "Local_X", "Beam", "Local X-axis (beam direction)",
                        4).Local_X = App.Vector(0, 0, 1)
        obj.addProperty("App::PropertyVector", "Local_Y", "Beam", "Local Y-axis", 4).Local_Y = App.Vector(1, 0, 0)
        obj.addProperty("App::PropertyVector", "Local_Z", "Beam", "Local Z-axis", 4).Local_Z = App.Vector(0, 1, 0)
        # Member end releases
        obj.addProperty("App::PropertyLink", "MemberRelease", "Beam",
                        "Member end release definition").MemberRelease = None

        # Offset properties
        obj.addProperty("App::PropertyBool", "OffsetAxis", "Offset", "Local axis system for offset").OffsetAxis = True
        obj.addProperty("App::PropertyVector", "StartOffset", "Offset",
                        "Offset at start node").StartOffset = App.Vector(0, 0, 0)
        obj.addProperty("App::PropertyVector", "EndOffset", "Offset",
                        "Offset at end node").EndOffset = App.Vector(0, 0, 0)

        # Section properties
        obj.addProperty("App::PropertyLink", "Section", "Section", "Cross-section from library")
        obj.addProperty("App::PropertyFloat", "angle", "Section", "section rotation (deg)", 1).angle = 0.0

        # text properties
        # Add text annotation properties
        obj.addProperty("App::PropertyStringList", "Texts", "Annotations", "List of text annotations", 4)
        obj.addProperty("App::PropertyFloatList", "TextPositions", "Annotations",
                        "List of text positions (0-1 along beam)", 4)
        obj.addProperty("App::PropertyVectorList", "TextOffsets", "Annotations", "List of text offset vectors", 4)
        obj.addProperty("App::PropertyFloat", "TextSize", "Annotations", "Text size", 1).TextSize = 10.0

        # Read-only properties
        obj.addProperty("App::PropertyLength", "Length", "Base", "Length of beam", 1).Length = 0.0
        obj.addProperty("App::PropertyVector", "StartPos", "Base", "Start position (hidden)",
                        4).StartPos = App.Vector(0, 0, 0)
        obj.addProperty("App::PropertyVector", "EndPos", "Base", "End position (hidden)", 4).EndPos = App.Vector(0, 0)
        obj.addProperty("App::PropertyVector", "StartPosWithOffset", "Base",
                        "Start position with offset (hidden)", 4).StartPosWithOffset = App.Vector(0, 0, 0)
        obj.addProperty("App::PropertyVector", "EndPosWithOffset", "Base",
                        "End position with offset (hidden)", 4).EndPosWithOffset = App.Vector(0, 0, 0)

        obj.addProperty("App::PropertyString", "Type", "Base", "Group Type", 4).Type = "BeamFeature"
        obj.addProperty("App::PropertyRotation", "beamRotation", "Hidden",
                        "Beam rotation matrix", 4).beamRotation = App.Rotation()

        # Diagram properties
        obj.addProperty("App::PropertyFloatList", "DiagramPositions", "Diagram",
                        "List of positions (0-1) along beam for diagram points", 4)
        obj.addProperty("App::PropertyString", "DiagramUnit", "Results", "Unit", 4).DiagramUnit = ""
        obj.addProperty("App::PropertyFloatList", "DiagramValues", "Diagram",
                        "List of values for diagram points")
        obj.addProperty("App::PropertyColor", "PositiveColor", "Diagram",
                        "Color for positive values", 4).PositiveColor = (1.0, 0.0, 0.0)  # Red
        obj.addProperty("App::PropertyColor", "NegativeColor", "Diagram",
                        "Color for negative values", 4).NegativeColor = (0.0, 0.0, 1.0)  # Blue
        obj.addProperty("App::PropertyFloat", "DiagramTransparency", "Diagram",
                        "Transparency for diagram fill (0-1)", 4).DiagramTransparency = 0.7
        obj.addProperty("App::PropertyFloat", "DiagramWidth", "Diagram",
                        "Width of diagram as fraction of beam width", 4).DiagramWidth = 0.5
        obj.addProperty("App::PropertyFloat", "DiagramMax", "Diagram",
                        "max value over all beam for of diagram scale ").DiagramMax = 1
        self.flagInit = False
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

    def get_releases(self, obj):
        """Get start and end releases from linked MemberRelease object"""
        if obj.MemberRelease and hasattr(obj.MemberRelease, 'Proxy'):
            return (
                obj.MemberRelease.Proxy.get_start_release(),
                obj.MemberRelease.Proxy.get_end_release()
            )
        else:
            # Default: no releases
            return ([False] * 6, [False] * 6)

    def get_show_sections(self, obj):
        """Get ShowSections property from parent group"""
        if obj.InList and hasattr(obj.InList[0], "ShowSections"):
            return obj.InList[0].ShowSections
        return True

    def calculate_local_axes(self, obj, beam_dir):
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
            local_x, local_y, local_z = self.calculate_local_axes(obj, beam_dir)
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
                local_x_offset, local_y_offset, local_z_offset = self.calculate_local_axes(obj, beam_dir_offset)
                obj.Local_X = local_x_offset
                obj.Local_Y = local_y_offset
                obj.Local_Z = local_z_offset
                obj.beamRotation = App.Rotation(rot)
            except Exception as e:
                App.Console.PrintWarning(f"Error recalculating local axes with offset: {str(e)}\n")
                obj.beamRotation = App.Rotation()

    def add_text(self, obj, text, position, offset=None):
        """Add a text annotation to the beam"""
        if position < 0 or position > 1:
            raise ValueError("Position must be between 0 and 1")

        if offset is None:
            offset = App.Vector(0, 0, 0)

        # Initialize properties if they don't exist
        if not hasattr(obj, "Texts"):
            obj.addProperty("App::PropertyStringList", "Texts", "Annotations", "List of text annotations")
            obj.addProperty("App::PropertyFloatList", "TextPositions", "Annotations",
                            "List of text positions (0-1 along beam)")
            obj.addProperty("App::PropertyVectorList", "TextOffsets", "Annotations", "List of text offset vectors")

        obj.Texts += [text]
        obj.TextPositions += [position]
        obj.TextOffsets += [offset]

        self.update_visualization(obj)

    def set_diagram(self, positions, values, max_value=None, unit_str=""):
        """Set the diagram with unit-aware floats"""
        obj = self.Object
        # PropertyFloatList requires basic floats
        obj.DiagramPositions = [float(p) for p in positions]
        obj.DiagramValues = [float(v) for v in values]
        obj.DiagramUnit = unit_str
        if max_value is not None:
            obj.DiagramMax = float(max_value)

        self.update_visualization(obj)

    def clear_diagram(self, obj):
        """Clear the diagram"""
        obj.DiagramPositions = []
        obj.DiagramValues = []
        self.update_visualization(obj)

    def remove_text(self, obj, index):
        """Remove a text annotation by index"""
        if index < 0 or index >= len(obj.Texts):
            raise IndexError("Invalid text index")

        obj.Texts = obj.Texts[:index] + obj.Texts[index + 1:]
        obj.TextPositions = obj.TextPositions[:index] + obj.TextPositions[index + 1:]
        obj.TextOffsets = obj.TextOffsets[:index] + obj.TextOffsets[index + 1:]

        self.update_visualization(obj)

    def clear_texts(self, obj):
        """Remove all text annotations"""
        obj.Texts = []
        obj.TextPositions = []
        obj.TextOffsets = []

        self.update_visualization(obj)

    def execute(self, obj):
        if 'Restore' in obj.State:
            return  # or do some special thing
        if obj.StartNode is None or obj.EndNode is None:
            return
        if hasattr(obj, "Type") and obj.Type == "BeamFeature":
            self.calculate_positions(obj)
            self.update_visualization(obj)

    def onChanged(self, obj, prop):
        if not hasattr(self, "flagInit"):
            return
        if self.flagInit:
            return
        if 'Restore' in obj.State:
            return
        if prop in ["StartNode", "EndNode", "StartOffset", "EndOffset", "OffsetAxis",
                    "SectionType", "Width", "Height", "Thickness", "SectionRotation",
                    "section_rotation", "Texts", "TextPositions", "TextOffsets", "TextSize",
                    "DiagramPositions", "DiagramValues", "PositiveColor", "NegativeColor",
                    "DiagramTransparency", "DiagramWidth", "MemberRelease"]:
            self.execute(obj)

    def update_visualization(self, obj):
        """Trigger view provider update instead of direct manipulation"""
        if hasattr(obj, 'ViewObject') and obj.ViewObject is not None:
            if hasattr(obj.ViewObject.Proxy, 'updateVisualization'):
                obj.ViewObject.Proxy.updateVisualization(obj)

    def dumps(self):
        return None

    def loads(self, state):
        return None


class ResultBeam(BeamFeature):
    def __init__(self, obj, base_beam=None):
        self.flagInit = True
        super(ResultBeam, self).__init__(obj)
        obj.Type = "ResultBeam"
        self.Object = obj

        # Add result-specific properties
        obj.addProperty("App::PropertyLink", "BaseBeam", "Base", "Original beam ")
        obj.addProperty("App::PropertyFloat", "MaxDiagramValue", "Results",
                        "Maximum absolute value for current diagram", 4)
        obj.addProperty("App::PropertyString", "ResultType", "Results",
                        "Type of result being displayed", 4)
        obj.addProperty("App::PropertyPercent", "Transparency", "Display",
                        "Transparency level").Transparency = 50

        # Initialize with base beam properties if provided
        if base_beam:
            self.initialize_from_base_beam(obj, base_beam)
        self.flagInit = False

    def initialize_from_base_beam(self, obj, base_beam):
        """Copy relevant properties from base beam"""
        obj.StartNode = base_beam.StartNode
        obj.EndNode = base_beam.EndNode
        obj.Section = base_beam.Section
        obj.StartOffset = base_beam.StartOffset
        obj.EndOffset = base_beam.EndOffset
        obj.OffsetAxis = base_beam.OffsetAxis
        obj.section_rotation = base_beam.section_rotation
        obj.BaseBeam = base_beam

        # Initialize result-specific properties
        obj.ResultType = "None"

    def validate_nodes(self, obj):
        """Validate that nodes exist and are proper node objects"""
        valid = True
        if not obj.StartNode or not (hasattr(obj.StartNode, "Proxy") or hasattr(obj.StartNode, "BaseNodeName")):
            App.Console.PrintWarning("Beam: Invalid start node\n")
            valid = False
        if not obj.EndNode or not (hasattr(obj.EndNode, "Proxy") or hasattr(obj.EndNode, "BaseNodeName")):
            App.Console.PrintWarning("Beam: Invalid end node\n")
            valid = False
        return valid

    def calculate_local_axes(self, obj, beam_dir):
        """Calculate the local coordinate system with consistent orientation"""
        if beam_dir.Length < 1e-6:
            # Handle zero-length beam case
            return App.Vector(1, 0, 0), App.Vector(0, 1, 0), App.Vector(0, 0, 1)

        # For ResultBeam, always use the base beam's local axes
        if obj.Type == "ResultBeam" and hasattr(obj, "BaseBeam") and obj.BaseBeam:
            local_x = beam_dir.normalize()
            local_y = obj.BaseBeam.Local_Y
            local_z = obj.BaseBeam.Local_Z

            # Apply section rotation if different from base
            if obj.section_rotation != obj.BaseBeam.section_rotation:
                rotation_angle = math.radians(obj.section_rotation - obj.BaseBeam.section_rotation)
                rot = App.Rotation(local_x, rotation_angle)
                local_y = rot.multVec(local_y)
                local_z = rot.multVec(local_z)

            return local_x, local_y, local_z
        else:
            # Use the original method for regular beams
            return self._calculate_default_local_axes(obj, beam_dir)

    def _calculate_default_local_axes(self, obj, beam_dir):
        """Original method for calculating local axes"""
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

    def set_displacements(self, start_disp, end_disp):
        """Set the displacements at beam ends"""
        obj = self.Object
        if hasattr(obj, "BaseBeam"):
            obj.StartNode = obj.BaseBeam.StartNode
            obj.EndNode = obj.BaseBeam.EndNode
        obj.StartNodeDisp = start_disp
        obj.EndNodeDisp = end_disp
        self.update_visualization(obj)

    def execute(self, obj):
        if 'Restore' in obj.State:
            return  # or do some special thing
        if obj.StartNode is None or obj.EndNode is None:
            return

        if hasattr(obj, "Type") and obj.Type == "ResultBeam":
            self.calculate_positions(obj)
            self.update_visualization(obj)


def create_result_beam(base_beam):
    """Create a result beam from a base beam"""
    doc = App.ActiveDocument
    if not doc or not base_beam:
        return None

    try:
        obj = doc.addObject("App::FeaturePython", "ResultBeam")
        ResultBeam(obj, base_beam)
        obj.Label = base_beam.Label
        obj.StartNode = base_beam.StartNode
        obj.EndNode = base_beam.EndNode

        if App.GuiUp:
            BeamViewProvider(obj.ViewObject)
            # Style for result beams
            obj.ViewObject.ShapeColor = (0.2, 0.8, 0.2)  # Greenish
            obj.ViewObject.Transparency = 30

        return obj

    except Exception as e:
        App.Console.PrintError(f"Error creating result beam: {str(e)}\n")
        return None


class BeamViewProvider():
    def __init__(self, vobj):
        vobj.Proxy = self
        self.Object = vobj.Object
        if not (hasattr(vobj, "ShapeColor")):
            vobj.addProperty("App::PropertyColor", "ShapeColor", "Appearance", "Shape color")
            vobj.addProperty("App::PropertyColor", "LineColor", "Appearance", "Line color")
            vobj.addProperty("App::PropertyPercent", "Transparency", "Appearance", "Transparency level")
        # Set defaults
        vobj.ShapeColor = (0.8, 0.2, 0.2)
        vobj.LineColor = (0.0, 0.0, 0.0)
        vobj.Transparency = 0
        # Make properties editable
        vobj.setEditorMode("ShapeColor", 0)
        vobj.setEditorMode("LineColor", 0)
        vobj.setEditorMode("Transparency", 0)

        # Store release visualization nodes
        self.start_release_visual = None
        self.end_release_visual = None

    def attach(self, vobj):
        if not (hasattr(vobj, "ShapeColor")):
            vobj.addProperty("App::PropertyColor", "ShapeColor", "Appearance", "Shape color")
        if not (hasattr(vobj, "LineColor")):
            vobj.addProperty("App::PropertyColor", "LineColor", "Appearance", "Line color")
        if not (hasattr(vobj, "Transparency")):
            vobj.addProperty("App::PropertyPercent", "Transparency", "Appearance", "Transparency level")
        if not (hasattr(self, "ViewObject")):
            self.ViewObject = vobj
        if not (hasattr(self, "Object")):
            self.Object = vobj.Object

        from pivy import coin
        # Create display mode nodes
        self.shaded_node = coin.SoGroup()
        self.shaded_node.setName("Shaded")

        self.line_node = coin.SoGroup()
        self.line_node.setName("Line")

        # Add display modes to view object
        vobj.addDisplayMode(self.shaded_node, "Shaded")
        vobj.addDisplayMode(self.line_node, "Line")

        # Store reference to view object
        self.updateVisualization(self.Object)

    def updateData(self, obj, prop):
        if prop in ["StartNode", "EndNode", "StartOffset", "EndOffset", "OffsetAxis",
                    "Section", "Local_X", "Local_Y", "Local_Z", "StartNodeDisp",
                    "EndNodeDisp", "Texts", "TextPositions", "TextOffsets", "TextSize", "beamRotation"]:
            self.updateVisualization(obj)

    def updateVisualization(self, obj):
        if not hasattr(self, "Object"):
            return
        if not obj.StartNode or not obj.EndNode:
            return

        # Clear existing nodes
        if hasattr(self, "shaded_node"):
            self.shaded_node.removeAllChildren()
        if hasattr(self, "line_node"):
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
            self.createLineMode(start_pos, end_pos)

        # Add member release visualizations if defined
        if obj.MemberRelease and hasattr(obj.MemberRelease, 'ViewObject'):
            self.add_member_release_visualization(obj)

        # Add text annotations if they exist
        if hasattr(obj, "Texts") and obj.Texts:
            self.createTextAnnotations(obj)

        if hasattr(obj, "DiagramPositions") and len(obj.DiagramPositions) > 0:
            diagram = self.createDiagram(obj)
            if diagram:
                self.shaded_node.addChild(diagram)
                self.line_node.addChild(diagram)

    def add_member_release_visualization(self, obj):
        """Add member release visualization at beam extremities"""
        if not obj.MemberRelease or not hasattr(obj.MemberRelease, 'ViewObject') or obj.MemberRelease == None:
            return
        from pivy import coin

        member_release = obj.MemberRelease
        release_vp = member_release.ViewObject.Proxy

        # Get beam data for positioning
        start_pos = obj.StartPosWithOffset
        end_pos = obj.EndPosWithOffset
        beam_dir = obj.Local_X  # Beam direction
        beam_length = obj.Length

        # Offset distance from node (5% of beam length or fixed small distance)
        offset_distance = min(beam_length * 0.05, 10.0)

        # Position start release - offset from start node along beam direction
        start_release_pos = start_pos + beam_dir * offset_distance

        # Position end release - offset from end node opposite to beam direction
        end_release_pos = end_pos - beam_dir * offset_distance

        # Get release nodes from member release - coin item
        try:
            start_release_node = release_vp.get_start_release_node()
            end_release_node = release_vp.get_end_release_node()
        except AttributeError:
            # Fallback if the VP exists but doesn't have these methods yet
            return

        # Add start release visualization
        if start_release_node:
            start_transform = self._create_release_transform(start_release_pos, obj.Local_X, obj.Local_Y, obj.Local_Z)
            start_visual_sep = coin.SoSeparator()
            start_visual_sep.addChild(start_transform)
            start_visual_sep.addChild(start_release_node)
            self.shaded_node.addChild(start_visual_sep)
            self.line_node.addChild(start_visual_sep)

        # Add end release visualization
        if end_release_node:
            end_transform = self._create_release_transform(end_release_pos, -obj.Local_X, obj.Local_Y, obj.Local_Z)
            end_visual_sep = coin.SoSeparator()
            end_visual_sep.addChild(end_transform)
            end_visual_sep.addChild(end_release_node)
            self.shaded_node.addChild(end_visual_sep)
            self.line_node.addChild(end_visual_sep)

    def _create_release_transform(self, position, local_x, local_y, local_z):
        """Create transform for positioning release visualization"""
        from pivy import coin

        transform = coin.SoTransform()

        # Create rotation matrix from local axes
        rotation = coin.SbMatrix(
            local_x.x, local_x.y, local_x.z, 0,
            local_y.x, local_y.y, local_y.z, 0,
            local_z.x, local_y.z, local_z.z, 0,
            position.x, position.y, position.z, 1
        )
        transform.setMatrix(rotation)

        return transform

    def createLineMode(self, start_pos, end_pos):
        """Create simple line representation"""
        from pivy import coin

        coords = coin.SoCoordinate3()
        coords.setName("Beam coordinate")
        coords.point.setValues(0, 2, [start_pos, end_pos])
        line = coin.SoLineSet()
        line.setName("Beam lineset")
        line.numVertices.setValue(2)

        # Add line style for better visibility
        line_style = coin.SoDrawStyle()
        line_style.setName("Beam linestyle")
        line_style.lineWidth = 2

        # Material for shaded mode
        material = coin.SoMaterial()
        material.diffuseColor = self.Object.ViewObject.LineColor[0:3]
        self.line_node.addChild(material)
        self.line_node.addChild(line_style)
        self.line_node.addChild(coords)
        self.line_node.addChild(line)

    def createTextAnnotations(self, obj):
        """Create 3D text annotations along the beam"""
        from pivy import coin
        if not obj.StartNode or not obj.EndNode:
            return

        start_pos = obj.StartPosWithOffset
        end_pos = obj.EndPosWithOffset
        beam_dir = end_pos - start_pos
        beam_length = beam_dir.Length

        # Create a separator for all text annotations
        text_sep = coin.SoSeparator()
        text_sep.setName("BeamTextAnnotations")

        # Add result text if available
        if hasattr(obj, "ResultText") and obj.ResultText:
            self._add_result_text(obj, text_sep, start_pos, end_pos, beam_dir)

        # Add user texts if they exist
        if hasattr(obj, "Texts") and obj.Texts:
            text_size = getattr(obj, "TextSize", 10.0)
            rotation = obj.beamRotation

            for i, (text, position, offset) in enumerate(zip(obj.Texts, obj.TextPositions, obj.TextOffsets)):
                pos_along_beam = start_pos + beam_dir * position
                offset_global = rotation.multVec(offset)
                text_pos = pos_along_beam + offset_global

                transform = coin.SoTransform()
                transform.translation.setValue(text_pos.x, text_pos.y, text_pos.z)

                # Create proper rotation for text
                beam_rot = rotation
                text_rot = App.Rotation(App.Vector(1, 0, 0), 90)
                final_rot = beam_rot * text_rot
                q = final_rot.Q
                transform.rotation.setValue(q[0], q[1], q[2], q[3])

                text_node = coin.SoAsciiText()
                text_node.string.setValue(text)
                text_node.justification = coin.SoAsciiText.CENTER

                font = coin.SoFont()
                font.size = text_size

                text_item = coin.SoSeparator()
                text_item.addChild(transform)
                text_item.addChild(font)
                text_item.addChild(text_node)

                text_sep.addChild(text_item)

        # Add text annotations to display modes
        self.shaded_node.addChild(text_sep)
        self.line_node.addChild(text_sep)

    def _add_result_text(self, obj, parent_sep, start_pos, end_pos, beam_dir):
        """Add the result value text annotation"""
        from pivy import coin

        # Position text at midpoint of beam
        text_pos = start_pos + beam_dir * 0.5
        text_pos += App.Vector(0, 0, obj.DiagramWidth * 1.2)  # Offset above beam

        transform = coin.SoTransform()
        transform.translation.setValue(text_pos.x, text_pos.y, text_pos.z)

        # Make text face camera
        transform.rotation.setValue(coin.SbRotation(coin.SbVec3f(0, 1, 0), coin.SbVec3f(0, 0, 1)))

        text_node = coin.SoText2()
        text_node.string.setValue(obj.ResultText)
        text_node.justification = coin.SoText2.CENTER

        font = coin.SoFont()
        font.size = 12.0
        font.bold = True

        material = coin.SoMaterial()
        material.diffuseColor = (1.0, 1.0, 0.0)  # Yellow for results

        text_item = coin.SoSeparator()
        text_item.addChild(transform)
        text_item.addChild(material)
        text_item.addChild(font)
        text_item.addChild(text_node)

        parent_sep.addChild(text_item)

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
        params = {}
        if hasattr(section, "ManagedProperties"):
            for prop_name in section.ManagedProperties:
                if not hasattr(section, prop_name): continue

                val = getattr(section, prop_name)
                # Convert Quantity to float (mm) if possible
                if hasattr(val, "getValueAs"):
                    try:
                        params[prop_name] = val.getValueAs("mm").Value
                    except (ValueError, TypeError):
                        # Fallback for non-length quantities (Area, Inertia, etc.)
                        # Use raw value (internal units)
                        params[prop_name] = val.Value
                else:
                    try:
                        params[prop_name] = float(val)
                    except (ValueError, TypeError):
                        pass

        # Get points and faces for this section type
        points, faces, _ = get_section_points(section.ProfileType, beam_length.getValueAs("mm").Value, params)
        # Create coordinates
        coords = coin.SoCoordinate3()
        coords.setName("beam 3d Coordinate")
        coords.point.setValues(0, len(points), points)

        # Create shaded mode
        shaded_sep = coin.SoSeparator()
        shaded_sep.setName("separator for shaded mode")
        shaded_sep.addChild(transform)

        # Material for shaded mode
        material = coin.SoMaterial()
        # material.diffuseColor.setValue(0.2,0.2,0.2)
        material.transparency = obj.ViewObject.Transparency
        material.diffuseColor = obj.ViewObject.ShapeColor[0:3]
        # material.specularColor.setValue(0.2, 0.2, 0.2)
        # material.shininess = 0.3
        shaded_sep.addChild(material)

        # Shaded style
        shaded_style = coin.SoDrawStyle()
        shaded_style.style = coin.SoDrawStyle.FILLED
        shaded_sep.addChild(shaded_style)
        shaded_sep.addChild(coords)

        if faces:
            face_set = coin.SoIndexedFaceSet()
            face_set.setName("Beam Indexed faces")
            indices = []
            for face in faces:
                indices.extend(face)
            # indices.append(-1)  # Face separator
            face_set.coordIndex.setValues(0, len(indices), indices)
            shaded_sep.addChild(face_set)

        self.shaded_node.addChild(shaded_sep)

    def createDiagram(self, obj):
        """Create the diagram visualization with max value annotation offsetted from ends"""
        from pivy import coin

        if not obj.DiagramPositions or not obj.DiagramValues:
            return None

        if len(obj.DiagramPositions) != len(obj.DiagramValues):
            return None

        if len(obj.DiagramPositions) < 2:
            return None

        # Get beam data
        start_pos = obj.StartPosWithOffset
        end_pos = obj.EndPosWithOffset
        beam_dir = end_pos - start_pos

        local_z = obj.Local_Z
        diagram_width = obj.DiagramWidth * 0.5

        # Create main separator
        diagram_sep = coin.SoSeparator()

        # --- 1. CALCULATE MAX VALUE & TEXT POSITION ---
        max_val = max(obj.DiagramValues, key=abs)
        max_index = obj.DiagramValues.index(max_val)
        max_pos = obj.DiagramPositions[max_index]

        # [NEW LOGIC] Clamp text position to avoid start/end overlap
        # If the max value is at 0.0 or 1.0, we shift the text inward by 5%
        text_margin = 0.05  # 5% margin
        text_t = max_pos

        if text_t < text_margin:
            text_t = text_margin
        elif text_t > (1.0 - text_margin):
            text_t = 1.0 - text_margin

        # Calculate the point specifically for the Text Label
        # We use text_t for position along beam, but keep the height of the actual max value
        text_base_point = start_pos + beam_dir * text_t

        max_offset = (local_z * (1 if max_val >= 0.0 else -1) * (abs(max_val))
                      * diagram_width * 1000)

        # This is the final 3D point for the text
        max_value_point = text_base_point + max_offset

        # --- 2. GENERATE DIAGRAM GEOMETRY (Standard, no gaps) ---
        all_points = []
        pos_polygons = []
        neg_polygons = []
        line_points = []

        # Start point
        all_points.append(start_pos)
        line_points.append(start_pos)

        sorted_points = sorted(zip(obj.DiagramPositions, obj.DiagramValues), key=lambda x: x[0])

        for i, (pos, val) in enumerate(sorted_points):
            base_point = start_pos + beam_dir * pos
            all_points.append(base_point)

            sign = 1 if val >= 0 else -1
            offset = local_z * sign * (abs(val)) * diagram_width * 1000
            value_point = base_point + offset
            all_points.append(value_point)
            line_points.append(value_point)

            if i == 0:
                prev_base = base_point
                prev_value = value_point
                prev_val = val
                continue

            # Create polygon
            if val >= 0 and prev_val >= 0:
                pos_polygons.append([prev_base, prev_value, value_point, base_point])
            elif val < 0 and prev_val < 0:
                neg_polygons.append([prev_base, prev_value, value_point, base_point])
            else:
                t = abs(prev_val) / (abs(prev_val) + abs(val))
                zero_pos = sorted_points[i - 1][0] + t * (pos - sorted_points[i - 1][0])
                zero_point = start_pos + beam_dir * zero_pos
                all_points.append(zero_point)

                if prev_val >= 0:
                    pos_polygons.append([prev_base, prev_value, zero_point])
                    neg_polygons.append([zero_point, value_point, base_point])
                else:
                    neg_polygons.append([prev_base, prev_value, zero_point])
                    pos_polygons.append([zero_point, value_point, base_point])

            prev_base = base_point
            prev_value = value_point
            prev_val = val

        # End point
        all_points.append(end_pos)
        line_points.append(end_pos)
        if prev_val >= 0:
            pos_polygons.append([prev_base, prev_value, end_pos])
        else:
            neg_polygons.append([prev_base, prev_value, end_pos])

        # --- 3. BUILD NODES ---

        # Coordinates
        coords = coin.SoCoordinate3()
        coords.point.setValues(0, len(all_points), all_points)

        # Materials
        pos_material = coin.SoMaterial()
        pos_material.diffuseColor = obj.PositiveColor[:3]
        pos_material.transparency = obj.DiagramTransparency

        neg_material = coin.SoMaterial()
        neg_material.diffuseColor = obj.NegativeColor[:3]
        neg_material.transparency = obj.DiagramTransparency

        # Face sets
        pos_face_set = coin.SoIndexedFaceSet()
        neg_face_set = coin.SoIndexedFaceSet()

        pos_indices = []
        for poly in pos_polygons:
            for pt in poly:
                pos_indices.append(all_points.index(pt))
            pos_indices.append(-1)

        neg_indices = []
        for poly in neg_polygons:
            for pt in poly:
                neg_indices.append(all_points.index(pt))
            neg_indices.append(-1)

        pos_face_set.coordIndex.setValues(0, len(pos_indices), pos_indices)
        neg_face_set.coordIndex.setValues(0, len(neg_indices), neg_indices)

        # Line set
        line_coords = coin.SoCoordinate3()
        line_coords.point.setValues(0, len(line_points), line_points)

        line_set = coin.SoLineSet()
        line_set.numVertices.setValue(len(line_points))

        line_style = coin.SoDrawStyle()
        line_style.lineWidth = 2.0

        # --- 4. TEXT ANNOTATION (Using offsetted position) ---
        max_sep = coin.SoSeparator()

        max_transform = coin.SoTransform()
        # Use the shifted max_value_point calculated at the top
        max_transform.translation.setValue(max_value_point.x, max_value_point.y, max_value_point.z)

        max_text = coin.SoText2()
        max_text.string.setValue(f"{max_val * obj.DiagramMax:.2g}" + obj.DiagramUnit)
        max_text.justification = coin.SoText2.CENTER

        text_font = coin.SoFont()
        text_font.size = 12.0

        max_sep.addChild(max_transform)
        max_sep.addChild(text_font)
        max_sep.addChild(max_text)

        # Build scene graph
        pos_sep = coin.SoSeparator()
        pos_sep.addChild(pos_material)
        pos_sep.addChild(pos_face_set)

        neg_sep = coin.SoSeparator()
        neg_sep.addChild(neg_material)
        neg_sep.addChild(neg_face_set)

        line_sep = coin.SoSeparator()
        line_sep.addChild(line_style)
        line_sep.addChild(line_coords)
        line_sep.addChild(line_set)

        diagram_sep.addChild(coords)
        diagram_sep.addChild(pos_sep)
        diagram_sep.addChild(neg_sep)
        diagram_sep.addChild(line_sep)
        diagram_sep.addChild(max_sep)

        return diagram_sep

    def onChanged(self, vobj, prop):
        if not hasattr(self, "shaded_node") or not hasattr(self, "line_node"):
            return
        if prop in ["ShapeColor", "LineColor", "Transparency"] and hasattr(self, "Object"):
            self.updateVisualization(self.Object)

    def doubleClicked(self, vobj):
        """Handle double-click event - open creator in modification mode"""
        # Import and show the boundary condition creator in modification mode
        from ui.dialog_BeamModifier import show_beam_modifier
        show_beam_modifier(beams=[vobj.Object])
        return True

    def setupContextMenu(self, vobj, menu):
        """Add custom context menu item"""
        from PySide import QtGui, QtCore
        action = QtGui.QAction("Modify Boundary Condition", menu)
        action.triggered.connect(lambda: self.onModifyBoundaryCondition(vobj.Object))
        menu.addAction(action)

    def onModifyBoundaryCondition(self, bc_obj):
        """Handle context menu action"""
        from ui.dialog_BoundaryConditionCreator import show_boundary_condition_creator
        show_boundary_condition_creator(boundary_condition=bc_obj)

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
                if hasattr(beam, "Type") and hasattr(beam, "Proxy"):
                    beam.Proxy.execute(beam)

    def getIcon(self):
        return BEAM_ICON_PATH


class BeamGroupViewProvider:
    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        return BEAM_GROUP_ICON_PATH

    # --- ATTACH & DATA METHODS (omitted for brevity) ---

    def updateData(self, obj, prop):
        pass

    def onChanged(self, vobj, prop):
        pass

    def getDisplayModes(self, obj):
        return ["Default"]

    def getDefaultDisplayMode(self):
        return "Default"

    # --- CONTEXT MENU IMPLEMENTATION ---
    def setupContextMenu(self, vobj, menu):
        """Adds a context menu item to list all Beams."""
        from PySide import QtGui

        if PrettyTable is None:
            # The check for PrettyTable is done here and in onListBeams
            return

        action = QtGui.QAction("List Beams in Report View", menu)
        action.triggered.connect(lambda: self.onListBeams(vobj.Object))
        menu.addAction(action)

    def onListBeams(self, beam_group):
        """Collects Beam data and prints it to the FreeCAD report view."""

        if PrettyTable is None:
            App.Console.PrintError("Cannot list Beams: PrettyTable module is missing.\n")
            return

        # --- 1. SETUP AND COLLECT DATA ---

        table = PrettyTable()
        table.field_names = ["Name", "Start Node", "End Node", "Length (m)", "Section", "Material"]
        table.align["Name"] = "l"
        table.set_style(TableStyle.SINGLE_BORDER)

        # Iterate over all objects in the group
        for obj in beam_group.Group:
            if hasattr(obj, "Type") and obj.Type in ["BeamFeature", "ResultBeam"]:

                # Get linked object names (or 'N/A')
                start_node_name = obj.StartNode.Label if obj.StartNode and hasattr(obj.StartNode, 'Label') else "N/A"
                end_node_name = obj.EndNode.Label if obj.EndNode and hasattr(obj.EndNode, 'Label') else "N/A"
                section_name = obj.Section.Label if obj.Section and hasattr(obj.Section, 'Label') else "N/A"
                material_name = obj.Material.Label if obj.Material and hasattr(obj.Material, 'Label') else "N/A"

                # Get Length in meters and format (Length is App::PropertyFloat)
                try:
                    length_m = Units.Quantity(obj.Length, Units.Unit('mm')).getValueAs('m').Value
                    length_str = f"{length_m:.4f}"
                except Exception:
                    # Fallback if unit conversion fails (e.g., if Length is already unitless float)
                    length_str = f"{obj.Length:.4f}"

                # Add row to the table
                table.add_row([
                    obj.Label,
                    start_node_name,
                    end_node_name,
                    length_str,
                    section_name,
                    material_name
                ])

        # --- 2. CONCATENATE AND PRINT OUTPUT (SINGLE CALL) ---

        header_string = "\n--- Beam List ---\n"
        table_string = table.get_string()
        final_output = header_string + table_string + "\n"

        App.Console.PrintMessage(final_output)
    # --- END CONTEXT MENU IMPLEMENTATION ---


class BeamResultGroupViewProvider(BeamGroupViewProvider):
    def __init__(self, vobj):
        super().__init__(vobj)

    def getIcon(self):
        return BEAM_GROUP_RESULTS_ICON_PATH


def make_beams_group():
    """Create or get the Beams group with custom icon"""
    doc = App.ActiveDocument
    if not doc:
        return None

    if hasattr(doc, "Beams"):
        beam_group = doc.Beams
    else:
        beam_group = doc.addObject("App::DocumentObjectGroupPython", "Beams")
        BeamGroup(beam_group)
        beam_group.Label = "Beams"
        # Add the Nodes group to the AnalysisGroup if it exists
        from features.AnalysisGroup import get_analysis_group
        analysis_group = get_analysis_group()

        if analysis_group and beam_group not in analysis_group.Group:
            analysis_group.addObject(beam_group)

        # Set view provider
        if App.GuiUp:
            beam_group.ViewObject.Proxy = BeamGroupViewProvider(beam_group.ViewObject)

    return beam_group


def make_result_beams_group():
    """Create or get the Nodes group with proper icon paths and add it to AnalysisGroup"""
    doc = App.ActiveDocument
    if not doc:
        App.Console.PrintError("No active document found\n")
        return None

    # Check if Nodes group already exists
    if hasattr(doc, "Beam_Results"):
        beam_group = doc.Beam_Results
    else:
        # Create new beams group
        beam_group = doc.addObject("App::DocumentObjectGroupPython", "BeamsResult")
        BeamGroup(beam_group)
        beam_group.Label = "Beams Result"
        if App.GuiUp:
            beam_group.ViewObject.Proxy = BeamResultGroupViewProvider(beam_group.ViewObject)
        doc.recompute()

    return beam_group


def create_beam(start_node, end_node, section, material=None, member_release=None):
    if not start_node or not end_node:
        print("Error", "Please select both start and end nodes")
        return
    if start_node == end_node:
        print("Error", "Identical nodes selected for start and end")
        return
    group = make_beams_group()
    beam = App.ActiveDocument.addObject("App::FeaturePython", "Beam")
    BeamFeature(beam)
    # Attach the view provider
    if App.GuiUp:
        BeamViewProvider(beam.ViewObject)
    # Set properties
    beam.StartNode = start_node
    beam.EndNode = end_node
    beam.Section = section
    # Note: Buckling and effective lengths are usually derived after beam creation/length calculation
    # We use beam.Length (calculated in execute/onChanged) which defaults to a float.
    # We must ensure to use the most recently calculated value or link it correctly.
    beam.BucklingLengthY = beam.Length
    beam.BucklingLengthZ = beam.Length
    beam.EffectiveLengthY = beam.Length
    beam.EffectiveLengthZ = beam.Length
    # Set member release if provided
    if member_release:
        beam.MemberRelease = member_release
    beam.Label = "Beam"
    group.addObject(beam)
    App.ActiveDocument.recompute()


def get_all_beams():
    """Get all beam objects from the document"""
    doc = App.ActiveDocument
    if not doc:
        return []

    beams = []

    # Check in Beams group
    beams_group = doc.getObject("Beams")
    if beams_group:
        for obj in beams_group.Group:
            if hasattr(obj, "Type") and obj.Type in ["BeamFeature", "ResultBeam"]:
                beams.append(obj)

    return beams