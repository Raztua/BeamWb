# ui/dialog_MaterialModifier.py
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtGui, QtCore


class MaterialModifierTaskPanel:
    """Task panel for modifying existing materials"""

    def __init__(self):
        self.form = QtGui.QWidget()
        self.form.setWindowTitle("Modify Materials")
        self.form.resize(400, 300)
        self.selected_materials = []
        self.setup_ui()

    def setup_ui(self):
        layout = QtGui.QVBoxLayout(self.form)

        # Selection Info
        self.info_label = QtGui.QLabel("No materials selected")
        layout.addWidget(self.info_label)

        # Property Inputs
        form_layout = QtGui.QFormLayout()
        self.e_input = QtGui.QLineEdit()
        self.e_input.setPlaceholderText("Young's Modulus (MPa)")
        form_layout.addRow("E (MPa):", self.e_input)

        self.g_input = QtGui.QLineEdit()
        self.g_input.setPlaceholderText("Shear Modulus (MPa)")
        form_layout.addRow("G (MPa):", self.g_input)

        self.rho_input = QtGui.QLineEdit()
        self.rho_input.setPlaceholderText("Density (kg/m3)")
        form_layout.addRow("Density:", self.rho_input)

        layout.addLayout(form_layout)
        layout.addStretch()

    def update_inputs(self):
        """Pre-fill inputs if materials are selected"""
        if not self.selected_materials:
            return

        # Use the first selected material as the baseline for pre-filling
        mat = self.selected_materials[0]

        # Helper to get the value regardless of whether it is a Quantity or float
        def get_val(prop, unit_str):
            val = getattr(mat, prop, 0)
            if hasattr(val, "getValueAs"):
                # Returns the float value converted to the requested unit
                return val.getValueAs(unit_str).Value
            else:
                # Fallback for raw floats (assumes document units)
                return float(val)

        # Fill the text fields
        self.e_input.setText(f"{get_val('YoungsModulus','MPa'):.0f}")
        self.g_input.setText(f"{get_val('ShearModulus','MPa'):.0f}")
        self.rho_input.setText(f"{get_val('Density','kg/m^3'):.2f}")

        # Update the info label to show what is being edited
        count = len(self.selected_materials)
        if count == 1:
            self.info_label.setText(f"Modifying: {mat.Label}")
        else:
            self.info_label.setText(f"Modifying {count} materials (Values from {mat.Label})")
    def apply_changes(self):
        if not self.selected_materials: return False

        for mat in self.selected_materials:
            try:
                if self.e_input.text(): mat.YoungsModulus = float(self.e_input.text())
                if self.g_input.text(): mat.ShearModulus = float(self.g_input.text())
                if self.rho_input.text(): mat.Density = float(self.rho_input.text())
            except ValueError:
                continue

        App.ActiveDocument.recompute()
        return True

    def getStandardButtons(self):
        return QtGui.QDialogButtonBox.Apply | QtGui.QDialogButtonBox.Close

    def clicked(self, button):
        if button == QtGui.QDialogButtonBox.Apply:
            self.apply_changes()
        elif button == QtGui.QDialogButtonBox.Close:
            Gui.Control.closeDialog()


def show_material_modifier(materials=None):
    if hasattr(Gui, 'Control') and Gui.Control.activeDialog():
        Gui.Control.closeDialog()

    panel = MaterialModifierTaskPanel()
    if materials:
        panel.selected_materials = materials
        panel.update_inputs()  # Ensure inputs update after materials are assigned

    Gui.Control.showDialog(panel)
    return panel