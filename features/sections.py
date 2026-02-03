import FreeCAD as App
import FreeCADGui as Gui
import os
import random
from features.sectionLibrary import STANDARD_PROFILES
from features.section_definitions import get_section_points
from PySide import QtGui, QtCore

# Import PrettyTable
try:
    from prettytable import PrettyTable, HRuleStyle, VRuleStyle, TableStyle
except ImportError:
    App.Console.PrintError("PrettyTable not found.\n")
    PrettyTable = None
    TableStyle = None

# Get the workbench directory
WORKBENCH_DIR = os.path.dirname(os.path.dirname(__file__))
ICON_DIR = os.path.join(WORKBENCH_DIR, "icons")

# Constants
PROFILE_TYPES = ["I-Shape", "H-Shape", "L-Shape", "U-Shape", "T-Shape",
                 "Rectangle", "Round Bar", "Tubular", "HSS", "C-Shape"]
SECTION_ICON_PATH = os.path.join(ICON_DIR, "beam_section.svg")
SECTION_GROUP_ICON_PATH = os.path.join(ICON_DIR, "beam_section_group.svg")

# Predefined colors for sections
SECTION_COLORS = [
    (0.2, 0.5, 0.8),  # Blue
    (0.8, 0.2, 0.2),  # Red
    (0.2, 0.8, 0.2),  # Green
    (0.8, 0.8, 0.2),  # Yellow
    (0.8, 0.2, 0.8),  # Magenta
    (0.2, 0.8, 0.8),  # Cyan
    (0.5, 0.5, 0.8),  # Light Blue
    (0.8, 0.5, 0.5),  # Light Red
    (0.5, 0.8, 0.5),  # Light Green
    (0.8, 0.8, 0.5)  # Light Yellow
]

# Definition of required properties for each section type
# Format: "Property Name": ("Description", DefaultValue)
PROFILE_PROPERTY_MAP = {
    "I-Shape": {
        "Height": ("Total height", "100.0 mm"),
        "Width": ("Total width", "55.0 mm"),
        "WebThickness": ("Web thickness", "4.1 mm"),
        "FlangeThickness": ("Flange thickness", "5.7 mm")
    },
    "H-Shape": {
        "Height": ("Total height", "100.0 mm"),
        "Width": ("Total width", "100.0 mm"),
        "WebThickness": ("Web thickness", "6.0 mm"),
        "FlangeThickness": ("Flange thickness", "10.0 mm")
    },
    "L-Shape": {
        "Height": ("Height (Leg 2)", 50.0),
        "Width": ("Width (Leg 1)", 50.0),
        "Thickness": ("Thickness", 5.0)
    },
    "U-Shape": {
        "Height": ("Total height", 100.0),
        "Width": ("Total width", 50.0),
        "Thickness": ("Web/Flange thickness", 6.0)
    },
    "C-Shape": {
        "Height": ("Total height", 100.0),
        "Width": ("Total width", 50.0),
        "Thickness": ("Thickness", 6.0)
    },
    "T-Shape": {
        "Height": ("Total height", 100.0),
        "Width": ("Total width", 100.0),
        "WebThickness": ("Web thickness", 6.0),
        "FlangeThickness": ("Flange thickness", 10.0)
    },
    "Rectangle": {
        "Height": ("Height", 100.0),
        "Width": ("Width", 50.0)
    },
    "Round Bar": {
        "Width": ("Diameter", 20.0)
    },
    "Tubular": {
        "Width": ("Outer Diameter", 48.3),
        "Thickness": ("Wall Thickness", 3.2)
    },
    "HSS": {
        "Height": ("Height", 100.0),
        "Width": ("Width", 50.0),
        "Thickness": ("Wall Thickness", 4.0)
    }
}

# Mapping from Library parameters (Eurocode/Standard keys) to FreeCAD Properties
PARAM_MAPPING = {
    "h": "Height",
    "b": "Width",
    "d": "Width",  # Diameter -> Width
    "tw": "WebThickness",
    "tf": "FlangeThickness",
    "t": "Thickness",
    "r": None  # Radius often not exposed as editable property
}


