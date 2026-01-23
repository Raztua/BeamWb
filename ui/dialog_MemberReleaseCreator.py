# ui/dialog_MemberReleaseCreator.py - UPDATED VERSION
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtGui, QtCore
from features.member_releases import create_member_release


class MemberReleaseCreatorTaskPanel:
    """Task panel for creating AND modifying member releases"""

    def __init__(self, release_objects=None):
        self.release_objects = release_objects or []  # Empty for create, has object for modify
        self.is_editing = len(self.release_objects) > 0

        self.form = QtGui.QWidget()
        self.form.setWindowTitle("Modify Member Release" if self.is_editing else "Create Member Release")
        self.setup_ui()

        if self.is_editing:
            self.load_existing_release(self.release_objects[0])
        else:
            # Set default name for new release
            self.name_edit.setText(self.get_next_release_name())

    def setup_ui(self):
        layout = QtGui.QVBoxLayout(self.form)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Release name/label
        name_group = QtGui.QGroupBox("Release Name")
        name_layout = QtGui.QVBoxLayout()

        self.name_edit = QtGui.QLineEdit()
        self.name_edit.setPlaceholderText("Enter a descriptive name for this release...")
        name_layout.addWidget(self.name_edit)

        name_group.setLayout(name_layout)
        layout.addWidget(name_group)

        # Start node releases
        start_group = QtGui.QGroupBox("Start Node Releases")
        start_layout = QtGui.QGridLayout()
        start_layout.setSpacing(8)

        start_layout.addWidget(QtGui.QLabel("Translation Releases:"), 0, 0)
        self.start_dx_check = QtGui.QCheckBox("DX")
        self.start_dy_check = QtGui.QCheckBox("DY")
        self.start_dz_check = QtGui.QCheckBox("DZ")

        trans_layout = QtGui.QHBoxLayout()
        trans_layout.addWidget(self.start_dx_check)
        trans_layout.addWidget(self.start_dy_check)
        trans_layout.addWidget(self.start_dz_check)
        start_layout.addLayout(trans_layout, 0, 1)

        start_layout.addWidget(QtGui.QLabel("Rotation Releases:"), 1, 0)
        self.start_rx_check = QtGui.QCheckBox("RX")
        self.start_ry_check = QtGui.QCheckBox("RY")
        self.start_rz_check = QtGui.QCheckBox("RZ")

        rot_layout = QtGui.QHBoxLayout()
        rot_layout.addWidget(self.start_rx_check)
        rot_layout.addWidget(self.start_ry_check)
        rot_layout.addWidget(self.start_rz_check)
        start_layout.addLayout(rot_layout, 1, 1)

        start_group.setLayout(start_layout)
        layout.addWidget(start_group)

        # End node releases
        end_group = QtGui.QGroupBox("End Node Releases")
        end_layout = QtGui.QGridLayout()
        end_layout.setSpacing(8)

        end_layout.addWidget(QtGui.QLabel("Translation Releases:"), 0, 0)
        self.end_dx_check = QtGui.QCheckBox("DX")
        self.end_dy_check = QtGui.QCheckBox("DY")
        self.end_dz_check = QtGui.QCheckBox("DZ")

        trans_layout_end = QtGui.QHBoxLayout()
        trans_layout_end.addWidget(self.end_dx_check)
        trans_layout_end.addWidget(self.end_dy_check)
        trans_layout_end.addWidget(self.end_dz_check)
        end_layout.addLayout(trans_layout_end, 0, 1)

        end_layout.addWidget(QtGui.QLabel("Rotation Releases:"), 1, 0)
        self.end_rx_check = QtGui.QCheckBox("RX")
        self.end_ry_check = QtGui.QCheckBox("RY")
        self.end_rz_check = QtGui.QCheckBox("RZ")

        rot_layout_end = QtGui.QHBoxLayout()
        rot_layout_end.addWidget(self.end_rx_check)
        rot_layout_end.addWidget(self.end_ry_check)
        rot_layout_end.addWidget(self.end_rz_check)
        end_layout.addLayout(rot_layout_end, 1, 1)

        end_group.setLayout(end_layout)
        layout.addWidget(end_group)

        # Preset buttons
        preset_group = QtGui.QGroupBox("Common Release Types")
        preset_layout = QtGui.QHBoxLayout()

        fixed_button = QtGui.QPushButton("Fixed Both Ends")
        fixed_button.clicked.connect(self.set_fixed_both)
        pinned_button = QtGui.QPushButton("Pinned Both Ends")
        pinned_button.clicked.connect(self.set_pinned_both)
        hinged_start_button = QtGui.QPushButton("Hinged Start Only")
        hinged_start_button.clicked.connect(self.set_hinged_start)
        hinged_end_button = QtGui.QPushButton("Hinged End Only")
        hinged_end_button.clicked.connect(self.set_hinged_end)

        preset_layout.addWidget(fixed_button)
        preset_layout.addWidget(pinned_button)
        preset_layout.addWidget(hinged_start_button)
        preset_layout.addWidget(hinged_end_button)

        preset_group.setLayout(preset_layout)
        layout.addWidget(preset_group)

        # Visual properties
        visual_group = QtGui.QGroupBox("Visual Properties")
        visual_layout = QtGui.QGridLayout()

        visual_layout.addWidget(QtGui.QLabel("Color:"), 0, 0)
        self.color_button = QtGui.QPushButton()
        self.color_button.clicked.connect(self.choose_color)
        self.color_button.setStyleSheet("background-color: rgb(0, 85, 255)")
        visual_layout.addWidget(self.color_button, 0, 1)

        visual_layout.addWidget(QtGui.QLabel("Scale:"), 1, 0)
        self.scale_spin = QtGui.QDoubleSpinBox()
        self.scale_spin.setRange(0.1, 5.0)
        self.scale_spin.setValue(1.0)
        self.scale_spin.setSingleStep(0.1)
        visual_layout.addWidget(self.scale_spin, 1, 1)

        visual_group.setLayout(visual_layout)
        layout.addWidget(visual_group)

        # Release description preview
        desc_group = QtGui.QGroupBox("Release Description")
        desc_layout = QtGui.QVBoxLayout()

        self.desc_label = QtGui.QLabel("Fully Fixed (No releases)")
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet("background-color: #f0f0f0; padding: 8px; border: 1px solid #ccc;")
        self.desc_label.setMinimumHeight(40)
        desc_layout.addWidget(self.desc_label)

        desc_group.setLayout(desc_layout)
        layout.addWidget(desc_group)

        layout.addStretch()

        # Connect signals for real-time updates
        self._connect_signals()

    def _connect_signals(self):
        """Connect all checkboxes to update the description"""
        checkboxes = [
            self.start_dx_check, self.start_dy_check, self.start_dz_check,
            self.start_rx_check, self.start_ry_check, self.start_rz_check,
            self.end_dx_check, self.end_dy_check, self.end_dz_check,
            self.end_rx_check, self.end_ry_check, self.end_rz_check
        ]

        for checkbox in checkboxes:
            checkbox.stateChanged.connect(self.update_description)

    def get_next_release_name(self):
        """Generate the next available member release name"""
        doc = App.ActiveDocument
        if not doc:
            return "MemberRelease_001"

        existing_names = []
        if hasattr(doc, "MemberReleases") and hasattr(doc.MemberReleases, "Group"):
            for obj in doc.MemberReleases.Group:
                if hasattr(obj, "Label"):
                    existing_names.append(obj.Label)

        # Find the highest number
        import re
        max_num = 0
        pattern = re.compile(r'^MemberRelease_(\d+)$', re.IGNORECASE)

        for name in existing_names:
            match = pattern.match(name)
            if match:
                num = int(match.group(1))
                if num > max_num:
                    max_num = num

        return f"MemberRelease_{max_num + 1:03d}"

    def load_existing_release(self, release_obj):
        """Load an existing member release's properties into the UI"""
        # Set UI values
        self.name_edit.setText(release_obj.Label)

        # Set start releases
        self.start_dx_check.setChecked(release_obj.Start_Dx)
        self.start_dy_check.setChecked(release_obj.Start_Dy)
        self.start_dz_check.setChecked(release_obj.Start_Dz)
        self.start_rx_check.setChecked(release_obj.Start_Rx)
        self.start_ry_check.setChecked(release_obj.Start_Ry)
        self.start_rz_check.setChecked(release_obj.Start_Rz)

        # Set end releases
        self.end_dx_check.setChecked(release_obj.End_Dx)
        self.end_dy_check.setChecked(release_obj.End_Dy)
        self.end_dz_check.setChecked(release_obj.End_Dz)
        self.end_rx_check.setChecked(release_obj.End_Rx)
        self.end_ry_check.setChecked(release_obj.End_Ry)
        self.end_rz_check.setChecked(release_obj.End_Rz)

        # Set visual properties
        color = release_obj.Color
        r = int(color[0] * 255)
        g = int(color[1] * 255)
        b = int(color[2] * 255)
        self.color_button.setStyleSheet(f"background-color: rgb({r}, {g}, {b})")
        self.scale_spin.setValue(release_obj.Scale)

        self.update_description()

    def update_description(self):
        """Update the release description based on current settings"""
        start_releases = []
        end_releases = []

        # Check start releases
        if self.start_dx_check.isChecked(): start_releases.append("SDx")
        if self.start_dy_check.isChecked(): start_releases.append("SDy")
        if self.start_dz_check.isChecked(): start_releases.append("SDz")
        if self.start_rx_check.isChecked(): start_releases.append("SRx")
        if self.start_ry_check.isChecked(): start_releases.append("SRy")
        if self.start_rz_check.isChecked(): start_releases.append("SRz")

        # Check end releases
        if self.end_dx_check.isChecked(): end_releases.append("EDx")
        if self.end_dy_check.isChecked(): end_releases.append("EDy")
        if self.end_dz_check.isChecked(): end_releases.append("EDz")
        if self.end_rx_check.isChecked(): end_releases.append("ERx")
        if self.end_ry_check.isChecked(): end_releases.append("ERy")
        if self.end_rz_check.isChecked(): end_releases.append("ERz")

        # Build description
        if not start_releases and not end_releases:
            description = "Fully Fixed (No releases)"
        else:
            description = "Releases: "
            if start_releases:
                description += f"Start[{', '.join(start_releases)}] "
            if end_releases:
                description += f"End[{', '.join(end_releases)}]"

        self.desc_label.setText(description)

    def set_fixed_both(self):
        """Set fixed both ends (no releases)"""
        self._clear_all_checks()
        self.name_edit.setText("Fixed_Both")
        self.update_description()

    def set_pinned_both(self):
        """Set pinned both ends (rotation releases only)"""
        self._clear_all_checks()
        self.start_rx_check.setChecked(True)
        self.start_ry_check.setChecked(True)
        self.start_rz_check.setChecked(True)
        self.end_rx_check.setChecked(True)
        self.end_ry_check.setChecked(True)
        self.end_rz_check.setChecked(True)
        self.name_edit.setText("Pinned_Both")
        self.update_description()

    def set_hinged_start(self):
        """Set hinged start only"""
        self._clear_all_checks()
        self.start_rx_check.setChecked(True)
        self.start_ry_check.setChecked(True)
        self.start_rz_check.setChecked(True)
        self.name_edit.setText("Hinged_Start")
        self.update_description()

    def set_hinged_end(self):
        """Set hinged end only"""
        self._clear_all_checks()
        self.end_rx_check.setChecked(True)
        self.end_ry_check.setChecked(True)
        self.end_rz_check.setChecked(True)
        self.name_edit.setText("Hinged_End")
        self.update_description()

    def _clear_all_checks(self):
        """Clear all release checkboxes"""
        checkboxes = [
            self.start_dx_check, self.start_dy_check, self.start_dz_check,
            self.start_rx_check, self.start_ry_check, self.start_rz_check,
            self.end_dx_check, self.end_dy_check, self.end_dz_check,
            self.end_rx_check, self.end_ry_check, self.end_rz_check
        ]

        for checkbox in checkboxes:
            checkbox.setChecked(False)

    def choose_color(self):
        """Choose color for the member release visualization"""
        color = QtGui.QColorDialog.getColor()
        if color.isValid():
            self.color_button.setStyleSheet(f"background-color: {color.name()}")

    def get_color_from_button(self):
        """Extract color from button stylesheet"""
        style = self.color_button.styleSheet()
        if "rgb" in style:
            import re
            match = re.search(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', style)
            if match:
                r = int(match.group(1)) / 255.0
                g = int(match.group(2)) / 255.0
                b = int(match.group(3)) / 255.0
                return (r, g, b)
        return (0.0, 0.33, 1.0)  # Default blue

    def create_or_update_member_release(self):
        """Create or update member release based on current settings"""
        try:
            # Get release settings
            start_release = (
                self.start_dx_check.isChecked(),
                self.start_dy_check.isChecked(),
                self.start_dz_check.isChecked(),
                self.start_rx_check.isChecked(),
                self.start_ry_check.isChecked(),
                self.start_rz_check.isChecked()
            )

            end_release = (
                self.end_dx_check.isChecked(),
                self.end_dy_check.isChecked(),
                self.end_dz_check.isChecked(),
                self.end_rx_check.isChecked(),
                self.end_ry_check.isChecked(),
                self.end_rz_check.isChecked()
            )

            # Get visual properties
            color = self.get_color_from_button()
            scale = self.scale_spin.value()
            name = self.name_edit.text().strip()

            if self.is_editing:
                # UPDATE existing release
                release_obj = self.release_objects[0]

                # Update properties
                release_obj.Start_Dx, release_obj.Start_Dy, release_obj.Start_Dz, \
                    release_obj.Start_Rx, release_obj.Start_Ry, release_obj.Start_Rz = start_release

                release_obj.End_Dx, release_obj.End_Dy, release_obj.End_Dz, \
                    release_obj.End_Rx, release_obj.End_Ry, release_obj.End_Rz = end_release

                if name:
                    release_obj.Label = name

                release_obj.Color = color
                release_obj.Scale = scale

                App.Console.PrintMessage(f"Updated member release: {release_obj.Label}\n")
                return release_obj
            else:
                # CREATE new release
                if not name:
                    name = self.get_next_release_name()

                release_obj = create_member_release(
                    start_release=start_release,
                    end_release=end_release,
                    label=name
                )

                if release_obj:
                    # Set visual properties
                    release_obj.Color = color
                    release_obj.Scale = scale
                    App.Console.PrintMessage(f"Created new member release: {release_obj.Label}\n")
                    return release_obj

            return None

        except Exception as e:
            App.Console.PrintError(f"Error creating/updating member release: {str(e)}\n")
            QtGui.QMessageBox.warning(self.form, "Error", f"Failed: {str(e)}")
            return None

    def apply_changes(self):
        """Apply button handler - create or update member release"""
        if self.create_or_update_member_release():
            if not self.is_editing:
                # Clear for next creation (only if creating new)
                self.name_edit.setText(self.get_next_release_name())
                self._clear_all_checks()
                self.color_button.setStyleSheet("background-color: rgb(0, 85, 255)")
                self.scale_spin.setValue(1.0)
                self.update_description()
            return True
        return False

    def getStandardButtons(self):
        """Return standard buttons for task panel"""
        return QtGui.QDialogButtonBox.Apply | QtGui.QDialogButtonBox.Close

    def clicked(self, button):
        """Handle button clicks"""
        if button == QtGui.QDialogButtonBox.Apply:
            self.apply_changes()
            App.ActiveDocument.recompute()
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


def show_member_release_modifier(release_objects=None):
    """Show the member release creator/modifier task panel"""
    panel = MemberReleaseCreatorTaskPanel(release_objects)
    Gui.Control.showDialog(panel)