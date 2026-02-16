import FreeCAD as App
import FreeCADGui as Gui

try:
    from PySide import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui

import features.nodes
import features.beams
import features.material
import features.sections
import features.member_releases
import features.boundary_condition
import features.AnalysisGroup


# =============================================================================
# DROPDOWN HELPERS
# =============================================================================

def get_node_labels():
    """Returns a list of labels for all NodeFeature objects."""
    return [n.Label for n in features.nodes.get_all_nodes()]


def get_section_labels():
    """Returns labels for all objects with a SectionFeature proxy."""
    return [obj.Label for obj in App.ActiveDocument.Objects
            if hasattr(obj, "Proxy") and isinstance(obj.Proxy, features.sections.SectionFeature)]


def get_material_labels():
    """Returns labels for all objects with a MaterialFeature proxy."""
    return [obj.Label for obj in App.ActiveDocument.Objects
            if hasattr(obj, "Proxy") and isinstance(obj.Proxy, features.material.MaterialFeature)]


def get_release_labels():
    """Returns labels for all objects with a MemberReleaseFeature proxy."""
    return [obj.Label for obj in App.ActiveDocument.Objects
            if hasattr(obj, "Proxy") and isinstance(obj.Proxy, features.member_releases.MemberReleaseFeature)]


def get_profile_types():
    """Returns the standard profile categories (I-Shape, etc.)."""
    return features.sections.PROFILE_TYPES

def get_load_id_labels():
    """Returns labels for all LoadIDFeature objects."""
    return [obj.Label for obj in App.ActiveDocument.Objects
            if hasattr(obj, "Type") and obj.Type == "LoadIDFeature"]


def get_beam_labels():
    """Returns labels for all BeamFeature objects."""
    return [b.Label for b in features.beams.get_all_beams()]

def get_load_combination_labels():
    """Returns labels for existing combinations (for nested combinations)."""
    return [obj.Label for obj in App.ActiveDocument.Objects
            if hasattr(obj, "Type") and obj.Type == "LoadCombination"]


# =============================================================================
# FIXITY HELPERS (Dx Dy Dz Rx Ry Rz)
# =============================================================================

def fixity_to_bin_str(obj, prefix=""):
    """Converts Boolean fixity properties to a 6-digit string like '111000'."""
    props = ["Dx", "Dy", "Dz", "Rx", "Ry", "Rz"]
    res = ""
    for p in props:
        val = getattr(obj, prefix + p, False)
        res += "1" if val else "0"
    return res


def bin_str_to_fixity(obj, s, prefix=""):
    """Parses a 6-digit string and sets Boolean fixity properties."""
    props = ["Dx", "Dy", "Dz", "Rx", "Ry", "Rz"]
    if not s or len(s) != 6:
        return
    for i, char in enumerate(s):
        if i < len(props):
            setattr(obj, prefix + props[i], char == "1")


# =============================================================================
# GENERIC DROPDOWN DELEGATE
# =============================================================================

class GenericDropdownDelegate(QtWidgets.QStyledItemDelegate):
    """Delegate providing QComboBox editors with 3D view highlighting."""

    def __init__(self, data_map, parent=None):
        super(GenericDropdownDelegate, self).__init__(parent)
        self.data_map = data_map

    def createEditor(self, parent, option, index):
        col = index.column()
        if col in self.data_map:
            editor = QtWidgets.QComboBox(parent)
            editor.setEditable(True)
            items = self.data_map[col]()
            editor.addItems(sorted(items))
            editor.view().setMouseTracking(True)
            editor.view().entered.connect(self.on_hover_highlight)
            return editor
        return super(GenericDropdownDelegate, self).createEditor(parent, option, index)

    def on_hover_highlight(self, index):
        """Highlights the hovered object in the 3D view."""
        label_text = index.data()
        if not label_text or not App.ActiveDocument: return
        obj = next((o for o in App.ActiveDocument.Objects if o.Label == label_text), None)
        if obj:
            Gui.Selection.clearSelection()
            Gui.Selection.addSelection(App.ActiveDocument.Name, obj.Name)

    def setEditorData(self, editor, index):
        if isinstance(editor, QtWidgets.QComboBox):
            text = index.data(QtCore.Qt.EditRole) or ""
            idx = editor.findText(text)
            if idx >= 0:
                editor.setCurrentIndex(idx)
            else:
                editor.setEditText(text)
        else:
            super(GenericDropdownDelegate, self).setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        if isinstance(editor, QtWidgets.QComboBox):
            model.setData(index, editor.currentText(), QtCore.Qt.EditRole)
            Gui.Selection.clearSelection()
        else:
            super(GenericDropdownDelegate, self).setModelData(editor, model, index)


# =============================================================================
# BASE SHEET CLASS
# =============================================================================

