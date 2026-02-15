import FreeCAD as App
import os
from PySide import QtGui, QtCore
from prettytable.prettytable import PrettyTable, HRuleStyle, VRuleStyle, TableStyle


WORKBENCH_DIR = os.path.dirname(os.path.dirname(__file__))
ICON_DIR = os.path.join(WORKBENCH_DIR, "icons")
LOAD_COMB_ICON_PATH = os.path.join(ICON_DIR, "beam_load_combination.svg")


class LoadCombination:
    """The Load Combination feature Python object"""

    def __init__(self, obj):
        self.Type = "LoadCombination"
        obj.Proxy = self

        # Add custom properties
        obj.addProperty("App::PropertyString", "Type", "Base", "Load Combination Type").Type = "LoadCombination"
        obj.addProperty("App::PropertyString", "Comment", "Base", "Combination description")
        obj.addProperty("App::PropertyFloatList", "Coefficients", "Load", "Load coefficients")
        obj.addProperty("App::PropertyLinkList", "Loads", "Load", "Combined loads")

        # Set defaults
        obj.Coefficients = []
        obj.Loads = []

    def execute(self, obj):
        """Called on document recompute"""
        pass

    def onChanged(self, obj, prop):
        """Called when a property changes"""
        if prop in ["Coefficients", "Loads"]:
            self._validate_coefficients(obj)

    def _validate_coefficients(self, obj):
        """Ensure coefficients match loads"""
        if len(obj.Coefficients) != len(obj.Loads):
            obj.Coefficients = [1.0] * len(obj.Loads)

    def update_visualization(self):
        """Update visualization of all loads in this combination"""
        if hasattr(self, "Object") and self.Object:
            if hasattr(self.Object, "ViewObject") and self.Object.ViewObject:
                if hasattr(self.Object.ViewObject.Proxy, "updateData"):
                    self.Object.ViewObject.Proxy.updateData(self.Object, "")


class LoadCombinationViewProvider:
    """View provider for Load Combination"""

    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        return LOAD_COMB_ICON_PATH

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

    def updateData(self, obj, prop):
        pass

    def onChanged(self, vobj, prop):
        pass

    def doubleClicked(self, vobj):
        """Handle double-click to open modifier"""
        try:
            from ui.dialog_LoadCombination import show_load_combination_modifier
            show_load_combination_modifier([vobj.Object])
            return True
        except Exception as e:
            App.Console.PrintError(f"Error: {str(e)}\n")
            return False

    def setupContextMenu(self, vobj, menu):
        """Add context menu item"""
        from PySide import QtGui
        action = QtGui.QAction("Modify Combination", menu)
        action.triggered.connect(lambda: self.onModify(vobj.Object))
        menu.addAction(action)

    def onModify(self, obj):
        from ui.dialog_LoadCombination import show_load_combination_modifier
        show_load_combination_modifier([obj])

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None

    def canDragObjects(self):
        return False

    def canDropObjects(self):
        return False


class LoadCombinationGroup:
    """Group for organizing load combinations"""

    def __init__(self, obj):
        obj.Proxy = self
        obj.addProperty("App::PropertyString", "Type", "Base", "Group Type").Type = "LoadCombinationGroup"

    def execute(self, obj):
        pass

    def onChanged(self, obj, prop):
        pass


