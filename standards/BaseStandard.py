import FreeCAD as App


class BaseStandard:
    """
    Abstract Base Class for all Structural Design Codes.
    To create a custom check, inherit from this and implement the methods.
    """

    name = "Base Standard"

    def __init__(self, beam_obj, section_props, mat_props, forces):
        """
        Initialize with standard data.

        Args:
            beam_obj: The FreeCAD beam object (for geometry/length access)
            section_props: Dict {A, Iy, Iz, Wel_y, ...} (SI Units: m, m^2, m^4)
            mat_props: Dict {fy, E, G} (SI Units: Pa)
            forces: List of Dicts [{'x':0.0, 'axial':-100, ...}, ...]
        """
        self.beam = beam_obj
        self.sec = section_props
        self.mat = mat_props
        self.forces = forces
        self.parameters = {}  # Dictionary to store user-set factors (Gamma, Phi, etc)

    def set_parameters(self, params):
        """Receive parameters from the FreeCAD Feature"""
        self.parameters = params

    @classmethod
    def get_parameter_definitions(cls):
        """
        Define what properties the FreeCAD feature should create.
        Returns dict: {'PropertyName': (Type, DefaultValue, Tooltip)}
        """
        return {}

    def run_check(self):
        """
        MAIN CALCULATION METHOD.
        Must return dictionary:
        {
            'values': [float],     # List of UC values matching force points
            'max_uc': float,       # Maximum UC
            'detailed_log': str    # Text report
        }
        """
        return {
            'values': [0.0] * len(self.forces),
            'max_uc': 0.0,
            'detailed_log': "Base Standard - No calculation implemented."
        }