class BaseSheet(QtWidgets.QWidget):
    """Abstract base class for all spreadsheet tabs."""
    proxy_class_name = None

    def __init__(self, parent=None):
        super(BaseSheet, self).__init__(parent)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.is_updating_table = False
        self.is_updating_model = False
        self.current_font_size = 10

        self.table = QtWidgets.QTableWidget()
        self.setup_table()
        self.layout.addWidget(self.table)
        self.create_actions()

        self.table.cellChanged.connect(self.on_cell_changed)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)

    def is_relevant_object(self, obj):
        if not hasattr(obj, "Proxy") or self.proxy_class_name is None:
            return False
        return obj.Proxy.__class__.__name__ == self.proxy_class_name

    def get_all_objects(self):
        if not App.ActiveDocument: return []
        return [o for o in App.ActiveDocument.Objects if self.is_relevant_object(o)]

    def setup_table(self):
        headers = self.get_headers()
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.ensure_empty_last_row()

    def create_actions(self):
        self.act_copy = QtWidgets.QAction("Copy", self)
        self.act_copy.setShortcut(QtGui.QKeySequence.Copy)
        self.act_copy.triggered.connect(self.copy_selection)
        self.table.addAction(self.act_copy)

        self.act_paste = QtWidgets.QAction("Paste", self)
        self.act_paste.setShortcut(QtGui.QKeySequence.Paste)
        self.act_paste.triggered.connect(self.paste_selection)
        self.table.addAction(self.act_paste)

        self.act_modify = QtWidgets.QAction("Modify Selection...", self)
        self.act_modify.triggered.connect(self.on_modify_triggered)
        self.table.addAction(self.act_modify)

        sep = QtWidgets.QAction(self);
        sep.setSeparator(True)
        self.table.addAction(sep)

        self.act_font = QtWidgets.QAction("Font Size...", self)
        self.act_font.triggered.connect(self.change_font_size)
        self.table.addAction(self.act_font)

    def on_modify_triggered(self):
        """Identifies selected objects and opens the dedicated modifier dialog."""
        selected_items = self.table.selectedItems()
        if not selected_items: return

        obj_names = list(set([self.table.item(i.row(), 0).data(QtCore.Qt.UserRole)
                              for i in selected_items if self.table.item(i.row(), 0)]))

        objects = [App.ActiveDocument.getObject(name) for name in obj_names if name]
        if objects:
            self.open_modifier_dialog(objects)

    def open_modifier_dialog(self, objects):
        """Implemented by subclasses to call specific dialogs."""
        pass

    def ensure_empty_last_row(self):
        self.table.blockSignals(True)
        try:
            rows = self.table.rowCount()
            if rows == 0:
                self.table.insertRow(0);
                return
            last_item = self.table.item(rows - 1, 0)
            if last_item and len(last_item.text().strip()) > 0:
                self.table.insertRow(rows)
            elif rows >= 2:
                prev_item = self.table.item(rows - 2, 0)
                if not prev_item or len(prev_item.text().strip()) == 0:
                    self.table.removeRow(rows - 1)
        finally:
            self.table.blockSignals(False)

    def find_row_by_id(self, obj_name):
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item and item.data(QtCore.Qt.UserRole) == obj_name: return r
        return None

    def on_cell_changed(self, row, col):
        if self.is_updating_table: return
        self.is_updating_model = True
        self.table.blockSignals(True)
        try:
            self.update_object_from_row(row)
            self.ensure_empty_last_row()
        except Exception as e:
            App.Console.PrintError(f"Sheet Error: {e}\n")
        finally:
            self.table.blockSignals(False);
            self.is_updating_model = False

    def on_selection_changed(self):
        if self.is_updating_table: return
        selected = self.table.selectedItems()
        names = list(set([self.table.item(i.row(), 0).data(QtCore.Qt.UserRole) for i in selected if
                          self.table.item(i.row(), 0)]))
        Gui.Selection.clearSelection()
        for name in names:
            if name: Gui.Selection.addSelection(App.ActiveDocument.Name, name)

    def parse_float(self, input_str):
        if not input_str: return 0.0
        try:
            return float(input_str)
        except:
            try:
                return App.Units.Quantity(input_str).Value
            except:
                return 0.0

    def set_cell(self, row, col, value, read_only=False):
        item = QtWidgets.QTableWidgetItem(str(value))
        if read_only:
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
            item.setBackground(QtGui.QColor(240, 240, 240))
        self.table.setItem(row, col, item)

    def get_cell_text(self, row, col):
        item = self.table.item(row, col);
        return item.text().strip() if item else ""

    def external_update(self, obj):
        if not self.isVisible(): return
        self.is_updating_table = True;
        self.table.blockSignals(True)
        try:
            row = self.find_row_by_id(obj.Name)
            if row is None:
                row = max(0, self.table.rowCount() - 1);
                self.table.insertRow(row)
            self.update_row_from_object(obj, row);
            self.ensure_empty_last_row()
        finally:
            self.table.blockSignals(False); self.is_updating_table = False

    def external_delete(self, obj_name):
        row = self.find_row_by_id(obj_name)
        if row is not None:
            self.is_updating_table = True;
            self.table.removeRow(row)
            self.ensure_empty_last_row();
            self.is_updating_table = False

    def full_reload(self):
        self.is_updating_table = True;
        self.table.blockSignals(True);
        self.table.setRowCount(0)
        for obj in self.get_all_objects():
            row = self.table.rowCount();
            self.table.insertRow(row)
            self.update_row_from_object(obj, row)
        self.ensure_empty_last_row();
        self.table.blockSignals(False);
        self.is_updating_table = False

    def clear_content(self):
        self.table.setRowCount(0);
        self.ensure_empty_last_row()

    def copy_selection(self):
        selection = self.table.selectedRanges()
        if not selection: return
        headers = [self.table.horizontalHeaderItem(c).text() for c in range(self.table.columnCount())]
        clipboard_text = ["\t".join(headers)]
        rows = sorted(list(set(r for ran in selection for r in range(ran.topRow(), ran.bottomRow() + 1))))
        for r in rows:
            data = [self.table.item(r, c).text() if self.table.item(r, c) else "" for c in
                    range(self.table.columnCount())]
            clipboard_text.append("\t".join(data))
        QtWidgets.QApplication.instance().clipboard().setText("\n".join(clipboard_text))

    def paste_selection(self):
        text = QtWidgets.QApplication.instance().clipboard().text()
        if not text: return
        lines = text.strip().split('\n')
        start_row = self.table.currentRow() if self.table.currentRow() >= 0 else self.table.rowCount() - 1
        if lines[0].split('\t')[0] == self.table.horizontalHeaderItem(0).text(): lines = lines[1:]
        App.ActiveDocument.openTransaction("Paste")
        try:
            self.is_updating_model = True;
            self.table.blockSignals(True)
            for i, line in enumerate(lines):
                r = start_row + i
                if r >= self.table.rowCount(): self.table.insertRow(r)
                for c, val in enumerate(line.split('\t')):
                    if c < self.table.columnCount(): self.table.setItem(r, c, QtWidgets.QTableWidgetItem(val.strip()))
                self.update_object_from_row(r)
            self.ensure_empty_last_row();
            App.ActiveDocument.commitTransaction()
        except:
            App.ActiveDocument.abortTransaction()
        finally:
            self.table.blockSignals(False); self.is_updating_model = False

    def change_font_size(self):
        val, ok = QtWidgets.QInputDialog.getInt(self, "Font Size", "Size:", self.current_font_size, 6, 72, 1)
        if ok:
            self.current_font_size = val;
            font = self.table.font();
            font.setPointSize(val)
            self.table.setFont(font);
            self.table.resizeRowsToContents()


