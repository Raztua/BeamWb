import FreeCADGui as Gui
import os
import FreeCAD

class BeamWB(Gui.Workbench):
    """FEM Workbench class"""
    MenuText = "Beam Workbench"
    ToolTip = "A workbench for Beam FEM modeling"

    def __init__(self):
        # Get the directory containing this file
        self.__class__.Icon = self.get_icon_path("workbench_icon.svg")

    def Initialize(self):
        """Initialize the workbench with lazy imports"""
        # Import commands only when needed
        from commands.nodes import ManageNodesCommand, ModifyNodeCommand,OffsetNodeCommand,CreateNodeCommand
        from commands.sections import CreateSectionCommand
        from commands.loads import CreateLoadIDCommand, CreateNodalLoadCommand,CreateMemberLoadCommand,CreateAccelerationLoadCommand
        from commands.beams import CreateBeamCommand, ModifyBeamCommand
        from commands.test import TestCommand
        from commands.load_combination import CreateLoadCombinationCommand
        from commands.boundary_conditions import CreateBoundaryConditionCommand
        from commands.AnalysisGroup import CreateAnalysisGroupCommand
        from commands.member_releases import CreateMemberReleaseCommand
        from commands.run_analysis import AnalysisCommand
        from commands.material import CreateMaterialCommand
        from commands.ItemLabeling import ItemLabelingCommand
        from commands.BeamColorizer import BeamColorizerCommand
        from commands.CodeCheck import CreateCodeCheckCommand
        from commands.results_viewer import ResultsViewerCommand
        from commands.solver import AnalysisCommand
        # Define command lists for each category
        model_setup_commands = [
            'CreateAnalysisGroup',
            'ManageNodes',
            'CreateNode',
            'ModifyNode',
            'OffsetNode',
            'CreateSection',
            'CreateMaterial',
            'CreateBeam',
            'ModifyBeam'
        ]

        loads_bc_commands = [
            'CreateBoundaryCondition',
            'CreateMemberRelease',
            'CreateLoadID',
            'CreateNodalLoad',
            'CreateMemberLoad',
            'CreateAccelerationLoad',
            'CreateLoadCombination'
        ]

        analysis_commands = [
            'AnalysisCommand',  # This is the new merged command
            'ResultsViewer'
        ]

        post_processing_commands = [
            'RunCodeCheck',
            'ItemLabeling',
            'BeamColorizer'
        ]

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
    
    def get_icon_path(self, icon_name):
        """Helper method to get absolute path to icons"""
        # Get the directory containing this file
        wb_path = os.path.dirname(__file__) if '__file__' in globals() else os.path.join(
            FreeCAD.getUserAppDataDir(), "Mod", "BeamWB")
        return os.path.join(wb_path, "icons", icon_name)
    
   
    def Activated(self):
        """When workbench is activated"""
        pass
    
    def Deactivated(self):
        """When workbench is deactivated"""
        pass

# Add the workbench to FreeCAD
Gui.addWorkbench(BeamWB())