class SectionFeature:
    def __init__(self, obj):
        obj.Proxy = self
        self.Object = obj
        # flag to prevent update before init - True if init ongoing
        self.flagInit = True
        # flag to prevent onchange when doing many changes - True if modification ongoing
        self.flagModification = False
        # --- Identification feature type ---
        obj.addProperty("App::PropertyString", "Type", "Base", "Feature Type").Type = "SectionFeature"
        # --- Standard Identification - I tube,etc.. ---
        obj.addProperty("App::PropertyEnumeration", "ProfileType", "Section", "Profile Type")
        obj.ProfileType = PROFILE_TYPES
        # --- Identification profile type - IPE IPN etcc---
        obj.addProperty("App::PropertyEnumeration", "SectionType", "Section", "Feature Type")
        obj.SectionType = ["Custom"]
        obj.SectionType = "Custom"
        # --- Identification profile - IPE 80 etcc---
        obj.addProperty("App::PropertyEnumeration", "SectionId", "Section", "Cross-section type")
        obj.SectionId = ["Custom"]
        obj.SectionId = "Custom"

        obj.addProperty("App::PropertyBool", "IsStandard", "Section", "Is standard section").IsStandard = False
        obj.addProperty("App::PropertyString", "Standard", "Section", "Standard specification").Standard = "EN"
        obj.addProperty("App::PropertyColor", "Color", "Appearance", "Section color")
        # --- Calculated Properties with Units ---
        # Area (Unit 2)
        obj.addProperty("App::PropertyQuantity", "Area", "Section Properties", "Cross-sectional Area")
        obj.Area = App.Units.Unit(2)

        # Moment of Inertia (Unit 4)
        obj.addProperty("App::PropertyQuantity", "Iyy", "Section Properties",
                        "Moment of Inertia about Y-axis (Major/Minor)")
        obj.Iyy = App.Units.Unit(4)
        obj.addProperty("App::PropertyQuantity", "Izz", "Section Properties",
                        "Moment of Inertia about Z-axis (Major/Minor)")
        obj.Izz = App.Units.Unit(4)
        obj.addProperty("App::PropertyQuantity", "Iyz", "Section Properties", "Product of Inertia")
        obj.Iyz = App.Units.Unit(4)
        obj.addProperty("App::PropertyQuantity", "J", "Section Properties", "Torsional Constant")
        obj.J = App.Units.Unit(4)

        # Centroid (Unit 1)
        obj.addProperty("App::PropertyQuantity", "Centroid_Y", "Section Properties", "Y Centroid Position")
        obj.Centroid_Y = App.Units.Unit(1)
        obj.addProperty("App::PropertyQuantity", "Centroid_Z", "Section Properties", "Z Centroid Position")
        obj.Centroid_Z = App.Units.Unit(1)

        # Section Moduli (Unit 3) - Standard Naming
        obj.addProperty("App::PropertyQuantity", "Wel_y", "Section Properties", "Elastic Modulus Y-Y")
        obj.Wel_y = App.Units.Unit(3)
        obj.addProperty("App::PropertyQuantity", "Wel_z", "Section Properties", "Elastic Modulus Z-Z")
        obj.Wel_z = App.Units.Unit(3)

        obj.addProperty("App::PropertyQuantity", "Wpl_y", "Section Properties", "Plastic Modulus Y-Y")
        obj.Wpl_y = App.Units.Unit(3)
        obj.addProperty("App::PropertyQuantity", "Wpl_z", "Section Properties", "Plastic Modulus Z-Z")
        obj.Wpl_z = App.Units.Unit(3)

        # --- Dynamic Properties Management ---
        # Container to track added properties
        if not hasattr(obj, "ManagedProperties"):
            obj.addProperty("App::PropertyStringList", "ManagedProperties", "Hidden", "Tracked dynamic properties")

        # Set default color
        obj.Color = random.choice(SECTION_COLORS)
        self.flagInit = False
        self.execute(obj)

    # modif ok
    def onChanged(self, obj, prop):
        if not hasattr(self, "flagInit") or self.flagInit:
            return
        # 2. Handle Standard Selection
        if prop == "ProfileType":
            # Set section & section type to custom to prevent errors
            obj.SectionType = "Custom"
            obj.SectionId = "Custom"
            self.update_sections(obj)
            obj.SectionType = "Custom"
            pt = obj.ProfileType
            # Get definitions for the current type
            req_props = PROFILE_PROPERTY_MAP[pt]
            # Get currently tracked properties
            current_tracked = list(obj.ManagedProperties) if hasattr(obj, "ManagedProperties") else []
            new_tracked = []
            # 1. Add required properties if missing - with default values
            for prop_name, (desc, default_val) in req_props.items():
                new_tracked.append(prop_name)
                if not hasattr(obj, prop_name):
                    obj.addProperty("App::PropertyQuantity", prop_name, "Dimensions", desc)
                    setattr(obj, prop_name, App.Units.Unit(1))
                    setattr(obj, prop_name, App.Units.Quantity(default_val))
            for prop_name in current_tracked:
                if prop_name not in new_tracked:
                    obj.removeProperty(prop_name)
            obj.ManagedProperties = new_tracked
        elif prop == "SectionType":
            obj.SectionId = "Custom"
            self.update_section_ids(obj)
        elif prop == "SectionId":
            if obj.SectionId != "Custom" and obj.SectionType != "Custom" and \
                    obj.ProfileType in STANDARD_PROFILES and \
                    obj.SectionType in STANDARD_PROFILES[obj.ProfileType].keys() and \
                    obj.SectionId in STANDARD_PROFILES[obj.ProfileType][obj.SectionType].keys():
                section_data = STANDARD_PROFILES[obj.ProfileType][obj.SectionType][obj.SectionId]
                try:
                    # Iterate through mapping to find relevant properties
                    for param_key, prop_name in PARAM_MAPPING.items():
                        if prop_name and param_key in section_data and hasattr(obj, prop_name):
                            # Set the property value (ensure unit is mm)
                            val = section_data[param_key]
                            setattr(obj, prop_name, f"{val} mm")
                    obj.IsStandard = True
                    if "Section" in obj.Label: obj.Label = str(obj.SectionId)
                    obj.IsStandard = True
                except Exception as e:
                    App.Console.PrintWarning(f"Error applying standard section: {e}\n")
            else:
                obj.IsStandard = False

        # 3. Handle Geometry Changes or Recompute Trigger
        elif prop in obj.ManagedProperties:
            pass

    def execute(self, obj):
        """Recalculate section properties"""
        try:
            if self.flagModification: return
            # 1. Extract float values from Quantity properties
            params = {}
            for prop_name in obj.ManagedProperties:
                if hasattr(obj, prop_name):
                    val = getattr(obj, prop_name)
                    # Convert Quantity to float (mm)
                    if hasattr(val, "getValueAs"):
                        params[prop_name] = val.getValueAs("mm").Value
                    else:
                        params[prop_name] = float(val)
            # 2. If this is a Standard Section, merge the full Library Dictionary
            # This ensures we pass 'A', 'Iy', 'm' etc. to the calculator
            if obj.SectionId != "Custom" and \
                    obj.ProfileType in STANDARD_PROFILES and \
                    obj.SectionType in STANDARD_PROFILES[obj.ProfileType] and \
                    obj.SectionId in STANDARD_PROFILES[obj.ProfileType][obj.SectionType]:
                standard_data = STANDARD_PROFILES[obj.ProfileType][obj.SectionType][obj.SectionId]
                # Update params with standard data (A, Iy, Wel_y, etc.)
                params.update(standard_data)
            # 3. Calculate properties
            # Note: length is passed as 1.0 just for point generation, doesn't affect 2D props
            _, _, props = get_section_points(obj.ProfileType, 1.0, params)
            # 4. Assign results back to properties with correct Units
            # Area (mm^2) -> Unit(2)
            obj.Area = App.Units.Quantity(props["area"], App.Units.Unit(2))

            # Inertia (mm^4) -> Unit(4)
            obj.Iyy = App.Units.Quantity(props["Iy"], App.Units.Unit(4))
            obj.Izz = App.Units.Quantity(props["Iz"], App.Units.Unit(4))
            obj.Iyz = App.Units.Quantity(props["Iyz"], App.Units.Unit(4))
            obj.J = App.Units.Quantity(props.get("J", 0.0), App.Units.Unit(4))
            obj.Centroid_Y = App.Units.Quantity(abs(props["centroid"][0]), App.Units.Unit(1))
            obj.Centroid_Z = App.Units.Quantity(abs(props["centroid"][1]), App.Units.Unit(1))

            obj.Wel_y = App.Units.Quantity(props.get("Wel_y", 0.0), App.Units.Unit(3))
            obj.Wel_z = App.Units.Quantity(props.get("Wel_z", 0.0), App.Units.Unit(3))
            obj.Wpl_y = App.Units.Quantity(props.get("Wpl_y", 0.0), App.Units.Unit(3))
            obj.Wpl_z = App.Units.Quantity(props.get("Wpl_z", 0.0), App.Units.Unit(3))

            # 5. Notify dependent objects
            for o in App.ActiveDocument.Objects:
                if hasattr(o, "Proxy") and hasattr(o, "Type"):
                    if hasattr(o, "Section") and o.Section == obj and o.Type == "BeamFeature":
                        # o.Proxy.execute(o)	  - test touch
                        o.Proxy.touch()

        except Exception as e:
            App.Console.PrintWarning(f"Error calculating section properties: {str(e)}\n")

    def update_sections(self, obj):
        # ok updated
        """Update the Profile type property with available sections for current type"""
        sectionType = ["Custom"]
        if obj.ProfileType == "Custom":
            pass
        elif obj.ProfileType in STANDARD_PROFILES:
            sectionType.extend(sorted(STANDARD_PROFILES[obj.ProfileType].keys()))
        else:
            # If not in standard profiles, we only have Custom
            pass

        obj.SectionType = sectionType

    def update_section_ids(self, obj):
        # ok updated
        """Update the section ID type property with available sections for current type"""
        sectionId = ["Custom"]
        if obj.SectionType == "Custom":
            pass
        elif obj.ProfileType in STANDARD_PROFILES and obj.SectionType in STANDARD_PROFILES[obj.ProfileType]:
            sectionId.extend(sorted(STANDARD_PROFILES[obj.ProfileType][obj.SectionType].keys()))
        obj.SectionId = sectionId

    def dumps(self):
        return None

    def loads(self, state):
        return None

    def onDocumentRestored(self, obj):
        """
		Restores unit signatures and proxy linkage when opening a saved file.
		Critically important for PropertyQuantity to retain units (mm^2, mm^4, etc).
		"""
        self.Object = obj
        obj.Proxy = self
        self.flagInit = True  # Prevent onChanged logic during restore
        self.flagModification = False

        if hasattr(obj, "Area"): obj.Area = App.Units.Unit(2)
        for prop in ["Iyy", "Izz", "Iyz", "J"]:
            if hasattr(obj, prop): setattr(obj, prop, App.Units.Unit(4))
        for prop in ["Wel_y", "Wel_z", "Wpl_y", "Wpl_z"]:
            if hasattr(obj, prop): setattr(obj, prop, App.Units.Unit(3))
        for prop in ["Centroid_Y", "Centroid_Z"]:
            if hasattr(obj, prop): setattr(obj, prop, App.Units.Unit(1))

        if hasattr(obj, "ManagedProperties"):
            for prop_name in obj.ManagedProperties:
                if hasattr(obj, prop_name): setattr(obj, prop_name, App.Units.Unit(1))
        self.flagInit = False


