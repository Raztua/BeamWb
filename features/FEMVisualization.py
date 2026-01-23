# features/FEMVisualization.py
from pivy import coin
import FreeCAD as App
import math
import warnings
import FreeCADGui


class FEMVisualization:
    def __init__(self):
        return

    @staticmethod
    def _get_rotation_between(v1, v2):
        """Safe rotation calculation between vectors"""
        try:
            v1 = coin.SbVec3f(v1.x, v1.y, v1.z)
            v2 = coin.SbVec3f(v2.x, v2.y, v2.z)
            return coin.SbRotation(v1, v2)
        except Exception as e:
            warnings.warn(f"Rotation calculation failed: {str(e)}")
            return coin.SbRotation()

    @staticmethod
    def create_force_arrow(force, position=App.Vector(0, 0, 0), scale=1.0, color=(1.0, 0.0, 0.0)):
        """Create a force arrow with position support"""
        root_sep = coin.SoSeparator()
        force_vec=App.Vector(force[0],force[1],force[2])
        try:
            if not hasattr(force_vec, 'Length'):
                return root_sep
            length = force_vec.Length * scale

            if length < 1e-6:
                return root_sep
            # Set reasonable dimensions
            length = max(0.1, length)
            shaft_length = length * 0.8
            head_length = length * 0.2
            shaft_radius = 0.01 * length
            head_radius = 0.1 * length

            # Position transform
            pos_transform = coin.SoTransform()
            pos_transform.translation.setValue(position.x, position.y, position.z)
            root_sep.addChild(pos_transform)

            # Color node
            color_node = coin.SoBaseColor()
            color_node.rgb = color
            root_sep.addChild(color_node)
            # Rotation (only if force has magnitude)
            if force_vec.Length > 0:
                rotation = FEMVisualization._get_rotation_between(
                    App.Vector(0, 1, 0),  # Default arrow points along Z
                    force_vec.normalize()
                )
                rot_transform = coin.SoTransform()
                rot_transform.rotation = rotation
                root_sep.addChild(rot_transform)

            # Arrow geometry
            arrow_sep = coin.SoSeparator()

            # Shaft (cylinder)
            shaft = coin.SoCylinder()
            shaft.setName("arrow shaft")
            shaft.radius = shaft_radius
            shaft.height = shaft_length
            shaft_tf = coin.SoTransform()
            shaft_tf.translation.setValue(0, -shaft_length / 2, 0)
            arrow_sep.addChild(shaft_tf)
            arrow_sep.addChild(shaft)

            # Head (cone)
            head = coin.SoCone()
            head.setName("arrow head")
            head.bottomRadius = head_radius
            head.height = head_length
            head_tf = coin.SoTransform()
            head_tf.translation.setValue(0, shaft_length / 2-head_length / 2,0) #shaft_length / 2 + head_length / 2, 0)
            arrow_sep.addChild(head_tf)
            arrow_sep.addChild(head)
            root_sep.addChild(arrow_sep)
            root_sep.setName("force")

        except Exception as e:
            warnings.warn(f"Force arrow creation failed: {str(e)}")
            return coin.SoSeparator()

        return root_sep

    @staticmethod
    def create_moment_symbol(moment, position=App.Vector(0, 0, 0), scale=0.1, color=(0.0, 0.0, 1.0)):
        """Create a moment symbol using line segments and arrows"""
        root_sep = coin.SoSeparator()
        root_sep.setName("Moment")
        moment_vec = App.Vector(moment[0], moment[1], moment[2])
        try:
            magnitude = moment_vec.Length * scale
            if magnitude < 1e-6:
                return root_sep

            # Position transform
            pos_transform = coin.SoTransform()
            pos_transform.setName("Position")
            pos_transform.translation.setValue(position.x, position.y, position.z)
            root_sep.addChild(pos_transform)

            # Color node
            color_node = coin.SoBaseColor()
            color_node.rgb = color
            root_sep.addChild(color_node)

            # Rotation to align with moment vector
            if moment_vec.Length > 0:
                rotation = FEMVisualization._get_rotation_between(
                    App.Vector(0, 0, 1),
                    moment_vec.normalize()
                )
                rot_transform = coin.SoTransform()
                rot_transform.rotation = rotation
                root_sep.addChild(rot_transform)

            # Create circular path using line segments
            circle_radius = magnitude * 0.5
            num_segments = 24
            vertices = coin.SoVertexProperty()

            for i in range(num_segments + 1):
                angle = 2 * math.pi * i / num_segments
                x = circle_radius * math.cos(angle)
                y = circle_radius * math.sin(angle)
                vertices.vertex.set1Value(i, x, y, 0)

            line_set = coin.SoLineSet()
            line_set.setName("Circle moment")
            line_set.vertexProperty = vertices
            line_set.numVertices.set1Value(0, num_segments + 1)
            root_sep.addChild(line_set)

            # Add direction arrows
            arrow = coin.SoCone()
            arrow.setName("arrow shape moment")
            arrow.bottomRadius = magnitude * 0.1
            arrow.height = magnitude * 0.3

            for i in range(3):  # Three arrows at 120° intervals
                arrow_sep = coin.SoSeparator()
                angle = i * 120 * math.pi / 180
                x = circle_radius * 0.95
                y = 0

                # Arrow rotation to point tangent to circle
                arrow_rot = coin.SoRotation()
                arrow_rot.rotation.setValue(coin.SbVec3f(0, 0, 1), angle - math.pi / 2)

                # Arrow position
                arrow_tf = coin.SoTransform()
                arrow_tf.translation.setValue(x, y, 0)

                arrow_sep.addChild(arrow_rot)
                arrow_sep.addChild(arrow_tf)
                arrow_sep.addChild(arrow)
                root_sep.addChild(arrow_sep)
                root_sep.setName("moment")

        except Exception as e:
            warnings.warn(f"Moment symbol creation failed: {str(e)}")
            return coin.SoSeparator()

        return root_sep
    @staticmethod
    def create_member_load(beam, load, load_scale ,load_color,moment_color):
        member_node = coin.SoSeparator()
        if not hasattr(beam, "Proxy"):
            return

        # Get beam properties
        start_pos = beam.StartPosWithOffset
        end_pos = beam.EndPosWithOffset
        beam_dir = end_pos - start_pos
        beam_length = beam_dir.Length

        # Calculate positions
        start_load_pos = start_pos + beam_dir * load.StartPosition
        end_load_pos = start_pos + beam_dir * load.EndPosition

        # Get local coordinate system if needed
        if load.LocalCS:
            rot_matrix = App.Matrix()
            rot_matrix.A11, rot_matrix.A12, rot_matrix.A13 = beam.Local_X.x, beam.Local_Y.x, beam.Local_Z.x
            rot_matrix.A21, rot_matrix.A22, rot_matrix.A23 = beam.Local_X.y, beam.Local_Y.y, beam.Local_Z.y
            rot_matrix.A31, rot_matrix.A32, rot_matrix.A33 = beam.Local_X.z, beam.Local_Y.z, beam.Local_Z.z

            # Transform forces to global coordinates for visualization
            start_force = rot_matrix.multVec(load.StartForce)
            end_force = rot_matrix.multVec(load.EndForce)
            start_moment = rot_matrix.multVec(load.StartMoment)
            end_moment = rot_matrix.multVec(load.EndMoment)
        else:
            start_force = load.StartForce
            end_force = load.EndForce
            start_moment = load.StartMoment
            end_moment = load.EndMoment

        # Calculate intermediate positions for additional arrows
        intermediate_positions = []
        # Calculate two intermediate positions#see to add more positions i/n+1
        pos1 = load.StartPosition + (load.EndPosition - load.StartPosition) * 0.33
        pos2 = load.StartPosition + (load.EndPosition - load.StartPosition) * 0.66
        intermediate_positions = [start_pos, start_pos + beam_dir * pos1,
                                  start_pos + beam_dir * pos2, end_pos
                                  ]

        # Calculate intermediate forces (linear interpolation)
        intermediate_forces = [start_force, start_force * 0.66 + end_force * 0.33,
                               start_force * 0.33 + end_force * 0.66, end_force
                               ]
        # Create arrows
        for pos, force in zip(intermediate_positions, intermediate_forces):
            if force.Length > 1e-6:
                # Point arrow toward the beam (reverse direction)
                force_arrow = FEMVisualization.create_force_arrow(
                    force, pos,
                    scale=load_scale,
                    color=load_color)
                member_node.addChild(force_arrow)
        # Calculate intermediate forces (linear interpolation)
        intermediate_moment = [start_moment, start_moment * 0.66 + end_moment * 0.33,
                               start_moment * 0.33 + end_moment * 0.66, end_moment
                               ]
        # Create moments at start and end positions
        for pos, moment in zip(intermediate_positions, intermediate_moment):
            if moment.Length > 1e-6:
                # Point arrow toward the beam (reverse direction)
                moment_symbol = FEMVisualization.create_moment_symbol(
                    moment, pos,
                    scale=load_scale,
                    color=moment_color)
                member_node.addChild(moment_symbol)
        return member_node
    @staticmethod
    def create_dimension_text(direction, position, text, color=(1.0, 1.0, 1.0), size=20.0):
        """Create text annotation"""
        sep = coin.SoSeparator()

        # Position
        transform = coin.SoTransform()
        transform.translation.setValue(position.x, position.y, position.z)
        sep.addChild(transform)

        # Color
        color_node = coin.SoBaseColor()
        color_node.rgb = color
        sep.addChild(color_node)
        # font
        font_node = coin.SoFont()
        font_node.name = "OIV_Simplex_Roman"
        font_node.size = size
        sep.addChild(font_node)

        # Rotation (only if force has magnitude)
        if direction.Length > 0:
            rotation = FEMVisualization._get_rotation_between(
                App.Vector(1, 0, 0),  # Default arrow points along Z
                direction.normalize()
            )
            rot_transform = coin.SoTransform()
            rot_transform.rotation = rotation
            sep.addChild(rot_transform)
        # Text
        text_node = coin.SoText3()
        text_node.string = text

        text_node.justification = coin.SoText3.LEFT
        sep.addChild(text_node)
        return sep