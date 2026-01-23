# ui/dialog_CodeCheckResults.py
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtGui, QtCore


class CodeCheckResultsDialog(QtGui.QDialog):
    def __init__(self, code_check_feature):
        super(CodeCheckResultsDialog, self).__init__()
        self.feature = code_check_feature
        self.setWindowTitle(f"Code Check Results: {code_check_feature.Label}")
        self.resize(1100, 700)
        self.layout = QtGui.QVBoxLayout(self)

        # Toolbar
        self.controls_layout = QtGui.QHBoxLayout()
        self.case_label = QtGui.QLabel("Load Case:")
        self.case_combo = QtGui.QComboBox()
        self.case_combo.setMinimumWidth(200)
        self.populate_cases()
        self.case_combo.currentTextChanged.connect(self.on_case_changed)
        self.controls_layout.addWidget(self.case_label)
        self.controls_layout.addWidget(self.case_combo)
        self.controls_layout.addStretch()
        self.layout.addLayout(self.controls_layout)

        # Splitter
        self.splitter = QtGui.QSplitter(QtCore.Qt.Horizontal)
        self.layout.addWidget(self.splitter)

        # Table
        self.table_widget = QtGui.QWidget()
        self.table_layout = QtGui.QVBoxLayout(self.table_widget)
        self.table_layout.setContentsMargins(0, 0, 0, 0)
        self.table = QtGui.QTableWidget()

        # Columns for LCr inputs
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Beam", "Max UC", "Status", "Load Case", "LCr y", "LCr z"])
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)

        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.table.itemChanged.connect(self.on_cell_changed)

        self.table_layout.addWidget(self.table)
        self.splitter.addWidget(self.table_widget)

        # Details
        self.detail_widget = QtGui.QWidget()
        self.detail_layout = QtGui.QVBoxLayout(self.detail_widget)
        self.detail_layout.setContentsMargins(0, 0, 0, 0)
        self.detail_label = QtGui.QLabel("Calculation Log:")
        self.detail_text = QtGui.QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setFontFamily("Courier")
        self.detail_layout.addWidget(self.detail_label)
        self.detail_layout.addWidget(self.detail_text)
        self.splitter.addWidget(self.detail_widget)
        self.splitter.setSizes([600, 500])

        # Buttons
        self.button_box = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Close)
        self.button_box.rejected.connect(self.close)

        self.refresh_btn = QtGui.QPushButton("Refresh / Recalculate")
        self.refresh_btn.clicked.connect(self.force_recompute)
        self.button_box.addButton(self.refresh_btn, QtGui.QDialogButtonBox.ActionRole)

        self.layout.addWidget(self.button_box)

        self.load_table_data()

    def populate_cases(self):
        current = self.feature.ActiveCase
        self.case_combo.blockSignals(True)
        self.case_combo.clear()
        cases = ["Envelope"]
        if hasattr(self.feature, "Proxy") and hasattr(self.feature.Proxy, "get_available_cases"):
            cases = self.feature.Proxy.get_available_cases()
        self.case_combo.addItems(cases)
        idx = self.case_combo.findText(current)
        if idx >= 0:
            self.case_combo.setCurrentIndex(idx)
        else:
            self.case_combo.setCurrentIndex(0)
        self.case_combo.blockSignals(False)

    def on_case_changed(self, text):
        if not text: return
        self.feature.ActiveCase = text
        self.feature.recompute()
        self.load_table_data()

    def force_recompute(self):
        self.feature.touch()
        App.ActiveDocument.recompute()
        self.load_table_data()

    def load_table_data(self):
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        self.detail_text.clear()

        if not hasattr(self.feature, "Proxy"):
            self.table.blockSignals(False)
            return

        results_cache = getattr(self.feature.Proxy, "cached_results", {})
        active_case = self.feature.ActiveCase

        if active_case not in results_cache:
            if "Envelope" in results_cache:
                active_case = "Envelope"
            else:
                self.table.blockSignals(False)
                return

        current_results = results_cache.get(active_case, {})
        beams_data = []
        doc = App.ActiveDocument

        # Default global values (if any)
        # Check for Lcr_y_ratio or buckling_length_ratio_y
        global_lcr_y = 1.0
        global_lcr_z = 1.0
        if hasattr(self.feature, "Lcr_y_ratio"):
            global_lcr_y = self.feature.Lcr_y_ratio
        elif hasattr(self.feature, "buckling_length_ratio_y"):
            global_lcr_y = self.feature.buckling_length_ratio_y

        if hasattr(self.feature, "Lcr_z_ratio"):
            global_lcr_z = self.feature.Lcr_z_ratio
        elif hasattr(self.feature, "buckling_length_ratio_z"):
            global_lcr_z = self.feature.buckling_length_ratio_z

        for beam_name, res_data in current_results.items():
            obj = doc.getObject(beam_name)
            label = obj.Label if obj else beam_name
            uc = res_data.get('max_uc', 0.0)
            status = "FAIL" if uc > 1.0 else "OK"

            # --- CALCULATE LCr FROM BEAM PROPERTIES ---
            # Ratio = BucklingLength / Length
            lcr_y = global_lcr_y
            lcr_z = global_lcr_z

            if obj and hasattr(obj, "Length"):
                # Get Length in mm
                beam_len = obj.Length.Value if hasattr(obj.Length, "Value") else obj.Length

                if beam_len > 1e-6:
                    if hasattr(obj, "BucklingLengthY"):
                        val = obj.BucklingLengthY.Value if hasattr(obj.BucklingLengthY,
                                                                   "Value") else obj.BucklingLengthY
                        lcr_y = val / beam_len
                    if hasattr(obj, "BucklingLengthZ"):
                        val = obj.BucklingLengthZ.Value if hasattr(obj.BucklingLengthZ,
                                                                   "Value") else obj.BucklingLengthZ
                        lcr_z = val / beam_len

            beams_data.append((label, uc, status, active_case, beam_name, lcr_y, lcr_z))

        beams_data.sort(key=lambda x: x[1], reverse=True)

        self.table.setRowCount(len(beams_data))
        for i, (label, uc, status, case, base_name, lcr_y, lcr_z) in enumerate(beams_data):
            # 0: Beam Label
            self.table.setItem(i, 0, QtGui.QTableWidgetItem(str(label)))
            self.table.item(i, 0).setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)

            # 1: UC
            uc_item = QtGui.QTableWidgetItem(f"{uc:.3f}")
            bg_color = QtGui.QColor(255, 200, 200) if uc > 1.0 else QtGui.QColor(200, 255, 200)
            uc_item.setBackground(bg_color)
            uc_item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
            self.table.setItem(i, 1, uc_item)

            # 2: Status
            stat_item = QtGui.QTableWidgetItem(str(status))
            stat_item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
            self.table.setItem(i, 2, stat_item)

            # 3: Load Case
            case_item = QtGui.QTableWidgetItem(str(case))
            case_item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
            self.table.setItem(i, 3, case_item)

            # 4: LCr y (Editable)
            lcry_item = QtGui.QTableWidgetItem(f"{lcr_y:.2f}")
            self.table.setItem(i, 4, lcry_item)

            # 5: LCr z (Editable)
            lcrz_item = QtGui.QTableWidgetItem(f"{lcr_z:.2f}")
            self.table.setItem(i, 5, lcrz_item)

            # Store hidden Beam Name for details lookup
            self.table.item(i, 0).setData(QtCore.Qt.UserRole, base_name)

        self.table.blockSignals(False)

    def on_selection_changed(self):
        sel = self.table.selectedItems()
        if not sel: return
        row = sel[0].row()
        item_0 = self.table.item(row, 0)
        base_name = item_0.data(QtCore.Qt.UserRole)

        if hasattr(self.feature, "Proxy"):
            txt = self.feature.Proxy.get_detail_info(base_name)
            self.detail_text.setText(txt)

        obj = App.ActiveDocument.getObject(base_name)
        if obj:
            Gui.Selection.clearSelection()
            Gui.Selection.addSelection(obj)

    def on_cell_changed(self, item):
        """Handle edits to LCr columns"""
        row = item.row()
        col = item.column()

        if col not in [4, 5]: return

        name_item = self.table.item(row, 0)
        beam_name = name_item.data(QtCore.Qt.UserRole)
        beam_obj = App.ActiveDocument.getObject(beam_name)
        if not beam_obj: return

        try:
            val = float(item.text())
        except ValueError:
            return

            # --- UPDATE BEAM PROPERTY ---
        # User input is Ratio (k). Property is Length (L_buckling).
        # L_buckling = Ratio * Beam_Length (in mm)

        beam_len = beam_obj.Length.Value if hasattr(beam_obj.Length, "Value") else beam_obj.Length
        new_buckling_len = val * beam_len

        prop_name = "BucklingLengthY" if col == 4 else "BucklingLengthZ"

        if hasattr(beam_obj, prop_name):
            setattr(beam_obj, prop_name, new_buckling_len)

        # Trigger recompute
        self.feature.touch()
        App.ActiveDocument.recompute()

        # Refresh table results
        self.load_table_data()
        self.table.selectRow(row)


def show_code_check_results(feature_obj):
    dlg = CodeCheckResultsDialog(feature_obj)
    dlg.exec_()