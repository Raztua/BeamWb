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
from . import Beam_Tools
from PySide import QtCore

translate = App.Qt.translate
# BeamColorizer.py


class BeamColorizerCommand:
    """Command to color beams based on properties"""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(
                Beam_Tools.getBeamModulePath(), "icons", "beam_colorizer.svg"
            ),  # You can create this icon later
            "MenuText": translate("BeamWorkbench", "Beam Colorizer"),
            "ToolTip": translate(
                "BeamWorkbench", "Automatically color beams based on their properties"
            ),
            "Accel": "C, B",
        }

    def Activated(self):
        """Execute when the command is clicked"""
        from ui.dialog_BeamColorizer import show_beam_colorizer

        show_beam_colorizer()

    def IsActive(self):
        """Determine if the command should be active"""
        return App.ActiveDocument is not None


# Only register the command if we're running in FreeCAD
if App.GuiUp:
    Gui.addCommand("BeamColorizer", BeamColorizerCommand())

