# ui/dialog_AccelerationLoad.py
from PySide import QtGui, QtCore
from pivy import coin
import FreeCAD as App
import FreeCADGui as Gui
from features.FEMVisualization import FEMVisualization
from features.LoadManager import LoadManager

class AccelerationLoadTaskPanel:
    """Task panel for creating Acceleration Loads with boundary condition style selection"""

    def __init__(self, selected_beams=None, acceleration_load_to_modify=None):
        self.form = QtGui.QWidget()
        self.form.setWindowTitle("Create Acceleration Load")
        self.selected_beams = selected_beams or []
        self.selection_callback = None
        self.is_picking = False
        self.temp_selected_beams = []
        self.preview_node = coin.SoSeparator()
        self.acceleration_load_to_modify = acceleration_load_to_modify
        self.is_modification_mode = acceleration_load_to_modify is not None

        self.setup_ui()
        self.update_load_id_combo()

        # Load existing data if in modification mode
        if self.is_modification_mode:
            self.load_acceleration_load_data()
            self.form.setWindowTitle("Modify Acceleration Load")
        else:
            # Check for pre-selected beams
            if not self.selected_beams:
                current_selection = Gui.Selection.getSelection()
                for obj in current_selection:
                    if self.is_valid_beam(obj):
                        self.selected_beams.append(obj)

        self.update_display()

        # Add preview to scene
        if App.GuiUp:
            Gui.ActiveDocument.ActiveView.getSceneGraph().addChild(self.preview_node)

        # Preview timer
        self.preview_timer = QtCore.QTimer()
        self.preview_timer.timeout.connect(self.update_preview)
        self.preview_timer.start(200)

    def setup_ui(self):
        layout = QtGui.QVBoxLayout(self.form)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Title - show different title for modification mode
        if self.is_modification_mode:
            title = QtGui.QLabel("Modify Acceleration Load")
        else:
            title = QtGui.QLabel("Create Acceleration Load")
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

        # Application Scope
        scope_group = QtGui.QGroupBox("Application Scope")
        scope_layout = QtGui.QVBoxLayout()

        self.scope_combo = QtGui.QComboBox()
        self.scope_combo.addItem("Whole Model")
        self.scope_combo.addItem("Selected Beams Only")

        # Set initial scope based on whether we have selected beams
        if self.selected_beams:
            self.scope_combo.setCurrentIndex(1)  # Selected Beams Only
        else:
            self.scope_combo.setCurrentIndex(0)  # Whole Model

        self.scope_combo.currentIndexChanged.connect(self.on_scope_changed)
        scope_layout.addWidget(self.scope_combo)

        scope_group.setLayout(scope_layout)
        layout.addWidget(scope_group)

        # Beam selection (only visible when scope is "Selected Beams Only")
        self.beam_group = QtGui.QGroupBox("Beam Selection")
        beam_layout = QtGui.QVBoxLayout()

        # Selection info
        self.selection_info = QtGui.QLabel("No beams selected")
        self.selection_info.setStyleSheet("font-weight: bold; color: blue;")
        beam_layout.addWidget(self.selection_info)

        # Beam list
        self.beam_list = QtGui.QListWidget()
        self.beam_list.setSelectionMode(QtGui.QListWidget.ExtendedSelection)
        self.beam_list.setMaximumHeight(120)
        self.beam_list.itemSelectionChanged.connect(self.on_beam_selection_changed)
        beam_layout.addWidget(self.beam_list)

        button_layout = QtGui.QHBoxLayout()
        self.pick_button = QtGui.QPushButton("Pick Beams")
        self.pick_button.clicked.connect(self.toggle_picking)
        self.clear_button = QtGui.QPushButton("Clear Selection")
        self.clear_button.clicked.connect(self.clear_selection)

        button_layout.addWidget(self.pick_button)
        button_layout.addWidget(self.clear_button)
        beam_layout.addLayout(button_layout)

        self.beam_group.setLayout(beam_layout)
        layout.addWidget(self.beam_group)

        # Load Values - Only Linear Acceleration
        load_group = QtGui.QGroupBox("Linear Acceleration (g=9.81m/s²)")
        load_layout = QtGui.QGridLayout()

        for i, coord in enumerate(["X", "Y", "Z"]):
            load_layout.addWidget(QtGui.QLabel(f"{coord}:"), i, 0)
            spinbox = QtGui.QDoubleSpinBox()
            spinbox.setRange(-1e6, 1e6)
            spinbox.setSingleStep(1)
            spinbox.setDecimals(2)
            spinbox.setValue(0.0)
            spinbox.valueChanged.connect(self.update_preview)
            setattr(self, f"linear_{coord.lower()}_input", spinbox)
            load_layout.addWidget(spinbox, i, 1)

        load_group.setLayout(load_layout)
        layout.addWidget(load_group)

        layout.addStretch()

        # Initial visibility setup
        self.update_beam_selection_visibility()

    def update_beam_selection_visibility(self):
        """Show or hide beam selection based on scope"""
        if self.scope_combo.currentIndex() == 0:  # Whole Model
            self.beam_group.setVisible(False)
        else:  # Selected Beams Only
            self.beam_group.setVisible(True)

    def load_acceleration_load_data(self):
        """Load existing acceleration load data for modification"""
        if not self.acceleration_load_to_modify:
            return

        # Load beams
        if hasattr(self.acceleration_load_to_modify, 'Beams') and self.acceleration_load_to_modify.Beams:
            self.selected_beams = list(self.acceleration_load_to_modify.Beams)

        # Set scope based on whether beams are defined
        if self.selected_beams:
            self.scope_combo.setCurrentIndex(1)  # Selected Beams Only
        else:
            self.scope_combo.setCurrentIndex(0)  # Whole Model

        # Load linear acceleration values
        if hasattr(self.acceleration_load_to_modify, 'LinearAcceleration'):
            linear_acc = self.acceleration_load_to_modify.LinearAcceleration
            self.linear_x_input.setValue(linear_acc.x)
            self.linear_y_input.setValue(linear_acc.y)
            self.linear_z_input.setValue(linear_acc.z)

        # Update display and visibility
        self.update_display()
        self.update_beam_selection_visibility()

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

    def on_scope_changed(self, index):
        """Handle scope change"""
        if index == 0:  # Whole Model
            # Clear beam selection when switching to whole model
            self.selected_beams = []
            Gui.Selection.clearSelection()
        # For "Selected Beams Only", keep current selection if any

        self.update_display()
        self.update_beam_selection_visibility()

    def is_valid_beam(self, obj):
        """Check if object is a valid beam"""
        return hasattr(obj, "Type") and obj.Type == "BeamFeature"

    def toggle_picking(self):
        """Toggle picking mode on/off"""
        if self.is_picking:
            self.stop_picking()
        else:
            self.start_picking()

    def start_picking(self):
        """Start picking beams using FreeCAD selection"""
        # Only allow picking when scope is "Selected Beams Only"
        if self.scope_combo.currentIndex() != 1:
            QtGui.QMessageBox.warning(self.form, "Warning", "Please select 'Selected Beams Only' scope to pick beams.")
            return

        Gui.Selection.clearSelection()

        # Add already selected beams to FreeCAD selection for visual feedback
        for beam in self.selected_beams:
            Gui.Selection.addSelection(beam)

        self.pick_button.setStyleSheet("font-weight: bold; background-color: lightgreen")
        self.pick_button.setText("Finish Selection")
        self.is_picking = True

        # Set up selection callback
        self.selection_callback = AccelerationLoadSelectionCallback(self)
        Gui.Selection.addObserver(self.selection_callback)

    def stop_picking(self):
        """Stop picking beams and process the selection"""
        if self.selection_callback:
            Gui.Selection.removeObserver(self.selection_callback)
            self.selection_callback = None

        # Get current FreeCAD selection and update our beam list
        current_selection = Gui.Selection.getSelection()
        self.selected_beams = []

        for obj in current_selection:
            if self.is_valid_beam(obj):
                if obj not in self.selected_beams:
                    self.selected_beams.append(obj)

        self.update_display()

        self.pick_button.setStyleSheet("")
        self.pick_button.setText("Pick Beams")
        self.is_picking = False
        self.temp_selected_beams = []

    def process_selection(self, doc_name, obj_name):
        """Process individual selection events"""
        try:
            doc = App.getDocument(doc_name)
            if not doc:
                return

            obj = doc.getObject(obj_name)
            if not obj:
                return

            if self.is_valid_beam(obj):
                # During picking, we only update the visual selection in FreeCAD
                # The actual selection is only updated when user clicks "Finish Selection"
                pass

        except Exception as e:
            print(f"Error processing selection: {e}")

    def on_beam_selection_changed(self):
        """Handle beam list selection changes"""
        selected_items = self.beam_list.selectedItems()
        if selected_items:
            # Update FreeCAD selection to match list widget selection
            Gui.Selection.clearSelection()
            for item in selected_items:
                beam_label = item.text().split(" - ")[0]
                beam = self.find_beam_by_label(beam_label)
                if beam:
                    Gui.Selection.addSelection(beam)

    def find_beam_by_label(self, label):
        """Find beam object by label"""
        doc = App.ActiveDocument
        if not doc:
            return None

        # Check in Beams group
        beams_group = doc.getObject("Beams")
        if beams_group:
            for beam in beams_group.Group:
                if beam.Label == label:
                    return beam

        return None

    def update_display(self):
        """Update the display based on current selection"""
        # Update beam list
        self.beam_list.clear()
        for beam in self.selected_beams:
            item_text = f"{beam.Label}"
            item = QtGui.QListWidgetItem(item_text)
            self.beam_list.addItem(item)

        # Update selection info based on scope
        scope_index = self.scope_combo.currentIndex()
        if scope_index == 0:  # Whole Model
            self.selection_info.setText("Applied to: whole model")
        else:  # Selected Beams Only
            count = len(self.selected_beams)
            if count == 0:
                self.selection_info.setText("No beams selected - please pick beams")
            else:
                self.selection_info.setText(f"Applied to: {count} beam(s) selected")

    def clear_selection(self):
        """Clear the beam selection"""
        self.selected_beams = []
        Gui.Selection.clearSelection()
        self.update_display()

    def update_preview(self):
        """Update the 3D preview"""
        if not hasattr(self, 'preview_node'):
            return

        # Use origin as center for preview
        center = App.Vector(0, 0, 0)

        linear_acc = App.Vector(
            self.linear_x_input.value(),
            self.linear_y_input.value(),
            self.linear_z_input.value()
        )

        self.preview_node.removeAllChildren()

        # Show linear acceleration arrow from origin
        if linear_acc.Length > 1e-6:
            arrow = FEMVisualization.create_force_arrow(
                linear_acc, center,
                scale=1000,
                color=(1.0, 0.0, 0.0)
            )
            self.preview_node.addChild(arrow)

    def get_current_load_id(self):
        """Get the currently selected Load ID"""
        if self.load_id_combo.currentData():
            return self.load_id_combo.currentData()
        else:
            QtGui.QMessageBox.warning(self.form, "Error", "Please select or create a Load ID first.")
            return None

    def create_acceleration_load(self):
        """Create a new acceleration load"""
        load_id = self.get_current_load_id()
        if not load_id:
            return False

        linear_acc = App.Vector(
            self.linear_x_input.value(),
            self.linear_y_input.value(),
            self.linear_z_input.value()
        )

        scope = self.scope_combo.currentText()
        selected_beams = self.selected_beams if scope == "Selected Beams Only" else None

        # Validation for Selected Beams Only scope
        if scope == "Selected Beams Only" and not self.selected_beams:
            QtGui.QMessageBox.warning(self.form, "Warning", "Please select at least one beam for 'Selected Beams Only' scope.")
            return False

        try:
            LoadManager.create_acceleration_load(
                load_id=load_id,
                linear_acceleration=linear_acc,
                beams=selected_beams
            )
            return True
        except Exception as e:
            QtGui.QMessageBox.critical(self.form, "Error", f"Failed to create acceleration load:\n{str(e)}")
            return False

    def modify_acceleration_load(self):
        """Modify an existing acceleration load"""
        try:
            al = self.acceleration_load_to_modify

            # Update scope and beams
            scope = self.scope_combo.currentText()
            if scope == "Whole Model":
                al.Beams = []
            else:  # Selected Beams Only
                al.Beams = self.selected_beams

            # Update linear acceleration
            al.LinearAcceleration = App.Vector(
                self.linear_x_input.value(),
                self.linear_y_input.value(),
                self.linear_z_input.value()
            )

            return True

        except Exception as e:
            App.Console.PrintError(f"Error modifying acceleration load: {str(e)}\n")
            return False

    def apply_changes(self):
        """Create or modify acceleration load"""
        if self.is_modification_mode:
            success = self.modify_acceleration_load()
            if success:
                QtGui.QMessageBox.information(self.form, "Success", "Acceleration load modified successfully.")
                return True
        else:
            success = self.create_acceleration_load()
            if success:
                QtGui.QMessageBox.information(self.form, "Success", "Acceleration load created successfully.")
                # Clear selection for next creation
                if self.scope_combo.currentIndex() == 1:  # Selected Beams Only
                    self.clear_selection()
                return True

        return False

    def cleanup(self):
        """Clean up resources including preview"""
        if self.is_picking:
            self.stop_picking()

        self.preview_timer.stop()
        if hasattr(self, 'preview_node') and App.GuiUp:
            Gui.ActiveDocument.ActiveView.getSceneGraph().removeChild(self.preview_node)

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


class AccelerationLoadSelectionCallback:
    """Callback class for handling acceleration load selection events"""

    def __init__(self, task_panel):
        self.task_panel = task_panel

    def addSelection(self, doc_name, obj_name, sub_name, pos):
        """Called when an object is selected"""
        self.task_panel.process_selection(doc_name, obj_name)


def show_acceleration_load_creator(selected_beams=None, acceleration_load_to_modify=None):
    """Show the acceleration load creator task panel"""
    # Close any existing task panel first
    if hasattr(Gui, 'Control') and Gui.Control.activeDialog():
        Gui.Control.closeDialog()

    panel = AccelerationLoadTaskPanel(selected_beams=selected_beams, acceleration_load_to_modify=acceleration_load_to_modify)
    Gui.Control.showDialog(panel)
    return panel