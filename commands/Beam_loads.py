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
from ui.dialog import show_nodal_load_creator, show_load_group_creator
from ui.dialog import show_member_load_creator, show_acceleration_load_creator
from features.LoadManager import LoadManager


class CreateLoadIDCommand:
    """Command to create a new Load ID"""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(
                Beam_Tools.getBeamModulePath(), "icons", "beam_load_ID.svg"
            ),
            "MenuText": translate("BeamWorkbench", "Create Load ID"),
            "ToolTip": translate(
                "BeamWorkbench", "Create a new Load ID for organizing loads"
            ),
        }

    def Activated(self):
        show_load_group_creator()

    def IsActive(self):
        if not (hasattr(App.ActiveDocument, "Analysis")):
            return False
        return App.ActiveDocument is not None


class CreateMemberLoadCommand:
    """Command to create member loads"""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(
                Beam_Tools.getBeamModulePath(), "icons", "beam_member_load.svg"
            ),
            "MenuText": translate("BeamWorkbench", "Create Member Load"),
            "ToolTip": translate(
                "BeamWorkbench", "Create distributed loads on selected beams"
            ),
        }

    def Activated(self):
        # Get selected beams first
        selected_beams = [
            obj
            for obj in Gui.Selection.getSelection()
            if hasattr(obj, "Type") and obj.Type == "BeamFeature"
        ]
        # Show dialog with pre-selected beams

        show_member_load_creator(selected_beams)

    def IsActive(self):
        # Only active when beams are selected
        if not (hasattr(App.ActiveDocument, "Analysis")):
            return False
        return App.ActiveDocument is not None


class CreateAccelerationLoadCommand:
    """Command to create acceleration loads"""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(
                Beam_Tools.getBeamModulePath(), "icons", "beam_acceleration_load.svg"
            ),
            "MenuText": translate("BeamWorkbench", "Create Acceleration Load"),
            "ToolTip": translate(
                "BeamWorkbench", "Create acceleration loads (linear and rotational)"
            ),
        }

    def Activated(self):
        # Get selected objects (beams or nothing for whole model)
        selected_objects = Gui.Selection.getSelection()
        selected_beams = [
            obj
            for obj in selected_objects
            if hasattr(obj, "Type") and obj.Type == "BeamFeature"
        ]

        # Show dialog with selection info

        show_acceleration_load_creator(selected_beams)

    def IsActive(self):
        if not (hasattr(App.ActiveDocument, "Analysis")):
            return False
        return App.ActiveDocument is not None


class CreateNodalLoadCommand:
    """Command to create nodal loads"""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(
                Beam_Tools.getBeamModulePath(), "icons", "beam_nodal_load.svg"
            ),
            "MenuText": translate("BeamWorkbench", "Create Nodal Load"),
            "ToolTip": translate(
                "BeamWorkbench", "Create nodal loads on selected nodes"
            ),
        }

    def Activated(self):
        # Get selected nodes first
        selected_nodes = [
            obj
            for obj in Gui.Selection.getSelection()
            if hasattr(obj, "Type") and obj.Type == "NodeFeature"
        ]

        # Show dialog with pre-selected nodes
        show_nodal_load_creator(selected_nodes)

    def IsActive(self):
        # Only active when nodes are selected
        if not (hasattr(App.ActiveDocument, "Analysis")):
            return False
        return App.ActiveDocument is not None


class CreateDistributedLoadCommand:
    """Command to create distributed loads"""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(
                Beam_Tools.getBeamModulePath(), "icons", "beam_distributed_load.svg"
            ),
            "MenuText": translate("BeamWorkbench", "Create Distributed Load"),
            "ToolTip": translate(
                "BeamWorkbench", "Create distributed loads on selected elements"
            ),
        }

    def Activated(self):
        # Implementation would mirror nodal load but for beam/shell elements
        pass

    def IsActive(self):
        # Only active when beam/shell elements are selected
        pass


class CreateLoadCombinationCommand:
    """Command to create/edit load combinations"""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(
                Beam_Tools.getBeamModulePath(), "icons", "beam_load_combination.svg"
            ),
            "MenuText": translate("BeamWorkbench", "Create/Edit Load Combination"),
            "ToolTip": translate(
                "BeamWorkbench", "Create or edit a linear combination of loads"
            ),
        }

    def Activated(self):
        from features.LoadManager import LoadManager
        from features.LoadCombination import LoadCombination

        # Get selection properly
        selection = Gui.Selection.getSelection()
        combination = None

        # Check if we're editing an existing combination
        if selection and len(selection) == 1:
            obj = selection[0]
            if (
                hasattr(obj, "Proxy")
                and hasattr(obj.Proxy, "Type")
                and obj.Proxy.Type == "LoadCombination"
            ):
                combination = obj

        # Call manager without recursion
        LoadManager.create_or_edit_combination(combination)

    def IsActive(self):
        if not (hasattr(App.ActiveDocument, "Analysis")):
            return False
        return App.ActiveDocument is not None


# Add all commands to FreeCAD
Gui.addCommand("CreateLoadID", CreateLoadIDCommand())
Gui.addCommand("CreateNodalLoad", CreateNodalLoadCommand())
Gui.addCommand("CreateMemberLoad", CreateMemberLoadCommand())
Gui.addCommand("CreateAccelerationLoad", CreateAccelerationLoadCommand())
Gui.addCommand("CreateLoadCombination", CreateLoadCombinationCommand())

