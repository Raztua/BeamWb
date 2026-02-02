# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2026                                                    *
# *                                                                         *
# *   This program is free software: you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License as        *
# *   published by the Free Software Foundation, either version 3 of the    *
# *   License, or (at your option) any later version.                       *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Lesser General Public License for more details.                   *
# *                                                                         *
# *   You should have received a copy of the GNU Lesser General Public      *
# *   License along with this program.  If not,                             *
# *   see <https://www.gnu.org/licenses/>.                                  *
# *                                                                         *
# ***************************************************************************

import FreeCAD as App
import FreeCADGui as Gui
import os
from . import BeamTools
from PySide import QtCore

translate = App.Qt.translate
import Spreadsheet
from features.LoadCombination import LoadCombinationViewProvider, LoadCombination

# commands.LoadCombination.py


class CreateLoadCombinationCommand:
    """Command to create a new Load Combination spreadsheet"""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(
                BeamTools.getBeamModulePath(), "icons", "beam_load_combination.svg"
            ),
            "MenuText": translate("BeamWorkbench", "Create Load Combination"),
            "ToolTip": translate(
                "BeamWorkbench", "Create a new Load Combination spreadsheet"
            ),
        }

    def Activated(self):
        doc = App.ActiveDocument
        if not doc:
            return

        # Create spreadsheet
        sheet = doc.addObject("Spreadsheet::Sheet", "LoadCombinations")

        # Get all load IDs (load cases)
        load_ids = [
            obj
            for obj in doc.Objects
            if hasattr(obj, "Type") and obj.Type == "LoadIDFeature"
        ]

        if not load_ids:
            return

        # Create header row
        sheet.set("A1", "Combination Name")
        for col, load_id in enumerate(load_ids, start=1):
            sheet.set("{0}1".format(chr(65 + col)), load_id.Label)

        # Add sample combination
        sheet.set("A2", "Combination 1")
        for col in range(1, len(load_ids) + 1):
            sheet.set("{0}2".format(chr(65 + col)), "0.0")

        # Create load combination object
        comb = doc.addObject("App::FeaturePython", "LoadCombination")
        LoadCombination(comb)
        comb.Spreadsheet = sheet
        LoadCombinationViewProvider(comb.ViewObject)

        # Open spreadsheet in editor
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(sheet)
        Gui.runCommand("Std_Spreadsheet", 0)

    def IsActive(self):
        if not (hasattr(App.ActiveDocument, "Analysis")):
            return False
        return App.ActiveDocument is not None

