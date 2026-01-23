# ui/dialog_BeamModifier.py
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtGui, QtCore
from features.beams import get_all_beams


class BeamModifierTaskPanel:
    """Task panel for modifying existing beams"""

    def __init__(self):
        self.form = QtGui.QWidget()
        self.form.setWindowTitle("Modify Beams")
        self.form.resize(600, 500)
        
        self.selected_beams = []
        self.selection_callback = None
        self.is_picking = False
        
        self.setup_ui()
        self.populate_section_combo()
        self.populate_material_combo()
        self.populate_member_release_combo()

    def setup_ui(self):
        layout = QtGui.QVBoxLayout(self.form)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Title
        title = QtGui.QLabel("Modify Existing Beams")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)

        # 1. Beam selection
        selection_group = QtGui.QGroupBox("Beam Selection")
        selection_layout = QtGui.QVBoxLayout()

        # Selection info
        self.selection_info = QtGui.QLabel("No beams selected")
        self.selection_info.setStyleSheet("font-weight: bold; color: blue;")
        selection_layout.addWidget(self.selection_info)

        # Beam list - limited height to show only 5 items
        self.beam_list = QtGui.QListWidget()
        self.beam_list.setSelectionMode(QtGui.QListWidget.ExtendedSelection)
        self.beam_list.setMaximumHeight(50)  
        self.beam_list.itemSelectionChanged.connect(self.on_beam_selection_changed)
        selection_layout.addWidget(self.beam_list)

        # Selection buttons
        button_layout = QtGui.QHBoxLayout()
        self.pick_button = QtGui.QPushButton("Pick Beams")
        self.pick_button.clicked.connect(self.toggle_picking)
        self.clear_button = QtGui.QPushButton("Clear Selection")
        self.clear_button.clicked.connect(self.clear_selection)
        self.select_all_btn = QtGui.QPushButton("Select All")
        self.select_all_btn.clicked.connect(self.select_all_beams)

        button_layout.addWidget(self.pick_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.select_all_btn)
        selection_layout.addLayout(button_layout)

        selection_group.setLayout(selection_layout)
        layout.addWidget(selection_group)

        # 2. Properties group
        properties_group = QtGui.QGroupBox("Properties")
        properties_layout = QtGui.QGridLayout()
        properties_layout.setSpacing(8)

        # Section
        properties_layout.addWidget(QtGui.QLabel("Section:"), 0, 0)
        self.section_combo = QtGui.QComboBox()
        properties_layout.addWidget(self.section_combo, 0, 1)

        # Material
        properties_layout.addWidget(QtGui.QLabel("Material:"), 1, 0)
        material_widget = QtGui.QWidget()
        material_widget_layout = QtGui.QVBoxLayout(material_widget)
        material_widget_layout.setContentsMargins(0, 0, 0, 0)
        
        self.material_combo = QtGui.QComboBox()
        material_widget_layout.addWidget(self.material_combo)
        
        self.material_info_label = QtGui.QLabel("No material selected")
        self.material_info_label.setWordWrap(True)
        self.material_info_label.setStyleSheet("color: gray; font-style: italic; font-size: 9px;")
        material_widget_layout.addWidget(self.material_info_label)
        
        properties_layout.addWidget(material_widget, 1, 1)

        # Member release
        properties_layout.addWidget(QtGui.QLabel("End Release:"), 2, 0)
        release_widget = QtGui.QWidget()
        release_widget_layout = QtGui.QVBoxLayout(release_widget)
        release_widget_layout.setContentsMargins(0, 0, 0, 0)
        
        self.member_release_combo = QtGui.QComboBox()
        self.member_release_combo.addItem("None (Fully Fixed)", None)
        release_widget_layout.addWidget(self.member_release_combo)
        
        self.release_info_label = QtGui.QLabel("No member release selected")
        self.release_info_label.setWordWrap(True)
        self.release_info_label.setStyleSheet("color: gray; font-style: italic; font-size: 9px;")
        release_widget_layout.addWidget(self.release_info_label)
        
        properties_layout.addWidget(release_widget, 2, 1)

        # Member type
        properties_layout.addWidget(QtGui.QLabel("Member Type:"), 3, 0)
        self.member_type_combo = QtGui.QComboBox()
        self.member_type_combo.addItems(["normal", "compression", "tension"])
        properties_layout.addWidget(self.member_type_combo, 3, 1)

        properties_group.setLayout(properties_layout)
        layout.addWidget(properties_group)

        # 3. Buckling & Torsional Buckling Lengths
        buckling_group = QtGui.QGroupBox("Buckling & Torsional Buckling Lengths (mm)")
        buckling_layout = QtGui.QGridLayout()
        buckling_layout.setSpacing(8)

        # Buckling lengths
        buckling_layout.addWidget(QtGui.QLabel("Buckling Length Y:"), 0, 0)
        self.buckling_length_y = QtGui.QLineEdit()
        self.buckling_length_y.setPlaceholderText("Leave blank to keep current")
        buckling_layout.addWidget(self.buckling_length_y, 0, 1)

        buckling_layout.addWidget(QtGui.QLabel("Buckling Length Z:"), 1, 0)
        self.buckling_length_z = QtGui.QLineEdit()
        self.buckling_length_z.setPlaceholderText("Leave blank to keep current")
        buckling_layout.addWidget(self.buckling_length_z, 1, 1)

        # Effective lengths (for lateral torsional buckling)
        buckling_layout.addWidget(QtGui.QLabel("Effective Length Y:"), 2, 0)
        self.effective_length_y = QtGui.QLineEdit()
        self.effective_length_y.setPlaceholderText("Leave blank to keep current")
        buckling_layout.addWidget(self.effective_length_y, 2, 1)

        buckling_layout.addWidget(QtGui.QLabel("Effective Length Z:"), 3, 0)
        self.effective_length_z = QtGui.QLineEdit()
        self.effective_length_z.setPlaceholderText("Leave blank to keep current")
        buckling_layout.addWidget(self.effective_length_z, 3, 1)

        buckling_group.setLayout(buckling_layout)
        layout.addWidget(buckling_group)

        layout.addStretch()

        # Connect signals
        self.material_combo.currentIndexChanged.connect(self.update_material_info)
        self.member_release_combo.currentIndexChanged.connect(self.update_release_info)

    def toggle_picking(self):
        """Toggle picking mode on/off using FreeCAD's built-in selection"""
        if self.is_picking:
            self.stop_picking()
        else:
            self.start_picking()

    def start_picking(self):
        """Start picking beams using FreeCAD selection"""
        # Clear FreeCAD selection and add currently selected beams
        Gui.Selection.clearSelection()
        
        # Add already selected beams to FreeCAD selection
        for beam in self.selected_beams:
            Gui.Selection.addSelection(beam)
        
        self.pick_button.setStyleSheet("font-weight: bold; background-color: lightgreen")
        self.pick_button.setText("Finish Selection")
        self.is_picking = True
        
        # Set up selection callback to monitor changes
        self.selection_callback = BeamSelectionCallback(self)
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
            if hasattr(obj, "Type") and obj.Type in ["BeamFeature", "ResultBeam"]:
                if obj not in self.selected_beams:
                    self.selected_beams.append(obj)
        
        self.update_display()

        self.pick_button.setStyleSheet("")
        self.pick_button.setText("Pick Beams")
        self.is_picking = False

    def process_selection(self, doc_name, obj_name):
        """Process individual selection events - update property values for each new beam"""
        try:
            doc = App.getDocument(doc_name)
            if not doc:
                return

            obj = doc.getObject(obj_name)
            if not obj:
                return

            # Check if it's a beam feature and not already in our list
            if (hasattr(obj, "Type") and obj.Type in ["BeamFeature", "ResultBeam"] 
                and obj not in self.selected_beams):
                self.selected_beams.append(obj)
                # Update property values immediately for consistency
                self.update_property_inputs()

        except Exception as e:
            print(f"Error processing selection: {e}")

    def clear_selection(self):
        """Clear the beam selection"""
        self.selected_beams = []
        Gui.Selection.clearSelection()
        self.update_display()

    def select_all_beams(self):
        """Select all beams in the document"""
        self.selected_beams = get_all_beams()
        # Also select them in FreeCAD
        Gui.Selection.clearSelection()
        for beam in self.selected_beams:
            Gui.Selection.addSelection(beam)
        self.update_display()

    def on_beam_selection_changed(self):
        """Handle beam list selection changes"""
        selected_items = self.beam_list.selectedItems()
        if selected_items:
            # Update the selected_beams list to match list widget selection
            self.selected_beams = []
            for item in selected_items:
                beam_label = item.text().split(" - ")[0]
                beam = self.find_beam_by_label(beam_label)
                if beam:
                    self.selected_beams.append(beam)
            
            # Also update FreeCAD selection
            Gui.Selection.clearSelection()
            for beam in self.selected_beams:
                Gui.Selection.addSelection(beam)
            
            self.update_property_inputs()

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
                    
        # Check in Beam_Results group
        beam_results_group = doc.getObject("Beam_Results")
        if beam_results_group:
            for beam in beam_results_group.Group:
                if beam.Label == label:
                    return beam
                    
        return None

    def update_display(self):
        """Update the display based on current selection"""
        # Update beam list
        self.beam_list.clear()
        for beam in self.selected_beams:
            start_label = beam.StartNode.Label if beam.StartNode else "None"
            end_label = beam.EndNode.Label if beam.EndNode else "None"
            section_label = beam.Section.Label if beam.Section else "None"
            
            item_text = f"{beam.Label} - {start_label} to {end_label} ({section_label})"
            item = QtGui.QListWidgetItem(item_text)
            self.beam_list.addItem(item)

        # Update selection info
        count = len(self.selected_beams)
        self.selection_info.setText(f"{count} beam(s) selected")

        # Update property inputs
        self.update_property_inputs()

    def update_property_inputs(self):
        """Update property inputs based on selected beams - called for each new beam addition"""
        if not self.selected_beams:
            self.clear_property_inputs()
            return

        # Get properties of all selected beams
        sections = []
        materials = []
        member_releases = []
        buckling_lengths_y = []
        buckling_lengths_z = []
        effective_lengths_y = []
        effective_lengths_z = []
        member_types = []

        for beam in self.selected_beams:
            sections.append(beam.Section if hasattr(beam, 'Section') else None)
            materials.append(beam.Material if hasattr(beam, 'Material') else None)
            member_releases.append(beam.MemberRelease if hasattr(beam, 'MemberRelease') else None)
            buckling_lengths_y.append(getattr(beam, 'BucklingLengthY', 0.0))
            buckling_lengths_z.append(getattr(beam, 'BucklingLengthZ', 0.0))
            effective_lengths_y.append(getattr(beam, 'EffectiveLengthY', 0.0))
            effective_lengths_z.append(getattr(beam, 'EffectiveLengthZ', 0.0))
            member_types.append(getattr(beam, 'MemberType', 'normal'))

        # Update section combo - only if all beams have same section
        if all(s == sections[0] for s in sections) and sections[0]:
            index = self.section_combo.findData(sections[0])
            if index >= 0:
                self.section_combo.setCurrentIndex(index)
        else:
            self.section_combo.setCurrentIndex(0)

        # Update material combo - only if all beams have same material
        if all(m == materials[0] for m in materials) and materials[0]:
            index = self.material_combo.findData(materials[0])
            if index >= 0:
                self.material_combo.setCurrentIndex(index)
        else:
            self.material_combo.setCurrentIndex(0)

        # Update member release combo - only if all beams have same release
        if all(mr == member_releases[0] for mr in member_releases) and member_releases[0]:
            index = self.member_release_combo.findData(member_releases[0])
            if index >= 0:
                self.member_release_combo.setCurrentIndex(index)
        else:
            self.member_release_combo.setCurrentIndex(0)

        # Update buckling lengths - only if all beams have same values
        if buckling_lengths_y and all(hasattr(v, 'Value') for v in buckling_lengths_y):
            self.buckling_length_y.setText(f"{buckling_lengths_y[0].Value:.2f}" if all(v.Value == buckling_lengths_y[0].Value for v in buckling_lengths_y) else "")
        else:
            self.buckling_length_y.setText("")
            
        if buckling_lengths_z and all(hasattr(v, 'Value') for v in buckling_lengths_z):
            self.buckling_length_z.setText(f"{buckling_lengths_z[0].Value:.2f}" if all(v.Value == buckling_lengths_z[0].Value for v in buckling_lengths_z) else "")
        else:
            self.buckling_length_z.setText("")
            
        if effective_lengths_y and all(hasattr(v, 'Value') for v in effective_lengths_y):
            self.effective_length_y.setText(f"{effective_lengths_y[0].Value:.2f}" if all(v.Value == effective_lengths_y[0].Value for v in effective_lengths_y) else "")
        else:
            self.effective_length_y.setText("")
            
        if effective_lengths_z and all(hasattr(v, 'Value') for v in effective_lengths_z):
            self.effective_length_z.setText(f"{effective_lengths_z[0].Value:.2f}" if all(v.Value == effective_lengths_z[0].Value for v in effective_lengths_z) else "")
        else:
            self.effective_length_z.setText("")

        # Update member type - only if all beams have same type
        if all(mt == member_types[0] for mt in member_types):
            index = self.member_type_combo.findText(member_types[0])
            if index >= 0:
                self.member_type_combo.setCurrentIndex(index)

        # Update info labels
        self.update_material_info()
        self.update_release_info()

    def clear_property_inputs(self):
        """Clear all property inputs"""
        self.section_combo.setCurrentIndex(0)
        self.material_combo.setCurrentIndex(0)
        self.member_release_combo.setCurrentIndex(0)
        self.buckling_length_y.clear()
        self.buckling_length_z.clear()
        self.effective_length_y.clear()
        self.effective_length_z.clear()
        self.member_type_combo.setCurrentIndex(0)
        self.material_info_label.setText("No material selected")
        self.release_info_label.setText("No member release selected")

    def populate_section_combo(self):
        """Populate the section combo box with available sections"""
        self.section_combo.clear()
        self.section_combo.addItem("Keep current section", None)
        
        doc = App.ActiveDocument
        if not doc:
            return
            
        # Look for Sections group
        sections_group = doc.getObject("Sections")
        if sections_group:
            for section_obj in sections_group.Group:
                if hasattr(section_obj, "Proxy"):
                    self.section_combo.addItem(section_obj.Label, section_obj)

    def populate_material_combo(self):
        """Populate the material combo box with available materials"""
        self.material_combo.clear()
        self.material_combo.addItem("Keep current material", None)
        
        doc = App.ActiveDocument
        if not doc:
            return
            
        # Look for Materials group
        materials_group = doc.getObject("Materials")
        if materials_group:
            for material_obj in materials_group.Group:
                if hasattr(material_obj, "Type") and material_obj.Type == "MaterialFeature":
                    self.material_combo.addItem(material_obj.Label, material_obj)

    def populate_member_release_combo(self):
        """Populate the member release combo box with available releases"""
        self.member_release_combo.clear()
        self.member_release_combo.addItem("Keep current release", None)
        self.member_release_combo.addItem("None (Fully Fixed)", "none")
        
        doc = App.ActiveDocument
        if not doc:
            return
            
        # Look for MemberReleases group
        member_releases_group = doc.getObject("MemberReleases")
        if member_releases_group:
            for release_obj in member_releases_group.Group:
                if hasattr(release_obj, "Type") and release_obj.Type == "MemberRelease":
                    self.member_release_combo.addItem(release_obj.Label, release_obj)
                    
    def sync_with_freecad_selection(self):
        """Sync the panel selection with FreeCAD's current selection"""
        current_selection = Gui.Selection.getSelection()
        self.selected_beams = []
        
        for obj in current_selection:
            if hasattr(obj, "Type") and obj.Type in ["BeamFeature", "ResultBeam"]:
                if obj not in self.selected_beams:
                    self.selected_beams.append(obj)
        
        self.update_display()
    def update_material_info(self):
        """Update the material information display"""
        current_data = self.material_combo.currentData()
        if current_data is None:
            self.material_info_label.setText("Keep current material")
            self.material_info_label.setStyleSheet("color: gray; font-style: italic;")
        elif current_data == "none":
            self.material_info_label.setText("No material (will remove material)")
            self.material_info_label.setStyleSheet("color: blue; font-style: italic;")
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

    def update_release_info(self):
        """Update the release information display"""
        current_data = self.member_release_combo.currentData()
        if current_data is None:
            self.release_info_label.setText("Keep current member release")
            self.release_info_label.setStyleSheet("color: gray; font-style: italic;")
        elif current_data == "none":
            self.release_info_label.setText("No member release (Fully Fixed)")
            self.release_info_label.setStyleSheet("color: blue; font-style: italic;")
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

    def modify_beams(self):
        """Apply property changes to selected beams"""
        if not self.selected_beams:
            QtGui.QMessageBox.warning(self.form, "Warning", "Please select at least one beam.")
            return False

        try:
            # Get current values
            section = self.section_combo.currentData()
            material = self.material_combo.currentData()
            member_release = self.member_release_combo.currentData()
            
            buckling_length_y_text = self.buckling_length_y.text().strip()
            buckling_length_z_text = self.buckling_length_z.text().strip()
            effective_length_y_text = self.effective_length_y.text().strip()
            effective_length_z_text = self.effective_length_z.text().strip()
            
            member_type = self.member_type_combo.currentText()

            # Apply changes to each selected beam
            for beam in self.selected_beams:
                if section is not None:
                    beam.Section = section
                    
                if material is not None:
                    if material == "none":
                        beam.Material = None
                    else:
                        beam.Material = material
                
                if member_release is not None:
                    if member_release == "none":
                        beam.MemberRelease = None
                    else:
                        beam.MemberRelease = member_release
                
                if buckling_length_y_text:
                    beam.BucklingLengthY = float(buckling_length_y_text)
                if buckling_length_z_text:
                    beam.BucklingLengthZ = float(buckling_length_z_text)
                if effective_length_y_text:
                    beam.EffectiveLengthY = float(effective_length_y_text)
                if effective_length_z_text:
                    beam.EffectiveLengthZ = float(effective_length_z_text)
                
                beam.MemberType = member_type

            self.update_display()  # Refresh display with new values
            
            return True

        except ValueError as e:
            QtGui.QMessageBox.warning(self.form, "Input Error", 
                                    "Please enter valid numeric values for lengths.")
            return False
        except Exception as e:
            QtGui.QMessageBox.warning(self.form, "Error", 
                                    f"An error occurred while modifying beams: {str(e)}")
            return False

    def apply_changes(self):
        """Apply button handler - modify beams"""
        return self.modify_beams()

    def getStandardButtons(self):
        """Return standard buttons for task panel"""
        return QtGui.QDialogButtonBox.Apply | QtGui.QDialogButtonBox.Close

    def clicked(self, button):
        """Handle button clicks"""
        if button == QtGui.QDialogButtonBox.Apply:
            if self.apply_changes():
                App.ActiveDocument.recompute()
                # Keep the dialog open for more modifications
                QtGui.QMessageBox.information(self.form, "Success", "Beam properties updated successfully.")
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


