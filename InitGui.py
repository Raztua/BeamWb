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

import sys


class BeamWB(Workbench):
    """FEM Workbench class"""

    MenuText = "Beam Workbench"
    ToolTip = "A workbench for Beam FEM modeling"

    def __init__(self):
        import os
        from commands import BeamTools
        from PySide import QtCore

        translate = FreeCAD.Qt.translate

        # Get the directory containing this file
        icon_path = os.path.join(
            BeamTools.getBeamModulePath(), "icons", "beam_workbench.svg"
        )
        self.__class__.Icon = icon_path
        self.__class__.MenuText = translate("BeamWorkbench", "Beam Workbench")
        self.__class__.ToolTip = translate(
            "BeamWorkbench", "A workbench for Beam FEM modeling"
        )

        icons_path = os.path.join(BeamTools.getBeamModulePath(), "icons")
        QtCore.QDir.addSearchPath("icons", icons_path)

    def Initialize(self):
        """Initialize the workbench with lazy imports"""
        # Import commands only when needed
        from commands.Beamnodes import (
            ManageNodesCommand,
            ModifyNodeCommand,
            OffsetNodeCommand,
            CreateNodeCommand,
        )
        from commands.Beamsections import CreateSectionCommand
        from commands.Beamloads import (
            CreateLoadIDCommand,
            CreateNodalLoadCommand,
            CreateMemberLoadCommand,
            CreateAccelerationLoadCommand,
        )
        from commands.beams import CreateBeamCommand, ModifyBeamCommand
        from commands.Beamtest import TestCommand
        from commands.Beamload_combination import CreateLoadCombinationCommand
        from commands.Beamboundary_conditions import CreateBoundaryConditionCommand
        from commands.BeamAnalysisGroup import CreateAnalysisGroupCommand
        from commands.Beammember_releases import CreateMemberReleaseCommand
        from commands.Beamrun_analysis import AnalysisCommand
        from commands.Beammaterial import CreateMaterialCommand
        from commands.BeamItemLabeling import ItemLabelingCommand
        from commands.BeamColorizer import BeamColorizerCommand
        from commands.BeamCodeCheck import CreateCodeCheckCommand
        from commands.Beamresults_viewer import ResultsViewerCommand
        from commands.Beamsolver import AnalysisCommand

        # Define command lists for each category
        model_setup_commands = [
            "CreateAnalysisGroup",
            "ManageNodes",
            "CreateNode",
            "ModifyNode",
            "OffsetNode",
            "CreateSection",
            "CreateMaterial",
            "CreateBeam",
            "ModifyBeam",
        ]

        loads_bc_commands = [
            "CreateBoundaryCondition",
            "CreateMemberRelease",
            "CreateLoadID",
            "CreateNodalLoad",
            "CreateMemberLoad",
            "CreateAccelerationLoad",
            "CreateLoadCombination",
        ]

        analysis_commands = [
            "AnalysisCommand",  # This is the new merged command
            "ResultsViewer",
        ]

        post_processing_commands = ["RunCodeCheck", "ItemLabeling", "BeamColorizer"]

        # Append toolbars and menus for each category
        self.appendToolbar("Model Setup", model_setup_commands)
        self.appendMenu("Model Setup", model_setup_commands)

        self.appendToolbar("Loads & BCs", loads_bc_commands)
        self.appendMenu("Loads & BCs", loads_bc_commands)

        self.appendToolbar("Analysis", analysis_commands)
        self.appendMenu("Analysis", analysis_commands)

        self.appendToolbar("Post-Processing", post_processing_commands)
        self.appendMenu("Post-Processing", post_processing_commands)

    #

    def Activated(self):
        """When workbench is activated"""
        pass

    def Deactivated(self):
        """When workbench is deactivated"""
        pass

    def GetClassName(self):
        return "Gui::PythonWorkbench"


# Add the workbench to FreeCAD
FreeCADGui.addWorkbench(BeamWB())
