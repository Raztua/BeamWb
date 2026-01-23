# ui/dialog_NodeModifier.py
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtGui, QtCore
from features.nodes import get_all_nodes
from FreeCAD import Units
import re


class NodeModifierTaskPanel:
    """Task panel for modifying existing nodes"""

    def __init__(self):
        self.form = QtGui.QWidget()
        self.form.setWindowTitle("Modify Nodes")
        self.form.resize(500, 400)

        self.selected_nodes = []
        self.selection_callback = None
        self.is_picking = False

        self.setup_ui()

    def setup_ui(self):
        layout = QtGui.QVBoxLayout(self.form)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Title
        title = QtGui.QLabel("Modify Existing Nodes")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)

        # Node selection
        selection_group = QtGui.QGroupBox("Node Selection")
        selection_layout = QtGui.QVBoxLayout()

        # Selection info
        self.selection_info = QtGui.QLabel("No nodes selected")
        self.selection_info.setStyleSheet("font-weight: bold; color: blue;")
        selection_layout.addWidget(self.selection_info)

        # Node list - limited height to show only 5 items
        self.node_list = QtGui.QListWidget()
        self.node_list.setSelectionMode(QtGui.QListWidget.ExtendedSelection)
        self.node_list.setMaximumHeight(50)
        self.node_list.itemSelectionChanged.connect(self.on_node_selection_changed)
        selection_layout.addWidget(self.node_list)

        # Selection buttons
        button_layout = QtGui.QHBoxLayout()
        self.pick_button = QtGui.QPushButton("Pick Nodes")
        self.pick_button.clicked.connect(self.toggle_picking)
        self.clear_button = QtGui.QPushButton("Clear Selection")
        self.clear_button.clicked.connect(self.clear_selection)
        self.select_all_btn = QtGui.QPushButton("Select All")
        self.select_all_btn.clicked.connect(self.select_all_nodes)

        button_layout.addWidget(self.pick_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.select_all_btn)
        selection_layout.addLayout(button_layout)

        selection_group.setLayout(selection_layout)
        layout.addWidget(selection_group)

        # Coordinate modification with unit handling
        coord_group = QtGui.QGroupBox("Modify Coordinates")
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
            return None  # Return None for empty input (meaning keep current value)

        try:
            quantity = Units.Quantity(text)
            if quantity is None:
                return None

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

    def toggle_picking(self):
        """Toggle picking mode on/off using FreeCAD's built-in selection"""
        if self.is_picking:
            self.stop_picking()
        else:
            self.start_picking()

    def start_picking(self):
        """Start picking nodes using FreeCAD selection"""
        # Clear FreeCAD selection and add currently selected nodes
        Gui.Selection.clearSelection()

        # Add already selected nodes to FreeCAD selection
        for node in self.selected_nodes:
            Gui.Selection.addSelection(node)

        self.pick_button.setStyleSheet("font-weight: bold; background-color: lightgreen")
        self.pick_button.setText("Finish Selection")
        self.is_picking = True

        # Set up selection callback to monitor changes
        self.selection_callback = NodeSelectionCallback(self)
        Gui.Selection.addObserver(self.selection_callback)

    def stop_picking(self):
        """Stop picking nodes and process the selection"""
        if self.selection_callback:
            Gui.Selection.removeObserver(self.selection_callback)
            self.selection_callback = None

        # Get current FreeCAD selection and update our node list
        current_selection = Gui.Selection.getSelection()
        self.selected_nodes = []

        for obj in current_selection:
            if hasattr(obj, "Type") and obj.Type == "NodeFeature":
                if obj not in self.selected_nodes:
                    self.selected_nodes.append(obj)

        self.update_display()

        self.pick_button.setStyleSheet("")
        self.pick_button.setText("Pick Nodes")
        self.is_picking = False

    def process_selection(self, doc_name, obj_name):
        """Process individual selection events - update coordinate values for each new node"""
        try:
            doc = App.getDocument(doc_name)
            if not doc:
                return

            obj = doc.getObject(obj_name)
            if not obj:
                return

            # Check if it's a node feature and not already in our list
            if (hasattr(obj, "Type") and obj.Type == "NodeFeature"
                    and obj not in self.selected_nodes):
                self.selected_nodes.append(obj)
                # Update coordinate values immediately for consistency
                self.update_coordinate_inputs()

        except Exception as e:
            print(f"Error processing selection: {e}")

    def clear_selection(self):
        """Clear the node selection"""
        self.selected_nodes = []
        Gui.Selection.clearSelection()
        self.update_display()

    def select_all_nodes(self):
        """Select all nodes in the document"""
        self.selected_nodes = get_all_nodes()
        # Also select them in FreeCAD
        Gui.Selection.clearSelection()
        for node in self.selected_nodes:
            Gui.Selection.addSelection(node)
        self.update_display()

    def on_node_selection_changed(self):
        """Handle node list selection changes"""
        selected_items = self.node_list.selectedItems()
        if selected_items:
            # Update the selected_nodes list to match list widget selection
            self.selected_nodes = []
            for item in selected_items:
                node_label = item.text().split(" - ")[0]
                node = self.find_node_by_label(node_label)
                if node:
                    self.selected_nodes.append(node)

            # Also update FreeCAD selection
            Gui.Selection.clearSelection()
            for node in self.selected_nodes:
                Gui.Selection.addSelection(node)

            self.update_coordinate_inputs()

    def find_node_by_label(self, label):
        """Find node object by label"""
        doc = App.ActiveDocument
        if not doc:
            return None

        # Check in Nodes group
        nodes_group = doc.getObject("Nodes")
        if nodes_group:
            for node in nodes_group.Group:
                if node.Label == label:
                    return node

        return None

    def get_coordinate_value(self, coord_property):
        """Extract float value from coordinate property which could be Quantity or float"""
        try:
            # Check if it's a Quantity object
            if hasattr(coord_property, 'Value'):
                # It's a Quantity, get the raw value
                return float(coord_property.Value)
            elif hasattr(coord_property, 'getValueAs'):
                # It's a Quantity with getValueAs method
                return coord_property.getValueAs('mm')
            else:
                # Try to convert to float directly
                return float(coord_property)
        except:
            # If all else fails, return 0
            return 0.0

    def update_display(self):
        """Update the display based on current selection"""
        # Update node list
        self.node_list.clear()
        for node in self.selected_nodes:
            # Get coordinate values as floats in mm
            x_val = self.get_coordinate_value(getattr(node, "X", 0.0))
            y_val = self.get_coordinate_value(getattr(node, "Y", 0.0))
            z_val = self.get_coordinate_value(getattr(node, "Z", 0.0))

            # Convert from mm to meters for display
            x_m = x_val / 1000.0
            y_m = y_val / 1000.0
            z_m = z_val / 1000.0

            item_text = f"{node.Label} - ({x_m:.3f}, {y_m:.3f}, {z_m:.3f}) m"
            item = QtGui.QListWidgetItem(item_text)
            self.node_list.addItem(item)

        # Update selection info
        count = len(self.selected_nodes)
        self.selection_info.setText(f"{count} node(s) selected")

        # Update coordinate inputs
        self.update_coordinate_inputs()

    def update_coordinate_inputs(self):
        """Update coordinate inputs based on selected nodes - called for each new node addition"""
        if not self.selected_nodes:
            self.x_input.clear()
            self.y_input.clear()
            self.z_input.clear()
            return

        # Get coordinates of all selected nodes (converted from mm to meters)
        coords = []
        for node in self.selected_nodes:
            # Get coordinate values as floats in mm
            x_val = self.get_coordinate_value(getattr(node, "X", 0.0))
            y_val = self.get_coordinate_value(getattr(node, "Y", 0.0))
            z_val = self.get_coordinate_value(getattr(node, "Z", 0.0))

            # Convert from mm to meters
            x_m = x_val / 1000.0
            y_m = y_val / 1000.0
            z_m = z_val / 1000.0

            coords.append((x_m, y_m, z_m))

        # Check if all nodes have same values - only update if all are the same
        x_values = [coord[0] for coord in coords]
        y_values = [coord[1] for coord in coords]
        z_values = [coord[2] for coord in coords]

        # Display values with 'm' unit
        if x_values and all(v == x_values[0] for v in x_values):
            self.x_input.setText(f"{x_values[0]:.3f} m")
        else:
            self.x_input.setText("")

        if y_values and all(v == y_values[0] for v in y_values):
            self.y_input.setText(f"{y_values[0]:.3f} m")
        else:
            self.y_input.setText("")

        if z_values and all(v == z_values[0] for v in z_values):
            self.z_input.setText(f"{z_values[0]:.3f} m")
        else:
            self.z_input.setText("")

    def modify_nodes(self):
        """Apply coordinate changes to selected nodes with unit handling"""
        if not self.selected_nodes:
            QtGui.QMessageBox.warning(self.form, "Warning", "Please select at least one node.")
            return False

        try:
            # Ensure all fields have units added when focus is lost
            for coord in ["x", "y", "z"]:
                self.add_unit_if_needed(coord)

            # Parse coordinate inputs with units (returns values in meters)
            x_val = self.parse_coordinate_input(self.x_input.text())
            y_val = self.parse_coordinate_input(self.y_input.text())
            z_val = self.parse_coordinate_input(self.z_input.text())

            # If any coordinate failed to parse (and wasn't empty), return False
            if (x_val is None and self.x_input.text().strip()) or \
                    (y_val is None and self.y_input.text().strip()) or \
                    (z_val is None and self.z_input.text().strip()):
                return False

            # Only update values that were provided (non-empty)
            for node in self.selected_nodes:
                if x_val is not None:
                    # Convert meters to mm and set as float
                    node.X = x_val * 1000
                if y_val is not None:
                    node.Y = y_val * 1000
                if z_val is not None:
                    node.Z = z_val * 1000

            # Recompute the document
            if App.ActiveDocument:
                App.ActiveDocument.recompute()

            self.update_display()  # Refresh display with new values

            return True

        except ValueError:
            QtGui.QMessageBox.warning(self.form, "Input Error",
                                      "Please enter valid values for coordinates.\nExamples: '1.5 m', '1500 mm', '2.0'")
            return False
        except Exception as e:
            QtGui.QMessageBox.warning(self.form, "Error", f"Failed to modify node: {str(e)}")
            return False

    def apply_changes(self):
        """Apply button handler - modify nodes"""
        return self.modify_nodes()

    def getStandardButtons(self):
        """Return standard buttons for task panel"""
        return QtGui.QDialogButtonBox.Apply | QtGui.QDialogButtonBox.Close

    def clicked(self, button):
        """Handle button clicks"""
        if button == QtGui.QDialogButtonBox.Apply:
            if self.apply_changes():
                App.ActiveDocument.recompute()
        elif button == QtGui.QDialogButtonBox.Close:
            self.stop_picking()
            Gui.Control.closeDialog()

    def reject(self):
        """Cancel operation"""
        self.stop_picking()
        return True

    def accept(self):
        """Apply changes and close"""
        self.stop_picking()
        if self.apply_changes():
            Gui.Control.closeDialog()
            return True
        return False


