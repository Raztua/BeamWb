from PySide import QtGui, QtCore
import FreeCAD as App
import FreeCADGui as Gui
from features.LoadCombination import make_load_combination_group, create_load_combination  # Ajout de l'import


class LoadCombinationTaskPanel:
    def __init__(self, combination=None):
        self.form = QtGui.QWidget()
        self.form.setWindowTitle("Create Load Combination")
        self.combination_object = combination[0]
        self.loads = []

        self.initUI()
        self.update_load_list()
        if combination:
            self.load_data()
            self.form.setWindowTitle("Modify Load Combination")  # Changement de titre pour modification

    def initUI(self):
        layout = QtGui.QVBoxLayout(self.form)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Combination Name
        name_layout = QtGui.QHBoxLayout()
        name_layout.addWidget(QtGui.QLabel("Combination Name:"))
        self.name_input = QtGui.QLineEdit()
        self.name_input.setPlaceholderText("e.g., LC1, ENVELOPE, etc.")
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # Description
        desc_layout = QtGui.QHBoxLayout()
        desc_layout.addWidget(QtGui.QLabel("Description:"))
        self.desc_input = QtGui.QLineEdit()
        self.desc_input.setPlaceholderText("Optional description")
        desc_layout.addWidget(self.desc_input)
        layout.addLayout(desc_layout)

        # Combination matrix table
        self.table = QtGui.QTableWidget()
        self.table.setColumnCount(0)
        self.table.setRowCount(1)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        layout.addStretch()

    def update_load_list(self):
        if not App.ActiveDocument:
            return

        self.loads = [obj for obj in App.ActiveDocument.Objects
                      if hasattr(obj, "Type") and obj.Type == "LoadIDFeature"]

        self.table.setColumnCount(len(self.loads))

        for col, load in enumerate(self.loads):
            self.table.setHorizontalHeaderItem(col, QtGui.QTableWidgetItem(load.Label))
            item = QtGui.QTableWidgetItem("0.0")
            item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable)
            self.table.setItem(0, col, item)

    def load_data(self):
        if not self.combination_object:
            return
        self.name_input.setText(self.combination_object.Label)
        # Use Comment property as defined in the feature
        if hasattr(self.combination_object, "Comment"):
            self.desc_input.setText(self.combination_object.Comment)
        self.update_load_list()
        # Create a mapping of Load Name -> Coefficient for stable comparison
        current_data = {l.Name: c for l, c in zip(self.combination_object.Loads, self.combination_object.Coefficients)
                        if l}

        for col, load in enumerate(self.loads):
            # Match using .Name instead of object equality
            if load.Name in current_data:
                try:
                    coeff = str(current_data[load.Name])
                    self.table.item(0, col).setText(coeff)
                except (ValueError, AttributeError):
                    pass

    def get_combination_data(self):
        loads = []
        coeffs = []

        for col, load in enumerate(self.loads):
            try:
                coeff = float(self.table.item(0, col).text())
                if abs(coeff) > 1e-9:  # Vérifie si le coefficient est non nul
                    loads.append(load)
                    coeffs.append(coeff)
            except (ValueError, AttributeError):
                continue

        return {
            "name": self.name_input.text(),
            "description": self.desc_input.text(),
            "loads": loads,
            "coefficients": coeffs
        }

    def create_or_update_combination(self):
        """Logic to create or update the load combination"""
        data = self.get_combination_data()
        if not data["name"]:
            QtGui.QMessageBox.warning(None, "Error", "Please enter a combination name")
            return False

        if not data["loads"]:
            QtGui.QMessageBox.warning(None, "Error", "Please specify at least one load with non-zero coefficient")
            return False

        try:
            if self.combination_object:
                # Update existing combination
                self.combination_object.Label = data["name"]
                self.combination_object.Comment = data["description"]
                self.combination_object.Loads = data["loads"]
                self.combination_object.Coefficients = data["coefficients"]
            else:
                # Create new combination
                self.create_load_combination(
                    data["name"],
                    data["description"],
                    data["loads"],
                    data["coefficients"]
                )

            return True
        except Exception as e:
            QtGui.QMessageBox.critical(None, "Error", f"Failed to process load combination:\n{str(e)}")
            return False



    def getStandardButtons(self):
        return QtGui.QDialogButtonBox.Apply | QtGui.QDialogButtonBox.Close

    def clicked(self, button):
        App.ActiveDocument.recompute()
        if button == QtGui.QDialogButtonBox.Apply:
            self.create_or_update_combination()
        elif button == QtGui.QDialogButtonBox.Close:
            Gui.Control.closeDialog()
        return True

    def reject(self):
        Gui.Control.closeDialog()
        return True

    def accept(self):

        if self.create_or_update_combination():
            Gui.Control.closeDialog()
            return True
        return False

    def create_load_combination(self, name, description, loads, coefficients):
        """Placeholder for the missing function - you'll need to implement this"""
        # make_load_combination_group() doit exister pour grouper les combinaisons
        make_load_combination_group()
        # create_load_combination() doit exister pour créer l'objet
        create_load_combination(name, description, loads, coefficients)


def show_load_combination_modifier(combination=None):
    """
    Standardized entry point for modifying load combinations.
    Uses the internal load_data() method to pre-fill the UI.
    """
    if hasattr(Gui, 'Control') and Gui.Control.activeDialog():
        Gui.Control.closeDialog()

    # The constructor calls load_data(combination) automatically
    panel = LoadCombinationTaskPanel(combination=combination)

    Gui.Control.showDialog(panel)
    return panel