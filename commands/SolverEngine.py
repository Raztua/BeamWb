import FreeCAD as App
from abc import ABC, abstractmethod

def find_object_by_name_or_label(obj_name, obj_type=None):
    """Find object by name or label with early termination"""
    if not App.ActiveDocument:
        return None
    obj = App.ActiveDocument.getObject(obj_name)
    if obj:
        return obj

    # Search by label with early termination
    for doc_obj in App.ActiveDocument.Objects:
        if obj_type and hasattr(doc_obj, "Type") and getattr(doc_obj, "Type", "") != obj_type:
            continue
        if doc_obj.Label == obj_name:
            return doc_obj
    return None


class FEMResult:
    """
    Standard container for solver results.
    Stores results for ALL load cases to decouple the Feature from the Solver Engine.
    """

    def __init__(self, solver_name="Unknown"):
        self.solver_name = solver_name
        self.load_cases = {}

    def get_max_displacement(self, load_case_name):
        """Helper to get max displacement for visualization scaling."""
        if load_case_name not in self.load_cases:
            return App.Units.Quantity(1.0, "mm")

        nodes = self.load_cases[load_case_name].get('nodes', {})
        max_disp_mag = 0.0

        # We need a reference quantity to return if results are empty
        # Defaulting to 1.0 mm for safe scaling
        max_q = App.Units.Quantity(0.0, "mm")

        for d in nodes.values():
            # Extract numerical values from the Quantity objects stored in nodes
            dx = d.get('DX', 0).Value if hasattr(d.get('DX', 0), 'Value') else float(d.get('DX', 0))
            dy = d.get('DY', 0).Value if hasattr(d.get('DY', 0), 'Value') else float(d.get('DY', 0))
            dz = d.get('DZ', 0).Value if hasattr(d.get('DZ', 0), 'Value') else float(d.get('DZ', 0))

            mag = (dx ** 2 + dy ** 2 + dz ** 2) ** 0.5
            if mag > max_disp_mag:
                max_disp_mag = mag
                # Capture the unit from one of the components (all are 'm' or 'mm')
                unit = d.get('DX', App.Units.Quantity(0, "mm")).UserString.split(' ')[-1]
                max_q = App.Units.Quantity(max_disp_mag, unit)

        return max_q if max_disp_mag > 0 else App.Units.Quantity(1.0, "mm")

    def get_max_diagram_value(self, load_case_name, result_key):
        """Helper to get max internal force Quantity for scaling with unit matching."""
        # Define default units based on key to prevent Unit Mismatch errors
        default_units = {
            'axial': 'N', 'shear_y': 'N', 'shear_z': 'N',
            'moment_y': 'N*m', 'moment_z': 'N*m', 'moment_x': 'N*m',
            'deflection_y': 'm', 'deflection_z': 'm','unity_check': ''
        }
        unit = default_units.get(result_key, "")
        if load_case_name not in self.load_cases:
            return App.Units.Quantity(0.0, unit)  # Returns 0.0 with correct unit

        members = self.load_cases[load_case_name].get('members', {})
        max_q = App.Units.Quantity(0.0, unit)
        for m in members.values():
            if result_key in m:
                # Direct access to Quantity objects stored in 'min' and 'max'
                q_min = m[result_key]['min']
                q_max = m[result_key]['max']

                # Compare absolute magnitudes using the .Value property
                if abs(q_min.Value) > abs(max_q.Value): max_q = -q_min
                if abs(q_max.Value) > abs(max_q.Value): max_q = q_max

        # Ensure we return a non-zero Quantity for scaling if max is 0
        if abs(max_q.Value) < 1e-12:
            return App.Units.Quantity(1.0, unit)
        return max_q

    def dumps(self):
        return None

    def loads(self, state):
        return None


class BaseSolverEngine(ABC):
    """Abstract base class for FEM solver engines."""

    def __init__(self, document):
        self.doc = document

    @abstractmethod
    def build_model(self):
        pass

    @abstractmethod
    def run_analysis(self, analysis_type="Linear Static"):
        pass

    @abstractmethod
    def extract_results(self, analysis_type="Linear Static") -> FEMResult:
        """Must return a populated FEMResult object"""
        return FEMResult()

    def analyze(self, analysis_type="Linear Static") -> FEMResult:
        self.build_model()
        self.run_analysis(analysis_type)
        return self.extract_results(analysis_type)