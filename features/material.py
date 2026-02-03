import FreeCAD as App
import FreeCADGui as Gui
import os
import random
from PySide import QtGui, QtCore
from prettytable.prettytable import PrettyTable, HRuleStyle, VRuleStyle, TableStyle

# Get the workbench directory
WORKBENCH_DIR = os.path.dirname(os.path.dirname(__file__))
ICON_DIR = os.path.join(WORKBENCH_DIR, "icons")

# Constants
MATERIAL_ICON_PATH = os.path.join(ICON_DIR, "beam_material.svg")
MATERIAL_GROUP_ICON_PATH = os.path.join(ICON_DIR, "beam_material_group.svg")

# Standard steel material database (values in MPa, kg/m³)
STANDARD_STEELS = {
    "S235": {
        "YoungsModulus": 210000,
        "PoissonsRatio": 0.3,
        "YieldStrength": 235,
        "TensileStrength": 360,
        "Density": 7850,
        "ThermalExpansion": 1.2e-5
    },
    "S275": {
        "YoungsModulus": 210000,
        "PoissonsRatio": 0.3,
        "YieldStrength": 275,
        "TensileStrength": 430,
        "Density": 7850,
        "ThermalExpansion": 1.2e-5
    },
    "S355": {
        "YoungsModulus": 210000,
        "PoissonsRatio": 0.3,
        "YieldStrength": 355,
        "TensileStrength": 510,
        "Density": 7850,
        "ThermalExpansion": 1.2e-5
    },
    "S420": {
        "YoungsModulus": 210000,
        "PoissonsRatio": 0.3,
        "YieldStrength": 420,
        "TensileStrength": 540,
        "Density": 7850,
        "ThermalExpansion": 1.2e-5
    },
    "S460": {
        "YoungsModulus": 210000,
        "PoissonsRatio": 0.3,
        "YieldStrength": 460,
        "TensileStrength": 550,
        "Density": 7850,
        "ThermalExpansion": 1.2e-5
    },
    "A36": {
        "YoungsModulus": 200000,
        "PoissonsRatio": 0.26,
        "YieldStrength": 250,
        "TensileStrength": 400,
        "Density": 7850,
        "ThermalExpansion": 1.2e-5
    },
    "A992": {
        "YoungsModulus": 200000,
        "PoissonsRatio": 0.3,
        "YieldStrength": 345,
        "TensileStrength": 450,
        "Density": 7850,
        "ThermalExpansion": 1.2e-5
    }
}

# Material types for future expansion
MATERIAL_TYPES = ["Steel", "Aluminum", "Concrete", "Timber", "Custom"]
STEEL_GRADES = list(STANDARD_STEELS.keys())