# =============================================================================
# SHEET SUBCLASSES
# =============================================================================

class NodeSheet(BaseSheet):
    proxy_class_name = "NodeFeature"

    def get_headers(self):
        return ["Label", "X (mm)", "Y (mm)", "Z (mm)", "Comment"]

    def open_modifier_dialog(self, objects):
        from ui.dialog_NodeModifier import show_node_modifier
        show_node_modifier(objects)

    def update_row_from_object(self, obj, row):
        item = QtWidgets.QTableWidgetItem(obj.Label);
        item.setData(QtCore.Qt.UserRole, obj.Name)
        self.table.setItem(row, 0, item)

        def v(p): return p.Value if hasattr(p, "Value") else p

        self.set_cell(row, 1, v(getattr(obj, "X", 0)))
        self.set_cell(row, 2, v(getattr(obj, "Y", 0)))
        self.set_cell(row, 3, v(getattr(obj, "Z", 0)))
        self.set_cell(row, 4, getattr(obj, "Comment", ""))

    def update_object_from_row(self, row):
        label = self.get_cell_text(row, 0);
        name = self.table.item(row, 0).data(QtCore.Qt.UserRole) if self.table.item(row, 0) else None
        if name and not label: App.ActiveDocument.removeObject(name); return
        if not label: return
        x, y, z = self.parse_float(self.get_cell_text(row, 1)), self.parse_float(
            self.get_cell_text(row, 2)), self.parse_float(self.get_cell_text(row, 3))
        comment = self.get_cell_text(row, 4)
        if name:
            obj = App.ActiveDocument.getObject(name)
            if obj:
                obj.Label, obj.X, obj.Y, obj.Z, obj.Comment = label, x, y, z, comment
                obj.recompute()
        else:
            new_node = features.nodes.create_node(X=x, Y=y, Z=z)
            new_node.Label, new_node.Comment = label, comment
            self.table.item(row, 0).setData(QtCore.Qt.UserRole, new_node.Name)


