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
# commands/results_viewer.py


class ResultsViewerCommand:
    """Command to show the results viewer dialog"""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(
                BeamTools.getBeamModulePath(), "icons", "beam_results.svg"
            ),  # You'll need to add this SVG
            "MenuText": translate("BeamWorkbench", "Results Viewer"),
            "ToolTip": translate("BeamWorkbench", "View and control analysis results"),
            "Accel": "R, V",
        }

    def Activated(self):
        """Run when command is clicked"""
        from ui.dialog_ResultsViewer import show_results_viewer

        show_results_viewer()

    def IsActive(self):
        """Determine if command should be active"""
        return App.ActiveDocument is not None


# Add command to FreeCAD
Gui.addCommand("ResultsViewer", ResultsViewerCommand())

