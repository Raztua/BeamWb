import FreeCAD as App
import FreeCADGui as Gui
import os
from PySide import QtGui, QtCore
from prettytable.prettytable import PrettyTable, HRuleStyle, VRuleStyle, TableStyle


WORKBENCH_DIR = os.path.dirname(os.path.dirname(__file__))
ICON_DIR = os.path.join(WORKBENCH_DIR, "icons")
LOAD_GROUP_ICON_PATH = os.path.join(ICON_DIR, "beam_load_group.svg")
LOAD_ID_ICON_PATH = os.path.join(ICON_DIR, "beam_load_ID.svg")


# Load group is the global load group
class LoadGroup:
    def __init__(self, obj):
        obj.Proxy = self
        obj.addProperty("App::PropertyString", "Type", "Base", "Group Type").Type = "LoadGroup"
        obj.addProperty("App::PropertyColor", "LoadColor", "Style", "Color for all loads").LoadColor = (1.0, 0.0, 0.0)
        obj.addProperty("App::PropertyFloat", "LoadScale", "Style", "Scale factor for loads").LoadScale = 2.0
        obj.addProperty("App::PropertyBool", "ShowLoads", "Display", "Show loads visualization").ShowLoads = True

    def onChanged(self, obj, prop):
        if prop in ["LoadColor", "LoadScale", "ShowLoads"]:
            # Update all loads in this group when properties change
            for child in obj.Group:
                if hasattr(child, "Proxy"):
                    if hasattr(child.Proxy, "ViewObject"):
                        child.Proxy.ViewObject.update_visualization()


# load ID is the group of a single load id
class LoadID:
    """The Load ID feature Python object"""

    def __init__(self, obj):
        """Initialize the Load ID object with custom properties"""
        self.Type = "LoadID"
        obj.Proxy = self

        # Add custom properties
        obj.addProperty("App::PropertyString", "Type", "Base", "Group Type", 4).Type = "LoadIDFeature"
        obj.addProperty("App::PropertyString", "Comment", "Base", "Comment", 4)


    def execute(self, obj):
        """Called on document recompute"""
        pass

    def onChanged(self, obj, prop):
        pass


