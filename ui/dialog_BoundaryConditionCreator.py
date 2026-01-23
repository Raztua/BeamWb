# Updated dialog_BoundaryConditionCreator.py
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtGui, QtCore
from features.boundary_condition import create_boundary_condition


class BoundaryConditionCreatorTaskPanel:
    """Task panel for creating and modifying boundary conditions"""

    def __init__(self, boundary_condition=None):
        self.form = QtGui.QWidget()
        self.form.setWindowTitle("Boundary Condition Creator")
        self.selected_nodes = []
        self.selection_callback = None
        self.is_picking = False
        self.temp_selected_nodes = []
        self.boundary_condition_to_modify = boundary_condition  # BC object to modify
        self.is_modification_mode = boundary_condition is not None
        
        self.setup_ui()
        # If in modification mode, load the existing boundary condition data
        if self.is_modification_mode:
            self.load_boundary_condition_data()

    def setup_ui(self):
        layout = QtGui.QVBoxLayout(self.form)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Title - show different title for modification mode
        if self.is_modification_mode:
            title = QtGui.QLabel("Modify Boundary Condition")
        else:
            title = QtGui.QLabel("Create Boundary Condition")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)

        # Node selection
        node_group = QtGui.QGroupBox("Node Selection")
        node_layout = QtGui.QVBoxLayout()

        # Selection info
        self.selection_info = QtGui.QLabel("No nodes selected")
        self.selection_info.setStyleSheet("font-weight: bold; color: blue;")
        node_layout.addWidget(self.selection_info)

        # Node list - limited height to show only 5 items
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

        # Fixity settings
        fixity_group = QtGui.QGroupBox("Boundary Conditions")
        fixity_layout = QtGui.QGridLayout()

        # Translation fixity
        fixity_layout.addWidget(QtGui.QLabel("Translation Fixity:"), 0, 0)
        self.dx_check = QtGui.QCheckBox("DX")
        self.dy_check = QtGui.QCheckBox("DY")
        self.dz_check = QtGui.QCheckBox("DZ")
        self.dx_check.setChecked(True)
        self.dy_check.setChecked(True)
        self.dz_check.setChecked(True)

        trans_layout = QtGui.QHBoxLayout()
        trans_layout.addWidget(self.dx_check)
        trans_layout.addWidget(self.dy_check)
        trans_layout.addWidget(self.dz_check)
        fixity_layout.addLayout(trans_layout, 0, 1)

        # Rotation fixity
        fixity_layout.addWidget(QtGui.QLabel("Rotation Fixity:"), 1, 0)
        self.rx_check = QtGui.QCheckBox("RX")
        self.ry_check = QtGui.QCheckBox("RY")
        self.rz_check = QtGui.QCheckBox("RZ")
        self.rx_check.setChecked(True)
        self.ry_check.setChecked(True)
        self.rz_check.setChecked(True)

        rot_layout = QtGui.QHBoxLayout()
        rot_layout.addWidget(self.rx_check)
        rot_layout.addWidget(self.ry_check)
        rot_layout.addWidget(self.rz_check)
        fixity_layout.addLayout(rot_layout, 1, 1)

        # Preset buttons
        preset_layout = QtGui.QHBoxLayout()
        fixed_button = QtGui.QPushButton("Fixed")
        fixed_button.clicked.connect(self.set_fixed)
        pinned_button = QtGui.QPushButton("Pinned")
        pinned_button.clicked.connect(self.set_pinned)
        roller_button = QtGui.QPushButton("Roller")
        roller_button.clicked.connect(self.set_roller)

        preset_layout.addWidget(fixed_button)
        preset_layout.addWidget(pinned_button)
        preset_layout.addWidget(roller_button)
        fixity_layout.addLayout(preset_layout, 2, 0, 1, 2)

        fixity_group.setLayout(fixity_layout)
        layout.addWidget(fixity_group)

        # Visual properties
        visual_group = QtGui.QGroupBox("Visual Properties")
        visual_layout = QtGui.QGridLayout()

        visual_layout.addWidget(QtGui.QLabel("Scale:"), 0, 0)
        self.scale_spin = QtGui.QDoubleSpinBox()
        self.scale_spin.setRange(0.1, 5.0)
        self.scale_spin.setValue(1.0)
        self.scale_spin.setSingleStep(0.1)
        visual_layout.addWidget(self.scale_spin, 0, 1)

        visual_group.setLayout(visual_layout)
        layout.addWidget(visual_group)

        layout.addStretch()

    def load_boundary_condition_data(self):
        """Load existing boundary condition data for modification"""
        if not self.boundary_condition_to_modify:
            return
        # Load nodes
        if hasattr(self.boundary_condition_to_modify, 'Nodes') and self.boundary_condition_to_modify.Nodes:
            self.selected_nodes = list(self.boundary_condition_to_modify.Nodes)
        
        # Load fixity settings
        if hasattr(self.boundary_condition_to_modify, 'Dx'):
            self.dx_check.setChecked(self.boundary_condition_to_modify.Dx)
            self.dy_check.setChecked(self.boundary_condition_to_modify.Dy)
            self.dz_check.setChecked(self.boundary_condition_to_modify.Dz)
            self.rx_check.setChecked(self.boundary_condition_to_modify.Rx)
            self.ry_check.setChecked(self.boundary_condition_to_modify.Ry)
            self.rz_check.setChecked(self.boundary_condition_to_modify.Rz)
        
        # Load scale
        if hasattr(self.boundary_condition_to_modify, 'Scale'):
            self.scale_spin.setValue(self.boundary_condition_to_modify.Scale)
        
        # Update display
        self.update_display()

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
        
        # Store current selection as starting point
        self.temp_selected_nodes = self.selected_nodes.copy()
        
        # Add already selected nodes to FreeCAD selection for visual feedback
        for node in self.temp_selected_nodes:
            Gui.Selection.addSelection(node)
        
        self.pick_button.setStyleSheet("font-weight: bold; background-color: lightgreen")
        self.pick_button.setText("Finish Selection")
        self.is_picking = True
        
        # Set up selection callback to monitor changes
        self.selection_callback = BoundarySelectionCallback(self)
        Gui.Selection.addObserver(self.selection_callback)

    def stop_picking(self):
        """Stop picking nodes and process the selection - only update when user finishes"""
        if self.selection_callback:
            Gui.Selection.removeObserver(self.selection_callback)
            self.selection_callback = None

        # Get current FreeCAD selection and update our node list
        current_selection = Gui.Selection.getSelection()
        
        # Only update the main selection when user explicitly finishes
        self.selected_nodes = []
        
        for obj in current_selection:
            if hasattr(obj, "Type") and obj.Type == "NodeFeature":
                if obj not in self.selected_nodes:
                    self.selected_nodes.append(obj)
        
        self.update_display()

        self.pick_button.setStyleSheet("")
        self.pick_button.setText("Pick Nodes")
        self.is_picking = False
        self.temp_selected_nodes = []

    def process_selection(self, doc_name, obj_name):
        """Process individual selection events - only update temporary storage during picking"""
        try:
            doc = App.getDocument(doc_name)
            if not doc:
                return

            obj = doc.getObject(obj_name)
            if not obj:
                return

            # Check if it's a node feature
            if hasattr(obj, "Type") and obj.Type == "NodeFeature":
                # During picking, we only update the visual selection in FreeCAD
                # The actual selection is only updated when user clicks "Finish Selection"
                if self.is_picking:
                    # Just update FreeCAD selection visually, don't update our internal list yet
                    pass

        except Exception as e:
            print(f"Error processing selection: {e}")

    def on_node_selection_changed(self):
        """Handle node list selection changes"""
        selected_items = self.node_list.selectedItems()
        if selected_items:
            # Update the selected_nodes list to match list widget selection
            new_selection = []
            for item in selected_items:
                node_label = item.text().split(" - ")[0]
                node = self.find_node_by_label(node_label)
                if node:
                    new_selection.append(node)
            
            # Also update FreeCAD selection
            Gui.Selection.clearSelection()
            for node in new_selection:
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
        # Update node list
        self.node_list.clear()
        for node in self.selected_nodes:
            x = getattr(node, "X", 0.0)
            y = getattr(node, "Y", 0.0)
            z = getattr(node, "Z", 0.0)
            
            item_text = f"{node.Label} - ({x.Value:.1f}, {y.Value:.1f}, {z.Value:.1f}) mm"
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

    def set_fixed(self):
        """Set fixed boundary condition (all DOFs constrained)"""
        self.dx_check.setChecked(True)
        self.dy_check.setChecked(True)
        self.dz_check.setChecked(True)
        self.rx_check.setChecked(True)
        self.ry_check.setChecked(True)
        self.rz_check.setChecked(True)

    def set_pinned(self):
        """Set pinned boundary condition (translation constrained)"""
        self.dx_check.setChecked(True)
        self.dy_check.setChecked(True)
        self.dz_check.setChecked(True)
        self.rx_check.setChecked(False)
        self.ry_check.setChecked(False)
        self.rz_check.setChecked(False)

    def set_roller(self):
        """Set roller boundary condition (vertical constrained only)"""
        self.dx_check.setChecked(False)
        self.dy_check.setChecked(False)
        self.dz_check.setChecked(True)
        self.rx_check.setChecked(False)
        self.ry_check.setChecked(False)
        self.rz_check.setChecked(False)

    def create_or_modify_boundary_condition(self):
        """Create new or modify existing boundary condition"""
        if not self.selected_nodes:
            QtGui.QMessageBox.warning(self.form, "Warning", "Please select at least one node.")
            return False

        # Get fixity settings
        fixity = (
            self.dx_check.isChecked(),
            self.dy_check.isChecked(),
            self.dz_check.isChecked(),
            self.rx_check.isChecked(),
            self.ry_check.isChecked(),
            self.rz_check.isChecked()
        )

        # Get visual properties
        scale = self.scale_spin.value()

        if self.is_modification_mode:
            # Modify existing boundary condition
            return self.modify_boundary_condition(fixity, scale)
        else:
            # Create new boundary condition
            return self.create_boundary_condition(fixity, scale)

    def create_boundary_condition(self, fixity, scale):
        """Create a new boundary condition"""
        bc = create_boundary_condition(nodes=self.selected_nodes, fixity=fixity)
        if bc:
            bc.Scale = scale
            bc.Label = f"BC_{len(self.selected_nodes)}nodes"
            return True
        return False

    def modify_boundary_condition(self, fixity, scale):
        """Modify an existing boundary condition"""
        try:
            bc = self.boundary_condition_to_modify
            
            # Update nodes
            bc.Nodes = self.selected_nodes
            
            # Update fixity
            bc.Dx, bc.Dy, bc.Dz, bc.Rx, bc.Ry, bc.Rz = fixity
            
            # Update scale
            bc.Scale = scale

            return True
            
        except Exception as e:
            App.Console.PrintError(f"Error modifying boundary condition: {str(e)}\n")
            return False

    def apply_changes(self):
        """Apply button handler - create or modify boundary condition"""
        #self.stop_picking()
        if self.create_or_modify_boundary_condition():
            if self.is_modification_mode:
                QtGui.QMessageBox.information(self.form, "Success", "Boundary condition modified successfully.")
                # Close dialog after successful modification
                Gui.Control.closeDialog()
            else:
                QtGui.QMessageBox.information(self.form, "Success", "Boundary condition created successfully.")
                # Clear selection for next boundary condition in creation mode
                self.clear_selection()

    def getStandardButtons(self):
        """Return standard buttons for task panel"""
        if self.is_modification_mode:
            return QtGui.QDialogButtonBox.Apply | QtGui.QDialogButtonBox.Close
        else:
            return QtGui.QDialogButtonBox.Apply | QtGui.QDialogButtonBox.Close

    def clicked(self, button):
        """Handle button clicks"""
        if button == QtGui.QDialogButtonBox.Apply:
            self.apply_changes()
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
        if self.create_or_modify_boundary_condition():
            Gui.Control.closeDialog()
            return True
        return False


class BoundarySelectionCallback:
    """Callback class for handling boundary condition selection events"""

    def __init__(self, task_panel):
        self.task_panel = task_panel

    def addSelection(self, doc_name, obj_name, sub_name, pos):
        """Called when an object is selected"""
        self.task_panel.process_selection(doc_name, obj_name)


def show_boundary_condition_creator(boundary_condition=None):
    """Show the boundary condition creator task panel"""
    # Close any existing task panel first
    if hasattr(Gui, 'Control') and Gui.Control.activeDialog():
        Gui.Control.closeDialog()
    
    panel = BoundaryConditionCreatorTaskPanel(boundary_condition=boundary_condition)
    
    # If not in modification mode, check if there are any selected nodes in FreeCAD
    if not boundary_condition:
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