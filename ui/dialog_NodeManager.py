# ui/dialog_NodeManager.py
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtGui, QtCore
from pivy import coin
import os
import re
from features.nodes import make_nodes_group, create_node, get_all_nodes, update_node, delete_node
from FreeCAD import Units


class NodeManagerTaskPanel:
    """Task panel for managing nodes using FreeCAD's embedded task manager"""

    # Define a consistent format spec for all quantity displays
    FORMAT_SPEC = {"NumberFormat": Units.NumberFormat.Fixed, "Decimals": 3}

    def __init__(self):
        # Create the form widget and set initial size
        self.form = QtGui.QWidget()
        self.form.setWindowTitle("Node Manager")

        # Set initial size for the task panel
        self.form.resize(700, 450)
        self.form.setMinimumSize(500, 350)

        self.nodes = []
        self.setup_ui()
        self.load_nodes()

    def setup_ui(self):
        layout = QtGui.QVBoxLayout(self.form)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Information label
        info_label = QtGui.QLabel("Enter coordinates (e.g., '1.5 m', '1500 mm', or '2.0').")
        info_label.setStyleSheet("color: gray; font-size: 10px; background-color: #f0f0f0; padding: 4px;")
        layout.addWidget(info_label)

        # Table for existing nodes
        self.table = QtGui.QTableWidget()
        self.table.setColumnCount(4)  # Removed "Units" column, as unit is part of the value string now
        self.table.setHorizontalHeaderLabels(["Name", "X", "Y", "Z"])
        self.table.horizontalHeader().setStretchLastSection(True)
        # No need for fixed column width for units anymore

        # Set delegates for coordinate columns
        for col in range(1, 4):  # Columns 1-3 (X, Y, Z)
            delegate = CoordinateDelegate(self.table)
            self.table.setItemDelegateForColumn(col, delegate)

        self.table.cellChanged.connect(self.on_cell_changed)
        self.table.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.table.verticalHeader().setDefaultSectionSize(8)
        self.table.setAlternatingRowColors(True)

        layout.addWidget(self.table, 1)

        # Buttons for table operations
        btn_layout = QtGui.QHBoxLayout()
        btn_layout.setSpacing(6)

        add_btn = QtGui.QPushButton("Add New Node")
        add_btn.clicked.connect(self.add_new_row)
        btn_layout.addWidget(add_btn)

        delete_btn = QtGui.QPushButton("Delete Selected")
        delete_btn.clicked.connect(self.delete_selected)
        btn_layout.addWidget(delete_btn)

        btn_layout.addStretch()

        layout.addLayout(btn_layout)

    # --- Removed get_quantity_value() as it's no longer needed ---

    def get_next_node_name(self):
        """Generate the next available node name (N001, N002, etc.)"""
        existing_names = []

        # Get names from existing nodes in document
        for node in get_all_nodes():
            if hasattr(node, 'Label') and node.Label:
                existing_names.append(node.Label)

        # Get names from table rows (including unsaved new nodes)
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 0)
            if name_item and name_item.text().strip():
                existing_names.append(name_item.text().strip())

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

    def load_nodes(self):
        """Load existing nodes into the table with units"""
        self.nodes = get_all_nodes()
        self.table.setRowCount(len(self.nodes))
        self.table.setColumnCount(4) # Ensure correct column count after removal of Units column

        # Disable cell change signals while loading
        self.table.blockSignals(True)

        for row, node in enumerate(self.nodes):
            # Node name
            name = node.Label
            name_item = QtGui.QTableWidgetItem(name)
            name_item.setFlags(name_item.flags() & ~QtCore.Qt.ItemIsEditable)
            self.table.setItem(row, 0, name_item)

            # Coordinates - use Quantity to display formatted user string
            for col, coord in enumerate(["X", "Y", "Z"], 1):
                quantity_value = getattr(node, coord, 0.0) # This is a float in meters

                # Convert float (in meters) to Quantity object
                # Note: FreeCAD properties (like node.X) are floats in internal units (m)
                # We assume here the float represents a value in meters, creating a Quantity
                if isinstance(quantity_value, (float, int)):
                    # Create a Quantity object, apply format, and get UserString
                    quantity = Units.Quantity(f"{quantity_value} m")
                else:
                    # Fallback if it's already a FreeCAD Quantity object
                    quantity = quantity_value

                quantity.Format = self.FORMAT_SPEC
                value_formated = quantity.UserString

                item = QtGui.QTableWidgetItem(value_formated)
                self.table.setItem(row, col, item)

        self.table.blockSignals(False)


    def add_new_row(self):
        """Add a new empty row for creating a node"""
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Add empty items
        for col in range(4): # 4 columns now
            item = QtGui.QTableWidgetItem("")
            if col == 0:
                # Set default name
                self.table.blockSignals(True)
                item.setText(self.get_next_node_name())
                self.table.blockSignals(False)
            self.table.setItem(row, col, item)

    def delete_selected(self):
        """Delete selected nodes"""
        selected_rows = set()
        for item in self.table.selectedItems():
            selected_rows.add(item.row())

        # Delete from bottom to top to avoid index issues
        for row in sorted(selected_rows, reverse=True):
            if row < len(self.nodes):
                # Delete existing node
                delete_node(self.nodes[row])
            self.table.removeRow(row)

        # Reload nodes after deletion
        self.load_nodes()

    def parse_coordinate_with_unit(self, text, default_unit="m"):
        """
        Parse coordinate text with unit and return a tuple:
        (value_in_meters, formatted_user_string)
        """
        if not text.strip():
            # Return 0.0m and an empty string for display
            return 0.0, ""

        try:
            # 1. Add default unit if no unit specified
            if text.strip() and not any(char.isalpha() for char in text.strip()):
                text = f"{text.strip()} {default_unit}"

            # 2. Parse the coordinate with unit
            value_m = Units.Quantity(text)

            # Check if it's a valid length unit
            if value_m.Unit.Type not in ['Length', 'Unit', 'Number']:
                App.Console.PrintWarning(f"Invalid length unit in: {text}\n")
                return None, None # Indicate failure

            # 3. Apply format spec to get the user-formatted string
            # IMPORTANT: The Quantity object must be formatted BEFORE getting the string
            value_m.Format = self.FORMAT_SPEC
            value_formated = value_m.UserString

            # 4. Return value in internal units (meters) and the formatted string
            return value_m.getValueAs('mm').Value, value_formated

        except Exception as e:
            App.Console.PrintWarning(f"Error parsing coordinate: {text} - {str(e)}\n")
            return None, None # Indicate failure

    def on_cell_changed(self, row, column):
        """Handle cell changes in the table"""
        if self.table.signalsBlocked():
            return

        # Only process coordinate columns (1-3)
        if column in [1, 2, 3]:
            try:
                coord_item = self.table.item(row, column)
                if not coord_item:
                    return

                text = coord_item.text().strip()
                if not text:
                    # Treat empty as 0.0m and update the cell display
                    value_m, value_formated = self.parse_coordinate_with_unit("0.0")
                else:
                    value_m, value_formated = self.parse_coordinate_with_unit(text)

                if value_m is None:
                    # Restore previous value if parsing failed
                    self.load_nodes()
                    return

                # Update display with formatted value (including unit, e.g., "1.500 m")
                coord_item.setText(value_formated)

                # If this is an existing node, update it
                if row < len(self.nodes):
                    node = self.nodes[row]
                    coord_name = ["X", "Y", "Z"][column - 1]
                    # value_m is already in meters (float), suitable for FreeCAD properties
                    setattr(node, coord_name, value_m)
                else:
                    # For a new node, just ensure the cell has the formatted value
                    pass

            except Exception as e:
                App.Console.PrintWarning(f"Error updating coordinate: {str(e)}\n")

    def apply_changes(self):
        """Apply all changes from the table"""
        created_nodes = []

        for row in range(self.table.rowCount()):
            try:
                name_item = self.table.item(row, 0)
                if not name_item or not name_item.text().strip():
                    continue

                name = name_item.text().strip()

                # Parse coordinates
                coords = []
                valid_row = True
                for col in range(1, 4):  # X, Y, Z columns
                    item = self.table.item(row, col)
                    # The text in the item is already the user-formatted string,
                    text_to_parse = item.text().strip() if item and item.text().strip() else "0.0"
                    value_m, _ = self.parse_coordinate_with_unit(text_to_parse)
                    if value_m is None:
                        # Skip this row if coordinate parsing failed
                        valid_row = False
                        break
                    coords.append(value_m)

                if not valid_row:
                    continue

                x, y, z = coords
                if row < len(self.nodes):
                    # Update existing node
                    node = self.nodes[row]
                    node.X = x
                    node.Y = y
                    node.Z = z
                    node.Label = name
                else:
                    # Create new node
                    node = create_node(X=x, Y=y, Z=z)
                    if node:
                        node.Label = name
                        created_nodes.append(node)
                App.ActiveDocument.recompute()
            except Exception as e:
                App.Console.PrintWarning(f"Error processing row {row + 1}: {str(e)}\n")

        if created_nodes:
            App.Console.PrintMessage(f"Created {len(created_nodes)} new node(s)\n")
        return True

    def reject(self):
        """Cancel operation"""
        return True

    def accept(self):
        """Apply changes and close"""
        if self.apply_changes():
            Gui.Control.closeDialog()
            return True
        return False

    def clicked(self, button):
        """Handle button clicks"""
        if button == QtGui.QDialogButtonBox.Apply:
            self.apply_changes()
            self.load_nodes()
        elif button == QtGui.QDialogButtonBox.Close:
            Gui.Control.closeDialog()

    def getStandardButtons(self):
        """Return standard buttons for task panel"""
        return QtGui.QDialogButtonBox.Apply | QtGui.QDialogButtonBox.Close




class CoordinateDelegate(QtGui.QItemDelegate):
    """Delegate for coordinate editing with unit suggestions"""

    def createEditor(self, parent, option, index):
        editor = QtGui.QLineEdit(parent)
        return editor

    def setEditorData(self, editor, index):
        # When editing starts, use the existing text which includes the unit
        text = index.model().data(index, QtCore.Qt.DisplayRole)
        editor.setText(str(text))

    def setModelData(self, editor, model, index):
        # Set the model data with the user's input string (e.g., "1500 mm")
        text = editor.text().strip()
        model.setData(index, text, QtCore.Qt.EditRole)


def show_node_manager():
    """Show the node manager task panel"""
    panel = NodeManagerTaskPanel()
    Gui.Control.showDialog(panel)