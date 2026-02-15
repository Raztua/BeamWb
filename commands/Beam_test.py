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
from features.FEMVisualization import FEMVisualization


class TestCommand:
    """Command to create sections"""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(
                Beam_Tools.getBeamModulePath(), "icons", "beam_section.svg"
            ),
            "MenuText": translate("BeamWorkbench", "test"),
            "ToolTip": translate("BeamWorkbench", "test function"),
            "Accel": "S, S",  # Optional keyboard shortcut
        }

    def Activated(self):
        """Run when command is clicked"""
        from pivy import coin
        from features.LoadNodal import NodalLoad, NodalLoadViewProvider

        doc = App.ActiveDocument
        load = doc.addObject("App::FeaturePython", "NodalLoad")
        NodalLoad(load)
        load.Nodes = App.ActiveDocument.getObject("Node")
        load.Force = App.Vector(10, 10, 0)
        NodalLoadViewProvider(load.ViewObject)

        print("after creation")

    def IsActive(self):
        """Determine if command should be active"""
        if not (hasattr(App.ActiveDocument, "Analysis")):
            return False
        return App.ActiveDocument is not None


# Add command to FreeCAD
Gui.addCommand("TestCommand", TestCommand())