class LoadIDViewProvider:
    """View provider for the Load ID object"""

    def __init__(self, vobj):
        """Initialize the view provider"""
        vobj.Proxy = self
        vobj.addProperty("App::PropertyColor", "LoadColor", "Load", "Load display color")
        vobj.addProperty("App::PropertyBool", "ShowLoads", "Load", "Toggle load visibility")
        vobj.addProperty("App::PropertyFloat", "LoadScale", "Load", "Load display scale factor")
        # Set default values
        vobj.LoadColor = (1.0, 0.0, 0.0)  # Red by default
        vobj.ShowLoads = True
        vobj.LoadScale = 1.0

    def getIcon(self):
        """Return the icon for this object"""
        return LOAD_ID_ICON_PATH

    def updateData(self, obj, prop):
        """Called when a property of the attached object changes"""
        pass

    def onChanged(self, vobj, prop):
        """Called when a view provider property changes"""
        if prop in ["LoadColor", "NodalLoadScale", "ShowLoads"]:
            for child in vobj.Object.Group:
                if hasattr(child, "Proxy"):
                    if hasattr(child.Proxy, "ViewObject"):
                        setattr(child.Proxy.ViewObject, prop, getattr(self, prop))
                        child.Proxy.ViewObject.update_visualization()

    def __getstate__(self):
        """Called when saving the document"""
        return None

    def __setstate__(self, state):
        """Called when restoring the document"""
        return None

    def canDragObjects(self):
        return False

    def canDropObjects(self):
        return False

    # --- CONTEXT MENU IMPLEMENTATION ---
    def setupContextMenu(self, vobj, menu):
        """Adds a context menu item to list all loads in this LoadID."""
        from PySide import QtGui

        if PrettyTable is None:
            App.Console.PrintWarning("PrettyTable not available for load listing.\n")
            return

        action = QtGui.QAction("List Contained Loads in Report View", menu)
        action.triggered.connect(lambda: self.onListLoads(vobj.Object))
        menu.addAction(action)

    def onListLoads(self, load_id_group):
        """Collects load data from contained objects and prints it to the FreeCAD report view."""

        if PrettyTable is None:
            App.Console.PrintError("Cannot list Loads: PrettyTable module is missing.\n")
            return

        # --- 1. SETUP AND COLLECT DATA ---

        table = PrettyTable()
        table.field_names = ["Name", "Type", "Nodes/Beams", "Force (N)", "Moment (Nm)", "Position/G-Vector"]
        table.align["Name"] = "l"
        table.set_style(TableStyle.SINGLE_BORDER)

        # Iterate over all loads in the group
        for obj in load_id_group.Group:
            load_type = getattr(obj, "Type", "Unknown")
            name = obj.Label

            nodes_beams_info = "N/A"
            force_info = "N/A"
            moment_info = "N/A"
            pos_info = "N/A"

            # --- Extract data based on Load Type ---

            # Nodal Load
            if load_type == "NodalLoad":
                nodes = getattr(obj, "Nodes", [])
                nodes_beams_info = ", ".join([n.Label for n in nodes]) if nodes else "Global"
                f = getattr(obj, "Force", App.Vector(0, 0, 0))
                m = getattr(obj, "Moment", App.Vector(0, 0, 0))
                force_info = f"({f.x:.1f}, {f.y:.1f}, {f.z:.1f})"
                moment_info = f"({m.x:.1f}, {m.y:.1f}, {m.z:.1f})"
                pos_info = "Nodal"

            # Member Load
            elif load_type == "MemberLoad":
                beams = getattr(obj, "Beams", [])
                nodes_beams_info = ", ".join([b.Label for b in beams]) if beams else "Global"
                sf = getattr(obj, "StartForce", App.Vector(0, 0, 0))
                ef = getattr(obj, "EndForce", App.Vector(0, 0, 0))
                sm = getattr(obj, "StartMoment", App.Vector(0, 0, 0))
                em = getattr(obj, "EndMoment", App.Vector(0, 0, 0))
                sp = getattr(obj, "StartPosition", 0.0)
                ep = getattr(obj, "EndPosition", 1.0)
                lcs = "Local" if getattr(obj, "LocalCS", True) else "Global"

                if sf == ef and sf.Length > 1e-6:
                    force_info = f"Uniform ({sf.x:.1f}, {sf.y:.1f}, {sf.z:.1f})"
                else:
                    force_info = f"Start: ({sf.x:.1f}), End: ({ef.x:.1f})"

                moment_info = f"Moments defined" if sm.Length > 1e-6 or em.Length > 1e-6 else "None"
                pos_info = f"{lcs}, Pos: {sp:.2f}-{ep:.2f}"

            # Acceleration Load
            elif load_type == "AccelerationLoad":
                beams = getattr(obj, "Beams", [])
                nodes_beams_info = ", ".join([b.Label for b in beams]) if beams else "Whole Model"
                la = getattr(obj, "LinearAcceleration", App.Vector(0, 0, 0))
                force_info = f"Linear Accel"
                moment_info = f"({la.x:.2g}, {la.y:.2g}, {la.z:.2g}) g"
                pos_info = "Gravity Vector"

            # Add row to the table
            table.add_row([
                name,
                load_type.replace("Load", ""),  # Use a shorter type name
                nodes_beams_info,
                force_info,
                moment_info,
                pos_info
            ])

        # --- 2. CONCATENATE AND PRINT OUTPUT (SINGLE CALL) ---

        header_string = f"\n--- Loads in Case: {load_id_group.Label} ---\n"
        table_string = table.get_string()
        final_output = header_string + table_string + "\n"

        App.Console.PrintMessage(final_output)
    # --- END CONTEXT MENU IMPLEMENTATION ---


