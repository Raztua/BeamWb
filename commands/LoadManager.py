import FreeCAD as App
import FreeCADGui as Gui
# Import Load-related classes needed by LoadManager methods
from features.LoadNodal import NodalLoad, NodalLoadViewProvider
from features.LoadAcceleration import AccelerationLoad, AccelerationLoadViewProvider
from features.LoadCombination import LoadCombination, LoadCombinationViewProvider, LoadCombinationGroupViewProvider, \
    LoadCombinationGroup


class LoadManager:
    """Handles creation of all load types (nodal, distributed, pressure, etc.)"""

    def create_acceleration_load(load_id, linear_acceleration, beams=None):
        """Create an acceleration load object - simplified without rotation"""
        doc = App.ActiveDocument
        if not doc:
            raise RuntimeError("No active document")

        # Create the load object
        acc = doc.addObject("App::FeaturePython", "AccelerationLoad")
        AccelerationLoad(acc)

        if App.GuiUp:
            AccelerationLoadViewProvider(acc.ViewObject)

        # Set properties
        acc.LinearAcceleration = linear_acceleration

        if beams:
            acc.Beams = beams
        acc.Label = "AccelLoad"
        if hasattr(load_id, "addObject"):
            load_id.addObject(acc)

        return acc

    def create_member_load(load_id, beams, start_force, end_force,
                           start_moment=None, end_moment=None,
                           start_position=0.0, end_position=1.0,
                           local_cs=True):
        """Create a member load on selected beams"""
        if not beams:
            raise ValueError("No beams selected")

        if start_moment is None:
            start_moment = (0.0, 0.0, 0.0)
        if end_moment is None:
            end_moment = (0.0, 0.0, 0.0)

        doc = App.ActiveDocument
        if not doc:
            raise RuntimeError("No active document")

        # Create the member load object
        member_load = doc.addObject("App::FeaturePython", "MemberLoad")
        from features.LoadMember import MemberLoad, MemberLoadViewProvider
        MemberLoad(member_load)

        if App.GuiUp:
            MemberLoadViewProvider(member_load.ViewObject)

        # Set properties
        member_load.Beams = beams
        member_load.StartForce = App.Vector(*start_force)
        member_load.EndForce = App.Vector(*end_force)
        member_load.StartMoment = App.Vector(*start_moment)
        member_load.EndMoment = App.Vector(*end_moment)
        member_load.StartPosition = start_position
        member_load.EndPosition = end_position
        member_load.LocalCS = local_cs

        # Add to load group if it exists
        if hasattr(load_id, "addObject"):
            load_id.addObject(member_load)

        return member_load

    @staticmethod
    def create_nodal_load(load_id, nodes, force, moment):
        """Create a nodal force/moment load"""
        doc = App.ActiveDocument
        if not doc:
            raise RuntimeError("No active document")
        # Validate inputs
        if not LoadManager._validate_load_id(load_id):
            raise ValueError("Invalid LoadID provided")

        if not isinstance(nodes, list) or len(nodes) == 0:
            raise ValueError("At least one node must be provided")
        # Create the load object
        load = doc.addObject("App::FeaturePython", "NodalLoad")
        NodalLoad(load)
        # Set properties
        load.Nodes = nodes
        load.Force = App.Vector(force)
        load.Moment = App.Vector(moment)

        # Add to LoadID group
        if hasattr(load_id, "addObject"):
            load_id.addObject(load)

        # attach the view provider
        if App.GuiUp:
            load.ViewObject.Proxy = NodalLoadViewProvider(load.ViewObject)

        return load

    @staticmethod
    def create_distributed_load(load_id, elements, magnitude, direction):
        """Create a distributed load on beam/shell elements"""
        # Implementation for distributed loads
        pass

    @staticmethod
    def create_pressure_load(load_id, surfaces, pressure):
        """Create a pressure load on surfaces"""
        # Implementation for pressure loads
        pass

    @staticmethod
    def _validate_load_id(load_id):
        """Validate LoadID object"""
        print("_validate_load_id", load_id, load_id.Type, load_id.Type == "LoadIDFeature")
        return (load_id is not None and
                hasattr(load_id, "Type") and
                load_id.Type == "LoadIDFeature")

    @staticmethod
    def create_load(load_type, load_id, *args, **kwargs):
        """Factory method for creating loads"""
        creators = {
            'nodal': LoadManager.create_nodal_load,
            'member': LoadManager.create_member_load,
            'acceleration': LoadManager.create_acceleration_load,
            'distributed': LoadManager.create_distributed_load,
            'pressure': LoadManager.create_pressure_load
        }

        if load_type not in creators:
            raise ValueError(f"Unknown load type: {load_type}")

        return creators[load_type](load_id, *args, **kwargs)

    @staticmethod
    def get_load_combination_group():
        """Get or create the Load Combinations group"""
        doc = App.ActiveDocument
        if not doc:
            return None

        # Check if group already exists by looking for an object with the right type
        for obj in doc.Objects:
            if hasattr(obj, "Type") and obj.Type == "LoadCombinationGroup":
                return obj

        # If not found, create a new group
        group = doc.addObject("App::DocumentObjectGroupPython", "LoadCombinations")
        LoadCombinationGroup(group)
        if App.GuiUp:
            group.ViewObject.Proxy = LoadCombinationGroupViewProvider(group.ViewObject)

        # Set the group type property
        group.Type = "LoadCombinationGroup"
        group.Label = "Load Combinations"

        return group

    @staticmethod
    def create_or_edit_combination(combination=None):
        """Create new or edit existing combination using task panel"""
        # Import the task panel
        from ui.dialog_LoadCombination import LoadCombinationTaskPanel

        # Create and open the task panel
        panel = LoadCombinationTaskPanel(combination)
        Gui.Control.showDialog(panel)
        App.ActiveDocument.recompute()

        # The task panel will handle the creation/editing through its accept() method
        return None