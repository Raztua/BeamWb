# ui/dialog_NodalLoad.py
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtGui, QtCore
from features.LoadManager import LoadManager
from FreeCAD import Units


class NodalLoadTaskPanel:
    """Task panel for creating and modifying Nodal Loads"""

    def __init__(self, selected_nodes=None, nodal_load_to_modify=None):
        self.form = QtGui.QWidget()
        self.form.setWindowTitle("Create Nodal Load")
        self.selected_nodes = selected_nodes or []
        self.selection_callback = None
        self.is_picking = False
        self.temp_selected_nodes = []
        self.nodal_load_to_modify = nodal_load_to_modify
        self.is_modification_mode = nodal_load_to_modify is not None

        self.setup_ui()
        self.update_load_id_combo()

        # Load existing data if in modification mode
        if self.is_modification_mode:
            self.load_nodal_load_data()
            self.form.setWindowTitle("Modify Nodal Load")
        else:
            # Check for pre-selected nodes
            if not self.selected_nodes:
                current_selection = Gui.Selection.getSelection()
                for obj in current_selection:
                    if self.is_valid_node(obj):
                        self.selected_nodes.append(obj)

        self.update_display()

    def setup_ui(self):
        layout = QtGui.QVBoxLayout(self.form)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Title - show different title for modification mode
        if self.is_modification_mode:
            title = QtGui.QLabel("Modify Nodal Load")
        else:
            title = QtGui.QLabel("Create Nodal Load")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)

        # Load ID Section
        load_id_group = QtGui.QGroupBox("Load ID")
        load_id_layout = QtGui.QHBoxLayout()

        self.load_id_combo = QtGui.QComboBox()
        load_id_layout.addWidget(self.load_id_combo)

        self.new_load_id_btn = QtGui.QPushButton("New Load ID")
        self.new_load_id_btn.clicked.connect(self.create_new_load_id)
        load_id_layout.addWidget(self.new_load_id_btn)

        load_id_group.setLayout(load_id_layout)
        layout.addWidget(load_id_group)

        # Node selection
        node_group = QtGui.QGroupBox("Node Selection")
        node_layout = QtGui.QVBoxLayout()

        # Selection info
        self.selection_info = QtGui.QLabel("No nodes selected")
        self.selection_info.setStyleSheet("font-weight: bold; color: blue;")
        node_layout.addWidget(self.selection_info)

        # Node list
        self.node_list = QtGui.QListWidget()
        self.node_list.setSelectionMode(QtGui.QListWidget.ExtendedSelection)
        self.node_list.setMaximumHeight(120)
        self.node_list.itemSelectionChanged.connect(self.on_node_selection_changed)
        node_layout.addWidget(self.node_list)

        button_layout = QtGui.QHBoxLayout()
        self.pick_button = QtGui.QPushButton("Pick Nodes")
        self.pick_button.clicked.connect(self.toggle_picking)
        self.clear_button = QtGui.QPushButton("Clear Selection")
        self.clear_button.clicked.connect(self.clear_selection)

        button_layout.addWidget(self.pick_button)
        button_layout.addWidget(self.clear_button)
        node_layout.addLayout(button_layout)

        node_group.setLayout(node_layout)
        layout.addWidget(node_group)

        # Force inputs with units
        force_group = QtGui.QGroupBox("Force")
        force_layout = QtGui.QGridLayout()

        for i, coord in enumerate(["X", "Y", "Z"]):
            force_layout.addWidget(QtGui.QLabel(f"{coord}:"), i, 0)
            line_edit = QtGui.QLineEdit()
            line_edit.setPlaceholderText("e.g., 10 kN")
            line_edit.editingFinished.connect(lambda coord=coord: self.add_unit_if_needed(f"force_{coord.lower()}"))
            setattr(self, f"force_{coord.lower()}_input", line_edit)
            force_layout.addWidget(line_edit, i, 1)

        force_group.setLayout(force_layout)
        layout.addWidget(force_group)

        # Moment inputs with units
        moment_group = QtGui.QGroupBox("Moment")
        moment_layout = QtGui.QGridLayout()

        for i, coord in enumerate(["X", "Y", "Z"]):
            moment_layout.addWidget(QtGui.QLabel(f"{coord}:"), i, 0)
            line_edit = QtGui.QLineEdit()
            line_edit.setPlaceholderText("e.g., 5 Nm")
            line_edit.editingFinished.connect(lambda coord=coord: self.add_unit_if_needed(f"moment_{coord.lower()}"))
            setattr(self, f"moment_{coord.lower()}_input", line_edit)
            moment_layout.addWidget(line_edit, i, 1)

        moment_group.setLayout(moment_layout)
        layout.addWidget(moment_group)

        layout.addStretch()

    def add_unit_if_needed(self, field_name):
        """Add 'kN' to force or 'Nm' to moment if no unit is specified"""
        line_edit = getattr(self, f"{field_name}_input")
        text = line_edit.text().strip()

        if text and not any(char.isalpha() for char in text):
            # No unit specified, add default unit
            if field_name.startswith('force'):
                line_edit.setText(f"{text} kN")
            elif field_name.startswith('moment'):
                line_edit.setText(f"{text} Nm")

    def parse_force_input(self, text):
        """Parse force input with units and return value in N"""
        if not text.strip():
            return 0.0

        try:
            quantity = Units.Quantity(text)
            if quantity is None:
                return 0.0

            # Convert to Newtons
            if quantity.Unit.Type == 'Force':
                return quantity.getValueAs('N')
            else:
                QtGui.QMessageBox.warning(self.form, "Warning",
                                          f"Invalid force unit. Please use N, kN, mN, etc.\nInput: {text}")
                return None
        except Exception as e:
            QtGui.QMessageBox.warning(self.form, "Warning",
                                      f"Error parsing force value: {str(e)}\nInput: {text}")
            return None

    def parse_moment_input(self, text):
        """Parse moment input with units and return value in Nm"""
        if not text.strip():
            return 0.0

        try:
            quantity = Units.Quantity(text)
            if quantity is None:
                return 0.0

            # Convert to Newton-meters
            if quantity.Unit.Type == 'Pressure':  # N/m² is pressure, but Nm is also in this category
                # Check if it's actually a moment (N·m, kN·m, etc.)
                # FreeCAD sometimes categorizes Nm as Pressure
                return quantity.getValueAs('N·m')
            else:
                QtGui.QMessageBox.warning(self.form, "Warning",
                                          f"Invalid moment unit. Please use Nm, kNm, etc.\nInput: {text}")
                return None
        except Exception as e:
            QtGui.QMessageBox.warning(self.form, "Warning",
                                      f"Error parsing moment value: {str(e)}\nInput: {text}")
            return None

    def load_nodal_load_data(self):
        """Load existing nodal load data for modification"""
        if not self.nodal_load_to_modify:
            return

        # Load nodes
        if hasattr(self.nodal_load_to_modify, 'Nodes') and self.nodal_load_to_modify.Nodes:
            self.selected_nodes = list(self.nodal_load_to_modify.Nodes)

        # Load force values with units
        if hasattr(self.nodal_load_to_modify, 'Force'):
            force = self.nodal_load_to_modify.Force

            # Convert N to kN for display
            self.force_x_input.setText(f"{force.x / 1000:.3f} kN")
            self.force_y_input.setText(f"{force.y / 1000:.3f} kN")
            self.force_z_input.setText(f"{force.z / 1000:.3f} kN")

        # Load moment values with units
        if hasattr(self.nodal_load_to_modify, 'Moment'):
            moment = self.nodal_load_to_modify.Moment

            # Keep as Nm for display
            self.moment_x_input.setText(f"{moment.x:.3f} Nm")
            self.moment_y_input.setText(f"{moment.y:.3f} Nm")
            self.moment_z_input.setText(f"{moment.z:.3f} Nm")

        # Update display
        self.update_display()

    def update_load_id_combo(self):
        self.load_id_combo.clear()
        doc = App.ActiveDocument
        if doc:
            for obj in doc.Objects:
                if hasattr(obj, "Type") and obj.Type == "LoadIDFeature":
                    self.load_id_combo.addItem(obj.Label, obj)

        if self.load_id_combo.count() == 0:
            self.load_id_combo.addItem("No Load IDs - Create one first", None)

    def create_new_load_id(self):
        """Create a new Load ID"""
        try:
            from features.LoadIDManager import create_load_id
            load_id = create_load_id()
            if load_id:
                self.update_load_id_combo()
                # Select the newly created Load ID
                for i in range(self.load_id_combo.count()):
                    if self.load_id_combo.itemData(i) == load_id:
                        self.load_id_combo.setCurrentIndex(i)
                        break
        except Exception as e:
            QtGui.QMessageBox.critical(self.form, "Error", f"Failed to create Load ID:\n{str(e)}")

    def is_valid_node(self, obj):
        """Check if object is a valid node"""
        return hasattr(obj, "Type") and obj.Type == "NodeFeature"

    def toggle_picking(self):
        """Toggle picking mode on/off"""
        if self.is_picking:
            self.stop_picking()
        else:
            self.start_picking()

    def start_picking(self):
        """Start picking nodes using FreeCAD selection"""
        Gui.Selection.clearSelection()

        # Add already selected nodes to FreeCAD selection for visual feedback
        for node in self.selected_nodes:
            Gui.Selection.addSelection(node)

        self.pick_button.setStyleSheet("font-weight: bold; background-color: lightgreen")
        self.pick_button.setText("Finish Selection")
        self.is_picking = True

        # Set up selection callback
        self.selection_callback = NodalLoadSelectionCallback(self)
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
            if self.is_valid_node(obj):
                if obj not in self.selected_nodes:
                    self.selected_nodes.append(obj)

        self.update_display()

        self.pick_button.setStyleSheet("")
        self.pick_button.setText("Pick Nodes")
        self.is_picking = False
        self.temp_selected_nodes = []

    def process_selection(self, doc_name, obj_name):
        """Process individual selection events"""
        try:
            doc = App.getDocument(doc_name)
            if not doc:
                return

            obj = doc.getObject(obj_name)
            if not obj:
                return

            if self.is_valid_node(obj):
                # During picking, we only update the visual selection in FreeCAD
                # The actual selection is only updated when user clicks "Finish Selection"
                pass

        except Exception as e:
            print(f"Error processing selection: {e}")

    def on_node_selection_changed(self):
        """Handle node list selection changes"""
        selected_items = self.node_list.selectedItems()
        if selected_items:
            # Update FreeCAD selection to match list widget selection
            Gui.Selection.clearSelection()
            for item in selected_items:
                node_label = item.text().split(" - ")[0]
                node = self.find_node_by_label(node_label)
                if node:
                    Gui.Selection.addSelection(node)

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

    def update_display(self):
        """Update the display based on current selection"""
        self.node_list.clear()
        for node in self.selected_nodes:
            if hasattr(node, "X") and hasattr(node, "Y") and hasattr(node, "Z"):
                x = getattr(node, "X", 0.0)
                y = getattr(node, "Y", 0.0)
                z = getattr(node, "Z", 0.0)

                if hasattr(x, "Value"):  # Handle Quantity objects
                    item_text = f"{node.Label} - ({x.Value:.1f}, {y.Value:.1f}, {z.Value:.1f}) mm"
                else:
                    item_text = f"{node.Label} - ({x:.1f}, {y:.1f}, {z:.1f}) mm"
            else:
                item_text = node.Label

            item = QtGui.QListWidgetItem(item_text)
            self.node_list.addItem(item)

        # Update selection info
        count = len(self.selected_nodes)
        self.selection_info.setText(f"{count} node(s) selected")

    def clear_selection(self):
        """Clear the node selection"""
        self.selected_nodes = []
        Gui.Selection.clearSelection()
        self.update_display()

    def get_current_load_id(self):
        """Get the currently selected Load ID"""
        if self.load_id_combo.currentData():
            return self.load_id_combo.currentData()
        else:
            QtGui.QMessageBox.warning(self.form, "Error", "Please select or create a Load ID first.")
            return None

    def create_nodal_load(self):
        """Create a new nodal load"""
        load_id = self.get_current_load_id()
        if not load_id:
            return False

        if not self.selected_nodes:
            QtGui.QMessageBox.warning(self.form, "Warning", "Please select at least one node.")
            return False

        # Parse force inputs
        force_values = []
        for coord in ["x", "y", "z"]:
            input_field = getattr(self, f"force_{coord}_input")
            value = self.parse_force_input(input_field.text())
            if value is None:
                return False
            force_values.append(value)

        # Parse moment inputs
        moment_values = []
        for coord in ["x", "y", "z"]:
            input_field = getattr(self, f"moment_{coord}_input")
            value = self.parse_moment_input(input_field.text())
            if value is None:
                return False
            moment_values.append(value)

        try:
            LoadManager.create_nodal_load(
                load_id=load_id,
                nodes=self.selected_nodes,
                force=tuple(force_values),
                moment=tuple(moment_values)
            )
            return True
        except Exception as e:
            QtGui.QMessageBox.critical(self.form, "Error", f"Failed to create nodal load:\n{str(e)}")
            return False

    def modify_nodal_load(self):
        """Modify an existing nodal load"""
        try:
            nl = self.nodal_load_to_modify

            # Update nodes
            nl.Nodes = self.selected_nodes

            # Parse and update force values
            force_values = []
            for coord in ["x", "y", "z"]:
                input_field = getattr(self, f"force_{coord}_input")
                value = self.parse_force_input(input_field.text())
                if value is None:
                    return False
                force_values.append(value)

            nl.Force = App.Vector(*force_values)

            # Parse and update moment values
            moment_values = []
            for coord in ["x", "y", "z"]:
                input_field = getattr(self, f"moment_{coord}_input")
                value = self.parse_moment_input(input_field.text())
                if value is None:
                    return False
                moment_values.append(value)

            nl.Moment = App.Vector(*moment_values)

            return True

        except Exception as e:
            App.Console.PrintError(f"Error modifying nodal load: {str(e)}\n")
            return False

    def apply_changes(self):
        """Create or modify nodal load"""
        # Ensure all fields have units added when focus is lost
        for coord in ["x", "y", "z"]:
            self.add_unit_if_needed(f"force_{coord}")
            self.add_unit_if_needed(f"moment_{coord}")

        if self.is_modification_mode:
            success = self.modify_nodal_load()
            if success:
                QtGui.QMessageBox.information(self.form, "Success", "Nodal load modified successfully.")
                return True
        else:
            success = self.create_nodal_load()
            if success:
                QtGui.QMessageBox.information(self.form, "Success", "Nodal load created successfully.")
                self.clear_selection()
                return True

        return False

    def cleanup(self):
        """Clean up resources"""
        if self.is_picking:
            self.stop_picking()

    def getStandardButtons(self):
        """Return standard buttons for task panel"""
        if self.is_modification_mode:
            return QtGui.QDialogButtonBox.Apply | QtGui.QDialogButtonBox.Close
        else:
            return QtGui.QDialogButtonBox.Apply | QtGui.QDialogButtonBox.Close

    def clicked(self, button):
        """Handle button clicks"""
        if button == QtGui.QDialogButtonBox.Apply:
            if self.apply_changes():
                if self.is_modification_mode:
                    # Close dialog after successful modification
                    self.cleanup()
                    Gui.Control.closeDialog()
                App.ActiveDocument.recompute()
        elif button == QtGui.QDialogButtonBox.Close:
            self.cleanup()
            Gui.Control.closeDialog()

    def reject(self):
        """Cancel operation"""
        self.cleanup()
        return True

    def accept(self):
        """Apply changes and close"""
        if self.apply_changes():
            self.cleanup()
            Gui.Control.closeDialog()
            return True
        return False


class NodalLoadSelectionCallback:
    """Callback class for handling nodal load selection events"""

    def __init__(self, task_panel):
        self.task_panel = task_panel

    def addSelection(self, doc_name, obj_name, sub_name, pos):
        """Called when an object is selected"""
        self.task_panel.process_selection(doc_name, obj_name)


def show_nodal_load_creator(selected_nodes=None, nodal_load_to_modify=None):
    """Show the nodal load creator task panel"""
    # Close any existing task panel first
    if hasattr(Gui, 'Control') and Gui.Control.activeDialog():
        Gui.Control.closeDialog()

    panel = NodalLoadTaskPanel(selected_nodes=selected_nodes, nodal_load_to_modify=nodal_load_to_modify)
    Gui.Control.showDialog(panel)
    return panel