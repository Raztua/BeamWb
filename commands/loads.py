import FreeCADGui as Gui
import FreeCAD as App
import os
from ui.dialog import show_nodal_load_creator, show_load_group_creator
from ui.dialog import show_member_load_creator, show_acceleration_load_creator
from features.LoadManager import LoadManager



def get_icon_path(icon_name):
    """Get absolute path to an icon"""
    WORKBENCH_DIR = os.path.dirname(os.path.dirname(__file__))
    ICON_DIR = os.path.join(WORKBENCH_DIR, "icons")
    return os.path.join(ICON_DIR, icon_name)


class CreateLoadIDCommand:
    """Command to create a new Load ID"""

    def GetResources(self):
        return {
            'Pixmap': get_icon_path("load_ID_icon.svg"),
            'MenuText': 'Create Load ID',
            'ToolTip': 'Create a new Load ID for organizing loads'
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
            'Pixmap': get_icon_path("member_load_icon.svg"),
            'MenuText': 'Create Member Load',
            'ToolTip': 'Create distributed loads on selected beams'
        }

    def Activated(self):
        # Get selected beams first
        selected_beams = [
            obj for obj in Gui.Selection.getSelection()
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
            'Pixmap': get_icon_path("acceleration_load_icon.svg"),
            'MenuText': 'Create Acceleration Load',
            'ToolTip': 'Create acceleration loads (linear and rotational)'
        }

    def Activated(self):
        # Get selected objects (beams or nothing for whole model)
        selected_objects = Gui.Selection.getSelection()
        selected_beams = [
            obj for obj in selected_objects
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
            'Pixmap': get_icon_path("nodal_load_icon.svg"),
            'MenuText': 'Create Nodal Load',
            'ToolTip': 'Create nodal loads on selected nodes'
        }

    def Activated(self):
        # Get selected nodes first
        selected_nodes = [
            obj for obj in Gui.Selection.getSelection()
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
            'Pixmap': get_icon_path("distributed_load_icon.svg"),
            'MenuText': 'Create Distributed Load',
            'ToolTip': 'Create distributed loads on selected elements'
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
            'Pixmap': get_icon_path("load_combination_icon.svg"),
            'MenuText': 'Create/Edit Load Combination',
            'ToolTip': 'Create or edit a linear combination of loads'
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
            if hasattr(obj, 'Proxy') and hasattr(obj.Proxy, 'Type') and obj.Proxy.Type == "LoadCombination":
                combination = obj

        # Call manager without recursion
        LoadManager.create_or_edit_combination(combination)

    def IsActive(self):
        if not (hasattr(App.ActiveDocument, "Analysis")):
            return False
        return App.ActiveDocument is not None


# Add all commands to FreeCAD
Gui.addCommand('CreateLoadID', CreateLoadIDCommand())
Gui.addCommand('CreateNodalLoad', CreateNodalLoadCommand())
Gui.addCommand('CreateMemberLoad', CreateMemberLoadCommand())
Gui.addCommand('CreateAccelerationLoad', CreateAccelerationLoadCommand())
Gui.addCommand('CreateLoadCombination', CreateLoadCombinationCommand())