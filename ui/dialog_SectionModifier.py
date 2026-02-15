# ui/dialog_SectionModifier.py
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtGui, QtCore
from features.sections import PROFILE_TYPES
from features.sectionLibrary import STANDARD_PROFILES


class SectionModifierTaskPanel:
    """Task panel for modifying existing sections"""

    def __init__(self):
        self.form = QtGui.QWidget()
        self.form.setWindowTitle("Modify Sections")
        self.form.resize(450, 550)

        self.selected_sections = []
        self.setup_ui()
        self.sync_with_selection()

    def setup_ui(self):
        layout = QtGui.QVBoxLayout(self.form)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # 1. Selection Info
        selection_group = QtGui.QGroupBox("Section Selection")
        sel_layout = QtGui.QVBoxLayout()
        self.section_list = QtGui.QListWidget()
        self.section_list.setSelectionMode(QtGui.QListWidget.ExtendedSelection)
        self.section_list.setMaximumHeight(80)
        sel_layout.addWidget(self.section_list)

        self.sync_btn = QtGui.QPushButton("Sync with Tree Selection")
        self.sync_btn.clicked.connect(self.sync_with_selection)
        sel_layout.addWidget(self.sync_btn)
        selection_group.setLayout(sel_layout)
        layout.addWidget(selection_group)

        # 2. Profile Definition
        type_group = QtGui.QGroupBox("Modify Profile Type")
        type_layout = QtGui.QFormLayout()

        self.profile_type_combo = QtGui.QComboBox()
        self.profile_type_combo.addItem("Keep current")
        self.profile_type_combo.addItems(PROFILE_TYPES)
        self.profile_type_combo.currentIndexChanged.connect(self.update_standard_type_combo)
        type_layout.addRow("Shape Family:", self.profile_type_combo)

        self.section_type_combo = QtGui.QComboBox()
        self.section_type_combo.currentIndexChanged.connect(self.update_standard_section_combo)
        type_layout.addRow("Standard Type:", self.section_type_combo)

        self.section_id_combo = QtGui.QComboBox()
        type_layout.addRow("Profile Size:", self.section_id_combo)

        type_group.setLayout(type_layout)
        layout.addWidget(type_group)

        # 3. Dimensions Override
        dim_group = QtGui.QGroupBox("Manual Dimension Override (mm)")
        self.dim_layout = QtGui.QGridLayout()
        self.inputs = {}
        fields = ["Height", "Width", "Thickness", "WebThickness", "FlangeThickness"]

        for i, name in enumerate(fields):
            self.dim_layout.addWidget(QtGui.QLabel(f"{name}:"), i, 0)
            edit = QtGui.QLineEdit()
            edit.setPlaceholderText("No change")
            self.dim_layout.addWidget(edit, i, 1)
            self.inputs[name] = edit

        dim_group.setLayout(self.dim_layout)
        layout.addWidget(dim_group)
        layout.addStretch()

    def sync_with_selection(self):
        """Finds all SectionFeatures in the current selection"""
        self.selected_sections = []
        self.section_list.clear()
        for obj in Gui.Selection.getSelection():
            if hasattr(obj, "Type") and obj.Type == "SectionFeature":
                self.selected_sections.append(obj)
                self.section_list.addItem(obj.Label)

    def update_standard_type_combo(self):
        current = self.profile_type_combo.currentText()
        self.section_type_combo.clear()
        if current in STANDARD_PROFILES:
            self.section_type_combo.addItems(sorted(STANDARD_PROFILES[current].keys()))
        else:
            self.section_type_combo.addItem("Custom")

    def update_standard_section_combo(self):
        shape = self.profile_type_combo.currentText()
        stype = self.section_type_combo.currentText()
        self.section_id_combo.clear()
        self.section_id_combo.addItem("Custom")
        if shape in STANDARD_PROFILES and stype in STANDARD_PROFILES[shape]:
            self.section_id_combo.addItems(sorted(STANDARD_PROFILES[shape][stype].keys()))

    def apply_changes(self):
        if not self.selected_sections:
            return False

        profile_type = self.profile_type_combo.currentText()
        section_type = self.section_type_combo.currentText()
        section_id = self.section_id_combo.currentText()

        for sec in self.selected_sections:
            sec.Proxy.flagModification = True

            # Apply Standard Profile
            if profile_type != "Keep current":
                sec.ProfileType = profile_type
                sec.SectionType = section_type
                sec.SectionId = section_id

            # Apply Dimension Overrides
            for name, edit in self.inputs.items():
                val = edit.text().strip()
                if val and hasattr(sec, name):
                    setattr(sec, name, App.Units.Quantity(float(val), App.Units.Length))

            sec.Proxy.flagModification = False
            sec.Proxy.execute(sec)

        App.ActiveDocument.recompute()
        return True

    def getStandardButtons(self):
        return QtGui.QDialogButtonBox.Apply | QtGui.QDialogButtonBox.Close

    def clicked(self, button):
        if button == QtGui.QDialogButtonBox.Apply:
            self.apply_changes()
        elif button == QtGui.QDialogButtonBox.Close:
            Gui.Control.closeDialog()


def show_section_modifier(sections=None):
    """Show the section modifier with optional pre-selection"""
    if hasattr(Gui, 'Control') and Gui.Control.activeDialog():
        Gui.Control.closeDialog()

    panel = SectionModifierTaskPanel()

    if sections:
        panel.selected_sections = sections
        # Sync the UI list and FreeCAD selection
        Gui.Selection.clearSelection()
        for sec in sections:
            Gui.Selection.addSelection(sec)
        panel.sync_with_selection()

    Gui.Control.showDialog(panel)
    return panel