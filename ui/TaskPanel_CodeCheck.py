# ui/TaskPanel_CodeCheck.py
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtGui, QtCore
from features.CodeCheck import make_code_check_feature
from ui.dialog_CodeCheckResults import show_code_check_results
from standards.Registry import StandardsRegistry


class CodeCheckTaskPanel:
    def __init__(self, feature):
        self.feature = feature
        self.form = QtGui.QWidget()
        self.form.setWindowTitle("Code Check Setup")
        self.input_widgets = {}
        self.setup_ui()

    def setup_ui(self):
        layout = QtGui.QVBoxLayout(self.form)

        # --- Standard Selection ---
        layout.addWidget(QtGui.QLabel("Design Standard:"))
        self.standard_combo = QtGui.QComboBox()
        avail_stds = StandardsRegistry.get_available_names()
        if not avail_stds: avail_stds = ["None"]
        self.standard_combo.addItems(avail_stds)

        # Select current
        curr = self.feature.Standard
        idx = self.standard_combo.findText(curr)
        if idx >= 0: self.standard_combo.setCurrentIndex(idx)

        self.standard_combo.currentTextChanged.connect(self.on_standard_changed)
        layout.addWidget(self.standard_combo)

        # --- Dynamic Settings Area ---
        layout.addWidget(QtGui.QLabel("Global Parameters:"))

        self.scroll = QtGui.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QtGui.QFrame.NoFrame)

        self.settings_widget = QtGui.QWidget()
        self.settings_layout = QtGui.QFormLayout(self.settings_widget)
        self.scroll.setWidget(self.settings_widget)

        layout.addWidget(self.scroll)

        # Populate initial settings
        self.populate_settings()

        # --- Action Buttons ---
        btn_layout = QtGui.QHBoxLayout()

        self.calc_btn = QtGui.QPushButton("Calculate & Show Results")
        self.calc_btn.clicked.connect(self.on_calculate_show)
        self.calc_btn.setStyleSheet("font-weight: bold; padding: 6px;")
        btn_layout.addWidget(self.calc_btn)

        layout.addLayout(btn_layout)

    def populate_settings(self):
        """Build input widgets based on the active standard's properties"""
        # Clear existing
        while self.settings_layout.count():
            item = self.settings_layout.takeAt(0)
            w = item.widget()
            if w: w.deleteLater()
        self.input_widgets = {}

        if not hasattr(self.feature, "ManagedProperties"): return

        props = self.feature.ManagedProperties
        if not props:
            self.settings_layout.addRow(QtGui.QLabel("No parameters."))
            return

        for prop_name in props:
            if not hasattr(self.feature, prop_name): continue

            # FILTER: Skip LCr ratios (Buckling lengths) in global panel
            # Checks for Lcr_y_ratio, Lcr_z_ratio, buckling_length, etc.
            if "Lcr_" in prop_name or "buckling_length" in prop_name.lower():
                continue

            val = getattr(self.feature, prop_name)

            label = QtGui.QLabel(prop_name.replace("_", " ") + ":")
            widget = None

            # Create appropriate widget based on value type
            if isinstance(val, bool):
                widget = QtGui.QCheckBox()
                widget.setChecked(val)

            elif isinstance(val, (int, float)):
                widget = QtGui.QDoubleSpinBox()
                widget.setRange(-1e9, 1e9)
                widget.setDecimals(3)
                widget.setValue(float(val))
                widget.setSingleStep(0.01 if abs(val) < 10 else 1.0)

            elif isinstance(val, str):
                # Check for Enumeration
                type_id = self.feature.getTypeIdOfProperty(prop_name)
                if type_id == "App::PropertyEnumeration":
                    widget = QtGui.QComboBox()
                    widget.addItems(self.feature.getEnumerationsOfProperty(prop_name))
                    idx = widget.findText(val)
                    if idx >= 0: widget.setCurrentIndex(idx)
                else:
                    widget = QtGui.QLineEdit(val)

            elif hasattr(val, "Value"):  # Quantity
                widget = QtGui.QDoubleSpinBox()
                widget.setRange(-1e9, 1e9)
                widget.setDecimals(3)
                widget.setValue(val.Value)
                label.setText(f"{prop_name} [{val.UserString.split(' ')[-1]}]:")

            if widget:
                self.settings_layout.addRow(label, widget)
                self.input_widgets[prop_name] = widget

    def on_standard_changed(self, text):
        if not text: return
        self.feature.Standard = text
        App.ActiveDocument.recompute()
        self.populate_settings()

    def on_calculate_show(self):
        """Apply settings, recompute, and open results"""
        # 1. Apply values from widgets to feature
        for prop_name, widget in self.input_widgets.items():
            if isinstance(widget, QtGui.QCheckBox):
                setattr(self.feature, prop_name, widget.isChecked())
            elif isinstance(widget, QtGui.QDoubleSpinBox):
                setattr(self.feature, prop_name, widget.value())
            elif isinstance(widget, QtGui.QComboBox):
                setattr(self.feature, prop_name, widget.currentText())
            elif isinstance(widget, QtGui.QLineEdit):
                setattr(self.feature, prop_name, widget.text())

        # 2. Recompute
        self.feature.touch()
        App.ActiveDocument.recompute()

        # 3. Show Results Dialog
        show_code_check_results(self.feature)

    def getStandardButtons(self):
        return QtGui.QDialogButtonBox.Close

    def reject(self):
        Gui.Control.closeDialog()


def show_code_check_task_panel():
    if hasattr(Gui, 'Control') and Gui.Control.activeDialog():
        Gui.Control.closeDialog()

    feature = make_code_check_feature()
    panel = CodeCheckTaskPanel(feature)
    Gui.Control.showDialog(panel)