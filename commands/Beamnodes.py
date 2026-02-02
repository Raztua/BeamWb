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
# nodes.py (command part)


class ManageNodesCommand:
    """Command to manage nodes using task panel"""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(
                BeamTools.getBeamModulePath(), "icons", "beam_node_manager.svg"
            ),
            "MenuText": translate("BeamWorkbench", "Manage Nodes"),
            "ToolTip": translate("BeamWorkbench", "Create and manage structural nodes"),
            "Accel": "N, M",
        }

    def Activated(self):
        """Run when command is clicked"""
        from ui.dialog_NodeManager import show_node_manager

        show_node_manager()

    def IsActive(self):
        """Determine if command should be active"""
        if not (hasattr(App.ActiveDocument, "Analysis")):
            return False
        return App.ActiveDocument is not None


class CreateNodeCommand:
    """Command to create nodes by entering coordinates"""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(
                BeamTools.getBeamModulePath(), "icons", "beam_node_create.svg"
            ),
            "MenuText": translate("BeamWorkbench", "Create Node"),
            "ToolTip": translate(
                "BeamWorkbench", "Create nodes by entering coordinates"
            ),
            "Accel": "N, C",
        }

    def Activated(self):
        """Run when command is clicked"""
        from ui.dialog_NodeCreator import show_node_creator

        show_node_creator()

    def IsActive(self):
        """Determine if command should be active"""
        return App.ActiveDocument is not None


class ModifyNodeCommand:
    """Command to modify existing nodes"""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(
                BeamTools.getBeamModulePath(), "icons", "beam_node_modify.svg"
            ),
            "MenuText": translate("BeamWorkbench", "Modify Nodes"),
            "ToolTip": translate("BeamWorkbench", "Modify selected nodes"),
            "Accel": "N, M",
        }

    def Activated(self):
        """Run when command is clicked"""
        from ui.dialog_NodeModifier import show_node_modifier

        show_node_modifier()

    def IsActive(self):
        """Determine if command should be active"""
        return App.ActiveDocument is not None


class OffsetNodeCommand:
    """Command to create offset nodes"""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(
                BeamTools.getBeamModulePath(), "icons", "beam_node_offset.svg"
            ),
            "MenuText": translate("BeamWorkbench", "Offset Nodes"),
            "ToolTip": translate(
                "BeamWorkbench", "Create nodes offset from selected nodes"
            ),
            "Accel": "N, O",
        }

    def Activated(self):
        """Run when command is clicked"""
        from ui.dialog_NodeOffset import show_node_offset

        show_node_offset()

    def IsActive(self):
        """Determine if command should be active"""
        return App.ActiveDocument is not None


# Add commands to FreeCAD
Gui.addCommand("CreateNode", CreateNodeCommand())
Gui.addCommand("ModifyNode", ModifyNodeCommand())
Gui.addCommand("OffsetNode", OffsetNodeCommand())
Gui.addCommand("ManageNodes", ManageNodesCommand())