class BeamSelectionCallback:
    """Callback class for handling beam selection events"""

    def __init__(self, task_panel):
        self.task_panel = task_panel

    def addSelection(self, doc_name, obj_name, sub_name, pos):
        """Called when an object is selected"""
        self.task_panel.process_selection(doc_name, obj_name)


def show_beam_modifier(beams=None):
    """Show the beam modifier task panel with optional beam pre-selection"""
    # Close any existing task panel first
    if hasattr(Gui, 'Control') and Gui.Control.activeDialog():
        Gui.Control.closeDialog()
    panel = BeamModifierTaskPanel()
    
    # If specific beams are provided, pre-select them
    if beams:
        panel.selected_beams = beams
        # Also select them in FreeCAD
        Gui.Selection.clearSelection()
        for beam in beams:
            if beam and hasattr(beam, 'Type') and beam.Type in ["BeamFeature"]:
                Gui.Selection.addSelection(beam)
        panel.update_display()
    else:
        # Check if there are any selected beams in FreeCAD and pre-select them
        current_selection = Gui.Selection.getSelection()
        beam_selection = []
        
        for obj in current_selection:
            if hasattr(obj, "Type") and obj.Type in ["BeamFeature", "ResultBeam"]:
                beam_selection.append(obj)
        
        if beam_selection:
            panel.selected_beams = beam_selection
            panel.update_display()
    
    Gui.Control.showDialog(panel)
    return panel