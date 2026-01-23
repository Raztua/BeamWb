# ui/dialog_SectionCreator.py
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtGui, QtCore
import random
from features.sections import create_section, PROFILE_TYPES, SECTION_COLORS
from features.sectionLibrary import STANDARD_PROFILES
from features.sections import make_section_group


class SectionCreatorTaskPanel:
    """Task panel for creating sections"""

    def __init__(self):
        self.form = QtGui.QWidget()
        self.form.setWindowTitle("Section Creator")
        self.current_color = random.choice(SECTION_COLORS)

        self.setup_ui()
        self.update_standard_section_combo()
        self.update_label()
        self.update_ui()

    def setup_ui(self):
        layout = QtGui.QVBoxLayout(self.form)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Section Type Selection
        type_group = QtGui.QGroupBox("1. Select Section Type")
        type_layout = QtGui.QVBoxLayout()
        self.section_type_combo = QtGui.QComboBox()
        self.section_type_combo.addItems(PROFILE_TYPES)
        self.section_type_combo.currentIndexChanged.connect(self.update_standard_section_combo)
        self.section_type_combo.currentIndexChanged.connect(self.update_ui)
        type_layout.addWidget(self.section_type_combo)
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)

        # Standard Section Selection
        section_group = QtGui.QGroupBox("2. Select Standard Section")
        section_layout = QtGui.QVBoxLayout()
        self.standard_section_combo = QtGui.QComboBox()
        self.standard_section_combo.currentIndexChanged.connect(self.load_section_properties)
        section_layout.addWidget(self.standard_section_combo)
        section_group.setLayout(section_layout)
        layout.addWidget(section_group)

        # Dimensions
        dim_group = QtGui.QGroupBox("3. Dimensions (mm)")
        self.dim_layout = QtGui.QGridLayout()

        # Common dimensions
        row = 0
        self.dim_layout.addWidget(QtGui.QLabel("Height:"), row, 0)
        self.height_input = QtGui.QDoubleSpinBox()
        self.height_input.setRange(1, 10000)
        self.height_input.setValue(100.0)
        self.dim_layout.addWidget(self.height_input, row, 1)
        row += 1

        self.dim_layout.addWidget(QtGui.QLabel("Width:"), row, 0)
        self.width_input = QtGui.QDoubleSpinBox()
        self.width_input.setRange(1, 10000)
        self.width_input.setValue(50.0)
        self.dim_layout.addWidget(self.width_input, row, 1)
        row += 1

        self.dim_layout.addWidget(QtGui.QLabel("Thickness:"), row, 0)
        self.thickness_input = QtGui.QDoubleSpinBox()
        self.thickness_input.setRange(1, 1000)
        self.thickness_input.setValue(5.0)
        self.dim_layout.addWidget(self.thickness_input, row, 1)
        row += 1

        # I/H Section specific
        self.web_thickness_label = QtGui.QLabel("Web Thickness:")
        self.dim_layout.addWidget(self.web_thickness_label, row, 0)
        self.web_thickness_input = QtGui.QDoubleSpinBox()
        self.web_thickness_input.setRange(1, 1000)
        self.web_thickness_input.setValue(5.0)
        self.dim_layout.addWidget(self.web_thickness_input, row, 1)
        row += 1

        self.flange_thickness_label = QtGui.QLabel("Flange Thickness:")
        self.dim_layout.addWidget(self.flange_thickness_label, row, 0)
        self.flange_thickness_input = QtGui.QDoubleSpinBox()
        self.flange_thickness_input.setRange(1, 1000)
        self.flange_thickness_input.setValue(8.0)
        self.dim_layout.addWidget(self.flange_thickness_input, row, 1)
        row += 1

        dim_group.setLayout(self.dim_layout)
        layout.addWidget(dim_group)

        # Identification
        id_group = QtGui.QGroupBox("4. Identification")
        id_layout = QtGui.QFormLayout()


        self.color_button = QtGui.QPushButton("Select Color")
        self.color_button.clicked.connect(self.select_color)
        self.update_color_button()
        id_layout.addRow("Section Color:", self.color_button)

        self.label_preview = QtGui.QLabel("Label will be generated automatically")
        id_layout.addRow("Section Label:", self.label_preview)

        id_group.setLayout(id_layout)
        layout.addWidget(id_group)

        layout.addStretch()

    def update_standard_section_combo(self):
        current_type = self.section_type_combo.currentText()
        self.standard_section_combo.clear()
        self.standard_section_combo.addItem("Custom")

        if current_type in STANDARD_PROFILES:
            for section_name in sorted(STANDARD_PROFILES[current_type].keys()):
                self.standard_section_combo.addItem(section_name)

        self.update_ui()

    def select_color(self):
        color = QtGui.QColorDialog.getColor()
        if color.isValid():
            self.current_color = (color.redF(), color.greenF(), color.blueF())
            self.update_color_button()
            self.update_label()

    def update_color_button(self):
        r, g, b = [int(255 * x) for x in self.current_color]
        self.color_button.setStyleSheet(f"background-color: rgb({r},{g},{b})")

    def load_section_properties(self):
        if self.standard_section_combo.currentText() == "Custom":
            self.update_label()
            return

        section_type = self.section_type_combo.currentText()
        section_name = self.standard_section_combo.currentText()

        if section_type in STANDARD_PROFILES and section_name in STANDARD_PROFILES[section_type]:
            section_data = STANDARD_PROFILES[section_type][section_name]

            # Update dimension inputs
            if 'Height' in section_data:
                self.height_input.setValue(section_data['Height'])
            if 'Width' in section_data:
                self.width_input.setValue(section_data['Width'])
            if 'Thickness' in section_data:
                self.thickness_input.setValue(section_data['Thickness'])
            if 'WebThickness' in section_data:
                self.web_thickness_input.setValue(section_data['WebThickness'])
            if 'FlangeThickness' in section_data:
                self.flange_thickness_input.setValue(section_data['FlangeThickness'])

            self.update_label()

    def update_ui(self):
        section_type = self.section_type_combo.currentText()

        # Default visibility - hide all first
        height_label = self.dim_layout.itemAtPosition(0, 0).widget()
        width_label = self.dim_layout.itemAtPosition(1, 0).widget()
        thickness_label = self.dim_layout.itemAtPosition(2, 0).widget()

        height_label.setVisible(False)
        self.height_input.setVisible(False)
        width_label.setVisible(False)
        self.width_input.setVisible(False)
        thickness_label.setVisible(False)
        self.thickness_input.setVisible(False)
        self.web_thickness_label.setVisible(False)
        self.web_thickness_input.setVisible(False)
        self.flange_thickness_label.setVisible(False)
        self.flange_thickness_input.setVisible(False)

        # Show relevant controls based on section type
        if section_type in ["I-Shape", "H-Shape", "Asymmetric I-Shape"]:
            height_label.setVisible(True)
            self.height_input.setVisible(True)
            width_label.setVisible(True)
            self.width_input.setVisible(True)
            self.web_thickness_label.setVisible(True)
            self.web_thickness_input.setVisible(True)
            self.flange_thickness_label.setVisible(True)
            self.flange_thickness_input.setVisible(True)

        elif section_type in ["L-Shape", "U-Shape", "C-Shape", "T-Shape", "Rectangle"]:
            height_label.setVisible(True)
            self.height_input.setVisible(True)
            width_label.setVisible(True)
            self.width_input.setVisible(True)
            thickness_label.setVisible(True)
            self.thickness_input.setVisible(True)

            if section_type == "T-Shape":
                self.web_thickness_label.setVisible(True)
                self.web_thickness_input.setVisible(True)

        elif section_type in ["Round Bar", "Tubular"]:
            width_label.setVisible(True)
            self.width_input.setVisible(True)
            width_label.setText("Diameter:" if section_type == "Round Bar" else "Outer Diameter:")

            if section_type in ["Tubular"]:
                thickness_label.setVisible(True)
                self.thickness_input.setVisible(True)
                thickness_label.setText("Wall Thickness:")

    def update_label(self):
        section_type = self.section_type_combo.currentText()
        standard_section = self.standard_section_combo.currentText()

        if standard_section != "Custom":
            self.label_preview.setText(f"{standard_section}")
        else:
            self.label_preview.setText(f"Custom {section_type}")

    def accept(self):
        """Create the section"""
        section_name = self.label_preview.text()
        if not section_name or section_name == "Label will be generated automatically":
            QtGui.QMessageBox.warning(None, "Error", "Please enter a valid section name")
            return False

        section_type = self.section_type_combo.currentText()
        standard_section = self.standard_section_combo.currentText()

        # Collect dimensions
        dimensions = {}
        if hasattr(self, 'height_input') and self.height_input.isVisible():
            dimensions['Height'] = self.height_input.value()
        if hasattr(self, 'width_input') and self.width_input.isVisible():
            dimensions['Width'] = self.width_input.value()
        if hasattr(self, 'thickness_input') and self.thickness_input.isVisible():
            dimensions['Thickness'] = self.thickness_input.value()
        if hasattr(self, 'web_thickness_input') and self.web_thickness_input.isVisible():
            dimensions['WebThickness'] = self.web_thickness_input.value()
        if hasattr(self, 'flange_thickness_input') and self.flange_thickness_input.isVisible():
            dimensions['FlangeThickness'] = self.flange_thickness_input.value()

        try:
            # Create the section using the features module
            section = create_section(
                self,  # Pass self reference for access to inputs
                section_type=section_type,
                section_type=standard_section,
                )

            # Set the label
            section.Label = section_name

            # Add to sections group
            group = make_section_group()
            group.addObject(section)

            return True

        except Exception as e:
            QtGui.QMessageBox.critical(None, "Error", f"Failed to create section:\n{str(e)}")
            return False

    def reject(self):
        return True

    def getStandardButtons(self):
        return QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel