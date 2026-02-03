import FreeCAD as App
from features.SolverEngine import BaseSolverEngine, FEMResult
from Pynite.FEModel3D import FEModel3D
import numpy as np
from FreeCAD import Units

N_POINTS = 5  # number of sampling points  - To be added to solver option later

# --- LOCAL IMPORT OF PRETTYTABLE (Re-imported here for the solver) ---
try:
    # Assuming 'prettytable.py' is a local module
    from prettytable.prettytable import PrettyTable, HRuleStyle, VRuleStyle, TableStyle
except ImportError:
    App.Console.PrintError("PrettyTable not found in PyNiteSolver. Solver Check Model will be limited.\n")
    PrettyTable = None
    TableStyle = None
# --------------------------------------------------------

# Type mappings
MEMBER_RESULT_KEYS = {
    "Axial": "axial",
    "Shear Y": "shear_y",
    "Shear Z": "shear_z",
    "Moment Y": "moment_y",
    "Moment Z": "moment_z",
    "Torsion": "moment_x",
    "Deflection Y": "deflection_y",
    "Deflection Z": "deflection_z",
    "Unity Check": "unity_check"
}

# print pynite model
PRINT_MODEL = True


class PyNiteSolverEngine(BaseSolverEngine):
    """Concrete implementation for the PyNite FEA solver."""

    def __init__(self, document):
        super().__init__(document)
        self.pynite_model = None

    def build_model(self):
        """Build the PyNite model by converting FreeCAD objects to PyNite entities."""
        App.Console.PrintMessage("Building PyNite Model...\n")

        self.pynite_model = FEModel3D()  # Reset model
        self._add_nodes()
        self._add_sections()
        self._add_beams()
        self._add_loads()
        self._create_dummy_combinations()

    def check_model(self):
        """
        Shows a detailed report of the PyNite model components (Nodes, BCs, Sections, Materials,
        Beams/Members, Loads, Load Combinations, and Results) using PrettyTable.
        """
        if PrettyTable is None:
            App.Console.PrintError("\nCannot check model: PrettyTable module is missing.\n")
            return

        App.Console.PrintMessage("\n" + "b" * 80)
        App.Console.PrintMessage("\n" + "=" * 80)
        App.Console.PrintMessage(" PyNite Model Verification Report ")
        App.Console.PrintMessage("=" * 80 + "\n")

        self._print_nodes_and_bcs()
        self._print_materials_and_sections()
        self._print_beams()
        self._print_loads_and_combos()
        self._print_results_summary()

        App.Console.PrintMessage("\n","=" * 80)
        App.Console.PrintMessage(" End of PyNite Model Verification Report ")
        App.Console.PrintMessage("=" * 80 + "\n")

    def _print_nodes_and_bcs(self):
        """Prints summaries for Nodes and Boundary Conditions."""
        # --- NODES and BCs ---
        header = "\n--- 1. Nodes and Boundary Conditions ---\n"
        node_table = PrettyTable()
        node_table.field_names = ["ID", "X (m)", "Y (m)", "Z (m)", "BCs (Dx, Dy, Dz, Rx, Ry, Rz)"]
        node_table.align = "r"
        node_table.align["ID"] = "l"

        for node_name, node in self.pynite_model.nodes.items():
            # Format coordinates (PyNite stores in meters)
            x_str = f"{node.X:.4f}"
            y_str = f"{node.Y:.4f}"
            z_str = f"{node.Z:.4f}"
            # Safely access BCs, defaulting to 0 or False if the attribute doesn't exist.
            # PyNite adds these attributes only when support is defined.
            bc_dx = getattr(node, 'support_DX', 0)
            bc_dy = getattr(node, 'support_DY', 0)
            bc_dz = getattr(node, 'support_DZ', 0)
            bc_rx = getattr(node, 'support_RX', 0)
            bc_ry = getattr(node, 'support_RY', 0)
            bc_rz = getattr(node, 'support_RZ', 0)

            # Format BCs
            bc_str = f"({bc_dx}, {bc_dy}, {bc_dz}, {bc_rx}, {bc_ry}, {bc_rz})"

            node_table.add_row([node_name, x_str, y_str, z_str, bc_str])

        if len(self.pynite_model.nodes) > 0:
            App.Console.PrintMessage(header + node_table.get_string())
        else:
            App.Console.PrintMessage("No nodes found in PyNite model.\n")

    def _print_materials_and_sections(self):
        """Prints summaries for Materials and Section Properties."""
        # --- MATERIALS ---
        header = "\n--- 2. Material Properties ---\n"
        material_table = PrettyTable()
        material_table.field_names = ["ID", "E (MPa)", "G (MPa)", "Nu (v)", "Rho (kg/m^3)"]
        material_table.align = "r"
        material_table.align["ID"] = "l"

        for mat_name, mat in self.pynite_model.materials.items():
            print(mat.nu)
            material_table.add_row([
                mat_name,
                f"{mat.E/1e6:e}",
                f"{mat.G/1e6:e}",
                f"{mat.nu}",
                f"{mat.rho}"
            ])

        if len(self.pynite_model.materials) > 0:
            App.Console.PrintMessage(header + material_table.get_string())
        else:
            App.Console.PrintMessage("No materials found in PyNite model.\n")

        # --- SECTIONS ---
        header ="\n--- 3. Section Properties ---\n"
        section_table = PrettyTable()
        section_table.field_names = ["ID", "A (m^2)", "Iyy (m^4)", "Izz (m^4)", "J (m^4)"]
        section_table.align = "r"
        section_table.align["ID"] = "l"

        for sec_name, sec in self.pynite_model.sections.items():
            section_table.add_row([
                sec_name,
                f"{sec.A:e}",
                f"{sec.Iy:e}",
                f"{sec.Iz:e}",
                f"{sec.J:e}"
            ])

        if len(self.pynite_model.sections) > 0:
            App.Console.PrintMessage(header + section_table.get_string())
        else:
            App.Console.PrintMessage(header + "No sections found in PyNite model.\n")

    def _print_beams(self):
        """Prints a summary of all 1D members/beams including their Transformation Matrices."""
        header = "\n--- 4. Beams (Members) Summary ---\n"
        member_table = PrettyTable()
        member_table.field_names = ["ID", "Node I", "Node J", "Material", "Section", "Rotation (deg)", "Releases"]
        member_table.align = "l"

        for mem_name, mem in self.pynite_model.members.items():
            member_table.add_row([
                mem_name,
                mem.i_node.name,
                mem.j_node.name,
                mem.material.name,
                mem.section.name,
                f"{mem.rotation:.2f}",
                mem.Releases
            ])

        App.Console.PrintMessage(header + member_table.get_string() + "\n")

    def _print_loads_and_combos(self):
        """Prints summaries for Loads and Load Combinations."""
        # --- 5. LOADS (CASES) ---
        App.Console.PrintMessage("\n--- 5. Load Cases and Applied Loads ---\n")

        # Access load_cases as a list of strings
        load_case_names = getattr(self.pynite_model, 'load_cases', [])

        if not load_case_names:
            App.Console.PrintMessage("\nNo load cases found in PyNite model.\n")
            return

        for case_name in load_case_names:
            App.Console.PrintMessage(f"\n>> Load Case: {case_name}")

            # --- Nodal Loads Table ---
            node_load_table = PrettyTable()
            node_load_table.field_names = ["Node ID", "FX (N)", "FY (N)", "FZ (N)", "MX (Nm)", "MY (Nm)", "MZ (Nm)"]
            node_load_table.align = "r"
            node_load_table.align["Node ID"] = "l"

            has_node_loads = False
            for node_name, node in self.pynite_model.nodes.items():
                # node_loads_list is a list of tuples: [('Dir', Val, 'Case'), ...]
                node_loads_list = getattr(node, 'NodeLoads', [])

                case_loads = {"FX": 0.0, "FY": 0.0, "FZ": 0.0, "MX": 0.0, "MY": 0.0, "MZ": 0.0}
                found_for_node = False

                for ld in node_loads_list:
                    # Check if the tuple has the expected 3 elements and matches the case
                    if isinstance(ld, tuple) and len(ld) >= 3:
                        ld_dir = ld[0]
                        ld_val = ld[1]
                        ld_case = ld[2]

                        if ld_case == case_name:
                            if ld_dir in case_loads:
                                case_loads[ld_dir] = float(ld_val)
                                found_for_node = True

                if found_for_node:
                    node_load_table.add_row([
                        node_name,
                        f"{case_loads['FX']:.2f}", f"{case_loads['FY']:.2f}", f"{case_loads['FZ']:.2f}",
                        f"{case_loads['MX']:.2f}", f"{case_loads['MY']:.2f}", f"{case_loads['MZ']:.2f}"
                    ])
                    has_node_loads = True

            if has_node_loads:
                App.Console.PrintMessage("\nNodal Loads:\n" + node_load_table.get_string())
            else:
                App.Console.PrintMessage("\nNodal Loads: None")

            # --- Member Loads Table ---
            mem_load_table = PrettyTable()
            mem_load_table.field_names = ["Member ID", "Type", "Dir", "Start Val", "End Val", "Start (m)", "End (m)"]
            mem_load_table.align = "r"
            mem_load_table.align["Member ID"] = "l"

            has_mem_loads = False
            for mem_name, mem in self.pynite_model.members.items():
                # Distributed Loads
                # Check if these are objects or tuples based on your nodal load findings
                for ld in getattr(mem, 'dist_loads', []):
                    # Trying object access first, then tuple fallback
                    ld_case = getattr(ld, 'case', ld[5] if isinstance(ld, tuple) and len(ld) > 5 else '')
                    if ld_case == case_name:
                        # Assuming objects for members, update indices if logs show tuples here too
                        mem_load_table.add_row([mem_name, "Dist", ld.direction,
                                                f"{ld.w1:.2f}", f"{ld.w2:.2f}",
                                                f"{ld.x1:.2f}", f"{ld.x2:.2f}"])
                        has_mem_loads = True

                # Point Loads
                for ld in getattr(mem, 'pt_loads', []):
                    ld_case = getattr(ld, 'case', ld[3] if isinstance(ld, tuple) and len(ld) > 3 else '')
                    if ld_case == case_name:
                        mem_load_table.add_row([mem_name, "Point", ld.direction,
                                                f"{ld.P:.2f}", "-",
                                                f"{ld.x:.2f}", "-"])
                        has_mem_loads = True

            if has_mem_loads:
                App.Console.PrintMessage("\nMember Loads:\n" + mem_load_table.get_string())
            else:
                App.Console.PrintMessage("\nMember Loads: None")

        # --- 6. LOAD COMBINATIONS ---
        App.Console.PrintMessage("\n--- 6. Load Combinations ---\n")
        pynite_combos = getattr(self.pynite_model, 'load_combos', {})
        if pynite_combos:
            combo_table = PrettyTable()
            combo_table.field_names = ["Combo ID", "Definition"]
            combo_table.align = "l"
            for combo_name, combo_obj in pynite_combos.items():
                factors_dict = getattr(combo_obj, 'factors', {})
                definition = " + ".join([f"{f}*{c}" for c, f in factors_dict.items()])
                combo_table.add_row([combo_name, definition])
            App.Console.PrintMessage("\n" + combo_table.get_string())

    def _print_results_summary(self):
        """Prints a summary of key results (Max Displacement, Max Reaction Force)."""

        text = "\n--- 7. Analysis Results Summary ---\n"
        results_table = PrettyTable()
        results_table.field_names = ["Load Case/Combo", "Max Disp. (m)", "Max Rxn F (N)", "Max Rxn M (N·m)"]
        results_table.align = "r"
        results_table.align["Load Case/Combo"] = "l"

        pynite_combos = getattr(self.pynite_model, 'load_combos', {})
        pynite_cases = getattr(self.pynite_model, 'load_cases', {})
        combo_names = list(pynite_combos.keys()) if isinstance(pynite_combos, dict) else []
        case_names = list(pynite_cases.keys()) if isinstance(pynite_cases, dict) else []

        all_load_names = list(set(combo_names + case_names))
        #all_load_names = list(self.pynite_model.load_cases)

        for load_name in all_load_names:
            max_disp = 0.0
            max_rxn_f = 0.0
            max_rxn_m = 0.0

            for node in self.pynite_model.nodes.values():
                # Retrieve raw PyNite results and ensure they are floats before numpy operations
                dx = float(node.DX.get(load_name, 0))
                dy = float(node.DY.get(load_name, 0))
                dz = float(node.DZ.get(load_name, 0))

                rxn_fx = float(node.RxnFX.get(load_name, 0))
                rxn_fy = float(node.RxnFY.get(load_name, 0))
                rxn_fz = float(node.RxnFZ.get(load_name, 0))

                rxn_mx = float(node.RxnMX.get(load_name, 0))
                rxn_my = float(node.RxnMY.get(load_name, 0))
                rxn_mz = float(node.RxnMZ.get(load_name, 0))

                # Displacement magnitude (all are already in PyNite's SI unit: m)
                # NOTE: Explicit float casting prevents Base.Quantity issue with numpy
                disp_mag = np.sqrt(dx ** 2 + dy ** 2 + dz ** 2)
                max_disp = max(max_disp, disp_mag)

                # Reaction Force magnitude (all are already in PyNite's SI unit: N)
                # NOTE: Explicit float casting prevents Base.Quantity issue with numpy
                rxn_f_mag = np.sqrt(rxn_fx ** 2 + rxn_fy ** 2 + rxn_fz ** 2)
                max_rxn_f = max(max_rxn_f, rxn_f_mag)

                # Reaction Moment magnitude (all are already in PyNite's SI unit: N*m)
                # NOTE: Explicit float casting prevents Base.Quantity issue with numpy
                rxn_m_mag = np.sqrt(rxn_mx ** 2 + rxn_my ** 2 + rxn_mz ** 2)
                max_rxn_m = max(max_rxn_m, rxn_m_mag)

            results_table.add_row([
                load_name,
                f"{max_disp:e}",
                f"{max_rxn_f:e}",
                f"{max_rxn_m:e}"
            ])

        if len(all_load_names) > 0:
            App.Console.PrintMessage(text + results_table.get_string())
        else:
            App.Console.PrintMessage(text + "No load cases or combinations to report results for.\n")

    def run_analysis(self, analysis_type="Linear Static"):
        """Run the analysis."""
        if analysis_type == "Linear Static":
            App.Console.PrintMessage("Running PyNite Linear Static Analysis...\n")
            self.pynite_model.analyze(sparse=False)
            if PRINT_MODEL:
                self.check_model()
        else:
            App.Console.PrintWarning(f"PyNiteSolver does not currently support {analysis_type}\n")

    def extract_results(self, analysis_type="Linear Static") -> FEMResult:
        """Extract results from PyNite and store them in a standardized FEMResult object."""
        App.Console.PrintMessage("Extracting PyNite Results...\n")

        if analysis_type == "Linear Static":
            return self._get_static_results()

        return FEMResult(solver_name="PyNite")

    def _add_nodes(self):
        """Add nodes and boundary conditions to the PyNite model."""
        # units in m
        if not hasattr(self.doc, "Nodes"): return

        node_fixities = {}
        if hasattr(self.doc, "BoundaryConditions"):
            for bc in self.doc.BoundaryConditions.Group:
                if hasattr(bc, "Nodes"):
                    fixity = [bc.Dx, bc.Dy, bc.Dz, bc.Rx, bc.Ry, bc.Rz]
                    for node in bc.Nodes:
                        node_fixities[node.Name] = fixity

        for node in self.doc.Nodes.Group:
            if hasattr(node, "X"):
                node_id = node.Name
                # Convert from FreeCAD's internal length unit (assumed mm) to meters for PyNite (SI base unit)
                x_si = Units.Quantity(node.X.Value, 'mm').getValueAs('m').Value
                y_si = Units.Quantity(node.Y.Value, 'mm').getValueAs('m').Value
                z_si = Units.Quantity(node.Z.Value, 'mm').getValueAs('m').Value

                self.pynite_model.add_node(node_id, x_si, y_si, z_si)

                # Apply boundary condition fixity
                if node_id in node_fixities:
                    fixity = node_fixities[node_id]
                    self.pynite_model.def_support(node_id, support_DX=fixity[0], support_DY=fixity[1],
                                                  support_DZ=fixity[2], support_RX=fixity[3],
                                                  support_RY=fixity[4], support_RZ=fixity[5])

    def _add_sections(self):
        """Add sections to the PyNite model."""
        if not hasattr(self.doc, "Sections"): return

        for section in self.doc.Sections.Group:
            section_name = section.Label

            area = getattr(section, "Area", 0.0)
            iyy = getattr(section, "Iyy", 0.0)
            izz = getattr(section, "Izz", 0.0)

            # Convert to PyNite units (m^2 and m^4)
            area_m2 = Units.Quantity(area.Value, 'mm^2').getValueAs('m^2').Value if hasattr(area, 'Value') else 0.0
            iyy_m4 = Units.Quantity(iyy, 'mm^4').getValueAs('m^4').Value
            izz_m4 = Units.Quantity(izz, 'mm^4').getValueAs('m^4').Value

            # Simplified J, use the SI values
            j_m4 = (iyy_m4 + izz_m4)

            self.pynite_model.add_section(section_name, area_m2, iyy_m4, izz_m4, j_m4)

    def _add_beams(self):
        """Add beams, material properties, and releases to the PyNite model."""
        if not hasattr(self.doc, "Beams"): return
        for beam in self.doc.Beams.Group:
            if hasattr(beam, "StartNode") and hasattr(beam, "EndNode"):
                beam_id = beam.Name
                start_node = beam.StartNode.Name
                end_node = beam.EndNode.Name
                section_name = beam.Section.Label if beam.Section else "DefaultSection"

                # Material Properties:
                material_name = beam.Material.Label if beam.Material else "DefaultSteel"

                # Young's and Shear Modulus handling
                E = beam.Material.YoungsModulus.getValueAs('Pa').Value if  hasattr(beam.Material,"YoungsModulus") \
                    else 2.1e11
                G = beam.Material.ShearModulus.getValueAs('Pa').Value if  hasattr(beam.Material,"ShearModulus") \
                    else 8.1e10
                # 1. Poisson's Ratio
                nu = beam.Material.PoissonsRatio.Value if hasattr(beam.Material,"PoissonsRatio") else 0.3
                # 2. Density
                rho = beam.Material.Density.getValueAs('kg/m^3').Value \
                    if beam.Material and hasattr(beam.Material, "Density") else 7850.0

                if material_name not in [mat.name for mat in self.pynite_model.materials.values()]:
                    self.pynite_model.add_material(material_name, E, G, nu, rho)
                rotation = getattr(beam, "section_rotation", 0.0)
                print("rotation",rotation,type(rotation))
                self.pynite_model.add_member(beam_id, start_node, end_node, material_name, section_name,
                                             rotation=rotation)

                # Member Releases
                start_release, end_release = [False] * 6, [False] * 6
                if hasattr(beam, "MemberRelease") and beam.MemberRelease is not None:
                    member_release = beam.MemberRelease
                    if hasattr(member_release, 'Proxy'):
                        start_release = list(member_release.Proxy.get_start_release())
                        end_release = list(member_release.Proxy.get_end_release())

                self.pynite_model.def_releases(beam_id, Dxi=start_release[0], Dyi=start_release[1],
                                               Dzi=start_release[2],
                                               Rxi=start_release[3], Ryi=start_release[4], Rzi=start_release[5],
                                               Dxj=end_release[0], Dyj=end_release[1], Dzj=end_release[2],
                                               Rxj=end_release[3], Ryj=end_release[4], Rzj=end_release[5])

    def _add_loads(self):
        """Add loads and load combinations to the PyNite model."""
        if hasattr(self.doc, "Loads"):
            for load_case in self.doc.Loads.Group:
                if getattr(load_case, "Type", "") == "LoadIDFeature":
                    self._add_load_case(load_case)

        if hasattr(self.doc, "LoadCombinations"):
            for comb in self.doc.LoadCombinations.Group:
                if getattr(comb, "Type", "") == "LoadCombination":
                    self._add_load_combination(comb)

    def _add_load_case(self, load_case):
        """Add loads nested under a load case."""
        case_name = load_case.Label
        print("add loadcade ",case_name)
        for child in load_case.Group:
            print("child type",getattr(child, "Type", ""))
            if getattr(child, "Type", "") == "NodalLoad":
                # Nodal forces are assumed to be in N (PyNite default)
                for node in child.Nodes:
                    if hasattr(child, "Force"):
                        self.pynite_model.add_node_load(node.Name, 'FX', child.Force.x, case=case_name)
                        self.pynite_model.add_node_load(node.Name, 'FY', child.Force.y, case=case_name)
                        self.pynite_model.add_node_load(node.Name, 'FZ', child.Force.z, case=case_name)
                    if hasattr(child, "Moment"):
                        # Convert moment from FreeCAD unit (assumed N*mm) to N*m (PyNite SI required unit)
                        mx = Units.Quantity(child.Moment.x, 'N*mm').getValueAs('N*m').Value
                        my = Units.Quantity(child.Moment.y, 'N*mm').getValueAs('N*m').Value
                        mz = Units.Quantity(child.Moment.z, 'N*mm').getValueAs('N*m').Value

                        self.pynite_model.add_node_load(node.Name, 'MX', mx, case=case_name)
                        self.pynite_model.add_node_load(node.Name, 'MY', my, case=case_name)
                        self.pynite_model.add_node_load(node.Name, 'MZ', mz, case=case_name)

            elif getattr(child, "Type", "") == "MemberLoad":
                # Distributed loads must be converted to N/m (PyNite SI required unit)
                axis_map = {'X': 'Fx', 'Y': 'Fy', 'Z': 'Fz'}
                if not getattr(child, "LocalCS", False): axis_map = {'X': 'FX', 'Y': 'FY', 'Z': 'FZ'}

                for beam in child.Beams:
                    length_beam =beam.Length.getValueAs('m').Value
                    start_f = getattr(child, "StartForce", (0.0, 0.0, 0.0))
                    end_f = getattr(child, "EndForce", (0.0, 0.0, 0.0))
                    start_pos = getattr(child, "StartPosition", 0.0)
                    end_pos = getattr(child, "EndPosition", 1.0)
                    for i, axis in enumerate(['X', 'Y', 'Z']):
                        if not (start_f[i] == 0.0 and end_f[i] == 0.0):
                            # Convert distributed load from FreeCAD unit  #too complex, may be optimized
                            start_val = Units.Quantity(start_f[i], 'N/mm').getValueAs('N/m').Value
                            end_val = Units.Quantity(end_f[i], 'N/mm').getValueAs('N/m').Value
                            self.pynite_model.add_member_dist_load(beam.Name, axis_map[axis],
                                                                   end_val, start_val, start_pos*length_beam,
                                                                   end_pos*length_beam, case_name)

            elif getattr(child, "Type", "") == "AccelerationLoad":
                acc_vector = getattr(child, "LinearAcceleration", App.Vector(0, 0, 0))
                factors = {'FX': acc_vector.x, 'FY': acc_vector.y, 'FZ': acc_vector.z}

                for direction, factor in factors.items():
                    if abs(factor) > 1e-6:
                        # PyNite self_weight applies to all members with mass.
                        self.pynite_model.add_member_self_weight(direction, factor, case_name)

    def _create_dummy_combinations(self):
        """Create dummy load combinations automatically if none exist"""
        # Check if there are any load combinations
        if (not hasattr(self.doc, "LoadCombinations") or
                not self.doc.LoadCombinations.Group):

            # Check if we have load cases
            if hasattr(self.doc, "Loads") and self.doc.Loads.Group:
                # Create simple 1:1 combinations
                for load_case in self.doc.Loads.Group:
                    combo_name = f"LC_{load_case.Label}"
                    # Create combination dict for PyNite
                    if hasattr(self.pynite_model, 'load_cases'):
                        self.pynite_model.add_load_combo(combo_name, {load_case.Label: 1.0})

    def _add_load_combination(self, comb):
        """Add a load combination to PyNite model."""
        comb_dict = {}
        for i, load_case in enumerate(comb.Loads):
            if i < len(comb.Coefficients):
                comb_dict[load_case.Label] = comb.Coefficients[i]
        if comb_dict:
            self.pynite_model.add_load_combo(comb.Label, comb_dict)

    def _get_static_results(self):
        """Extract static analysis results from PyNite and convert to FEMResult."""
        results = FEMResult(solver_name="PyNite")

        # Get all load names (cases and combinations)

        # Safely access load_combos and load_cases, defaulting to an empty dict.
        # Check if they are dictionaries before trying to get keys, addressing the list error.
        pynite_combos = getattr(self.pynite_model, 'load_combos', {})
        pynite_cases = getattr(self.pynite_model, 'load_cases', {})

        combo_names = list(pynite_combos.keys()) if isinstance(pynite_combos, dict) else []
        case_names = list(pynite_cases.keys()) if isinstance(pynite_cases, dict) else []

        all_load_names = list(set(combo_names + case_names))

        for load_name in all_load_names:
            results.load_cases[load_name] = {
                'nodes': self._get_node_results(load_name),
                'members': self._get_member_results(load_name)
            }
        return results

    def _get_node_results(self, load_name):
        """Get node results for a specific load case/combo."""
        nr = {}
        for n in self.pynite_model.nodes.values():
            nr[n.name] = {
                'DX': Units.Quantity(float(n.DX.get(load_name, 0)), 'm'),
                'DY': Units.Quantity(float(n.DY.get(load_name, 0)), 'm'),
                'DZ': Units.Quantity(float(n.DZ.get(load_name, 0)), 'm'),
                'RX': Units.Quantity(float(n.RX.get(load_name, 0)), 'rad'),
                'RY': Units.Quantity(float(n.RY.get(load_name, 0)), 'rad'),
                'RZ': Units.Quantity(float(n.RZ.get(load_name, 0)), 'rad'),
                'RXN_FX': Units.Quantity(float(n.RxnFX.get(load_name, 0)), 'N'),
                'RXN_FY': Units.Quantity(float(n.RxnFY.get(load_name, 0)), 'N'),
                'RXN_FZ': Units.Quantity(float(n.RxnFZ.get(load_name, 0)), 'N'),
                'RXN_MX': Units.Quantity(float(n.RxnMX.get(load_name, 0)), 'N*m'),
                'RXN_MY': Units.Quantity(float(n.RxnMY.get(load_name, 0)), 'N*m'),
                'RXN_MZ': Units.Quantity(float(n.RxnMZ.get(load_name, 0)), 'N*m'),
            }
        return nr

    def _get_torque_array(self, member, positions, load_name):
        """
        Manually generate torque array by sampling at positions.
        Workaround for member.torque_array() potentially returning None.
        """
        values = []
        for x in positions:
            try:
                # member.torque() returns a float
                val = member.torque(x, load_name)
                # Handle numpy scalar if returned
                if hasattr(val, 'item'): val = val.item()
            except Exception:
                val = 0.0
            values.append(val)
        return np.array(values)

    def _get_member_results(self, load_name):
        """Get member results for a specific load case/combo using Units.Quantity."""
        mr = {}
        n_points = N_POINTS

        for member in self.pynite_model.members.values():

            # Position array (shared)
            axial_data = member.axial_array(n_points, load_name)
            pos_arr = axial_data[0]

            # Generate Torque manually - workaround as torque_array in pynite has an error
            torq_values = self._get_torque_array(member, pos_arr, load_name)

            raw_data = {
                'axial': (axial_data, 'N'),
                'shear_y': (member.shear_array('Fy', n_points, load_name), 'N'),
                'shear_z': (member.shear_array('Fz', n_points, load_name), 'N'),
                'moment_y': (member.moment_array('My', n_points, load_name), 'N*m'),
                'moment_z': (member.moment_array('Mz', n_points, load_name), 'N*m'),
                'moment_x': ((pos_arr, torq_values), 'N*m'), # Torsion using manual array
                'deflection_y': (member.deflection_array('dy', n_points, load_name), 'm'),
                'deflection_z': (member.deflection_array('dz', n_points, load_name), 'm'),
                # Placeholder for CodeCheck to fill later
                'unity_check': ((pos_arr, np.zeros(n_points)), '')
            }

            structured_results = {}
            for key, (arr, unit_str) in raw_data.items():
                # arr[0] = positions, arr[1] = values (numpy array)

                # 1. Standard Quantities (for UI/Graphs)
                # Convert to Python list of Quantities - SLOW but needed for UI
                val_quantities = [Units.Quantity(float(v), unit_str) for v in arr[1]]
                pos_m = [float(p) for p in arr[0]]

                structured_results[key] = {
                    'values': [pos_m, val_quantities],

                    # 2. RAW DATA (for CodeCheck Speed)
                    # Store numpy arrays directly to bypass Quantity overhead later
                    'raw_values': arr[1],
                    'raw_positions': arr[0],

                    'min': Units.Quantity(float(np.min(arr[1])), unit_str),
                    'max': Units.Quantity(float(np.max(arr[1])), unit_str)
                }
            mr[member.name] = structured_results
        return mr