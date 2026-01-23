import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtGui, QtCore
from features.LoadIDManager import create_load_id


class LoadIDTaskPanel:
    """Task panel for creating Load IDs"""

    def __init__(self):
        self.form = QtGui.QWidget()
        self.form.setWindowTitle("Create Load ID")
        self.load_color = QtGui.QColor(255, 0, 0)
        self.setup_ui()

    def setup_ui(self):
        layout = QtGui.QVBoxLayout(self.form)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Load ID Section
        load_id_group = QtGui.QGroupBox("Load ID Properties")
        load_id_layout = QtGui.QFormLayout()

        self.load_id_input = QtGui.QLineEdit("Load1")
        load_id_layout.addRow("Load ID Name:", self.load_id_input)

        self.color_btn = QtGui.QPushButton()
        self.color_btn.setStyleSheet("background-color: rgb(255, 0, 0)")
        self.color_btn.clicked.connect(self.choose_color)
        load_id_layout.addRow("Load Color:", self.color_btn)

        self.show_loads = QtGui.QCheckBox()
        self.show_loads.setChecked(True)
        load_id_layout.addRow("Show Loads:", self.show_loads)

        self.scale_input = QtGui.QDoubleSpinBox()
        self.scale_input.setValue(1.0)
        self.scale_input.setSingleStep(0.1)
        self.scale_input.setMinimum(0.1)
        self.scale_input.setMaximum(10.0)
        load_id_layout.addRow("Load Scale:", self.scale_input)

        load_id_group.setLayout(load_id_layout)
        layout.addWidget(load_id_group)

        layout.addStretch()

    def choose_color(self):
        color = QtGui.QColorDialog.getColor()
        if color.isValid():
            self.load_color = color
            self.color_btn.setStyleSheet(f"background-color: {color.name()}")

    def create_load_id_and_apply(self):
        """Logic for creating Load ID and applying properties"""
        load_id_name = self.load_id_input.text()
        if not load_id_name:
            QtGui.QMessageBox.warning(None, "Error", "Please enter a Load ID name")
            return False

        load_id = create_load_id(load_id_name)
        if load_id:
            if hasattr(load_id, "ViewObject"):
                load_id.ViewObject.LoadColor = (
                    self.load_color.red() / 255.0,
                    self.load_color.green() / 255.0,
                    self.load_color.blue() / 255.0
                )
                load_id.ViewObject.ShowLoads = self.show_loads.isChecked()
                load_id.ViewObject.LoadScale = self.scale_input.value()

            return True
        return False



    def getStandardButtons(self):
        return QtGui.QDialogButtonBox.Apply | QtGui.QDialogButtonBox.Close

    def clicked(self, button):
        App.ActiveDocument.recompute()
        if button == QtGui.QDialogButtonBox.Apply:
            self.create_load_id_and_apply()
        elif button == QtGui.QDialogButtonBox.Close:
            Gui.Control.closeDialog()

        return True

    def reject(self):
        return True

    def accept(self):
        if self.create_load_id_and_apply():
            Gui.Control.closeDialog()
            return True
        return False