class MaterialFeature:
    def __init__(self, obj):
        obj.Proxy = self
        self.flagInit = True

        # Basic identification
        obj.addProperty("App::PropertyString", "Type", "Base", "Material Type").Type = "MaterialFeature"
        obj.addProperty("App::PropertyEnumeration", "MaterialType", "Material", "Material category")
        obj.MaterialType = MATERIAL_TYPES
        obj.MaterialType = "Steel"  # Default to steel

        obj.addProperty("App::PropertyEnumeration", "SteelGrade", "Material", "Standard steel grade")
        obj.SteelGrade = STEEL_GRADES
        obj.SteelGrade = "S355"  # Default grade

        obj.addProperty("App::PropertyString", "CustomName", "Material", "Custom material name").CustomName = ""

        # Mechanical properties
        # Format for App.Units.Unit(Length, Mass, Time, Current, Temp, Amount, Intensity, Angle)

        # Young's Modulus: Pressure (MPa) -> Mass / (Length * Time^2) -> (-1, 1, -2)
        obj.addProperty("App::PropertyQuantity", "YoungsModulus", "Mechanical", "Young's Modulus")
        obj.YoungsModulus = App.Units.Unit(-1, 1, -2)
        obj.YoungsModulus = "210000 MPa"


        # Poisson's Ratio: Dimensionless -> (0)
        obj.addProperty("App::PropertyQuantity", "PoissonsRatio", "Mechanical", "Poisson's Ratio")
        obj.PoissonsRatio = App.Units.Unit(0)
        obj.PoissonsRatio = "0.3"

        # Shear Modulus: Pressure (MPa) -> (-1, 1, -2)
        obj.addProperty("App::PropertyQuantity", "ShearModulus", "Mechanical", "Shear Modulus")
        obj.ShearModulus = App.Units.Unit(-1, 1, -2)
        obj.ShearModulus = "81000 MPa"

        # Yield Strength: Pressure (MPa) -> (-1, 1, -2)
        obj.addProperty("App::PropertyQuantity", "YieldStrength", "Mechanical", "Yield Strength")
        obj.YieldStrength = App.Units.Unit(-1, 1, -2)
        obj.YieldStrength = "355 MPa"

        # Tensile Strength: Pressure (MPa) -> (-1, 1, -2)
        obj.addProperty("App::PropertyQuantity", "TensileStrength", "Mechanical", "Tensile Strength")
        obj.TensileStrength = App.Units.Unit(-1, 1, -2)
        obj.TensileStrength = "510 MPa"

        # Physical properties

        # Density: Mass / Length^3 -> (-3, 1)
        obj.addProperty("App::PropertyQuantity", "Density", "Physical", "Density")
        obj.Density = App.Units.Unit(-3, 1)
        obj.Density = "7850 kg/m^3"

        # Thermal Expansion: 1/Temperature -> (0,0,0,0,-1)
        obj.addProperty("App::PropertyQuantity", "ThermalExpansion", "Physical", "Thermal expansion coefficient")
        obj.ThermalExpansion = App.Units.Unit(0, 0, 0, 0, -1)
        obj.ThermalExpansion = "1.2e-5 K^-1"

        # Thermal Conductivity: Mass*Length / (Time^3 * Temp) -> (1, 1, -3, 0, -1)
        obj.addProperty("App::PropertyQuantity", "ThermalConductivity", "Physical", "Thermal conductivity")
        obj.ThermalConductivity = App.Units.Unit(1, 1, -3, 0, -1)
        obj.ThermalConductivity = "50 W/m/K"

        # Calculation properties (read-only)

        # Specific Weight: Force / Volume -> Mass / (Length^2 * Time^2) -> (-2, 1, -2)
        obj.addProperty("App::PropertyQuantity", "SpecificWeight", "Calculated", "Specific weight")
        obj.SpecificWeight = App.Units.Unit(-2, 1, -2)
        obj.SpecificWeight = "77000 N/m^3"

        # Appearance
        obj.addProperty("App::PropertyColor", "Color", "Appearance", "Material color")

        # Set random color for new material
        obj.Color = self.get_random_material_color()

        self.flagInit = False
        self.execute(obj)

    def get_random_material_color(self):
        """Get a random color appropriate for steel materials"""
        steel_colors = [
            (0.5, 0.5, 0.5),  # Gray
            (0.4, 0.4, 0.5),  # Blue-gray
            (0.5, 0.4, 0.3),  # Brown-gray
            (0.6, 0.6, 0.7),  # Light gray
            (0.3, 0.3, 0.4)  # Dark gray
        ]
        return random.choice(steel_colors)

    def onChanged(self, obj, prop):
        if not hasattr(self, "flagInit") or self.flagInit:
            return

        if prop == "SteelGrade" and obj.MaterialType == "Steel":
            if obj.SteelGrade in STANDARD_STEELS:
                steel_data = STANDARD_STEELS[obj.SteelGrade]

                # Use standard MPa for internal storage
                obj.YoungsModulus = f"{steel_data['YoungsModulus']} MPa"
                obj.PoissonsRatio = steel_data['PoissonsRatio']
                obj.YieldStrength = f"{steel_data['YieldStrength']} MPa"
                obj.TensileStrength = f"{steel_data['TensileStrength']} MPa"
                obj.Density = f"{steel_data['Density']} kg/m^3"
                obj.ThermalExpansion = f"{steel_data['ThermalExpansion']} K^-1"

                # Consistent Calculation for G
                val_E = get_val(obj, "YoungsModulus", "MPa")
                val_nu = obj.PoissonsRatio.Value if hasattr(obj.PoissonsRatio, "Value") else obj.PoissonsRatio
                # Calculate G in MPa
                g_val = val_E / (2 * (1 + val_nu))
                obj.ShearModulus = f"{g_val} MPa"

                if not obj.CustomName:
                    obj.Label = f"Steel {obj.SteelGrade}"

        elif prop in ["YoungsModulus", "PoissonsRatio"]:
            # Recalculate shear modulus using MPa consistently
            val_E = get_val(obj, "YoungsModulus", "MPa")
            val_nu = obj.PoissonsRatio.Value if hasattr(obj.PoissonsRatio, "Value") else obj.PoissonsRatio
            g_val = val_E / (2 * (1 + val_nu))
            obj.ShearModulus = f"{g_val} MPa"
            # Update label
            if not obj.CustomName:
                obj.Label = f"Steel {obj.SteelGrade}"

        elif prop in ["YoungsModulus", "PoissonsRatio"]:
            # Recalculate shear modulus when E or ν changes
            if hasattr(obj.YoungsModulus, "Value"):

                val_E = get_val(obj,"YoungsModulus","MPa")
                val_nu = obj.PoissonsRatio
                print(val_E, val_nu)
                obj.ShearModulus = val_E / (2 * (1 + val_nu))

        elif prop == "Density":
            # Calculate specific weight (γ = ρ * g) where g ≈ 9.81 m/s²
            gravity = App.Units.Quantity("9.81 m/s^2")
            obj.SpecificWeight = obj.Density * gravity

        elif prop == "MaterialType":
            if obj.MaterialType != "Steel":
                # Reset steel grade if material type changes
                obj.SteelGrade = STEEL_GRADES[0]

        # Update dependent objects (beams using this material)
        self.update_dependent_objects(obj)

    def update_dependent_objects(self, obj):
        """Update beams that use this material"""
        for doc_obj in App.ActiveDocument.Objects:
            if hasattr(doc_obj, "Proxy") and hasattr(doc_obj, "Type"):
                if hasattr(doc_obj, "Material") and doc_obj.Material == obj:
                    if doc_obj.Type == "BeamFeature":
                        # Trigger beam update
                        doc_obj.Proxy.execute(doc_obj)
                    elif doc_obj.Type == "ResultBeam":
                        # Trigger result beam update
                        doc_obj.Proxy.execute(doc_obj)

    def execute(self, obj):
        gravity = App.Units.Quantity("9.81 m/s^2")
        obj.SpecificWeight = obj.Density * gravity

        # Ensure shear modulus is calculated in MPa if it's missing or zero
        if obj.ShearModulus.Value == 0:
            val_E = get_val(obj, "YoungsModulus", "MPa")
            val_nu = obj.PoissonsRatio.Value if hasattr(obj.PoissonsRatio, "Value") else obj.PoissonsRatio
            g_val = val_E / (2 * (1 + val_nu))
            obj.ShearModulus = f"{g_val} MPa"

    def dumps(self):
        return None

    def loads(self, state):
        return None

    def onDocumentRestored(self, obj):
        """
        Restores the unit signatures when opening a saved file.
        This is critical for App::PropertyQuantity to retain unit behaviors (like MPa).
        """
        self.Object = obj
        obj.Proxy = self
        self.flagInit = True  # Prevent onChanged logic during restore
        # Re-apply Unit Signatures for  Properties
        if hasattr(obj, "YoungsModulus"):
            obj.YoungsModulus = App.Units.Unit(-1, 1, -2)
        if hasattr(obj, "ShearModulus"):
            obj.ShearModulus = App.Units.Unit(-1, 1, -2)
        if hasattr(obj, "YieldStrength"):
            obj.YieldStrength = App.Units.Unit(-1, 1, -2)
        if hasattr(obj, "TensileStrength"):
            obj.TensileStrength = App.Units.Unit(-1, 1, -2)
        if hasattr(obj, "Density"):
            obj.Density = App.Units.Unit(-3, 1)
        if hasattr(obj, "ThermalExpansion"):
            obj.ThermalExpansion = App.Units.Unit(0, 0, 0, 0, -1)
        if hasattr(obj, "ThermalConductivity"):
            obj.ThermalConductivity = App.Units.Unit(1, 1, -3, 0, -1)
        if hasattr(obj, "SpecificWeight"):
            obj.SpecificWeight = App.Units.Unit(-2, 1, -2)
        if hasattr(obj, "PoissonsRatio"):
            obj.PoissonsRatio = App.Units.Unit(0)

        self.flagInit = False

