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
        from commands import Beam_Tools
        from PySide import QtCore

        translate = FreeCAD.Qt.translate

        # Get the directory containing this file
        icon_path = os.path.join(
            Beam_Tools.getBeamModulePath(), "icons", "beam_workbench.svg"
        )
        self.__class__.Icon = icon_path
        self.__class__.MenuText = translate("BeamWorkbench", "Beam Workbench")
        self.__class__.ToolTip = translate(
            "BeamWorkbench", "A workbench for Beam FEM modeling"
        )

        icons_path = os.path.join(Beam_Tools.getBeamModulePath(), "icons")
        QtCore.QDir.addSearchPath("icons", icons_path)

    def Initialize(self):
        """Initialize the workbench with lazy imports"""
        # Import commands only when needed
        from commands.Beam_nodes import (
            ManageNodesCommand,
            ModifyNodeCommand,
            OffsetNodeCommand,
            CreateNodeCommand,
        )
        from commands.Beam_sections import CreateSectionCommand
        from commands.Beam_loads import (
            CreateLoadIDCommand,
            CreateNodalLoadCommand,
            CreateMemberLoadCommand,
            CreateAccelerationLoadCommand,
        )
        from commands.Beam_beams import CreateBeamCommand, ModifyBeamCommand
        from commands.Beam_test import TestCommand
        from commands.Beam_load_combination import CreateLoadCombinationCommand
        from commands.Beam_boundary_conditions import CreateBoundaryConditionCommand
        from commands.Beam_AnalysisGroup import CreateAnalysisGroupCommand
        from commands.Beam_member_releases import CreateMemberReleaseCommand
        from commands.Beam_run_analysis import AnalysisCommand
        from commands.Beam_material import CreateMaterialCommand
        from commands.Beam_ItemLabeling import ItemLabelingCommand
        from commands.Beam_Colorizer import BeamColorizerCommand
        from commands.Beam_CodeCheck import CreateCodeCheckCommand
        from commands.Beam_results_viewer import ResultsViewerCommand
        from commands.Beam_solver import AnalysisCommand

        # Define command lists for each category
        model_setup_commands = [
            "CreateAnalysisGroup",
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

        self.dock_panel = None

    def Activated(self):
        """When workbench is activated"""
        from PySide import QtCore, QtGui, QtWidgets
        import ui.SpreadsheetPanel as SpreadsheetPanel
        # Check if dock already exists to avoid duplicates
        mw = FreeCADGui.getMainWindow()
        dock = mw.findChild(QtWidgets.QDockWidget, "BeamSpreadsheet")

        if not dock:
            # Create the Dock Widget wrapper
            dock = QtWidgets.QDockWidget("Beam Spreadsheet", mw)
            dock.setObjectName("BeamSpreadsheet")  # Crucial for finding it later
            empty_title_bar = QtWidgets.QWidget()
            dock.setTitleBarWidget(empty_title_bar)

            # Create our custom content widget
            self.panel_widget = SpreadsheetPanel.SpreadsheetPanel()
            dock.setWidget(self.panel_widget)

            # Add to Main Window
            mw.addDockWidget(QtCore.Qt.BottomDockWidgetArea, dock)

        dock.setVisible(True)


    def Deactivated(self):
        # Optional: Hide the dock when leaving the workbench
        from PySide import QtCore, QtGui,QtWidgets
        mw = FreeCADGui.getMainWindow()
        dock = mw.findChild(QtWidgets.QDockWidget, "BeamSpreadsheet")
        if dock:
            dock.setVisible(False)

    def GetClassName(self):
        return "Gui::PythonWorkbench"


# Add the workbench to FreeCAD
FreeCADGui.addWorkbench(BeamWB())