class NodeSelectionCallback:
    """Callback class for handling node selection events"""

    def __init__(self, task_panel):
        self.task_panel = task_panel

    def addSelection(self, doc_name, obj_name, sub_name, pos):
        """Called when an object is selected"""
        self.task_panel.process_selection(doc_name, obj_name)


def show_node_modifier(nodes=None):
    """Show the node modifier task panel with optional node pre-selection"""
    # Close any existing task panel first
    if hasattr(Gui, 'Control') and Gui.Control.activeDialog():
        Gui.Control.closeDialog()

    panel = NodeModifierTaskPanel()

    # If specific nodes are provided, pre-select them
    if nodes:
        panel.selected_nodes = nodes
        # Also select them in FreeCAD
        Gui.Selection.clearSelection()
        for node in nodes:
            if node and hasattr(node, 'Type') and node.Type == "NodeFeature":
                Gui.Selection.addSelection(node)
        panel.update_display()
    else:
        # Check if there are any selected nodes in FreeCAD and pre-select them
        current_selection = Gui.Selection.getSelection()
        node_selection = []

        for obj in current_selection:
            if hasattr(obj, "Type") and obj.Type == "NodeFeature":
                node_selection.append(obj)

        if node_selection:
            panel.selected_nodes = node_selection
            panel.update_display()

    Gui.Control.showDialog(panel)
    return panel