class MaterialViewProvider:
    """View provider for individual materials"""

    def __init__(self, vobj):
        vobj.Proxy = self
        self.Object = vobj.Object
        self.ViewObject = vobj

    def getIcon(self):
        """Return the icon for individual materials"""
        return MATERIAL_ICON_PATH

    def attach(self, vobj):
        """Setup the scene sub-graph of the view provider"""
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


class MaterialLibrary:
    def __init__(self, obj):
        obj.Proxy = self
        obj.addProperty("App::PropertyString", "Type", "Base", "Material library type").Type = "MaterialLibrary"

    def getIcon(self):
        return MATERIAL_ICON_PATH

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None


class MaterialLibraryViewProvider:
    """View provider for the material library/group"""

    def __init__(self, vobj):
        vobj.Proxy = self
        self.Object = vobj.Object

    def getIcon(self):
        """Return the icon for material groups"""
        return MATERIAL_GROUP_ICON_PATH

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
        """Adds a context menu item to list all materials."""
        from PySide import QtGui

        if PrettyTable is None:
            App.Console.PrintWarning("PrettyTable not available for material listing.\n")
            return

        action = QtGui.QAction("List Materials in Report View", menu)
        action.triggered.connect(lambda: self.onListMaterials(vobj.Object))
        menu.addAction(action)

    def onListMaterials(self, material_group):
        """Collects material data and prints it to the FreeCAD report view."""

        if PrettyTable is None:
            App.Console.PrintError("Cannot list Materials: PrettyTable module is missing.\n")
            return

        table = PrettyTable()
        table.field_names = [
            "Name", "Type", "Grade", "E (GPa)", "fy (MPa)", "fu (MPa)", "Density (kg/m³)"
        ]
        table.align["Name"] = "l"
        table.set_style(TableStyle.SINGLE_BORDER)

        # Iterate over all objects in the group
        for obj in material_group.Group:
            if hasattr(obj, "Type") and obj.Type == "MaterialFeature":
                # Get basic ID properties
                name = obj.Label
                mat_type = getattr(obj, "MaterialType", "N/A")
                grade = getattr(obj, "SteelGrade", "")

                # Helper to safely get value in unit
                E_MPa = get_val(obj,"YoungsModulus", "MPa")
                fy_MPa = get_val(obj,"YieldStrength", "MPa")
                fu_MPa = get_val(obj,"TensileStrength", "MPa")
                density_kg = get_val(obj,"Density", "kg/m^3")

                # Convert Young's Modulus to GPa (MPa / 1000)
                E_gpa = E_MPa / 1000.0

                # Add row to the table
                table.add_row([
                    name,
                    mat_type,
                    grade if mat_type == "Steel" else "-",
                    f"{E_gpa:.1f}",
                    f"{fy_MPa:.0f}",
                    f"{fu_MPa:.0f}",
                    f"{density_kg:.0f}"
                ])

        header_string = "\n--- Material Properties List ---\n"
        table_string = table.get_string()
        final_output = header_string + table_string + "\n"

        App.Console.PrintMessage(final_output)