class BeamSheet(BaseSheet):
    proxy_class_name = "BeamFeature"

    def __init__(self, parent=None):
        super(BeamSheet, self).__init__(parent)
        self.delegate = GenericDropdownDelegate({
            1: get_node_labels,
            2: get_node_labels,
            3: get_section_labels,
            4: get_material_labels,
            5: get_release_labels
        }, self.table)
        self.table.setItemDelegate(self.delegate)

    def get_headers(self):
        return ["Label", "Start Node", "End Node", "Section", "Material", "Release", "Comment"]

    def open_modifier_dialog(self, objects):
        from ui.dialog_BeamModifier import show_beam_modifier
        show_beam_modifier(beams=objects)

    def update_row_from_object(self, obj, row):
        item = QtWidgets.QTableWidgetItem(obj.Label);
        item.setData(QtCore.Qt.UserRole, obj.Name)
        self.table.setItem(row, 0, item)
        self.set_cell(row, 1, obj.StartNode.Label if getattr(obj, "StartNode", None) else "")
        self.set_cell(row, 2, obj.EndNode.Label if getattr(obj, "EndNode", None) else "")
        self.set_cell(row, 3, obj.Section.Label if getattr(obj, "Section", None) else "")
        self.set_cell(row, 4, obj.Material.Label if getattr(obj, "Material", None) else "")
        self.set_cell(row, 5, obj.MemberRelease.Label if getattr(obj, "MemberRelease", None) else "")
        self.set_cell(row, 6, getattr(obj, "Comment", ""))

    def update_object_from_row(self, row):
        label = self.get_cell_text(row, 0);
        name = self.table.item(row, 0).data(QtCore.Qt.UserRole) if self.table.item(row, 0) else None
        if name and not label: App.ActiveDocument.removeObject(name); return
        if not label: return

        def find(l):
            return next((o for o in App.ActiveDocument.Objects if o.Label == l), None)

        s, e, sec, mat, rel = find(self.get_cell_text(row, 1)), find(self.get_cell_text(row, 2)), find(
            self.get_cell_text(row, 3)), find(self.get_cell_text(row, 4)), find(self.get_cell_text(row, 5))
        com = self.get_cell_text(row, 6)
        if name:
            obj = App.ActiveDocument.getObject(name)
            if obj:
                obj.Label = label
                if s: obj.StartNode = s
                if e: obj.EndNode = e
                if sec: obj.Section = sec
                if mat: obj.Material = mat
                if rel: obj.MemberRelease = rel
                if hasattr(obj, "Comment"): obj.Comment = com
                obj.recompute()
        else:
            if s and e:
                features.beams.create_beam(s, e, sec)
                new_b = App.ActiveDocument.Objects[-1]
                new_b.Label, new_b.Material, new_b.MemberRelease, new_b.Comment = label, mat, rel, com
                self.table.item(row, 0).setData(QtCore.Qt.UserRole, new_b.Name)


class MaterialSheet(BaseSheet):
    proxy_class_name = "MaterialFeature"

    def get_headers(self):
        return ["Label", "E (MPa)", "G (MPa)", "Density (kg/m3)", "Comment"]

    def update_row_from_object(self, obj, row):
        item = QtWidgets.QTableWidgetItem(obj.Label);
        item.setData(QtCore.Qt.UserRole, obj.Name)
        self.table.setItem(row, 0, item)

        def v(prop,unit_str, force_int=False):
            if hasattr(obj, prop):
                val = getattr(obj, prop,0)
                return int(val.getValueAs(unit_str).Value) if force_int else val.getValueAs(unit_str).Value
            return 0

        self.set_cell(row, 1, v("YoungsModulus","MPa", True))
        self.set_cell(row, 2, v("ShearModulus","MPa", True))
        self.set_cell(row, 3, v("Density",'kg/m^3',True))
        self.set_cell(row, 4, getattr(obj, "Comment", ""))

    def update_object_from_row(self, row):
        label = self.get_cell_text(row, 0);
        name = self.table.item(row, 0).data(QtCore.Qt.UserRole) if self.table.item(row, 0) else None
        if name and not label: App.ActiveDocument.removeObject(name); return
        if not label: return
        e, g, d = self.parse_float(self.get_cell_text(row, 1)), self.parse_float(
            self.get_cell_text(row, 2)), self.parse_float(self.get_cell_text(row, 3))
        c = self.get_cell_text(row, 4)
        if name:
            obj = App.ActiveDocument.getObject(name)
            if obj:
                obj.Label, obj.YoungsModulus, obj.ShearModulus, obj.Density, obj.Comment = label, e, g, d, c
                obj.recompute()
        else:
            features.material.create_material()
            new_m = App.ActiveDocument.Objects[-1]
            new_m.Label, new_m.YoungsModulus, new_m.ShearModulus, new_m.Density, new_m.Comment = label, e, g, d, c
            self.table.item(row, 0).setData(QtCore.Qt.UserRole, new_m.Name)

    def open_modifier_dialog(self, objects):
        """Link spreadsheet selection to the material modifier"""
        from ui.dialog_MaterialModifier import show_material_modifier
        show_material_modifier(objects)

