# commands.LoadCombination.py
import FreeCAD as App
import FreeCADGui as Gui
import os
import Spreadsheet
from features.LoadCombination import LoadCombinationViewProvider,LoadCombination

class CreateLoadCombinationCommand:
    """Command to create a new Load Combination spreadsheet"""

    def GetResources(self):
        return {
            'Pixmap': os.path.join(os.path.dirname(__file__), "icons", "load_combination_icon.svg"),
            'MenuText': 'Create Load Combination',
            'ToolTip': 'Create a new Load Combination spreadsheet'
        }

    def Activated(self):
        doc = App.ActiveDocument
        if not doc:
            return

        # Create spreadsheet
        sheet = doc.addObject('Spreadsheet::Sheet', 'LoadCombinations')

        # Get all load IDs (load cases)
        load_ids = [obj for obj in doc.Objects
                    if hasattr(obj, "Type") and obj.Type == "LoadIDFeature"]

        if not load_ids:
            return

        # Create header row
        sheet.set('A1', 'Combination Name')
        for col, load_id in enumerate(load_ids, start=1):
            sheet.set("{0}1".format(chr(65 + col)), load_id.Label)

        # Add sample combination
        sheet.set('A2', 'Combination 1')
        for col in range(1, len(load_ids) + 1):
            sheet.set("{0}2".format(chr(65 + col)), '0.0')

        # Create load combination object
        comb = doc.addObject("App::FeaturePython", "LoadCombination")
        LoadCombination(comb)
        comb.Spreadsheet = sheet
        LoadCombinationViewProvider(comb.ViewObject)

        # Open spreadsheet in editor
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(sheet)
        Gui.runCommand('Std_Spreadsheet', 0)


    def IsActive(self):
        if not (hasattr(App.ActiveDocument, "Analysis")):
            return False
        return App.ActiveDocument is not None