def get_val(obj,prop_name, unit):
    prop = getattr(obj, prop_name, None)
    if hasattr(prop, "getValueAs"):
        return prop.getValueAs(unit).Value
    # Fallback if prop is not a quantity (e.g. old object)
    return float(prop) if prop is not None else 0.0

def make_material_group():
    """Create or get the Materials library with proper icon paths"""
    doc = App.ActiveDocument
    if not doc:
        App.Console.PrintError("No active document found\n")
        return None

    if hasattr(doc, "Materials"):
        material_group = doc.Materials
    else:
        material_group = doc.addObject("App::DocumentObjectGroupPython", "Materials")
        MaterialLibrary(material_group)
        material_group.Label = "Materials"

        material_group.ViewObject.Proxy = MaterialLibraryViewProvider(material_group.ViewObject)

        # Add to AnalysisGroup if it exists
        from features.AnalysisGroup import get_analysis_group
        analysis_group = get_analysis_group()
        if analysis_group and material_group not in analysis_group.Group:
            analysis_group.addObject(material_group)

    return material_group


def create_steel_material(steel_grade="S355", custom_name=""):
    """Create a steel material with standard properties"""
    doc = App.ActiveDocument
    if not doc:
        return None

    library = make_material_group()

    material = doc.addObject("App::FeaturePython", "Material")
    MaterialFeature(material)

    if App.GuiUp:
        MaterialViewProvider(material.ViewObject)

    # Set properties
    material.MaterialType = "Steel"
    material.SteelGrade = steel_grade

    if custom_name:
        material.CustomName = custom_name
        material.Label = custom_name
    else:
        material.Label = f"Steel {steel_grade}"

    library.addObject(material)
    App.ActiveDocument.recompute()
    return material


def create_custom_material(name, youngs_modulus, poissons_ratio, density,
                           yield_strength=0, tensile_strength=0):
    """
    Create a custom material with specified properties.
    Note: Input values are assumed to be in standard engineering units:
    - Youngs Modulus: MPa
    - Poissons Ratio: Dimensionless
    - Density: kg/m³
    - Yield/Tensile: MPa
    """
    doc = App.ActiveDocument
    if not doc:
        return None

    library = make_material_group()

    material = doc.addObject("App::FeaturePython", "Material")
    MaterialFeature(material)

    if App.GuiUp:
        MaterialViewProvider(material.ViewObject)

    # Set as custom material
    material.MaterialType = "Custom"
    material.CustomName = name

    # Assign properties using unit strings to ensure Quantity parses correctly
    material.YoungsModulus = f"{youngs_modulus} MPa"
    material.PoissonsRatio = f"{poissons_ratio}"
    material.Density = f"{density} kg/m^3"
    material.YieldStrength = f"{yield_strength} MPa"
    material.TensileStrength = f"{tensile_strength} MPa"

    material.Label = name

    library.addObject(material)
    return material