class LoadCombinationGroupViewProvider:
    """View provider for Load Combination Group"""

    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        return os.path.join(ICON_DIR, "beam_load_combination_group.svg")

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

    def updateData(self, obj, prop):
        pass

    def onChanged(self, vobj, prop):
        pass

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None

    def canDragObjects(self):
        return False

    def canDropObjects(self):
        return False

    # --- CONTEXT MENU IMPLEMENTATION ---
    def setupContextMenu(self, vobj, menu):
        """Adds a context menu item to list all Load Combinations."""
        from PySide import QtGui

        if PrettyTable is None:
            return

        action = QtGui.QAction("List Load Combinations Matrix in Report View", menu)
        action.triggered.connect(lambda: self.onListLoadCombinations(vobj.Object))
        menu.addAction(action)

    def onListLoadCombinations(self, lcomb_group):
        """Collects Load Combination data and prints it as a matrix (rows=comb, cols=LoadID)."""

        if PrettyTable is None:
            App.Console.PrintError("Cannot list Load Combinations: PrettyTable module is missing.\n")
            return

        # --- 1. COLLECT ALL UNIQUE LOAD IDS ---

        # We need a centralized way to get ALL LoadID features in the document.
        # Assuming the main "Loads" group is accessible and contains LoadID features.
        doc = App.ActiveDocument
        if not hasattr(doc, "Loads") or not doc.Loads:
            App.Console.PrintWarning("\nNo main 'Loads' group found. Cannot determine load ID columns.\n")
            return

        # Collect unique LoadID objects (the direct children of the main 'Loads' group)
        all_load_ids = [
            obj for obj in doc.Loads.Group
            if hasattr(obj, 'Type') and obj.Type == 'LoadIDFeature'
        ]

        # Map Load ID object to its column name/label
        load_id_map = {load_id: load_id.Label for load_id in all_load_ids}

        # Define table fields (columns)
        field_names = ["Combination", "Comment"] + list(load_id_map.values())

        if not all_load_ids:
            App.Console.PrintWarning("\nNo Load IDs found in the document. Cannot display matrix.\n")
            return

        # --- 2. SETUP TABLE AND POPULATE ROWS ---

        table = PrettyTable()
        table.field_names = field_names
        table.align["Combination"] = "l"
        table.align["Comment"] = "l"
        table.set_style(TableStyle.SINGLE_BORDER)

        # Iterate over each Load Combination (rows)
        for comb in lcomb_group.Group:
            if hasattr(comb, "Type") and comb.Type == "LoadCombination":

                # Dictionary to store coefficients for this combination: {LoadID_Label: Coefficient}
                comb_coeffs = {load.Label: coeff for load, coeff in zip(comb.Loads, comb.Coefficients)}

                row_data = [comb.Label, getattr(comb, "Comment", "N/A")]

                # Fill coefficient columns based on the load_id_map order
                for load_id_label in load_id_map.values():
                    # Retrieve coefficient, defaulting to 0.0 if not found in the combination
                    coeff = comb_coeffs.get(load_id_label, 0.0)
                    row_data.append(f"{coeff:.2f}")

                table.add_row(row_data)

        # --- 3. CONCATENATE AND PRINT OUTPUT (SINGLE CALL) ---

        header_string = "\n--- Load Combinations Matrix (Coefficients) ---\n"
        table_string = table.get_string()
        final_output = header_string + table_string + "\n"

        App.Console.PrintMessage(final_output)
    # --- END CONTEXT MENU IMPLEMENTATION ---


def make_load_combination_group():
    """Create or get the Nodes group with proper icon paths and add it to AnalysisGroup"""
    doc = App.ActiveDocument
    if not doc:
        App.Console.PrintError("No active document found\n")
        return None

    # Check if Load combination group already exists
    if hasattr(doc, "LoadCombinations"):
        lcomb_group = doc.LoadCombinations
    else:
        # Create new Nodes group
        lcomb_group = doc.addObject("App::DocumentObjectGroupPython", "LoadCombinations")
        LoadCombinationGroup(lcomb_group)
        lcomb_group.Label = "LoadCombinations"

        # Add the Nodes group to the AnalysisGroup if it exists
        from features.AnalysisGroup import get_analysis_group
        analysis_group = get_analysis_group()
        if analysis_group and lcomb_group not in analysis_group.Group:
            analysis_group.addObject(lcomb_group)

        if App.GuiUp:
            lcomb_group.ViewObject.Proxy = LoadCombinationGroupViewProvider(lcomb_group.ViewObject)


    return lcomb_group


def create_load_combination(name=None, comment=None, loads=None, coefficients=None):
    doc = App.ActiveDocument
    if not doc:
        App.Console.PrintError("No active document found\n")
        return None

    try:
        group = make_load_combination_group()
        if not group:
            App.Console.PrintError("Failed to Load combination  group\n")
            return None
        comb = doc.addObject("Part::FeaturePython", "LoadCombination")
        LoadCombination(comb)
        comb.Label = name
        comb.Comment = comment
        comb.Loads = loads
        comb.Coefficients = coefficients
        group.addObject(comb)
        if App.GuiUp:
            LoadCombinationViewProvider(comb.ViewObject)
        App.ActiveDocument.recompute()

        return comb
    except Exception as e:
        App.Console.PrintError(f"Error in create_load_combination: {str(e)}\n")
        return None