class SectionSheet(BaseSheet):
    proxy_class_name = "SectionFeature"

    def __init__(self, parent=None):
        super(SectionSheet, self).__init__(parent)
        self.table.setItemDelegate(GenericDropdownDelegate({1: get_profile_types}, self.table))

    def get_headers(self):
        return ["Label", "Type", "Area (cm2)", "Iyy (cm4)", "Izz (cm4)", "Comment"]

    def open_modifier_dialog(self, objects):
        """Opens the dedicated section modifier for the spreadsheet selection"""
        from ui.dialog_SectionModifier import show_section_modifier
        show_section_modifier(objects)
    def update_row_from_object(self, obj, row):
        item = QtWidgets.QTableWidgetItem(obj.Label);
        item.setData(QtCore.Qt.UserRole, obj.Name)
        self.table.setItem(row, 0, item)
        self.set_cell(row, 1, getattr(obj, "ProfileType", "Rectangle"))

        def cm(p, f):
            if hasattr(obj, p):
                val = getattr(obj, p).Value if hasattr(getattr(obj, p), "Value") else getattr(obj, p)
                return f"{val / f:.2f}"
            return "0.00"

        self.set_cell(row, 2, cm("Area", 100), True)
        self.set_cell(row, 3, cm("Iyy", 10000), True)
        self.set_cell(row, 4, cm("Izz", 10000), True)
        self.set_cell(row, 5, getattr(obj, "Comment", ""))

    def update_object_from_row(self, row):
        label = self.get_cell_text(row, 0);
        name = self.table.item(row, 0).data(QtCore.Qt.UserRole) if self.table.item(row, 0) else None
        if name and not label: App.ActiveDocument.removeObject(name); return
        if not label: return
        t, c = self.get_cell_text(row, 1), self.get_cell_text(row, 5)
        if name:
            obj = App.ActiveDocument.getObject(name)
            if obj:
                obj.Label = label
                if hasattr(obj, "ProfileType"): obj.ProfileType = t
                if hasattr(obj, "Comment"): obj.Comment = c
                obj.recompute()
        else:
            new_s = features.sections.create_section(t, "Custom", "Custom")
            new_s.Label = label
            if hasattr(new_s, "Comment"): new_s.Comment = c
            self.table.item(row, 0).setData(QtCore.Qt.UserRole, new_s.Name)


class BoundaryConditionSheet(BaseSheet):
    proxy_class_name = "BoundaryConditionFeature"

    def get_headers(self):
        return ["Label", "Fixity (DxDyDzRxRyRz)", "Nodes", "Comment"]

    def open_modifier_dialog(self, objects):
        from ui.dialog_BoundaryConditionCreator import show_boundary_condition_creator
        if objects: show_boundary_condition_creator(boundary_condition=objects[0])

    def update_row_from_object(self, obj, row):
        item = QtWidgets.QTableWidgetItem(obj.Label);
        item.setData(QtCore.Qt.UserRole, obj.Name)
        self.table.setItem(row, 0, item)
        self.set_cell(row, 1, fixity_to_bin_str(obj))

        nodes_list = getattr(obj, "Nodes", [])
        self.set_cell(row, 2, ", ".join([n.Label for n in nodes_list if n]), read_only=True)

        self.set_cell(row, 3, getattr(obj, "Comment", ""))

    def update_object_from_row(self, row):
        label = self.get_cell_text(row, 0);
        name = self.table.item(row, 0).data(QtCore.Qt.UserRole) if self.table.item(row, 0) else None
        if name and not label: App.ActiveDocument.removeObject(name); return
        if not label: return
        fix_str, com = self.get_cell_text(row, 1), self.get_cell_text(row, 3)
        if name:
            obj = App.ActiveDocument.getObject(name)
            if obj:
                obj.Label = label
                bin_str_to_fixity(obj, fix_str)
                obj.Comment = com
                obj.recompute()
        else:
            new_bc = features.boundary_condition.create_boundary_condition()
            new_bc.Label = label
            bin_str_to_fixity(new_bc, fix_str)
            new_bc.Comment = com
            self.table.item(row, 0).setData(QtCore.Qt.UserRole, new_bc.Name)