class SectionViewProvider:
    """View provider for individual sections"""

    def __init__(self, vobj):
        vobj.Proxy = self
        self.Object = vobj.Object
        self.ViewObject = vobj
        self.default = None

    def getIcon(self):
        """Return the icon for individual sections"""
        return SECTION_ICON_PATH

    def attach(self, vobj):
        """Setup the scene sub-graph of the view provider"""
        if not hasattr(self, "ViewObject"):
            self.ViewObject = vobj
        if not hasattr(self, "Object"):
            self.Object = vobj.Object

        from pivy import coin
        self.default = coin.SoGroup()
        vobj.addDisplayMode(self.default, "Default")

    def updateData(self, obj, prop):
        pass

    def onChanged(self, vobj, prop):
        pass

    def getDisplayModes(self, obj):
        return ["Default"]

    def getDefaultDisplayMode(self):
        return "Default"

    def dumps(self):
        return None

    def loads(self, state):
        return None

    def canDragObjects(self):
        return False

    def canDropObjects(self):
        return False


class SectionLibrary:
    def __init__(self, obj):
        obj.Proxy = self
        obj.addProperty("App::PropertyString", "Type", "Base", "Section library type").Type = "SectionLibrary"

    def getIcon(self):
        return SECTION_ICON_PATH

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None


