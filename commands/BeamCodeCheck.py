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
from ui.TaskPanel_CodeCheck import show_code_check_task_panel


class CreateCodeCheckCommand:
    """
    Command to open the Code Check Setup Task Panel.
    """

    def GetResources(self):
        return {
            "Pixmap": os.path.join(
                BeamTools.getBeamModulePath(), "icons", "beam_Codecheck.svg"
            ),
            "MenuText": translate("BeamWorkbench", "Code Check Setup"),
            "ToolTip": translate(
                "BeamWorkbench", "Setup standards and parameters for code checking"
            ),
        }

    def Activated(self):
        # Open the Setup Task Panel
        show_code_check_task_panel()

    def IsActive(self):
        """Determine if the command should be active"""
        return App.ActiveDocument is not None


if Gui.getMainWindow():
    Gui.addCommand("RunCodeCheck", CreateCodeCheckCommand())

