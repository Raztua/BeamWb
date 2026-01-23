import FreeCAD as App
import FreeCADGui as Gui
from pivy import coin
import math


class BaseShape:
    """Base class for all boundary condition shapes"""

    def __init__(self):
        self.separator = coin.SoSeparator()

    def get_separator(self):
        """Return the pivy separator for this shape"""
        return self.separator


class BoxShape(BaseShape):
    def __init__(self, length=2.0, depth=1.5, height=1.0, offset_x=0, offset_y=0, offset_z=0):
        super().__init__()
        self.create_shape(length, depth, height, offset_x, offset_y, offset_z)

    def create_shape(self, length, depth, height, offset_x, offset_y, offset_z):
        """Create rectangular box boundary condition shape with offset"""
        box = coin.SoCube()
        box.width = length
        box.height = depth
        box.depth = height
        transform = coin.SoTransform()
        transform.translation.setValue(offset_x, offset_y, offset_z - height / 2)
        self.separator.addChild(transform)
        self.separator.addChild(box)


class CylinderShape(BaseShape):
    def __init__(self, radius=1.0, length=2.0, offset_x=0, offset_y=0, offset_z=0):
        super().__init__()
        self.create_shape(radius, length, offset_x, offset_y, offset_z)

    def create_shape(self, radius, length, offset_x, offset_y, offset_z):
        """Create cylindrical boundary condition shape with offset"""
        cylinder = coin.SoCylinder()
        cylinder.radius = radius
        cylinder.height = length

        # Rotate cylinder to be horizontal by default and apply offset
        rotation = coin.SoRotation()
        rotation.rotation.setValue(coin.SbVec3f(1, 0, 0), math.pi / 2)

        transform = coin.SoTransform()
        transform.translation.setValue(offset_x, offset_y, offset_z - length)

        self.separator.addChild(transform)
        self.separator.addChild(rotation)
        self.separator.addChild(cylinder)


class PyramidShape(BaseShape):
    def __init__(self, length_base=2.0, height=1.5, offset_x=0, offset_y=0, offset_z=0):
        super().__init__()
        self.create_shape(length_base, height, offset_x, offset_y, offset_z)

    def create_shape(self, length_base, height, offset_x, offset_y, offset_z):
        """Create pyramid boundary condition shape with offset"""
        vertices = coin.SoVertexProperty()
        hb = length_base / 2

        # Vertices: base 0-3, apex 4
        for i, (x, y, z) in enumerate([(-hb, -hb, 0), (hb, -hb, 0), (hb, hb, 0), (-hb, hb, 0), (0, 0, height)]):
            vertices.vertex.set1Value(i, x, y, z)

        faces = coin.SoIndexedFaceSet()
        faces.vertexProperty = vertices

        # All faces in one list (-1 separates faces)
        for i, idx in enumerate([3, 2, 1, 0, -1, 0, 1, 4, -1, 1, 2, 4, -1, 2, 3, 4, -1, 3, 0, 4, -1]):
            faces.coordIndex.set1Value(i, idx)

        transform = coin.SoTransform()
        transform.translation.setValue(offset_x, offset_y, offset_z - height)

        self.separator.addChild(transform)
        self.separator.addChild(faces)
