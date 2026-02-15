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

from ui.dialog import show_section_creator


class CreateSectionCommand:
    """Command to create sections"""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(
                Beam_Tools.getBeamModulePath(), "icons", "beam_section.svg"
            ),
            "MenuText": translate("BeamWorkbench", "Create Section"),
            "ToolTip": translate("BeamWorkbench", "Creates a new cross-section"),
            "Accel": "S, S",
        }

    def Activated(self):
        """Run when command is clicked"""
        show_section_creator()  # Now shows task panel

    def IsActive(self):
        """Determine if command should be active"""
        if not (hasattr(App.ActiveDocument, "Analysis")):
            return False
        return App.ActiveDocument is not None

class ModifySectionCommand:
    """Command to modify existing sections"""
    def GetResources(self):
        return {
            "Pixmap": os.path.join(
                Beam_Tools.getBeamModulePath(), "icons", "beam_section.svg"
            ),
            "MenuText": translate("BeamWorkbench", "Modify Section"),
            "ToolTip": translate("BeamWorkbench", "Modify cross-section"),
        }

    def Activated(self):
        from ui.dialog_SectionModifier import show_section_modifier
        # Check current selection for pre-selection
        selection = Gui.Selection.getSelection()
        sections = [obj for obj in selection if hasattr(obj, "Type") and obj.Type == "SectionFeature"]
        show_section_modifier(sections if sections else None)

# Add command to FreeCAD
if App.GuiUp:
    Gui.addCommand("CreateSection", CreateSectionCommand())
    Gui.addCommand('ModifySection', ModifySectionCommand())
