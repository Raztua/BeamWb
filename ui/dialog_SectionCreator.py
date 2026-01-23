import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtGui, QtCore
import random
from features.sections import create_section, PROFILE_TYPES, SECTION_COLORS
from features.sectionLibrary import STANDARD_PROFILES


class SectionCreatorTaskPanel:
    """Task panel for creating sections with 3-level cascading selection"""

    def __init__(self):
        self.form = QtGui.QWidget()
        self.form.setWindowTitle("Section Creator")
        self.current_color = random.choice(SECTION_COLORS)

        self.setup_ui()

        # Initialize the cascading combos
        self.update_standard_type_combo()
        self.update_label()
        self.update_ui()

    def setup_ui(self):
        layout = QtGui.QVBoxLayout(self.form)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # --- 1. Section Shape Family (Level 1) ---
        type_group = QtGui.QGroupBox("1. Shape Family")
        type_layout = QtGui.QVBoxLayout()
        self.profile_type_combo = QtGui.QComboBox()
        self.profile_type_combo.addItems(PROFILE_TYPES)

        # Connect: Level 1 -> Updates Level 2
        self.profile_type_combo.currentIndexChanged.connect(self.update_standard_type_combo)
        self.profile_type_combo.currentIndexChanged.connect(self.update_ui)

        type_layout.addWidget(self.profile_type_combo)
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)

        # --- 2. Standard Type (Level 2 - NEW) ---
        # e.g., Select "HEA" or "HEB" here
        subtype_group = QtGui.QGroupBox("2. Standard Type")
        subtype_layout = QtGui.QVBoxLayout()
        self.section_type_combo = QtGui.QComboBox()

        # Connect: Level 2 -> Updates Level 3
        self.section_type_combo.currentIndexChanged.connect(self.update_standard_section_combo)

        subtype_layout.addWidget(self.section_type_combo)
        subtype_group.setLayout(subtype_layout)
        layout.addWidget(subtype_group)

        # --- 3. Standard Section Size (Level 3) ---
        # e.g., Select "HEA 100" here
        section_group = QtGui.QGroupBox("3. Profile Size")
        section_layout = QtGui.QVBoxLayout()
        self.section_combo = QtGui.QComboBox()
        self.section_combo.currentIndexChanged.connect(self.load_section_properties)
        section_layout.addWidget(self.section_combo)
        section_group.setLayout(section_layout)
        layout.addWidget(section_group)

        # --- 4. Dimensions ---
        dim_group = QtGui.QGroupBox("4. Dimensions")
        self.dim_layout = QtGui.QGridLayout()

        # Helper to create consistent dimension inputs with units
        def create_dim_input(val=0.0):
            sb = QtGui.QDoubleSpinBox()
            sb.setRange(0.1, 100000.0)
            sb.setDecimals(2)
            sb.setValue(val)
            sb.setSuffix(" mm")
            return sb

        # Initialize Inputs
        row = 0
        self.height_label = QtGui.QLabel("Height:")
        self.dim_layout.addWidget(self.height_label, row, 0)
        self.height_input = create_dim_input(100.0)
        self.dim_layout.addWidget(self.height_input, row, 1)
        row += 1

        self.width_label = QtGui.QLabel("Width:")
        self.dim_layout.addWidget(self.width_label, row, 0)
        self.width_input = create_dim_input(50.0)
        self.dim_layout.addWidget(self.width_input, row, 1)
        row += 1

        self.thickness_label = QtGui.QLabel("Thickness:")
        self.dim_layout.addWidget(self.thickness_label, row, 0)
        self.thickness_input = create_dim_input(5.0)
        self.dim_layout.addWidget(self.thickness_input, row, 1)
        row += 1

        # Specific inputs for I/H/T Shapes
        self.web_thickness_label = QtGui.QLabel("Web Thickness:")
        self.dim_layout.addWidget(self.web_thickness_label, row, 0)
        self.web_thickness_input = create_dim_input(5.0)
        self.dim_layout.addWidget(self.web_thickness_input, row, 1)
        row += 1

        self.flange_thickness_label = QtGui.QLabel("Flange Thickness:")
        self.dim_layout.addWidget(self.flange_thickness_label, row, 0)
        self.flange_thickness_input = create_dim_input(8.0)
        self.dim_layout.addWidget(self.flange_thickness_input, row, 1)
        row += 1

        dim_group.setLayout(self.dim_layout)
        layout.addWidget(dim_group)

        # --- 5. Identification ---
        id_group = QtGui.QGroupBox("5. Identification")
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

    def update_standard_type_combo(self):
        """
        NEW FUNCTION: Updates Level 2 (Standard Type) based on Level 1 (Shape Family).
        Examples: H-Shape -> [HEA, HEB, HEM]
        """
        current_shape = self.profile_type_combo.currentText()

        self.section_type_combo.blockSignals(True)
        self.section_type_combo.clear()

        # Check if the Shape Family exists in the Library
        if current_shape in STANDARD_PROFILES:
            # Get the types (keys of the second level dictionary)
            # Assuming structure: { "H-Shape": { "HEA": {...}, "HEB": {...} } }
            types = sorted(STANDARD_PROFILES[current_shape].keys())
            self.section_type_combo.addItems(types)
        else:
            # Fallback for shapes not in library (Rectangle, HSS, etc.)
            self.section_type_combo.addItem("Custom")

        self.section_type_combo.blockSignals(False)

        # Trigger update of Level 3
        self.update_standard_section_combo()

    def update_standard_section_combo(self):
        """
        UPDATED: Updates Level 3 (Profile Size) based on Level 2 (Standard Type).
        Examples: HEA -> [HEA 100, HEA 120]
        """
        current_shape = self.profile_type_combo.currentText()  # Level 1
        current_type = self.section_type_combo.currentText()  # Level 2

        self.section_combo.blockSignals(True)
        self.section_combo.clear()
        self.section_combo.addItem("Custom")

        # Validate existence in nested dictionary
        if (current_shape in STANDARD_PROFILES and
                current_type in STANDARD_PROFILES[current_shape]):

            # Get dimensions/profiles data
            type_data = STANDARD_PROFILES[current_shape][current_type]

            try:
                # Sort numerically if possible
                keys = sorted(type_data.keys(),
                              key=lambda x: int(''.join(filter(str.isdigit, x))) if any(c.isdigit() for c in x) else x)
            except:
                keys = sorted(type_data.keys())

            for section_name in keys:
                self.section_combo.addItem(section_name)

        self.section_combo.blockSignals(False)

        # Trigger property load and label update
        self.load_section_properties()
        self.update_label()

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
        """Pre-fill dimensions. Now traverses 3 levels of dictionary."""
        if self.section_combo.currentText() == "Custom":
            self.update_label()
            return

        profile_type = self.profile_type_combo.currentText()  # Level 1
        section_type = self.section_type_combo.currentText()  # Level 2
        section = self.section_combo.currentText()  # Level 3

        # Traverse nested library: Shape -> Type -> Name
        if (profile_type in STANDARD_PROFILES and
                section_type in STANDARD_PROFILES[profile_type] and
                section in STANDARD_PROFILES[profile_type][section_type]):

            data = STANDARD_PROFILES[profile_type][section_type][section]

            # Helper to safely block signals during update
            widgets = [self.height_input, self.width_input, self.thickness_input,
                       self.web_thickness_input, self.flange_thickness_input]
            for w in widgets: w.blockSignals(True)

            try:
                # 1. Height ('h')
                if 'h' in data:
                    self.height_input.setValue(float(data['h']))

                # 2. Width ('b') or Diameter ('d')
                if 'b' in data:
                    self.width_input.setValue(float(data['b']))
                elif 'd' in data:  # Tubular/Round
                    self.width_input.setValue(float(data['d']))
                elif 'Width' in data:
                    self.width_input.setValue(float(data['Width']))

                # 3. Thickness ('t' or 'tw' for simple shapes)
                if 't' in data:
                    self.thickness_input.setValue(float(data['t']))
                elif 'tw' in data and profile_type in ["U-Shape", "C-Shape"]:
                    self.thickness_input.setValue(float(data['tw']))

                # 4. Web Thickness ('tw')
                if 'tw' in data:
                    self.web_thickness_input.setValue(float(data['tw']))

                # 5. Flange Thickness ('tf')
                if 'tf' in data:
                    self.flange_thickness_input.setValue(float(data['tf']))

            except Exception as e:
                print(f"Error loading section properties: {e}")
            finally:
                for w in widgets: w.blockSignals(False)

            self.update_label()

    def update_ui(self):
        section_type = self.profile_type_combo.currentText()

        # Hide all inputs initially
        self.height_label.setVisible(False);
        self.height_input.setVisible(False)
        self.width_label.setVisible(False);
        self.width_input.setVisible(False)
        self.thickness_label.setVisible(False);
        self.thickness_input.setVisible(False)
        self.web_thickness_label.setVisible(False);
        self.web_thickness_input.setVisible(False)
        self.flange_thickness_label.setVisible(False);
        self.flange_thickness_input.setVisible(False)

        # Logic to show specific inputs based on Type
        if section_type in ["I-Shape", "H-Shape", "Asymmetric I-Shape"]:
            self.height_label.setVisible(True);
            self.height_input.setVisible(True)
            self.width_label.setVisible(True);
            self.width_input.setVisible(True)
            self.web_thickness_label.setVisible(True);
            self.web_thickness_input.setVisible(True)
            self.flange_thickness_label.setVisible(True);
            self.flange_thickness_input.setVisible(True)

        elif section_type == "T-Shape":
            self.height_label.setVisible(True);
            self.height_input.setVisible(True)
            self.width_label.setVisible(True);
            self.width_input.setVisible(True)
            self.web_thickness_label.setVisible(True);
            self.web_thickness_input.setVisible(True)
            self.flange_thickness_label.setVisible(True);
            self.flange_thickness_input.setVisible(True)

        elif section_type in ["L-Shape", "U-Shape", "C-Shape", "Rectangle", "HSS"]:
            self.height_label.setVisible(True);
            self.height_input.setVisible(True)
            self.width_label.setVisible(True);
            self.width_input.setVisible(True)
            if section_type != "Rectangle":
                self.thickness_label.setVisible(True);
                self.thickness_input.setVisible(True)

        elif section_type in ["Round Bar", "Tubular", "CHS"]:
            self.width_label.setVisible(True);
            self.width_input.setVisible(True)
            self.width_label.setText("Diameter:" if section_type == "Round Bar" else "Outer Diameter:")
            if section_type in ["Tubular", "CHS"]:
                self.thickness_label.setVisible(True);
                self.thickness_input.setVisible(True)
                self.thickness_label.setText("Wall Thickness:")
            else:
                self.width_label.setText("Diameter:")

    def update_label(self):
        profile_type = self.profile_type_combo.currentText()
        section_type = self.section_type_combo.currentText()
        section = self.section_combo.currentText()


        if section_type != "Custom":
            self.label_preview.setText(f"{section}")
        else:
            self.label_preview.setText(f"Custom {profile_type}")

    def accept(self):
        """Create the section"""
        section_name = self.label_preview.text()
        if not section_name:
            section_name = "Section"

        profile_type = self.profile_type_combo.currentText()
        section_type = self.section_type_combo.currentText()
        section = self.section_combo.currentText()
        try:
            # 1. Create the section using the features module
            section = create_section(
                profile_type=profile_type,
                section_type=section_type,
                section_id=section
            )
            # 2. Set the label
            section.Label = section_name

            # 3. Apply Dimensions Manually if Custom
            if section_type == "Custom":
                def set_dim(prop, widget):
                    if widget.isVisible():
                        val = widget.value()
                        if hasattr(section, prop):
                            setattr(section, prop, App.Units.Quantity(val, App.Units.Length))

                # Apply visible fields
                set_dim("Height", self.height_input)
                set_dim("Width", self.width_input)
                set_dim("Thickness", self.thickness_input)
                set_dim("WebThickness", self.web_thickness_input)
                set_dim("FlangeThickness", self.flange_thickness_input)
            # Ensure properties calculation triggers
            #if hasattr(section.Proxy, "execute"):
            #    section.Proxy.execute(section)
            #App.ActiveDocument.recompute()
            return True

        except Exception as e:
            QtGui.QMessageBox.critical(None, "Error", f"Failed to create section:\n{str(e)}")
            return False

    def reject(self):
        return True

    def getStandardButtons(self):
        return QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel