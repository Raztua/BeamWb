# features/CodeCheck.py
import FreeCAD as App
import FreeCADGui
from standards.Registry import StandardsRegistry
import standards
import numpy as np


class CodeCheckFeature:
    def __init__(self, obj):
        self.Type = "CodeCheckFeature"
        obj.Proxy = self
        avail_stds = StandardsRegistry.get_available_names()
        if not avail_stds: avail_stds = ["None"]

        if not hasattr(obj, "Standard"):
            obj.addProperty("App::PropertyEnumeration", "Standard", "Settings", "Design Code")
        obj.Standard = avail_stds

        if not hasattr(obj, "ActiveCase"):
            obj.addProperty("App::PropertyString", "ActiveCase", "Display", "Result Case").ActiveCase = "Envelope"

        if not hasattr(obj, "ManagedProperties"):
            obj.addProperty("App::PropertyStringList", "ManagedProperties", "Hidden", "Tracked dynamic properties")

        self.cached_results = {}
        self.available_cases = ["Envelope"]
        self.update_standard_properties(obj)

    def __getstate__(self):
        """
        Serialization hook: Called when the document is saved.
        Returns a sanitized dictionary where all numpy arrays are converted to lists
        to prevent JSON/Pickle serialization errors.
        """
        return self._sanitize_data(self.__dict__)

    def __setstate__(self, state):
        """
        Deserialization hook: Called when the document is restored.
        Restores the object state.
        """
        self.__dict__ = state

    def onDocumentRestored(self, obj):
        """
        Called after the document is fully restored.
        Can be used for additional re-initialization if needed.
        """
        pass

    def _sanitize_data(self, data):
        """
        Recursively convert numpy types to standard python types.
        """
        if isinstance(data, np.ndarray):
            return data.tolist()
        if isinstance(data, np.generic):  # Handles np.float64, np.int32, etc.
            return data.item()
        if isinstance(data, dict):
            return {k: self._sanitize_data(v) for k, v in data.items()}
        if isinstance(data, list):
            return [self._sanitize_data(v) for v in data]
        if isinstance(data, tuple):
            return tuple(self._sanitize_data(v) for v in data)
        return data

    def execute(self, obj):
        if hasattr(self, '_in_execute') and self._in_execute: return
        self._in_execute = True
        doc = App.ActiveDocument

        try:
            if hasattr(doc, 'openTransaction'): doc.openTransaction("CodeCheckExecute")
            self._ensure_properties(obj)
            solver_obj = self._find_solver(obj)
            if not solver_obj or not solver_obj.Results.load_cases: return

            fem_results = solver_obj.Results
            self.available_cases = list(fem_results.load_cases.keys())
            current_std = obj.Standard
            std_class = StandardsRegistry.get_standard(current_std)
            if not std_class: return

            # 1. Get Global Parameters from CodeCheck Object
            global_params = {}
            def_props = std_class.get_parameter_definitions()
            for prop_name in def_props:
                if hasattr(obj, prop_name):
                    global_params[prop_name] = getattr(obj, prop_name)

            self.cached_results = {}
            all_beams_data = {}

            for case_name, case_data in fem_results.load_cases.items():
                self.cached_results[case_name] = {}
                for beam_name, res_data in case_data.get('members', {}).items():
                    beam_obj = App.ActiveDocument.getObject(beam_name)
                    if not beam_obj: continue

                    # 2. Prepare Beam Data & Apply Overrides
                    s_props, m_props, forces_dict, beam_params = self._prepare_beam_data(beam_obj, res_data,
                                                                                         global_params)

                    checker = std_class(beam_obj, s_props, m_props, forces_dict)
                    checker.set_parameters(beam_params)  # Use the merged parameters

                    res = checker.run_check()
                    res['positions'] = forces_dict['x']

                    self.cached_results[case_name][beam_name] = res
                    if beam_name not in all_beams_data: all_beams_data[beam_name] = []
                    all_beams_data[beam_name].append(res)

                    uc_vals = [App.Units.Quantity(float(v), "") for v in res['values']]

                    # Note: We sanitize 'raw_values' here just in case fem_results is also serialized later,
                    # but strictly speaking __getstate__ handles self.cached_results.
                    # It is safer to convert what we put into fem_results too.
                    clean_positions = self._sanitize_data(forces_dict['x'])
                    clean_raw = self._sanitize_data(res['values'])

                    result_entry = {
                        'values': [clean_positions, uc_vals],
                        'raw_values': clean_raw,
                        'min': App.Units.Quantity(float(np.min(res['values'])), ""),
                        'max': App.Units.Quantity(float(np.max(res['values'])), "")
                    }
                    fem_results.load_cases[case_name]['members'][beam_name]['unity_check'] = result_entry

            self._calc_envelope_and_inject(fem_results, all_beams_data)
            solver_obj.Results = fem_results
            if hasattr(doc, 'commitTransaction'): doc.commitTransaction()
            solver_obj.touch()

        except Exception as e:
            if hasattr(doc, 'abortTransaction'): doc.abortTransaction()
            App.Console.PrintError(f"CodeCheck execute failed: {str(e)}\n")

        finally:
            self._in_execute = False

    def onChanged(self, obj, prop):
        if prop == "Standard": self.update_standard_properties(obj)

    def update_standard_properties(self, obj):
        if obj.Standard == "None": return
        std_class = StandardsRegistry.get_standard(obj.Standard)
        if not std_class: return

        if not hasattr(obj, "ManagedProperties"):
            obj.addProperty("App::PropertyStringList", "ManagedProperties", "Hidden", "Tracked dynamic properties")

        current_tracked = list(obj.ManagedProperties)
        req_props_def = std_class.get_parameter_definitions()
        req_names = list(req_props_def.keys())

        for p in current_tracked:
            if p not in req_names: obj.removeProperty(p)

        for name, data in req_props_def.items():
            prop_type, default, tooltip = data[0], data[1], data[2]
            candidates = data[3] if len(data) > 3 else None
            if not hasattr(obj, name):
                obj.addProperty(prop_type, name, "Settings", tooltip)
                if prop_type == "App::PropertyEnumeration":
                    if candidates:
                        setattr(obj, name, candidates)
                    else:
                        setattr(obj, name, [default])
                setattr(obj, name, default)
        obj.ManagedProperties = req_names

    def _ensure_properties(self, obj):
        avail = StandardsRegistry.get_available_names()
        if not avail: avail = ["None"]
        obj.Standard = avail
        if (obj.Standard == "None" or obj.Standard not in avail) and len(avail) > 0 and avail[0] != "None":
            obj.Standard = avail[0]
        self.update_standard_properties(obj)

    def _prepare_beam_data(self, beam_obj, res_data, global_params):
        """
        Extract data and handle per-beam overrides for LCr.
        Returns: s_props, m_props, forces, final_params
        """
        s = beam_obj.Section
        mat = beam_obj.Material
        st = getattr(s, "ProfileType", "Unknown")

        # --- 1. Extract Dimensions ---
        dims = {'h': 0.0, 'b': 0.0, 'tw': 0.0, 'tf': 0.0, 't': 0.0, 'd': 0.0}

        def get_dim(p):
            return getattr(s, p).getValueAs('m').Value if hasattr(s, p) else 0.0

        if st in ["I-Shape", "H-Shape", "T-Shape"]:
            dims.update({'h': get_dim("Height"), 'b': get_dim("Width"), 'tw': get_dim("WebThickness"),
                         'tf': get_dim("FlangeThickness")})
        elif st in ["Rectangle", "HSS", "Tubular"]:
            dims.update({'h': get_dim("Height"), 'b': get_dim("Width"),
                         't': get_dim("Thickness") if hasattr(s, "Thickness") else 0.0})
            if st == "Tubular": dims['d'] = dims['b']

        # --- 2. Section Properties ---
        sp = dims.copy()
        sp['type'] = st
        sp['A'] = s.Area.getValueAs('m^2').Value
        sp['Iy'] = s.Iyy.getValueAs('m^4').Value
        sp['Iz'] = s.Izz.getValueAs('m^4').Value
        sp['L'] = beam_obj.Length.getValueAs('m').Value
        sp['J'] = s.J.getValueAs('m^4').Value if hasattr(s, "J") and s.J.Value > 0 else sp['Iy'] * 0.01

        if hasattr(s, "Wel_y"):
            sp['Wel_y'] = s.Wel_y.getValueAs('m^3').Value
        else:
            sp['Wel_y'] = getattr(s, "Zymin", App.Units.Quantity(0)).getValueAs('m^3').Value

        if hasattr(s, "Wel_z"):
            sp['Wel_z'] = s.Wel_z.getValueAs('m^3').Value
        else:
            sp['Wel_z'] = getattr(s, "Zzmin", App.Units.Quantity(0)).getValueAs('m^3').Value

        if hasattr(s, "Wpl_y"):
            sp['Wpl_y'] = s.Wpl_y.getValueAs('m^3').Value
        else:
            sf = 1.25 if st in ["Tubular", "Rectangle"] else 1.14
            sp['Wpl_y'] = sp['Wel_y'] * sf

        if hasattr(s, "Wpl_z"):
            sp['Wpl_z'] = s.Wpl_z.getValueAs('m^3').Value
        else:
            sf = 1.25 if st in ["Tubular", "Rectangle"] else 1.14
            sp['Wpl_z'] = sp['Wel_z'] * sf

        # --- 3. Material Properties ---
        mp = {
            'fy': mat.YieldStrength.getValueAs('Pa').Value,
            'E': mat.YoungsModulus.getValueAs('Pa').Value,
            'G': getattr(mat, "ShearModulus", mat.YoungsModulus).getValueAs('Pa').Value
        }

        # --- 4. Forces ---
        def get_raw(key):
            return res_data.get(key, {}).get('raw_values', [])

        forces = {
            'x': res_data.get('axial', {}).get('raw_positions', []),
            'P': get_raw('axial'),
            'My': get_raw('moment_y'),
            'Mz': get_raw('moment_z'),
            'Vy': get_raw('shear_y'),
            'Vz': get_raw('shear_z'),
            'Tx': get_raw('moment_x')
        }

        # --- 5. Parameter Overrides (Using Beam BucklingLength Properties) ---
        final_params = global_params.copy()

        # We calculate the ratio: Ratio = BucklingLength / BeamLength
        # WARNING: sp['L'] is in Meters. beam_obj.BucklingLengthY is in mm (usually).
        # We must use beam_obj.Length.Value (mm) to get a correct ratio.

        beam_len_val = 1.0
        if hasattr(beam_obj, "Length"):
            if hasattr(beam_obj.Length, "Value"):
                beam_len_val = beam_obj.Length.Value  # mm
            else:
                beam_len_val = float(beam_obj.Length)  # assuming mm

        if beam_len_val > 1e-6:
            if hasattr(beam_obj, "BucklingLengthY"):
                val = beam_obj.BucklingLengthY
                if hasattr(val, "Value"): val = val.Value
                # Ratio = L_buckling (mm) / L_beam (mm)
                final_params['Lcr_y_ratio'] = val / beam_len_val

            if hasattr(beam_obj, "BucklingLengthZ"):
                val = beam_obj.BucklingLengthZ
                if hasattr(val, "Value"): val = val.Value
                # Ratio = L_buckling (mm) / L_beam (mm)
                final_params['Lcr_z_ratio'] = val / beam_len_val

        return sp, mp, forces, final_params

    def _calc_envelope_and_inject(self, fem_results, all_beams_data):
        env_case = "Envelope"
        if env_case not in fem_results.load_cases:
            fem_results.load_cases[env_case] = {'nodes': {}, 'members': {}}
        self.cached_results[env_case] = {}

        for beam_name, results_list in all_beams_data.items():
            if not results_list: continue
            raw_arrays = [np.array(r['values']) for r in results_list]
            if not raw_arrays: continue

            max_len = max(arr.shape[0] for arr in raw_arrays)
            valid_indices = [i for i, arr in enumerate(raw_arrays) if arr.shape[0] == max_len]
            if not valid_indices: continue

            valid_arrays = [raw_arrays[i] for i in valid_indices]
            max_vals = np.max(np.vstack(valid_arrays), axis=0)
            positions = results_list[valid_indices[0]]['positions']

            max_uc_overall = float(np.max(max_vals))
            best_log = "Envelope Log"
            for i in valid_indices:
                r = results_list[i]
                if abs(r['max_uc'] - max_uc_overall) < 1e-5:
                    best_log = r['detailed_log']
                    break

            env_res = {
                'values': max_vals.tolist(),
                'positions': positions,
                'max_uc': max_uc_overall,
                'detailed_log': "=== ENVELOPE CASE ===\n" + best_log
            }
            # Although runtime uses numpy (in positions etc), we let __getstate__ handle saving cleanup
            self.cached_results[env_case][beam_name] = env_res

            uc_vals = [App.Units.Quantity(float(v), "") for v in max_vals]
            if beam_name not in fem_results.load_cases[env_case]['members']:
                fem_results.load_cases[env_case]['members'][beam_name] = {}

            # Sanitize for injection into fem_results just in case
            clean_positions = self._sanitize_data(positions)
            clean_raw = self._sanitize_data(max_vals)

            fem_results.load_cases[env_case]['members'][beam_name]['unity_check'] = {
                'values': [clean_positions, uc_vals],
                'raw_values': clean_raw,
                'min': App.Units.Quantity(float(np.min(max_vals)), ""),
                'max': App.Units.Quantity(float(np.max(max_vals)), "")
            }

    def _find_solver(self, obj):
        doc = App.ActiveDocument
        for obj in doc.Objects:
            if hasattr(obj, "Results") and hasattr(obj.Results, "load_cases"): return obj
        return None

    def get_detail_info(self, beam_name):
        active = self.ActiveCase if hasattr(self, "ActiveCase") else "Envelope"
        if active not in self.cached_results: active = "Envelope"
        return self.cached_results.get(active, {}).get(beam_name, {}).get('detailed_log', "No Data")

    def get_available_cases(self):
        return ["Envelope"] + self.available_cases


class CodeCheckViewProvider:
    def __init__(self, vobj): vobj.Proxy = self

    def getIcon(self): return ":/icons/preferences-system.svg"

    def doubleClicked(self, vobj):
        from ui.dialog_CodeCheckResults import show_code_check_results
        show_code_check_results(vobj.Object)
        return True


def make_code_check_feature():
    doc = App.ActiveDocument
    if hasattr(doc, "CodeCheck"): return doc.CodeCheck
    cg = doc.addObject("App::DocumentObjectGroupPython", "CodeCheck")
    CodeCheckFeature(cg)
    if App.GuiUp: CodeCheckViewProvider(cg.ViewObject)
    from features.AnalysisGroup import get_analysis_group
    analysis_group = get_analysis_group()
    if analysis_group and cg not in analysis_group.Group:
        analysis_group.addObject(cg)
    App.ActiveDocument.recompute()
    return cg