# ui/dialog_NodeCreator.py
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtGui, QtCore
from features.nodes import create_node, make_nodes_group
import re
from FreeCAD import Units


class NodeCreatorTaskPanel:
    """Task panel for creating nodes by entering coordinates"""

    def __init__(self):
        self.form = QtGui.QWidget()
        self.form.setWindowTitle("Create Nodes")
        self.form.resize(400, 250)  # Increased height for unit labels
        self.setup_ui()

    def setup_ui(self):
        layout = QtGui.QVBoxLayout(self.form)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Title
        title = QtGui.QLabel("Create New Node")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)

        # Coordinate inputs with units
        coord_group = QtGui.QGroupBox("Node Coordinates")
        coord_layout = QtGui.QGridLayout()

        # Unit label at the top
        unit_label = QtGui.QLabel("Units: meters (m) - enter values like '1.5 m', '1500 mm', or '1.5'")
        unit_label.setStyleSheet("color: gray; font-size: 10px;")
        coord_layout.addWidget(unit_label, 0, 0, 1, 2)

        coord_layout.addWidget(QtGui.QLabel("X:"), 1, 0)
        self.x_input = QtGui.QLineEdit()
        self.x_input.setPlaceholderText("e.g., 1.5 m or 1500 mm")
        self.x_input.editingFinished.connect(lambda: self.add_unit_if_needed("x"))
        coord_layout.addWidget(self.x_input, 1, 1)

        coord_layout.addWidget(QtGui.QLabel("Y:"), 2, 0)
        self.y_input = QtGui.QLineEdit()
        self.y_input.setPlaceholderText("e.g., 1.5 m or 1500 mm")
        self.y_input.editingFinished.connect(lambda: self.add_unit_if_needed("y"))
        coord_layout.addWidget(self.y_input, 2, 1)

        coord_layout.addWidget(QtGui.QLabel("Z:"), 3, 0)
        self.z_input = QtGui.QLineEdit()
        self.z_input.setPlaceholderText("e.g., 1.5 m or 1500 mm")
        self.z_input.editingFinished.connect(lambda: self.add_unit_if_needed("z"))
        coord_layout.addWidget(self.z_input, 3, 1)

        coord_group.setLayout(coord_layout)
        layout.addWidget(coord_group)

        # Node name
        name_group = QtGui.QGroupBox("Node Name")
        name_layout = QtGui.QHBoxLayout()

        self.name_input = QtGui.QLineEdit()
        self.name_input.setPlaceholderText("Auto-generated if empty")
        name_layout.addWidget(self.name_input)

        name_group.setLayout(name_layout)
        layout.addWidget(name_group)

        layout.addStretch()

    def add_unit_if_needed(self, coord):
        """Add 'm' (meters) unit if no unit is specified"""
        line_edit = getattr(self, f"{coord}_input")
        text = line_edit.text().strip()

        if text and not any(char.isalpha() for char in text):
            # No unit specified, add default unit 'm'
            line_edit.setText(f"{text} m")

    def parse_coordinate_input(self, text):
        """Parse coordinate input with units and return value in meters"""
        if not text.strip():
            return 0.0

        try:
            quantity = Units.Quantity(text)
            if quantity is None:
                return 0.0

            # Convert to meters
            if quantity.Unit.Type in ['Length', 'Unit', 'Number']:
                return quantity.getValueAs('m')
            else:
                QtGui.QMessageBox.warning(self.form, "Warning",
                                          f"Invalid length unit. Please use m, mm, cm, etc.\nInput: {text}")
                return None
        except Exception as e:
            QtGui.QMessageBox.warning(self.form, "Warning",
                                      f"Error parsing coordinate value: {str(e)}\nInput: {text}")
            return None

    def get_next_node_name(self):
        """Generate the next available node name (N001, N002, etc.)"""
        existing_names = []
        doc = App.ActiveDocument

        if doc and hasattr(doc, "Nodes") and hasattr(doc.Nodes, "Group"):
            for obj in doc.Nodes.Group:
                if hasattr(obj, "Label") and obj.Label:
                    existing_names.append(obj.Label)

        # Find the highest existing number
        max_number = 0
        pattern = re.compile(r'^N(\d+)$', re.IGNORECASE)

        for name in existing_names:
            match = pattern.match(name)
            if match:
                number = int(match.group(1))
                if number > max_number:
                    max_number = number

        return f"N{max_number + 1:03d}"

    def create_node(self):
        """Create a single node with unit handling"""
        try:
            # Parse coordinate inputs with units
            x_val = self.parse_coordinate_input(self.x_input.text())
            y_val = self.parse_coordinate_input(self.y_input.text())
            z_val = self.parse_coordinate_input(self.z_input.text())
            if x_val is None or y_val is None or z_val is None:
                return False

            name = self.name_input.text().strip()
            if not name:
                name = self.get_next_node_name()

            # Create node with coordinates in meters
            node = create_node(X=x_val*1000, Y=y_val*1000, Z=z_val*1000)
            if node:
                node.Label = name
                # Clear inputs for next node
                self.x_input.clear()
                self.y_input.clear()
                self.z_input.clear()
                self.name_input.clear()
                App.ActiveDocument.recompute()
                return True

        except ValueError:
            QtGui.QMessageBox.warning(self.form, "Input Error",
                                      "Please enter valid values for coordinates.\nExamples: '1.5 m', '1500 mm', '2.0'")
            return False
        except Exception as e:
            QtGui.QMessageBox.warning(self.form, "Error", f"Failed to create node: {str(e)}")
            return False

        return False

    def apply_changes(self):
        """Apply button handler - create node"""
        # Ensure all fields have units added when focus is lost
        for coord in ["x", "y", "z"]:
            self.add_unit_if_needed(coord)
        if self.create_node():
            return True
        return False

    def getStandardButtons(self):
        """Return standard buttons for task panel"""
        return QtGui.QDialogButtonBox.Apply | QtGui.QDialogButtonBox.Close

    def clicked(self, button):
        """Handle button clicks"""
        if button == QtGui.QDialogButtonBox.Apply:
            if self.apply_changes():
                # Keep the dialog open for creating more nodes
                App.ActiveDocument.recompute()
                pass
        elif button == QtGui.QDialogButtonBox.Close:
            Gui.Control.closeDialog()

    def reject(self):
        """Cancel operation"""
        return True

    def accept(self):
        """Apply changes and close"""
        if self.apply_changes():
            Gui.Control.closeDialog()
            return True
        return False


def show_node_creator():
    """Show the node creator task panel"""
    panel = NodeCreatorTaskPanel()
    Gui.Control.showDialog(panel)