class SectionLibraryViewProvider:
    """View provider for the section library/group"""

    def __init__(self, vobj):
        vobj.Proxy = self
        self.Object = vobj.Object

    def getIcon(self):
        """Return the icon for section groups"""
        return SECTION_GROUP_ICON_PATH

    def attach(self, vobj):
        self.Object = vobj.Object

    def updateData(self, obj, prop):
        pass

    def onChanged(self, vobj, prop):
        pass

    def getDisplayModes(self, obj):
        return ["Default"]

    def getDefaultDisplayMode(self):
        return "Default"

    def setDisplayMode(self, mode):
        return mode

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None

    def canDragObjects(self):
        return False

    def canDropObjects(self):
        return False

    # --- CONTEXT MENU IMPLEMENTATION ---
    def setupContextMenu(self, vobj, menu):
        """Adds a context menu item to list all Sections."""
        from PySide import QtGui

        if PrettyTable is None:
            App.Console.PrintWarning("PrettyTable not available for Section listing.\n")
            return

        action = QtGui.QAction("List Sections in Report View", menu)
        action.triggered.connect(lambda: self.onListSections(vobj.Object))
        menu.addAction(action)

    def onListSections(self, section_group):
        """Collects Section data and prints it to the FreeCAD report view in requested units."""

        if PrettyTable is None:
            App.Console.PrintError("Cannot list Sections: PrettyTable module is missing.\n")
            return

        # --- 1. SETUP AND COLLECT DATA ---

        table = PrettyTable()
        table.field_names = [
            "Name", "Type", "Area (cm^2)", "Iyy (cm^4)", "Izz (cm^4)",
            "Wel,y (cm^3)", "Wpl,y (cm^3)", "Wel,z (cm^3)", "Wpl,z (cm^3)"
        ]
        table.align["Name"] = "l"
        table.set_style(TableStyle.SINGLE_BORDER)

        # Iterate over all objects in the group
        for obj in section_group.Group:
            if hasattr(obj, "SectionType") and hasattr(obj, "Area"):
                try:
                    name = obj.Label
                    sec_type = obj.SectionType

                    # Helper to get float value from quantity or float
                    def get_val(prop, target_unit):
                        if hasattr(prop, "getValueAs"): return prop.getValueAs(target_unit).Value
                        val = prop
                        if target_unit == "cm^2": return val / 100.0
                        if target_unit == "cm^4": return val / 10000.0
                        if target_unit == "cm^3": return val / 1000.0
                        return val

                    table.add_row([
                        name, sec_type,
                        f"{get_val(obj.Area, 'cm^2'):.2f}",
                        f"{get_val(obj.Iyy, 'cm^4'):.2f}",
                        f"{get_val(obj.Izz, 'cm^4'):.2f}",
                        f"{get_val(obj.Wel_y, 'cm^3'):.2f}",
                        f"{get_val(obj.Wpl_y, 'cm^3'):.2f}",
                        f"{get_val(obj.Wel_z, 'cm^3'):.2f}",
                        f"{get_val(obj.Wpl_z, 'cm^3'):.2f}"
                    ])
                except Exception as e:
                    App.Console.PrintPrintWarning(f"Skipping section {obj.Label}: {e}\n")

        # --- 2. PRINT OUTPUT ---
        header_string = "\n--- Section Properties List ---\n"
        table_string = table.get_string()
        final_output = header_string + table_string + "\n"
        App.Console.PrintMessage(final_output)