class MemberReleaseSheet(BaseSheet):
    proxy_class_name = "MemberReleaseFeature"

    def get_headers(self):
        return ["Label", "Start Fixity", "End Fixity", "Comment"]

    def open_modifier_dialog(self, objects):
        from ui.dialog_MemberReleaseCreator import show_member_release_modifier
        show_member_release_modifier(objects)

    def update_row_from_object(self, obj, row):
        item = QtWidgets.QTableWidgetItem(obj.Label);
        item.setData(QtCore.Qt.UserRole, obj.Name)
        self.table.setItem(row, 0, item)
        self.set_cell(row, 1, fixity_to_bin_str(obj, "Start_"))
        self.set_cell(row, 2, fixity_to_bin_str(obj, "End_"))
        self.set_cell(row, 3, getattr(obj, "Comment", ""))

    def update_object_from_row(self, row):
        label = self.get_cell_text(row, 0);
        name = self.table.item(row, 0).data(QtCore.Qt.UserRole) if self.table.item(row, 0) else None
        if name and not label: App.ActiveDocument.removeObject(name); return
        if not label: return
        s_fix, e_fix, com = self.get_cell_text(row, 1), self.get_cell_text(row, 2), self.get_cell_text(row, 3)
        if name:
            obj = App.ActiveDocument.getObject(name)
            if obj:
                obj.Label = label
                bin_str_to_fixity(obj, s_fix, "Start_")
                bin_str_to_fixity(obj, e_fix, "End_")
                if hasattr(obj, "Comment"): obj.Comment = com
                obj.recompute()
        else:
            new_rel = features.member_releases.create_member_release()
            new_rel.Label = label
            bin_str_to_fixity(new_rel, s_fix, "Start_")
            bin_str_to_fixity(new_rel, e_fix, "End_")
            if hasattr(new_rel, "Comment"): new_rel.Comment = com
            self.table.item(row, 0).setData(QtCore.Qt.UserRole, new_rel.Name)

class LoadIDSheet(BaseSheet):
    proxy_class_name = "LoadID"
    def get_headers(self):
        return ["Label", "Description"]

    def update_row_from_object(self, obj, row):
        item = QtWidgets.QTableWidgetItem(obj.Label)
        item.setData(QtCore.Qt.UserRole, obj.Name)
        self.table.setItem(row, 0, item)
        self.set_cell(row, 1, getattr(obj, "Description", ""))

    def update_object_from_row(self, row):
        label = self.get_cell_text(row, 0)
        name = self.table.item(row, 0).data(QtCore.Qt.UserRole) if self.table.item(row, 0) else None
        if name and not label: App.ActiveDocument.removeObject(name); return
        if not label: return
        desc = self.get_cell_text(row, 1)
        if name:
            obj = App.ActiveDocument.getObject(name)
            if obj: obj.Label, obj.Comment = label, desc
        else:
            from features.LoadIDManager import create_load_id
            new_id = create_load_id(label)
            new_id.Comment = desc
            self.table.item(row, 0).setData(QtCore.Qt.UserRole, new_id.Name)

class NodalLoadSheet(BaseSheet):
    proxy_class_name = "NodalLoad"
    def get_headers(self): return ["Label", "Nodes (CSV)", "Force (X,Y,Z)", "Moment (X,Y,Z)"]

    def update_row_from_object(self, obj, row):
        item = QtWidgets.QTableWidgetItem(obj.Label)
        item.setData(QtCore.Qt.UserRole, obj.Name)
        self.table.setItem(row, 0, item)
        nodes = ", ".join([n.Label for n in getattr(obj, "Nodes", [])])
        self.set_cell(row, 1, nodes)
        f, m = obj.Force, obj.Moment
        self.set_cell(row, 2, f"{f.x}, {f.y}, {f.z}",read_only=True)
        self.set_cell(row, 3, f"{m.x}, {m.y}, {m.z}",read_only=True)

    def update_object_from_row(self, row):
        # Implementation follows the pattern of parsing vectors and fetching node objects by label
        pass

    def open_modifier_dialog(self, objects):
        """Link spreadsheet selection to the nodal load modifier"""
        from ui.dialog_NodalLoad import show_nodal_load_creator
        show_nodal_load_creator(nodal_load_to_modify=objects[0])

