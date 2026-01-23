# ui/dialog_AnalysisSetup.py
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtGui, QtCore
from features.Solver import make_solver
from features.CodeCheck import make_code_check_feature
from standards.Registry import StandardsRegistry


class AnalysisSetupTaskPanel:
    """Task panel for setting up and controlling analysis"""

    def __init__(self, solver_obj=None):
        self.form = QtGui.QWidget()
        self.form.setWindowTitle("Analysis Setup")
        self.selected_nodes = []
        self.selection_callback = None
        self.is_picking = False
        self.temp_selected_nodes = []
        self.solver = solver_obj

        # Get existing CodeCheck to pre-fill selection and handle clearing
        self.code_check = make_code_check_feature()

        self.setup_ui()

    def setup_ui(self):
        layout = QtGui.QVBoxLayout(self.form)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Title
        title = QtGui.QLabel("Analysis Setup")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)

        # Solver Engine Selection
        engine_group = QtGui.QGroupBox("Solver Engine")
        engine_layout = QtGui.QVBoxLayout()

        self.engine_combo = QtGui.QComboBox()
        self.engine_combo.addItems(["PyNite"])
        # Set current solver engine if available
        if self.solver and hasattr(self.solver, "SolverEngine"):
            idx = self.engine_combo.findText(self.solver.SolverEngine)
            if idx >= 0: self.engine_combo.setCurrentIndex(idx)
        engine_layout.addWidget(self.engine_combo)

        engine_group.setLayout(engine_layout)
        layout.addWidget(engine_group)

        # Analysis Type
        analysis_group = QtGui.QGroupBox("Analysis Type")
        analysis_layout = QtGui.QVBoxLayout()

        self.analysis_combo = QtGui.QComboBox()
        self.analysis_combo.addItems(["Linear Static", "Modal", "Buckling"])
        # Set current analysis type if available
        if self.solver and hasattr(self.solver, "AnalysisType"):
            idx = self.analysis_combo.findText(self.solver.AnalysisType)
            if idx >= 0: self.analysis_combo.setCurrentIndex(idx)
        analysis_layout.addWidget(self.analysis_combo)

        analysis_group.setLayout(analysis_layout)
        layout.addWidget(analysis_group)

        # Code Check Selection
        check_group = QtGui.QGroupBox("Code Check Standard")
        check_layout = QtGui.QVBoxLayout()

        self.check_combo = QtGui.QComboBox()
        avail_stds = StandardsRegistry.get_available_names()
        if not avail_stds: avail_stds = ["None"]
        self.check_combo.addItems(avail_stds)

        # Set current standard
        if self.code_check and hasattr(self.code_check, "Standard"):
            idx = self.check_combo.findText(self.code_check.Standard)
            if idx >= 0: self.check_combo.setCurrentIndex(idx)

        check_layout.addWidget(self.check_combo)
        check_group.setLayout(check_layout)
        layout.addWidget(check_group)

        # Status display
        status_group = QtGui.QGroupBox("Status")
        status_layout = QtGui.QVBoxLayout()

        self.status_label = QtGui.QLabel("Ready")
        self.status_label.setStyleSheet("font-weight: bold; color: blue;")
        status_layout.addWidget(self.status_label)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        layout.addStretch()

        # Action Buttons
        button_layout = QtGui.QHBoxLayout()

        self.run_button = QtGui.QPushButton("Run Analysis")
        self.run_button.clicked.connect(self.run_analysis)
        button_layout.addWidget(self.run_button)

        self.clear_button = QtGui.QPushButton("Clear Results")
        self.clear_button.clicked.connect(self.clear_results)
        button_layout.addWidget(self.clear_button)

        self.close_button = QtGui.QPushButton("Close")
        self.close_button.clicked.connect(self.close_dialog)
        button_layout.addWidget(self.close_button)

        layout.addLayout(button_layout)

    def run_analysis(self):
        """Run the analysis and then the code check"""
        # Ensure we have a solver object
        if not self.solver:
            self.solver = make_solver()

        # Update solver properties from dialog
        self.solver.SolverEngine = self.engine_combo.currentText()
        self.solver.AnalysisType = self.analysis_combo.currentText()

        # Update CodeCheck properties
        if not self.code_check:
            self.code_check = make_code_check_feature()
        self.code_check.Standard = self.check_combo.currentText()

        self.status_label.setText("Running Solver...")
        QtGui.QApplication.processEvents()

        # Run analysis (Recompute triggers the Solver.execute because RunAnalysis=True)
        self.solver.RunAnalysis = True
        App.ActiveDocument.recompute()

        # Run Code Check
        self.status_label.setText("Running Code Check...")
        QtGui.QApplication.processEvents()

        # Mark CodeCheck for recompute to ensure it picks up new solver results
        self.code_check.touch()
        App.ActiveDocument.recompute()

        # Update status
        self.status_label.setText("Analysis & Check complete")
        self.status_label.setStyleSheet("font-weight: bold; color: green;")

        # Show success message
        QtGui.QMessageBox.information(self.form, "Complete",
                                      "Analysis and Code Check completed successfully.")

    def clear_results(self):
        """Clear analysis and code check results"""
        if not self.solver:
            QtGui.QMessageBox.warning(self.form, "No Solver",
                                      "No solver object found.")
            return

        # 1. Clear Solver Results
        self.solver.Results = None

        # Clear result objects (Visualizations)
        if hasattr(self.solver, 'Proxy') and hasattr(self.solver.Proxy, '_clear_result_objects'):
            self.solver.Proxy._clear_result_objects(self.solver)

        # 2. Clear Code Check Results
        # Ensure we have the reference
        if not self.code_check:
            self.code_check = make_code_check_feature()

        if self.code_check and hasattr(self.code_check, "Proxy"):
            # The code check results are stored in the cached_results dictionary on the proxy
            # and inside the solver.Results (which we just cleared above).
            # We must clear the cache so the dialog doesn't show stale data.
            self.code_check.Proxy.cached_results = {}

        # Update status
        self.status_label.setText("Results cleared")
        self.status_label.setStyleSheet("font-weight: bold; color: blue;")

        # Show confirmation
        QtGui.QMessageBox.information(self.form, "Results Cleared",
                                      "Analysis and Code Check results have been cleared.")

    def close_dialog(self):
        """Close the dialog"""
        Gui.Control.closeDialog()

    def getStandardButtons(self):
        """Return standard buttons for task panel"""
        return QtGui.QDialogButtonBox.Close | QtGui.QDialogButtonBox.Apply

    def clicked(self, button):
        """Handle button clicks"""
        if button == QtGui.QDialogButtonBox.Apply:
            self.run_analysis()
        elif button == QtGui.QDialogButtonBox.Close:
            self.close_dialog()

    def reject(self):
        """Cancel operation"""
        self.close_dialog()
        return True


def show_analysis_setup():
    """Show the analysis setup task panel"""
    # Close any existing task panel first
    if hasattr(Gui, 'Control') and Gui.Control.activeDialog():
        Gui.Control.closeDialog()

    # Find existing solver
    solver = None
    doc = App.ActiveDocument
    if doc:
        for obj in doc.Objects:
            if hasattr(obj, "Type") and obj.Type == "Solver":
                solver = obj
                break

    # Create and show panel
    panel = AnalysisSetupTaskPanel(solver)
    Gui.Control.showDialog(panel)
    return panel