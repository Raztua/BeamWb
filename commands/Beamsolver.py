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
# commands/AnalysisCommand.py


class AnalysisCommand:
    """Command to setup and run analysis"""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(
                BeamTools.getBeamModulePath(), "icons", "beam_solver.svg"
            ),
            "MenuText": translate("BeamWorkbench", "Run Analysis"),
            "ToolTip": translate("BeamWorkbench", "Setup and run structural analysis"),
            "Accel": "F5",
        }

    def Activated(self):
        """Run when command is clicked"""
        from ui.dialog_AnalysisSetup import show_analysis_setup

        show_analysis_setup()

    def IsActive(self):
        """Determine if command should be active"""
        if not (hasattr(App.ActiveDocument, "Analysis")):
            return False
        return App.ActiveDocument is not None


# Only register the command if we're running in FreeCAD
if App.GuiUp:
    Gui.addCommand("AnalysisCommand", AnalysisCommand())