class MemberLoadSheet(BaseSheet):
    proxy_class_name = "MemberLoad"
    def __init__(self, parent=None):
        super().__init__(parent)
        # Delegate for beam selection
        self.table.setItemDelegate(GenericDropdownDelegate({1: get_beam_labels}, self.table))

    def get_headers(self):
        return ["Label", "Beams", "Start Force", "End Force", "Start Pos", "End Pos"]

    def update_row_from_object(self, obj, row):
        item = QtWidgets.QTableWidgetItem(obj.Label)
        item.setData(QtCore.Qt.UserRole, obj.Name)
        self.table.setItem(row, 0, item)
        beams = ", ".join([b.Label for b in getattr(obj, "Beams", [])])
        self.set_cell(row, 1, beams)
        sf, ef = obj.StartForce, obj.EndForce
        self.set_cell(row, 2, f"{sf.x}, {sf.y}, {sf.z}",read_only=True)
        self.set_cell(row, 3, f"{ef.x}, {ef.y}, {ef.z}",read_only=True)
        self.set_cell(row, 4, obj.StartPosition,read_only=True)
        self.set_cell(row, 5, obj.EndPosition,read_only=True)

    def update_object_from_row(self, row):
        pass


class LoadCombinationSheet(BaseSheet):
    proxy_class_name = "LoadCombination"

    def __init__(self, parent=None):
        super(LoadCombinationSheet, self).__init__(parent)
        self.load_id_cache = []  # Stores objects to maintain column order

    def get_headers(self):
        """Builds headers: Label | Description | LC1 | LC2 | ... | Comment"""
        base_headers = ["Label", "Description"]
        if App.ActiveDocument is None:
            return base_headers + ["Comment"]
        # Fetch LoadID objects using your existing logic
        self.load_id_cache = [obj for obj in App.ActiveDocument.Objects
                              if hasattr(obj, "Type") and obj.Type == "LoadIDFeature"]

        lc_labels = [obj.Label for obj in self.load_id_cache]
        return base_headers + lc_labels + ["Comment"]

    def full_reload(self):
        """Refreshes the matrix structure whenever the tab is selected."""
        self.is_updating_table = True
        self.table.blockSignals(True)

        headers = self.get_headers()
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

        self.table.setRowCount(0)
        for obj in self.get_all_objects():
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.update_row_from_object(obj, row)

        self.ensure_empty_last_row()
        self.table.blockSignals(False)
        self.is_updating_table = False

    def update_row_from_object(self, obj, row):
        # Set ID and Basic Info
        item = QtWidgets.QTableWidgetItem(obj.Label)
        item.setData(QtCore.Qt.UserRole, obj.Name)
        self.table.setItem(row, 0, item)
        self.set_cell(row, 1, getattr(obj, "Description", ""))

        # Create a mapping of Load Object -> Coefficient for quick lookup
        if not hasattr(obj,"Loads"):
            return

        current_data = {l: c for l, c in zip(obj.Loads, obj.Coefficients) if l}

        # Fill LC columns (starting at index 2)
        for i, lc_obj in enumerate(self.load_id_cache):
            coeff = current_data.get(lc_obj, 0.0)
            self.set_cell(row, i + 2, f"{coeff:.2g}")

        # Set Comment in the last column
        last_idx = self.table.columnCount() - 1
        self.set_cell(row, last_idx, getattr(obj, "Comment", ""))

    def update_object_from_row(self, row):
        label = self.get_cell_text(row, 0)
        name = self.table.item(row, 0).data(QtCore.Qt.UserRole) if self.table.item(row, 0) else None

        if name and not label:
            App.ActiveDocument.removeObject(name)
            return
        if not label: return

        # Get or create the LoadCombination object
        if name:
            obj = App.ActiveDocument.getObject(name)
        else:
            from features.LoadCombination import create_load_combination
            obj = create_load_combination(name=label, comment="", loads=[], coefficients=[])
            self.table.item(row, 0).setData(QtCore.Qt.UserRole, obj.Name)

        # Update Properties
        obj.Label = label
        obj.Comment = self.get_cell_text(row, 1)

        # Sync Matrix to the Lists
        new_loads = []
        new_coeffs = []
        for i, lc_obj in enumerate(self.load_id_cache):
            val = self.parse_float(self.get_cell_text(row, i + 2))
            if abs(val) > 1e-9:  # Only include non-zero coefficients
                new_loads.append(lc_obj)
                new_coeffs.append(val)

        obj.Loads = new_loads
        obj.Coefficients = new_coeffs

        last_idx = self.table.columnCount() - 1
        obj.Comment = self.get_cell_text(row, last_idx)
        obj.recompute()

    def open_modifier_dialog(self, objects):
        """Standard right-click modifier call."""
        from ui.dialog_LoadCombination import show_load_combination_modifier
        # Pass the list of selected objects; the helper above will handle it
        show_load_combination_modifier(objects[0])
# =============================================================================
# MAIN PANEL
# =============================================================================

