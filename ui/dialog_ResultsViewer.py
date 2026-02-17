# dialog_ResultsViewer.py
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtGui, QtCore
from features.Solver import DIAGRAM_TYPE_MAP


class ResultsViewerTaskPanel:
    """Task panel for viewing and controlling analysis results"""

    def __init__(self):
        self.form = QtGui.QWidget()
        self.form.setWindowTitle("Results Viewer")
        self.solver = None
        self.diagram_types = ["None"] + list(DIAGRAM_TYPE_MAP.keys())

        self.setup_ui()
        self.update_from_solver()

    def setup_ui(self):
        layout = QtGui.QVBoxLayout(self.form)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Title
        title = QtGui.QLabel("Results Viewer")
        title.setStyleSheet("font-weight: bold; font-size: 16px; color: #2c3e50;")
        layout.addWidget(title)

        # Separator
        layout.addWidget(self.create_separator())

        # Solver Status
        status_group = QtGui.QGroupBox("Solver Status")
        status_layout = QtGui.QVBoxLayout()

        self.status_label = QtGui.QLabel("No analysis results available")
        self.status_label.setStyleSheet("font-weight: bold; padding: 5px;")
        status_layout.addWidget(self.status_label)

        self.results_info = QtGui.QLabel("")
        status_layout.addWidget(self.results_info)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # Load Case Selection
        load_case_group = QtGui.QGroupBox("Load Case")
        load_case_layout = QtGui.QVBoxLayout()

        load_case_layout.addWidget(QtGui.QLabel("Select Load Case:"))
        self.load_case_combo = QtGui.QComboBox()
        self.load_case_combo.currentTextChanged.connect(self.on_load_case_changed)
        load_case_layout.addWidget(self.load_case_combo)

        load_case_group.setLayout(load_case_layout)
        layout.addWidget(load_case_group)

        # Deformation Settings
        deform_group = QtGui.QGroupBox("Deformation Display")
        deform_layout = QtGui.QGridLayout()

        deform_layout.addWidget(QtGui.QLabel("Scale Factor:"), 0, 0)
        self.deform_scale = QtGui.QDoubleSpinBox()
        self.deform_scale.setRange(0.0, 1000.0)
        self.deform_scale.setValue(10.0)
        self.deform_scale.setSingleStep(0.1)
        self.deform_scale.setDecimals(2)
        self.deform_scale.valueChanged.connect(self.on_deform_scale_changed)
        deform_layout.addWidget(self.deform_scale, 0, 1)

        deform_group.setLayout(deform_layout)
        layout.addWidget(deform_group)

        # Diagram Settings
        diagram_group = QtGui.QGroupBox("Internal Force Diagrams")
        diagram_layout = QtGui.QGridLayout()

        diagram_layout.addWidget(QtGui.QLabel("Diagram Type:"), 0, 0)
        self.diagram_combo = QtGui.QComboBox()
        self.diagram_combo.addItems(self.diagram_types)
        self.diagram_combo.currentTextChanged.connect(self.on_diagram_type_changed)
        diagram_layout.addWidget(self.diagram_combo, 0, 1)

        diagram_layout.addWidget(QtGui.QLabel("Scale Factor:"), 1, 0)
        self.diagram_scale = QtGui.QDoubleSpinBox()
        self.diagram_scale.setRange(0.0, 100.0)
        self.diagram_scale.setValue(1)
        self.diagram_scale.setSingleStep(0.1)
        self.diagram_scale.setDecimals(2)
        self.diagram_scale.valueChanged.connect(self.on_diagram_scale_changed)
        diagram_layout.addWidget(self.diagram_scale, 1, 1)

        diagram_group.setLayout(diagram_layout)
        layout.addWidget(diagram_group)

        # Delete Results Button
        self.delete_button = QtGui.QPushButton("Delete All Results")
        self.delete_button.setIcon(QtGui.QIcon.fromTheme("edit-delete"))
        self.delete_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #ecf0f1;
                color: #95a5a6;
            }
        """)
        self.delete_button.clicked.connect(self.delete_all_results)
        layout.addWidget(self.delete_button)

        layout.addStretch()

    def create_separator(self):
        line = QtGui.QFrame()
        line.setFrameShape(QtGui.QFrame.HLine)
        line.setFrameShadow(QtGui.QFrame.Sunken)
        return line

    def update_from_solver(self):
        """Update the dialog with current solver state"""
        self.solver = App.ActiveDocument.getObject("Solver")

        if not self.solver or not self.solver.Results.load_cases:
            self.status_label.setText("No analysis results available")
            self.status_label.setStyleSheet(
                "font-weight: bold; color: #e74c3c; background-color: #f9ebea; padding: 5px;")
            self.results_info.setText("Run an analysis first")

            # Disable controls
            self.load_case_combo.clear()
            self.load_case_combo.addItem("None")
            self.load_case_combo.setEnabled(False)
            self.deform_scale.setEnabled(False)
            self.diagram_combo.setEnabled(False)
            self.diagram_scale.setEnabled(False)
            self.delete_button.setEnabled(False)

        else:
            self.status_label.setText("Analysis Results Available")
            self.status_label.setStyleSheet(
                "font-weight: bold; color: #27ae60; background-color: #e8f6f3; padding: 5px;")

            # Update load cases
            load_cases = list(self.solver.Results.load_cases.keys())
            current_lc = self.solver.LoadCase if hasattr(self.solver, 'LoadCase') else "None"

            self.load_case_combo.clear()
            self.load_case_combo.addItems(load_cases)

            if current_lc in load_cases:
                self.load_case_combo.setCurrentText(current_lc)

            # Update deformation scale
            if hasattr(self.solver, 'DeformationScale'):
                self.deform_scale.setValue(self.solver.DeformationScale)

            # Update diagram type
            if hasattr(self.solver, 'DiagramType'):
                current_diagram = self.solver.DiagramType
                if current_diagram in self.diagram_types:
                    self.diagram_combo.setCurrentText(current_diagram)

            # Update diagram scale
            if hasattr(self.solver, 'DiagramScale'):
                self.diagram_scale.setValue(self.solver.DiagramScale)

            # Update view properties
            if self.solver.ViewObject:
                vobj = self.solver.ViewObject

            # Enable controls
            self.load_case_combo.setEnabled(True)
            self.deform_scale.setEnabled(True)
            self.diagram_combo.setEnabled(True)
            self.diagram_scale.setEnabled(True)
            self.delete_button.setEnabled(True)

            # Update results info
            num_cases = len(load_cases)
            self.results_info.setText(f"{num_cases} load case(s) available")

    def on_load_case_changed(self, text):
        """Handle load case selection change"""
        if self.solver and text:
            self.solver.LoadCase = text


    def on_deform_scale_changed(self, value):
        """Handle deformation scale change"""
        if self.solver:
            self.solver.DeformationScale = value


    def on_diagram_type_changed(self, text):
        """Handle diagram type change"""
        if self.solver and text in self.diagram_types:
            self.solver.DiagramType = text


    def on_diagram_scale_changed(self, value):
        """Handle diagram scale change"""
        if self.solver:
            self.solver.DiagramScale = value

    def delete_all_results(self):
        """Delete all analysis results"""
        if not self.solver:
            return

        reply = QtGui.QMessageBox.question(
            self.form,
            "Delete All Results",
            "Are you sure you want to delete all analysis results?\n\n"
            "This will remove all calculated displacements, reactions, and internal forces.",
            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
            QtGui.QMessageBox.No
        )

        if reply == QtGui.QMessageBox.Yes:
            try:
                # Clear the results object
                from features.SolverEngine import FEMResult
                self.solver.Results = FEMResult()

                # Reset solver properties
                self.solver.LoadCase = ["None"]
                self.solver.DiagramType = ["None"] + list(DIAGRAM_TYPE_MAP.keys())
                self.solver.DiagramScale = 1.0
                self.solver.DeformationScale = 1.0

                # Clear result groups
                self._clear_result_groups()

                # Reset view properties
                if self.solver.ViewObject:
                    self.solver.ViewObject.ShowDeformedShape = True
                    self.solver.ViewObject.ShowUndeformedShape = True


                # Update the dialog
                self.update_from_solver()

                QtGui.QMessageBox.information(
                    self.form,
                    "Results Deleted",
                    "All analysis results have been deleted successfully."
                )

            except Exception as e:
                App.Console.PrintError(f"Error deleting results: {str(e)}\n")
                QtGui.QMessageBox.critical(
                    self.form,
                    "Error",
                    f"Failed to delete results: {str(e)}"
                )

    def _clear_result_groups(self):
        """Clear all result visualization objects"""
        doc = App.ActiveDocument
        if not doc:
            return

        # Clear NodesResult group
        nodes_result = doc.getObject("NodesResult")
        if nodes_result:
            for obj in list(nodes_result.Group):
                doc.removeObject(obj.Name)

        # Clear BeamsResult group
        beams_result = doc.getObject("BeamsResult")
        if beams_result:

            for obj in list(beams_result.Group):
                doc.removeObject(obj.Name)

    def getStandardButtons(self):
        """Return standard buttons for task panel"""
        return QtGui.QDialogButtonBox.Close

    def clicked(self, button):
        """Handle button clicks"""
        App.ActiveDocument.recompute()
        if button == QtGui.QDialogButtonBox.Close:
            Gui.Control.closeDialog()

    def reject(self):
        """Cancel operation"""
        return True

    def accept(self):
        """Apply changes and close"""
        Gui.Control.closeDialog()
        return True


def show_results_viewer():
    """Show the results viewer task panel"""
    # Close any existing task panel first
    if hasattr(Gui, 'Control') and Gui.Control.activeDialog():
        Gui.Control.closeDialog()

    panel = ResultsViewerTaskPanel()
    Gui.Control.showDialog(panel)
    return panel