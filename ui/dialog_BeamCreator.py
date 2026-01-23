import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtGui, QtCore
from features.beams import make_beams_group, BeamFeature, BeamViewProvider


class SelectionCallback:
    """Callback class for handling selection events"""

    def __init__(self, task_panel):
        self.task_panel = task_panel

    def addSelection(self, doc_name, obj_name, sub_name, pos):
        """Called when an object is selected"""
        self.task_panel.process_selection(doc_name, obj_name)


class BeamCreatorTaskPanel:
    """Task panel for creating beams"""

    def __init__(self):
        self.form = QtGui.QWidget()
        self.form.setWindowTitle("Beam Creator")
        self.current_selection_field = None
        self.selection_callback = None
        self.chain_mode = False
        self.setup_ui()
        self.populate_node_combo(self.start_node_combo)
        self.populate_node_combo(self.end_node_combo)
        self.populate_section_combo()
        self.populate_member_release_combo()
        self.populate_material_combo()

    def setup_ui(self):
        layout = QtGui.QVBoxLayout(self.form)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Node selection
        node_group = QtGui.QGroupBox("Node Selection")
        node_layout = QtGui.QGridLayout()
        node_layout.setSpacing(6)

        # Start Node
        node_layout.addWidget(QtGui.QLabel("Start Node:"), 0, 0)
        start_node_widget = QtGui.QWidget()
        start_node_layout = QtGui.QHBoxLayout(start_node_widget)
        start_node_layout.setContentsMargins(0, 0, 0, 0)
        start_node_layout.setSpacing(4)

        self.start_node_combo = QtGui.QComboBox()
        self.start_node_combo.setEditable(True)
        self.start_node_combo.setInsertPolicy(QtGui.QComboBox.NoInsert)
        start_node_layout.addWidget(self.start_node_combo)

        self.start_node_pick_btn = QtGui.QPushButton("Pick")
        self.start_node_pick_btn.clicked.connect(lambda: self.start_picking("start"))
        start_node_layout.addWidget(self.start_node_pick_btn)

        node_layout.addWidget(start_node_widget, 0, 1)

        # End Node
        node_layout.addWidget(QtGui.QLabel("End Node:"), 1, 0)
        end_node_widget = QtGui.QWidget()
        end_node_layout = QtGui.QHBoxLayout(end_node_widget)
        end_node_layout.setContentsMargins(0, 0, 0, 0)
        end_node_layout.setSpacing(4)

        self.end_node_combo = QtGui.QComboBox()
        self.end_node_combo.setEditable(True)
        self.end_node_combo.setInsertPolicy(QtGui.QComboBox.NoInsert)
        end_node_layout.addWidget(self.end_node_combo)

        self.end_node_pick_btn = QtGui.QPushButton("Pick")
        self.end_node_pick_btn.clicked.connect(lambda: self.start_picking("end"))
        end_node_layout.addWidget(self.end_node_pick_btn)

        node_layout.addWidget(end_node_widget, 1, 1)

        node_group.setLayout(node_layout)
        layout.addWidget(node_group)

        # Section selection
        section_group = QtGui.QGroupBox("Section Properties")
        section_layout = QtGui.QVBoxLayout()
        section_layout.setSpacing(6)

        self.section_combo = QtGui.QComboBox()
        section_layout.addWidget(self.section_combo)

        # Material selection
        material_group = QtGui.QGroupBox("Material Properties")
        material_layout = QtGui.QVBoxLayout()

        self.material_combo = QtGui.QComboBox()
        material_layout.addWidget(self.material_combo)
        self.material_combo.currentIndexChanged.connect(self.update_material_info)

        # Material info display
        self.material_info_label = QtGui.QLabel("No material selected")
        self.material_info_label.setWordWrap(True)
        self.material_info_label.setStyleSheet("color: gray; font-style: italic;")
        material_layout.addWidget(self.material_info_label)

        material_group.setLayout(material_layout)
        section_layout.addWidget(material_group)

        # Member Release selection
        member_release_group = QtGui.QGroupBox("Member End Releases")
        member_release_layout = QtGui.QVBoxLayout()
        member_release_layout.setSpacing(6)

        self.member_release_combo = QtGui.QComboBox()
        self.member_release_combo.addItem("None (Fully Fixed)", None)  # Default option
        member_release_layout.addWidget(self.member_release_combo)

        # Display current release info
        self.release_info_label = QtGui.QLabel("No member release selected")
        self.release_info_label.setWordWrap(True)
        self.release_info_label.setStyleSheet("color: gray; font-style: italic;")
        member_release_layout.addWidget(self.release_info_label)

        member_release_group.setLayout(member_release_layout)
        section_layout.addWidget(member_release_group)

        # Color selection
        color_group = QtGui.QGroupBox("Appearance")
        color_layout = QtGui.QGridLayout()
        color_layout.setSpacing(6)

        color_layout.addWidget(QtGui.QLabel("Flange Color:"), 0, 0)
        self.flange_color = QtGui.QPushButton()
        self.flange_color.clicked.connect(lambda: self.choose_color("flange"))
        self.flange_color.setStyleSheet("background-color: rgb(51, 128, 204)")
        color_layout.addWidget(self.flange_color, 0, 1)

        color_group.setLayout(color_layout)
        section_layout.addWidget(color_group)

        section_group.setLayout(section_layout)
        layout.addWidget(section_group)

        # Options group
        options_group = QtGui.QGroupBox("Creation Options")
        options_layout = QtGui.QVBoxLayout()
        options_layout.setSpacing(8)

        # Auto-create checkbox
        self.auto_create_checkbox = QtGui.QCheckBox("Auto-create beam when both nodes are picked")
        self.auto_create_checkbox.setChecked(True)
        options_layout.addWidget(self.auto_create_checkbox)

        # Chain mode checkbox
        self.chain_mode_checkbox = QtGui.QCheckBox("Chain node mode")
        self.chain_mode_checkbox.stateChanged.connect(self.toggle_chain_mode)
        options_layout.addWidget(self.chain_mode_checkbox)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Add stretch before buttons to push them to the bottom
        layout.addStretch()

        # Button box placeholder (standard buttons are added by FreeCAD Gui)
        self.button_box = QtGui.QDialogButtonBox()
        layout.addWidget(self.button_box)

        # Connect member release combo change
        self.member_release_combo.currentIndexChanged.connect(self.update_release_info)

        # Set minimum width to ensure all elements are visible
        self.form.setMinimumWidth(450)

    def populate_material_combo(self):
        """Populate the material combo box with available materials"""
        self.material_combo.clear()
        doc = App.ActiveDocument
        if not doc:
            return

        # Look for Materials group
        materials_group = doc.getObject("Materials")
        if materials_group:
            for material_obj in materials_group.Group:
                if hasattr(material_obj, "Type") and material_obj.Type == "MaterialFeature":
                    self.material_combo.addItem(material_obj.Label, material_obj)

        # Update info for current selection
        self.update_material_info()

    def update_material_info(self):
        """Update the material information display"""
        current_data = self.material_combo.currentData()
        if current_data is None:
            self.material_info_label.setText("No material selected")
            self.material_info_label.setStyleSheet("color: gray; font-style: italic;")
        elif hasattr(current_data, 'Proxy'):
            try:
                material_type = getattr(current_data, "MaterialType", "Unknown")
                steel_grade = getattr(current_data, "SteelGrade", "")
                youngs_modulus = getattr(current_data, "YoungsModulus", 0)

                if material_type == "Steel" and steel_grade:
                    info = f"Steel {steel_grade} - E={youngs_modulus:,.0f} MPa"
                else:
                    info = f"{material_type} - E={youngs_modulus:,.0f} MPa"

                self.material_info_label.setText(f"Selected: {info}")
                self.material_info_label.setStyleSheet("color: black; font-style: normal;")
            except Exception as e:
                self.material_info_label.setText(f"Selected: {current_data.Label}")
                self.material_info_label.setStyleSheet("color: black; font-style: normal;")
        else:
            self.material_info_label.setText("No material selected")
            self.material_info_label.setStyleSheet("color: gray; font-style: italic;")

    def populate_member_release_combo(self):
        """Populate the member release combo box with available releases"""
        self.member_release_combo.clear()
        self.member_release_combo.addItem("None (Fully Fixed)", None)  # Default option

        doc = App.ActiveDocument
        if not doc:
            return

        # Look for MemberReleases group
        member_releases_group = doc.getObject("MemberReleases")
        if member_releases_group:
            for release_obj in member_releases_group.Group:
                if hasattr(release_obj, "Type") and release_obj.Type == "MemberRelease":
                    self.member_release_combo.addItem(release_obj.Label, release_obj)

        # Update info for current selection
        self.update_release_info()

    def update_release_info(self):
        """Update the release information display"""
        current_data = self.member_release_combo.currentData()
        if current_data is None:
            self.release_info_label.setText("No member release selected (Fully Fixed)")
            self.release_info_label.setStyleSheet("color: gray; font-style: italic;")
        elif hasattr(current_data, 'Proxy'):
            try:
                description = current_data.Proxy.get_release_description()
                self.release_info_label.setText(f"Selected: {description}")
                self.release_info_label.setStyleSheet("color: black; font-style: normal;")
            except:
                self.release_info_label.setText(f"Selected: {current_data.Label}")
                self.release_info_label.setStyleSheet("color: black; font-style: normal;")
        else:
            self.release_info_label.setText("No member release selected")
            self.release_info_label.setStyleSheet("color: gray; font-style: italic;")

    def create_new_member_release(self):
        """Open dialog to create a new member release"""
        from features.member_releases import create_member_release_dialog
        new_release = create_member_release_dialog()
        if new_release:
            # Refresh the combo box and select the new release
            self.populate_member_release_combo()
            index = self.member_release_combo.findText(new_release.Label)
            if index >= 0:
                self.member_release_combo.setCurrentIndex(index)

    def toggle_chain_mode(self, state):
        """Toggle chain node mode"""
        self.chain_mode = state == QtCore.Qt.Checked
        if self.chain_mode and self.end_node_combo.currentText():
            # If chain mode is enabled and we have an end node, set it as start node
            self.start_node_combo.setCurrentText(self.end_node_combo.currentText())

    def start_picking(self, field_type):
        """Start picking mode for the specified field"""
        # Remove any existing selection callback
        if self.selection_callback:
            Gui.Selection.removeObserver(self.selection_callback)
            self.selection_callback = None

        self.current_selection_field = field_type

        # Change button appearance to indicate picking mode (bold text)
        if field_type == "start":
            self.start_node_pick_btn.setStyleSheet("font-weight: bold;")
            self.end_node_pick_btn.setStyleSheet("")
        else:
            self.end_node_pick_btn.setStyleSheet("font-weight: bold;")
            self.start_node_pick_btn.setStyleSheet("")

        # Set up selection callback
        self.selection_callback = SelectionCallback(self)
        Gui.Selection.addObserver(self.selection_callback)

        # Clear selection to ensure we get fresh events
        Gui.Selection.clearSelection()

    def process_selection(self, doc_name, obj_name):
        """Process the selected object"""
        if not self.current_selection_field:
            return

        try:
            doc = App.getDocument(doc_name)
            if not doc:
                return

            obj = doc.getObject(obj_name)
            if not obj:
                return

            # Check if it's a node feature
            if hasattr(obj, "Type") and obj.Type == "NodeFeature":
                node_name = obj.Label

                if self.current_selection_field == "start":
                    self.set_combo_text(self.start_node_combo, node_name)
                    # Remove current callback and set up new one for end node
                    if self.selection_callback:
                        Gui.Selection.removeObserver(self.selection_callback)
                        self.selection_callback = None

                    # Set up new callback for end node
                    self.current_selection_field = "end"
                    self.start_node_pick_btn.setStyleSheet("")
                    self.end_node_pick_btn.setStyleSheet("font-weight: bold;")
                    self.selection_callback = SelectionCallback(self)
                    Gui.Selection.addObserver(self.selection_callback)

                else:
                    self.set_combo_text(self.end_node_combo, node_name)

                    # Auto-create beam if enabled and both nodes are selected
                    if (self.auto_create_checkbox.isChecked() and
                            self.start_node_combo.currentText() and
                            self.end_node_combo.currentText()):
                        success = self.create_beam()

                        # If chain mode is enabled and beam was created successfully
                        if success and self.chain_mode:
                            self.start_node_combo.setCurrentText(self.end_node_combo.currentText())
                            self.end_node_combo.setCurrentText("")
                            # Stay in end node picking mode for next beam
                            self.current_selection_field = "end"
                            self.start_node_pick_btn.setStyleSheet("")
                            self.end_node_pick_btn.setStyleSheet("font-weight: bold;")
                            return

                    # Exit picking mode if not in chain mode or auto-create failed
                    self.current_selection_field = None
                    self.start_node_pick_btn.setStyleSheet("")
                    self.end_node_pick_btn.setStyleSheet("")

                    # Remove selection callback
                    if self.selection_callback:
                        Gui.Selection.removeObserver(self.selection_callback)
                        self.selection_callback = None

            else:
                print("Selected object is not a NodeFeature")

        except Exception as e:
            print(f"Error processing selection: {e}")

    def set_combo_text(self, combo, text):
        """Set combo box text, adding to list if not present"""
        index = combo.findText(text)
        if index >= 0:
            combo.setCurrentIndex(index)
        else:
            combo.addItem(text)
            combo.setCurrentIndex(combo.count() - 1)

    def populate_section_combo(self):
        self.section_combo.clear()
        doc = App.ActiveDocument
        sections_group = doc.getObject("Sections")
        if sections_group:
            for section in sections_group.Group:
                if hasattr(section, "Proxy"):
                    self.section_combo.addItem(section.Label, section)

    def populate_node_combo(self, combo):
        combo.clear()
        doc = App.ActiveDocument
        nodes_group = doc.getObject("Nodes")
        if nodes_group:
            for node in nodes_group.Group:
                if hasattr(node, "Proxy") and node.Type == "NodeFeature":
                    combo.addItem(node.Label, node)

    def choose_color(self, which):
        color = QtGui.QColorDialog.getColor()
        if color.isValid():
            if which == "flange":
                self.flange_color.setStyleSheet(f"background-color: {color.name()}")

    def create_beam(self):
        """Create beam with current settings"""
        start_node_name = self.start_node_combo.currentText()
        end_node_name = self.end_node_combo.currentText()
        section = self.section_combo.itemData(self.section_combo.currentIndex())
        member_release = self.member_release_combo.currentData()
        material = self.material_combo.currentData()
        if not start_node_name or not end_node_name or start_node_name == end_node_name:
            # Optionally show a warning message here if this function is called manually
            return False

        # Find node objects by name
        doc = App.ActiveDocument
        nodes_group = doc.getObject("Nodes")
        start_node = None
        end_node = None
        if nodes_group:
            for node in nodes_group.Group:
                if node.Label == start_node_name:
                    start_node = node
                if node.Label == end_node_name:
                    end_node = node

        if not start_node or not end_node:
            return False
        group = make_beams_group()
        beam = App.ActiveDocument.addObject("App::FeaturePython", "Beam")
        BeamFeature(beam)
        BeamViewProvider(beam.ViewObject)
        beam.StartNode = start_node
        beam.EndNode = end_node
        beam.Section = section
        beam.MemberRelease = member_release
        beam.Material = material
        # Set buckling and effective lengths initially equal to beam length
        beam.BucklingLengthY = beam.Length
        beam.BucklingLengthZ = beam.Length
        beam.EffectiveLengthY = beam.Length
        beam.EffectiveLengthZ = beam.Length
        beam.Label = f"Beam_{start_node.Label}_{end_node.Label}"
        group.addObject(beam)
        return True

    def apply(self):
        """Apply button handler - create beam but don't close panel"""
        # Ensure that picking mode is stopped before attempting to create the beam
        if self.selection_callback:
            Gui.Selection.removeObserver(self.selection_callback)
            self.selection_callback = None

        if self.create_beam():
            # If chain mode is enabled, set end node as start node for next beam
            if self.chain_mode:
                self.start_node_combo.setCurrentText(self.end_node_combo.currentText())
                self.end_node_combo.setCurrentText("")

            # Clear selection mode if active
            self.current_selection_field = None
            self.start_node_pick_btn.setStyleSheet("")
            self.end_node_pick_btn.setStyleSheet("")

    def getStandardButtons(self):
        """Define the standard buttons for the task panel"""
        # Use Apply to create without closing, and Close to close
        return QtGui.QDialogButtonBox.Apply | QtGui.QDialogButtonBox.Close

    def clicked(self, button):
        """Handle standard button clicks (Apply and Close)"""
        # Close button is clicked
        if button == QtGui.QDialogButtonBox.Close:
            self.reject()  # Cleanup
            Gui.Control.closeDialog()  # Close the task panel

        # Apply button is clicked
        elif button == QtGui.QDialogButtonBox.Apply:
            self.apply()  # Create beam and handle chain mode
            App.ActiveDocument.recompute()

        return True  # Indicate that the dialog is ready to handle the action

    def accept(self):
        """OK handler (unused but kept for FreeCAD structure)"""
        return True

    def reject(self):
        """Cancel/Close button handler - cleanup"""
        # Remove selection callback if active
        if self.selection_callback:
            Gui.Selection.removeObserver(self.selection_callback)
            self.selection_callback = None

        # Ensure pick buttons are unstyled
        self.current_selection_field = None
        self.start_node_pick_btn.setStyleSheet("")
        self.end_node_pick_btn.setStyleSheet("")
        return True