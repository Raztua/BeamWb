# ui/dialog_MemberLoad.py
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtGui, QtCore
from features.LoadManager import LoadManager
from FreeCAD import Units


class MemberLoadTaskPanel:
    """Task panel for creating and modifying Member Loads (Distributed)"""

    def __init__(self, selected_beams=None, member_load_to_modify=None):
        self.form = QtGui.QWidget()
        self.form.setWindowTitle("Create Member Load")
        self.selected_beams = selected_beams or []
        self.selection_callback = None
        self.is_picking = False
        self.temp_selected_beams = []
        self.member_load_to_modify = member_load_to_modify
        self.is_modification_mode = member_load_to_modify is not None

        self.setup_ui()
        self.update_load_id_combo()

        # Load existing data if in modification mode
        if self.is_modification_mode:
            self.load_member_load_data()
            self.form.setWindowTitle("Modify Member Load")
        else:
            # Check for pre-selected beams
            if not self.selected_beams:
                current_selection = Gui.Selection.getSelection()
                for obj in current_selection:
                    if self.is_valid_beam(obj):
                        self.selected_beams.append(obj)

        self.update_display()
        self.update_end_load_enable_state()

    def setup_ui(self):
        layout = QtGui.QVBoxLayout(self.form)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Title
        title_text = "Modify Member Load" if self.is_modification_mode else "Create Member Load"
        title = QtGui.QLabel(title_text)
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

        # Beam selection
        beam_group = QtGui.QGroupBox("Beam Selection")
        beam_layout = QtGui.QVBoxLayout()
        self.selection_info = QtGui.QLabel("No beams selected")
        self.selection_info.setStyleSheet("font-weight: bold; color: blue;")
        beam_layout.addWidget(self.selection_info)
        self.beam_list = QtGui.QListWidget()
        self.beam_list.setMaximumHeight(100)
        beam_layout.addWidget(self.beam_list)
        
        button_layout = QtGui.QHBoxLayout()
        self.pick_button = QtGui.QPushButton("Pick Beams")
        self.pick_button.clicked.connect(self.toggle_picking)
        self.clear_button = QtGui.QPushButton("Clear Selection")
        self.clear_button.clicked.connect(self.clear_selection)
        button_layout.addWidget(self.pick_button)
        button_layout.addWidget(self.clear_button)
        beam_layout.addLayout(button_layout)
        beam_group.setLayout(beam_layout)
        layout.addWidget(beam_group)

        # Position and Settings
        settings_layout = QtGui.QHBoxLayout()
        
        # Coordinate System
        cs_group = QtGui.QGroupBox("System")
        cs_layout = QtGui.QVBoxLayout()
        self.global_cs_radio = QtGui.QRadioButton("Global")
        self.local_cs_radio = QtGui.QRadioButton("Local")
        self.local_cs_radio.setChecked(True)
        cs_layout.addWidget(self.global_cs_radio)
        cs_layout.addWidget(self.local_cs_radio)
        cs_group.setLayout(cs_layout)
        settings_layout.addWidget(cs_group)

        # Load Position
        pos_group = QtGui.QGroupBox("Range (0.0 - 1.0)")
        pos_layout = QtGui.QFormLayout()
        self.start_pos_input = QtGui.QDoubleSpinBox()
        self.start_pos_input.setRange(0.0, 1.0)
        self.start_pos_input.setValue(0.0)
        self.end_pos_input = QtGui.QDoubleSpinBox()
        self.end_pos_input.setRange(0.0, 1.0)
        self.end_pos_input.setValue(1.0)
        pos_layout.addRow("Start:", self.start_pos_input)
        pos_layout.addRow("End:", self.end_pos_input)
        pos_group.setLayout(pos_layout)
        settings_layout.addWidget(pos_group)
        
        layout.addLayout(settings_layout)

        # Equal Load Checkbox
        self.equal_load_checkbox = QtGui.QCheckBox("Uniform Load (Start = End)")
        self.equal_load_checkbox.setChecked(True)
        self.equal_load_checkbox.stateChanged.connect(self.on_equal_load_changed)
        layout.addWidget(self.equal_load_checkbox)

        # Load Values Group
        load_group = QtGui.QGroupBox("Distributed Load Values")
        load_layout = QtGui.QGridLayout()

        # Headers
        load_layout.addWidget(QtGui.QLabel("<b>Start (kN/m or Nm/m)</b>"), 0, 1)
        load_layout.addWidget(QtGui.QLabel("<b>End (kN/m or Nm/m)</b>"), 0, 2)

        coords = ["X", "Y", "Z"]
        # Forces (kN/m)
        for i, coord in enumerate(coords):
            load_layout.addWidget(QtGui.QLabel(f"Force {coord}:"), i + 1, 0)
            
            # Start Force
            sf_in = QtGui.QLineEdit()
            sf_in.setPlaceholderText("kN/m")
            sf_in.editingFinished.connect(lambda c=coord: self.add_unit_if_needed(f"start_force_{c.lower()}"))
            sf_in.textChanged.connect(self.copy_start_to_end)
            setattr(self, f"start_force_{coord.lower()}_input", sf_in)
            load_layout.addWidget(sf_in, i + 1, 1)

            # End Force
            ef_in = QtGui.QLineEdit()
            ef_in.setPlaceholderText("kN/m")
            ef_in.editingFinished.connect(lambda c=coord: self.add_unit_if_needed(f"end_force_{c.lower()}"))
            setattr(self, f"end_force_{coord.lower()}_input", ef_in)
            load_layout.addWidget(ef_in, i + 1, 2)

        # Moments (Nm/m)
        for i, coord in enumerate(coords):
            row = i + 4
            load_layout.addWidget(QtGui.QLabel(f"Moment {coord}:"), row, 0)
            
            # Start Moment
            sm_in = QtGui.QLineEdit()
            sm_in.setPlaceholderText("kN*m/m")
            sm_in.editingFinished.connect(lambda c=coord: self.add_unit_if_needed(f"start_moment_{c.lower()}"))
            sm_in.textChanged.connect(self.copy_start_to_end)
            setattr(self, f"start_moment_{coord.lower()}_input", sm_in)
            load_layout.addWidget(sm_in, row, 1)

            # End Moment
            em_in = QtGui.QLineEdit()
            em_in.setPlaceholderText("kN*m/m")
            em_in.editingFinished.connect(lambda c=coord: self.add_unit_if_needed(f"end_moment_{c.lower()}"))
            setattr(self, f"end_moment_{coord.lower()}_input", em_in)
            load_layout.addWidget(em_in, row, 2)

        load_group.setLayout(load_layout)
        layout.addWidget(load_group)
        layout.addStretch()

    def add_unit_if_needed(self, field_name):
        """Add 'kN/m' to force or 'Nm/m' to moment if no unit is specified"""
        line_edit = getattr(self, f"{field_name}_input")
        text = line_edit.text().strip()
        if not text: return

        # If it's just a number, add the distributed unit
        if not any(char.isalpha() for char in text):
            if 'force' in field_name:
                line_edit.setText(f"{text} kN/m")
            elif 'moment' in field_name:
                line_edit.setText(f"{text} kN*m/m")

    def parse_distributed_force(self, text):
        """Parse input for Force per Length (N/mm in FreeCAD internal, usually kN/m)"""
        if not text.strip(): return 0.0
        try:
            q = Units.Quantity(text)
            # Line loads are often internally 'ForcePerLength' or similar
            # We convert to N/m for the solver/manager
            return q.getValueAs('N/mm')
        except Exception:
            QtGui.QMessageBox.warning(self.form, "Unit Error", f"Invalid Force/Length: {text}. Use kN/m or N/m")
            return None

    def parse_distributed_moment(self, text):
        """Parse input for Moment per Length (Nm/m)"""
        if not text.strip(): return 0.0
        try:
            q = Units.Quantity(text)
            # Moment is Force*Length, so Moment/Length is effectively just Force units (N) 
            # or custom. We ensure we return the value in Nm/m.
            return q.getValueAs('N*mm/mm')
        except Exception:
            QtGui.QMessageBox.warning(self.form, "Unit Error", f"Invalid Moment/Length: {text}. Use N*m/m or kN*m/m")
            return None

    def on_equal_load_changed(self, state):
        self.update_end_load_enable_state()
        if state == QtCore.Qt.Checked:
            self.copy_start_to_end()

    def update_end_load_enable_state(self):
        is_checked = self.equal_load_checkbox.isChecked()
        style = "background-color: #f0f0f0; color: #888888;" if is_checked else ""
        
        for coord in ["x", "y", "z"]:
            for type_ in ["force", "moment"]:
                field = getattr(self, f"end_{type_}_{coord}_input")
                field.setEnabled(not is_checked)
                field.setStyleSheet(style)

    def copy_start_to_end(self):
        if not self.equal_load_checkbox.isChecked():
            return
        for coord in ["x", "y", "z"]:
            self.end_force_z_input.setText(self.start_force_z_input.text()) # Example logic
            getattr(self, f"end_force_{coord}_input").setText(getattr(self, f"start_force_{coord}_input").text())
            getattr(self, f"end_moment_{coord}_input").setText(getattr(self, f"start_moment_{coord}_input").text())

    def update_load_id_combo(self):
        self.load_id_combo.clear()
        doc = App.ActiveDocument
        if doc:
            for obj in doc.Objects:
                if hasattr(obj, "Type") and obj.Type == "LoadIDFeature":
                    self.load_id_combo.addItem(obj.Label, obj)
        if self.load_id_combo.count() == 0:
            self.load_id_combo.addItem("Create a Load ID first", None)

    def create_new_load_id(self):
        try:
            from features.LoadIDManager import create_load_id
            if create_load_id(): self.update_load_id_combo()
        except Exception as e:
            App.Console.PrintError(str(e))

    def is_valid_beam(self, obj):
        return hasattr(obj, "Type") and obj.Type == "BeamFeature"

    def toggle_picking(self):
        if self.is_picking: self.stop_picking()
        else: self.start_picking()

    def start_picking(self):
        Gui.Selection.clearSelection()
        for b in self.selected_beams: Gui.Selection.addSelection(b)
        self.pick_button.setStyleSheet("background-color: lightgreen")
        self.is_picking = True
        self.selection_callback = MemberLoadSelectionCallback(self)
        Gui.Selection.addObserver(self.selection_callback)

    def stop_picking(self):
        if self.selection_callback:
            Gui.Selection.removeObserver(self.selection_callback)
            self.selection_callback = None
        self.selected_beams = [obj for obj in Gui.Selection.getSelection() if self.is_valid_beam(obj)]
        self.update_display()
        self.pick_button.setStyleSheet("")
        self.is_picking = False

    def process_selection(self, doc_name, obj_name):
        pass

    def update_display(self):
        self.beam_list.clear()
        for beam in self.selected_beams:
            self.beam_list.addItem(beam.Label)
        self.selection_info.setText(f"{len(self.selected_beams)} beam(s) selected")

    def clear_selection(self):
        self.selected_beams = []
        Gui.Selection.clearSelection()
        self.update_display()

    def apply_changes(self):
        # Trigger unit check
        for coord in ["x", "y", "z"]:
            for t in ["force", "moment"]:
                self.add_unit_if_needed(f"start_{t}_{coord}")
                self.add_unit_if_needed(f"end_{t}_{coord}")

        # Validation and Parsing
        start_f = []
        end_f = []
        start_m = []
        end_m = []

        for c in ["x", "y", "z"]:
            val_sf = self.parse_distributed_force(getattr(self, f"start_force_{c}_input").text())
            val_sm = self.parse_distributed_moment(getattr(self, f"start_moment_{c}_input").text())
            if val_sf is None or val_sm is None: return False
            start_f.append(val_sf)
            start_m.append(val_sm)
            
            if self.equal_load_checkbox.isChecked():
                end_f.append(val_sf)
                end_m.append(val_sm)
            else:
                val_ef = self.parse_distributed_force(getattr(self, f"end_force_{c}_input").text())
                val_em = self.parse_distributed_moment(getattr(self, f"end_moment_{c}_input").text())
                if val_ef is None or val_em is None: return False
                end_f.append(val_ef)
                end_m.append(val_em)

        try:
            if self.is_modification_mode:
                ml = self.member_load_to_modify
                ml.Beams = self.selected_beams
                ml.StartForce = App.Vector(*start_f)
                ml.EndForce = App.Vector(*end_f)
                ml.StartMoment = App.Vector(*start_m)
                ml.EndMoment = App.Vector(*end_m)
                ml.StartPosition = self.start_pos_input.value()
                ml.EndPosition = self.end_pos_input.value()
                ml.LocalCS = self.local_cs_radio.isChecked()
            else:
                load_id = self.load_id_combo.currentData()
                if not load_id: return False
                LoadManager.create_member_load(
                    load_id=load_id, beams=self.selected_beams,
                    start_force=tuple(start_f), end_force=tuple(end_f),
                    start_moment=tuple(start_m), end_moment=tuple(end_m),
                    start_position=self.start_pos_input.value(),
                    end_position=self.end_pos_input.value(),
                    local_cs=self.local_cs_radio.isChecked()
                )
            App.ActiveDocument.recompute()
            return True
        except Exception as e:
            QtGui.QMessageBox.critical(self.form, "Error", str(e))
            return False

    def load_member_load_data(self):
        ml = self.member_load_to_modify
        if not ml: return
        self.selected_beams = list(getattr(ml, 'Beams', []))
        self.start_pos_input.setValue(getattr(ml, 'StartPosition', 0.0))
        self.end_pos_input.setValue(getattr(ml, 'EndPosition', 1.0))
        self.local_cs_radio.setChecked(getattr(ml, 'LocalCS', True))
        
        # Display as kN/m (dividing internal N/m by 1000)
        sf = ml.StartForce
        self.start_force_x_input.setText(f"{sf.x:.3f} kN/m")
        self.start_force_y_input.setText(f"{sf.y:.3f} kN/m")
        self.start_force_z_input.setText(f"{sf.z:.3f} kN/m")
        # Display Moments as Nm/m
        sm = ml.StartMoment
        self.start_moment_x_input.setText(f"{sm.x/1000:.3f} kN*m/m")
        self.start_moment_y_input.setText(f"{sm.y/1000:.3f} kN*m/m")
        self.start_moment_z_input.setText(f"{sm.z/1000:.3f} kN*m/m")


    def getStandardButtons(self):
        return QtGui.QDialogButtonBox.Apply | QtGui.QDialogButtonBox.Close

    def clicked(self, button):
        if button == QtGui.QDialogButtonBox.Apply:
            if self.apply_changes():
                if self.is_modification_mode: Gui.Control.closeDialog()
        elif button == QtGui.QDialogButtonBox.Close:
            Gui.Control.closeDialog()

class MemberLoadSelectionCallback:
    def __init__(self, task_panel):
        self.task_panel = task_panel
    def addSelection(self, doc_name, obj_name, sub_name, pos):
        self.task_panel.process_selection(doc_name, obj_name)

def show_member_load_creator(selected_beams=None, member_load_to_modify=None):
    if hasattr(Gui, 'Control') and Gui.Control.activeDialog():
        Gui.Control.closeDialog()
    panel = MemberLoadTaskPanel(selected_beams=selected_beams, member_load_to_modify=member_load_to_modify)
    Gui.Control.showDialog(panel)
    return panel