class SpreadsheetPanel(QtWidgets.QWidget):
    """Container widget managing multiple sheet tabs with document observers."""

    def __init__(self, parent=None):
        super(SpreadsheetPanel, self).__init__(parent)
        self.layout = QtWidgets.QVBoxLayout(self);
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.status_label = QtWidgets.QLabel("No Active Analysis Group found.");
        self.status_label.setStyleSheet("color: red; font-weight: bold; padding: 5px;");
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.status_label)

        self.tabs = QtWidgets.QTabWidget()
        # Connect tab change to auto-refresh
        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.layout.addWidget(self.tabs)

        self.sheets = []
        self.add_sheet(NodeSheet(), "Nodes")
        self.add_sheet(BeamSheet(), "Beams")
        self.add_sheet(MaterialSheet(), "Materials")
        self.add_sheet(SectionSheet(), "Sections")
        self.add_sheet(BoundaryConditionSheet(), "BCs")
        self.add_sheet(MemberReleaseSheet(), "Releases")
        self.add_sheet(LoadIDSheet(), "Load Cases")
        self.add_sheet(NodalLoadSheet(), "Nodal Loads")
        self.add_sheet(MemberLoadSheet(), "Member Loads")
        self.add_sheet(LoadCombinationSheet(), "Combinations")

        self.current_doc_name = None;
        self.pending_reload = False
        Gui.Selection.addObserver(self);
        App.addDocumentObserver(self);
        self.check_and_load()

    def add_sheet(self, s, n):
        self.sheets.append(s); self.tabs.addTab(s, n)

    def is_analysis_active(self):
        """Checks if an AnalysisGroup exists in the active document."""
        if not App.ActiveDocument: return False
        return any(
            hasattr(o, "Proxy") and o.Proxy.__class__.__name__ == "AnalysisGroup" for o in App.ActiveDocument.Objects)

    def check_and_load(self):
        """Initial check and load of data."""
        self.current_doc_name = App.ActiveDocument.Name if App.ActiveDocument else None
        active = self.is_analysis_active();
        self.tabs.setEnabled(active);
        self.status_label.setVisible(not active)
        if active and self.sheets:
            self.sheets[self.tabs.currentIndex()].full_reload()
        elif not active:
            for s in self.sheets: s.clear_content()
        self.pending_reload = False

    def on_tab_changed(self, index):
        """Forced refresh of the list when switching tabs."""
        if self.is_analysis_active() and 0 <= index < len(self.sheets):
            self.sheets[index].full_reload()

    def closeEvent(self, e):
        try:
            Gui.Selection.removeObserver(self); App.removeDocumentObserver(self)
        except:
            pass
        super().closeEvent(e)

    def resolve_args(self, args):
        if len(args) == 3: return args[1]
        if len(args) == 2: return args[0] if isinstance(args[1], str) else args[1]
        return args[0] if args else None

    def slotCreatedObject(self, *args):
        self.process_change(args)

    def slotChangedObject(self, *args):
        self.process_change(args)

    def process_change(self, args):
        """Updates specific sheet rows based on external model changes."""
        if not self.isVisible(): self.pending_reload = True; return
        obj = self.resolve_args(args)
        if not obj or isinstance(obj, str): return
        if hasattr(obj, "Proxy") and obj.Proxy.__class__.__name__ == "AnalysisGroup": self.check_and_load(); return
        if self.tabs.isEnabled():
            for s in self.sheets:
                if s.is_relevant_object(obj): s.external_update(obj)

    def slotDeletedObject(self, *args):
        if not self.isVisible(): self.pending_reload = True; return
        obj = self.resolve_args(args)
        if not obj: return
        if hasattr(obj, "Proxy") and obj.Proxy.__class__.__name__ == "AnalysisGroup": self.check_and_load(); return
        if self.tabs.isEnabled():
            for s in self.sheets:
                if s.is_relevant_object(obj): s.external_delete(obj.Name)

    def slotDeletedDocument(self, *args):
        if args[0].Name == self.current_doc_name: self.current_doc_name = None; self.check_and_load()

    def setSelection(self, doc_name):
        """Syncs table row selection with 3D view selection."""
        if doc_name != self.current_doc_name:
            if App.ActiveDocument and App.ActiveDocument.Name == doc_name: self.check_and_load()
            return
        if not self.isVisible() or not self.tabs.isEnabled(): return
        names = [s.Object.Name for s in Gui.Selection.getSelectionEx()]
        for s in self.sheets:
            s.table.blockSignals(True);
            s.table.clearSelection()
            for r in range(s.table.rowCount()):
                item = s.table.item(r, 0)
                if item and item.data(QtCore.Qt.UserRole) in names:
                    s.table.selectionModel().select(s.table.model().index(r, 0),
                                                    QtCore.QItemSelectionModel.Select | QtCore.QItemSelectionModel.Rows)
            s.table.blockSignals(False)