def make_section_group():
    """Create or get the Sections library"""
    doc = App.ActiveDocument
    if not doc: return None
    if hasattr(doc, "Sections"):
        section_group = doc.Sections
    else:
        section_group = doc.addObject("App::DocumentObjectGroupPython", "Sections")
        SectionLibrary(section_group)
        section_group.Label = "Sections"
        section_group.ViewObject.Proxy = SectionLibraryViewProvider(section_group.ViewObject)
        from features.AnalysisGroup import get_analysis_group
        analysis_group = get_analysis_group()
        if analysis_group and section_group not in analysis_group.Group:
            analysis_group.addObject(section_group)
    return section_group


def create_section(profile_type, section_type, section_id):
    # This helper is often called from UI dialogs
    if section_type != "Custom":
        label = f"{section_id}"
    else:
        label = f"Custom {section_type}"
    library = make_section_group()
    section = App.ActiveDocument.addObject("App::FeaturePython", "Section")
    SectionFeature(section)
    if App.GuiUp:
        SectionViewProvider(section.ViewObject)
    section.Proxy.flagModification = True
    section.ProfileType = profile_type
    section.SectionType = section_type
    section.SectionId = section_id
    section.Standard = "EN"
    section.Label = label
    section.Proxy.flagModification = False
    library.addObject(section)
    App.ActiveDocument.recompute()
    return section