class LoadGroupViewProvider:
    """View provider for the Loads group"""

    def __init__(self, vobj):
        """Initialize the view provider"""
        vobj.Proxy = self

    def getIcon(self):
        """Return the icon for this group"""
        return LOAD_GROUP_ICON_PATH

    def attach(self, vobj):
        """Setup the scene sub-graph of the view provider"""
        self.ViewObject = vobj
        self.Object = vobj.Object

    def updateData(self, obj, prop):
        """Called when a property of the attached object changes"""
        pass

    def onChanged(self, vobj, prop):
        """Called when a view provider property changes"""
        pass

    def __getstate__(self):
        """Called when saving the document"""
        return None

    def __setstate__(self, state):
        """Called when restoring the document"""
        return None

    def canDragObjects(self):
        return False

    def canDropObjects(self):
        return False

    # --- LOAD GROUP CONTEXT MENU (List Load IDs) ---
    def setupContextMenu(self, vobj, menu):
        """Adds a context menu item to list all Load IDs."""
        from PySide import QtGui

        if PrettyTable is None:
            return

        action = QtGui.QAction("List Load Cases (IDs) in Report View", menu)
        action.triggered.connect(lambda: self.onListLoadIDs(vobj.Object))
        menu.addAction(action)

    def onListLoadIDs(self, load_group):
        """Collects Load ID data and prints it to the FreeCAD report view."""

        if PrettyTable is None:
            App.Console.PrintError("Cannot list Load IDs: PrettyTable module is missing.\n")
            return

        table = PrettyTable()
        table.field_names = ["ID Name", "Type", "Description", "Load Count"]
        table.align["ID Name"] = "l"
        table.set_style(TableStyle.SINGLE_BORDER)

        for obj in load_group.Group:
            if hasattr(obj, "Type") and obj.Type == "LoadIDFeature":
                load_count = len(getattr(obj, 'Group', []))
                description = getattr(obj, "Description", "N/A")

                table.add_row([
                    obj.Label,
                    "LoadID",
                    description,
                    load_count
                ])

        header_string = "\n--- Load Cases (Load IDs) List ---\n"
        table_string = table.get_string()
        final_output = header_string + table_string + "\n"

        App.Console.PrintMessage(final_output)
    # --- END LOAD GROUP CONTEXT MENU ---


def create_load_id(name="Load"):
    """Create a new Load ID with automatic naming"""
    doc = App.ActiveDocument
    if not doc:
        raise RuntimeError("No active document")

    # Ensure unique name
    base_name = name
    while True:
        label = f"{base_name}"
        if not any(obj.Label == label for obj in doc.Objects):
            break

    # Create the LoadID object
    load_id = doc.addObject("App::DocumentObjectGroupPython", label)
    LoadID(load_id)

    # Add to main loads group
    main_group = make_loads_group()
    if main_group:
        main_group.addObject(load_id)
    if App.GuiUp:
        load_id.ViewObject.Proxy = LoadIDViewProvider(load_id.ViewObject)
    App.ActiveDocument.recompute()

    return load_id


def make_loads_group():
    """Get or create the main Loads container"""
    doc = App.ActiveDocument
    if not doc:
        App.Console.PrintError("No active document found\n")
        return None

    if hasattr(doc, "Loads"):
        loads_group = doc.Loads
    else:
        loads_group = doc.addObject("App::DocumentObjectGroupPython", "Loads")
        LoadGroup(loads_group)
        from features.AnalysisGroup import get_analysis_group
        analysis_group = get_analysis_group()
        if analysis_group and loads_group not in analysis_group.Group:
            analysis_group.addObject(loads_group)
        # group.Label = "Loads"
        if App.GuiUp:
            loads_group.ViewObject.Proxy = LoadGroupViewProvider(loads_group.ViewObject)

    return loads_group