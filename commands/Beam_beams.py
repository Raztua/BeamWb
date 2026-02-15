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


class CreateBeamCommand:
    """Command to create beams between nodes"""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(Beam_Tools.getBeamModulePath(), "icons", "beam.svg"),
            "MenuText": translate("BeamWorkbench", "Create Beam"),
            "ToolTip": translate(
                "BeamWorkbench", "Creates a new beam between two nodes"
            ),
            "Accel": "B, B",
        }

    def Activated(self):
        """Execute when the command is clicked"""
        from ui.dialog import (
            show_beam_creator,
        )  # Local import to prevent circular imports

        show_beam_creator()

    def IsActive(self):
        """Determine if the command should be active"""
        if App.ActiveDocument is None:
            return False
        if not hasattr(App.ActiveDocument, "Nodes"):
            return False
        if not (hasattr(App.ActiveDocument, "Analysis")):
            return False
        if App.ActiveDocument.Nodes is None:
            return False
        if (
            len(App.ActiveDocument.Nodes.Group) < 2
        ):  # Need at least 2 nodes to create a beam
            return False
        return True


class ModifyBeamCommand:
    """Command to modify existing nodes"""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(
                Beam_Tools.getBeamModulePath(), "icons", "beam_modify.svg"
            ),
            "MenuText": translate("BeamWorkbench", "Modify Beams"),
            "ToolTip": translate("BeamWorkbench", "Modify selected Beams"),
            "Accel": "B, M",
        }

    def Activated(self):
        """Run when command is clicked"""
        from ui.dialog_BeamModifier import show_beam_modifier

        show_beam_modifier()

    def IsActive(self):
        """Determine if command should be active"""
        return App.ActiveDocument is not None


# Only register the command if we're running in FreeCAD
if App.GuiUp:
    Gui.addCommand("CreateBeam", CreateBeamCommand())
    Gui.addCommand("ModifyBeam", ModifyBeamCommand())

