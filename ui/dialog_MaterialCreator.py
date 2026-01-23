import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtGui, QtCore
from features.material import create_steel_material, create_custom_material, STEEL_GRADES, MATERIAL_TYPES


class MaterialCreatorTaskPanel:
    """Task panel for creating materials"""

    def __init__(self):
        self.form = QtGui.QWidget()
        self.form.setWindowTitle("Material Creator")
        self.setup_ui()

    def setup_ui(self):
        layout = QtGui.QVBoxLayout(self.form)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Material Type Selection
        type_group = QtGui.QGroupBox("1. Select Material Type")
        type_layout = QtGui.QVBoxLayout()
        self.material_type_combo = QtGui.QComboBox()
        self.material_type_combo.addItems(MATERIAL_TYPES)
        self.material_type_combo.currentIndexChanged.connect(self.update_ui)
        type_layout.addWidget(self.material_type_combo)
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)

        # Steel Grade Selection (for steel materials)
        self.steel_group = QtGui.QGroupBox("2. Select Steel Grade")
        steel_layout = QtGui.QVBoxLayout()
        self.steel_grade_combo = QtGui.QComboBox()
        self.steel_grade_combo.addItems(STEEL_GRADES)
        steel_layout.addWidget(self.steel_grade_combo)
        self.steel_group.setLayout(steel_layout)
        layout.addWidget(self.steel_group)

        # Custom Material Properties
        self.custom_group = QtGui.QGroupBox("2. Custom Material Properties")
        custom_layout = QtGui.QFormLayout()

        self.youngs_input = QtGui.QDoubleSpinBox()
        self.youngs_input.setRange(1000, 1000000)
        self.youngs_input.setValue(210000)
        self.youngs_input.setSuffix(" MPa")
        self.youngs_input.setSingleStep(1000)
        custom_layout.addRow("Young's Modulus:", self.youngs_input)

        self.poisson_input = QtGui.QDoubleSpinBox()
        self.poisson_input.setRange(0.0, 0.5)
        self.poisson_input.setValue(0.3)
        self.poisson_input.setSingleStep(0.01)
        custom_layout.addRow("Poisson's Ratio:", self.poisson_input)

        self.density_input = QtGui.QDoubleSpinBox()
        self.density_input.setRange(1, 20000)
        self.density_input.setValue(7850)
        self.density_input.setSuffix(" kg/m³")
        self.density_input.setSingleStep(100)
        custom_layout.addRow("Density:", self.density_input)

        self.yield_input = QtGui.QDoubleSpinBox()
        self.yield_input.setRange(0, 2000)
        self.yield_input.setValue(355)
        self.yield_input.setSuffix(" MPa")
        self.yield_input.setSingleStep(50)
        custom_layout.addRow("Yield Strength:", self.yield_input)

        self.tensile_input = QtGui.QDoubleSpinBox()
        self.tensile_input.setRange(0, 2000)
        self.tensile_input.setValue(510)
        self.tensile_input.setSuffix(" MPa")
        self.tensile_input.setSingleStep(50)
        custom_layout.addRow("Tensile Strength:", self.tensile_input)

        self.custom_group.setLayout(custom_layout)
        layout.addWidget(self.custom_group)

        # Material Identification
        id_group = QtGui.QGroupBox("3. Material Identification")
        id_layout = QtGui.QFormLayout()

        self.material_name_input = QtGui.QLineEdit()
        self.material_name_input.textChanged.connect(self.update_label_preview)
        id_layout.addRow("Material Name:", self.material_name_input)

        self.label_preview = QtGui.QLabel("Label will be generated automatically")
        id_layout.addRow("Material Label:", self.label_preview)

        id_group.setLayout(id_layout)
        layout.addWidget(id_group)

        layout.addStretch()

        # Set initial UI state
        self.update_ui()
        self.update_label_preview()

    def update_ui(self):
        material_type = self.material_type_combo.currentText()

        if material_type == "Steel":
            self.steel_group.setVisible(True)
            self.custom_group.setVisible(False)
        else:
            self.steel_group.setVisible(False)
            self.custom_group.setVisible(True)

    def update_label_preview(self):
        material_type = self.material_type_combo.currentText()
        custom_name = self.material_name_input.text().strip()

        if material_type == "Steel":
            steel_grade = self.steel_grade_combo.currentText()
            if custom_name:
                self.label_preview.setText(custom_name)
            else:
                self.label_preview.setText(f"Steel {steel_grade}")
        else:
            if custom_name:
                self.label_preview.setText(custom_name)
            else:
                self.label_preview.setText(f"Custom {material_type}")

    def create_material(self):
        """Create the material logic"""
        material_type = self.material_type_combo.currentText()
        custom_name = self.material_name_input.text().strip()
        material = None

        if material_type == "Steel":
            steel_grade = self.steel_grade_combo.currentText()
            material = create_steel_material(steel_grade, custom_name)
        else:
            if not custom_name:
                QtGui.QMessageBox.warning(None, "Error", "Please enter a material name for custom materials")
                return False

            material = create_custom_material(
                name=custom_name,
                youngs_modulus=self.youngs_input.value(),
                poissons_ratio=self.poisson_input.value(),
                density=self.density_input.value(),
                yield_strength=self.yield_input.value(),
                tensile_strength=self.tensile_input.value()
            )

        if material:
            # Set the final label
            final_label = self.label_preview.text()
            if final_label and final_label != "Label will be generated automatically":
                material.Label = final_label

            return True

        return False

    def getStandardButtons(self):
        return QtGui.QDialogButtonBox.Apply | QtGui.QDialogButtonBox.Close

    def clicked(self, button):
        if button == QtGui.QDialogButtonBox.Apply:
            self.create_material()
            App.ActiveDocument.recompute()
        elif button == QtGui.QDialogButtonBox.Close:
            Gui.Control.closeDialog()
        return True

    def reject(self):
        return True

    def accept(self):
        if self.create_material():
            Gui.Control.closeDialog()
            return True
        return False