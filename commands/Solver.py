import FreeCAD as App
import FreeCADGui as Gui
import os

from solvers.PyNiteSolver import PyNiteSolverEngine, MEMBER_RESULT_KEYS
from features.SolverEngine import FEMResult
from features.nodes import make_result_nodes_group
from features.beams import make_result_beams_group

# Constants
WORKBENCH_DIR = os.path.dirname(os.path.dirname(__file__))
ICON_DIR = os.path.join(WORKBENCH_DIR, "icons")
SOLVER_ICON_PATH = os.path.join(ICON_DIR, "solver_icon.svg")

DIAGRAM_TYPE_MAP = MEMBER_RESULT_KEYS
DIAGRAM_TYPES = ["None"] + list(DIAGRAM_TYPE_MAP.keys())


class Solver():
    def __init__(self, obj):
        self.flagInit = True
        obj.Proxy = self
        self.solver_engine = None
        self.setup_properties(obj)
        self.flagInit = False

    def setup_properties(self, obj):
        obj.addProperty("App::PropertyString", "Type", "Base", "Solver Type").Type = "Solver"
        obj.addProperty("App::PropertyEnumeration", "SolverEngine", "Solver", "Engine").SolverEngine = ["PyNite"]
        obj.addProperty("App::PropertyEnumeration", "AnalysisType", "Solver", "Type").AnalysisType = ["Linear Static",
                                                                                                      "Modal",
                                                                                                      "Buckling"]
        obj.addProperty("App::PropertyBool", "RunAnalysis", "Solver", "Run analysis").RunAnalysis = False

        # Stores the full results dict
        obj.addProperty("App::PropertyPythonObject", "Results", "Results", "Full Analysis Results", 4)
        obj.Results = FEMResult()  # Initialize empty

        # Vis Properties
        obj.addProperty("App::PropertyEnumeration", "LoadCase", "Results", "Load case").LoadCase = ["None"]
        obj.addProperty("App::PropertyEnumeration", "DiagramType", "Results",
                        "Diagram type").DiagramType = DIAGRAM_TYPES
        obj.addProperty("App::PropertyFloat", "DiagramScale", "Results", "Diagram scale").DiagramScale = 1.0
        obj.addProperty("App::PropertyFloat", "DeformationScale", "Results", "Deformation scale").DeformationScale = 1.0

        obj.addProperty("App::PropertyLink", "SelectedNode", "NodeResults", "Selected node for result display")
        obj.addProperty("App::PropertyBool", "ShowNodeResults", "NodeResults", "Show node results").ShowNodeResults = False
        obj.addProperty("App::PropertyBool", "ShowReactions", "NodeResults", "Show reaction forces").ShowReactions = True

        self._create_result_groups(obj)

    def _create_result_groups(self, obj):
        solver_group = make_solver()
        if not App.ActiveDocument.getObject("NodesResult"):
            solver_group.addObject(make_result_nodes_group())
        if not App.ActiveDocument.getObject("BeamsResult"):
            solver_group.addObject(make_result_beams_group())

    def execute(self, obj):
        if 'Restore' in obj.State: return
        if obj.RunAnalysis:
            self.run_analysis(obj)
            obj.RunAnalysis = False

    def run_analysis(self, obj):
        """Executes analysis and stores ALL results in obj.Results"""
        # Skip clearing - we'll reuse existing objects
        # self._clear_result_objects(obj)  # REMOVE THIS LINE

        if obj.SolverEngine == "PyNite":
            self.solver_engine = PyNiteSolverEngine(App.ActiveDocument)
        else:
            App.Console.PrintError(f"Solver {obj.SolverEngine} not implemented.\n")
            return

        App.Console.PrintMessage(f"Running Analysis with {obj.SolverEngine}...\n")

        # Run Engine and get FEMResult object
        full_results = self.solver_engine.analyze(obj.AnalysisType)

        # Store the FULL results object in the FreeCAD Property
        obj.Results = full_results

        if not obj.Results.load_cases:
            App.Console.PrintWarning("Analysis finished but no results returned.\n")
            self._update_result_properties(obj)
            return

        App.Console.PrintMessage("Analysis Complete. Results stored.\n")

        # 3. Visualization updates - don't create new objects, just update existing ones
        self._update_result_properties(obj)
        self._update_or_create_result_objects(obj)  # Use new method
        self._update_results(obj)
        self.update_visualization(obj)

    def _update_or_create_result_objects(self, obj):
        """Update existing result objects or create if they don't exist"""
        if not obj.Results or not obj.Results.load_cases:
            return

        # Get or create result groups
        nodes_group = self._ensure_result_group("NodesResult", make_result_nodes_group)
        beams_group = self._ensure_result_group("BeamsResult", make_result_beams_group)

        # We use the *first* case to define the structure
        first_case = next(iter(obj.Results.load_cases))
        case_data = obj.Results.load_cases[first_case]

        # Update or Create Nodes
        existing_nodes = {n.BaseNode.Name: n for n in nodes_group.Group if hasattr(n, "BaseNode")}

        for node_name in case_data.get('nodes', {}):
            base = App.ActiveDocument.getObject(node_name)
            if base:
                if node_name in existing_nodes:
                    # Update existing node
                    res_node = existing_nodes[node_name]
                    res_node.BaseNode = base
                    res_node.Label = f"Result_{base.Label}"
                else:
                    # Create new node if needed
                    res = self._create_result_node(obj, base)
                    if res:
                        nodes_group.addObject(res)

        # Update or Create Beams
        existing_beams = {b.BaseBeam.Name: b for b in beams_group.Group if hasattr(b, "BaseBeam")}

        for beam_name in case_data.get('members', {}):
            base = App.ActiveDocument.getObject(beam_name)
            if base:
                if beam_name in existing_beams:
                    # Update existing beam
                    res_beam = existing_beams[beam_name]
                    res_beam.BaseBeam = base
                    res_beam.Label = f"Result_{base.Label}"
                    self._link_beam_nodes(obj, res_beam, base)
                    # Copy basic props
                    for p in ["Section", "StartOffset", "EndOffset", "OffsetAxis", "section_rotation"]:
                        if hasattr(base, p):
                            setattr(res_beam, p, getattr(base, p))
                else:
                    # Create new beam if needed
                    res = self._create_result_beam(obj, base)
                    if res:
                        beams_group.addObject(res)

    def _ensure_result_group(self, group_name, create_function):
        """Ensure a result group exists, create if it doesn't"""
        doc = App.ActiveDocument
        group = doc.getObject(group_name)
        if not group:
            group = create_function()
        return group

    def _clear_orphaned_objects(self, obj):
        """Remove result objects whose base objects no longer exist"""
        doc = App.ActiveDocument

        for grp_name in ["NodesResult", "BeamsResult"]:
            group = doc.getObject(grp_name)
            if not group:
                continue

            objects_to_remove = []
            for res_obj in group.Group:
                if grp_name == "NodesResult" and hasattr(res_obj, "BaseNode"):
                    if not res_obj.BaseNode or res_obj.BaseNode.Name not in doc.Objects:
                        objects_to_remove.append(res_obj)
                elif grp_name == "BeamsResult" and hasattr(res_obj, "BaseBeam"):
                    if not res_obj.BaseBeam or res_obj.BaseBeam.Name not in doc.Objects:
                        objects_to_remove.append(res_obj)

            # Remove orphaned objects
            for orphan in objects_to_remove:
                group.removeObject(orphan)
                try:
                    doc.removeObject(orphan.Name)
                except:
                    pass

    def _create_result_node(self, obj, base):
        from features.nodes import create_result_node
        r = create_result_node(base)
        if r:
            r.BaseNode = base
            r.Label = f"Result_{base.Label}"
        return r

    def _create_result_beam(self, obj, base):
        from features.beams import create_result_beam
        r = create_result_beam(base)
        if r:
            r.Label = f"Result_{base.Label}"
            r.BaseBeam = base
            self._link_beam_nodes(obj, r, base)
            # Copy basic props
            for p in ["Section", "StartOffset", "EndOffset", "OffsetAxis", "section_rotation"]:
                if hasattr(base, p): setattr(r, p, getattr(base, p))
        return r

    def _link_beam_nodes(self, obj, r_beam, base):
        # Find corresponding result nodes
        res_nodes = App.ActiveDocument.NodesResult.Group
        s_name = base.StartNode.Name
        e_name = base.EndNode.Name
        for n in res_nodes:
            if hasattr(n, "BaseNode"):
                if n.BaseNode.Name == s_name:
                    r_beam.StartNode = n
                elif n.BaseNode.Name == e_name:
                    r_beam.EndNode = n

    def _clear_result_objects(self, obj):
        doc = App.ActiveDocument
        if not doc: return
        for grp_name in ["NodesResult", "BeamsResult"]:
            g = doc.getObject(grp_name)
            if g:
                for c in list(g.Group): doc.removeObject(c.Name)

    def _update_result_properties(self, obj):
        # Update dropdown list with all available cases
        if obj.Results and obj.Results.load_cases:
            obj.LoadCase = list(obj.Results.load_cases.keys())
        else:
            obj.LoadCase = ["None"]

    def _update_results(self, obj):
        # Updates VISUALIZATION only
        if not obj.Results.load_cases: return
        lc = obj.LoadCase
        if lc == "None" or lc not in obj.Results.load_cases: return

        data = obj.Results.load_cases[lc]

        # Update Nodes
        self._update_node_vis(obj, data.get('nodes', {}))
        # Update Beams
        self._update_beam_vis(obj, data.get('members', {}))


    def _update_node_vis(self, obj, nodes_data):
        max_disp = obj.Results.get_max_displacement(obj.LoadCase)
        scale = 0.0 if obj.DeformationScale == 0 else max_disp.getValueAs("mm") / obj.DeformationScale

        grp = App.ActiveDocument.getObject("NodesResult")
        if not grp:
            return

        for n in grp.Group:
            # Skip if base node doesn't exist or isn't in results
            if not hasattr(n, "BaseNode") or not n.BaseNode:
                continue
            if n.BaseNode.Name not in nodes_data:
                # Clear displacement for nodes not in current results
                if hasattr(n, "Proxy") and hasattr(n.Proxy, "set_displacement"):
                    n.Proxy.set_displacement(App.Vector(0, 0, 0), 1)
                continue

            d = nodes_data[n.BaseNode.Name]
            disp = App.Vector(d.get('DX', 0), d.get('DY', 0), d.get('DZ', 0))
            if scale == 0:
                n.Proxy.set_displacement(App.Vector(0, 0, 0), 1)
            else:
                n.Proxy.set_displacement(disp, scale)
            self._add_node_result_annotations(obj, n, d)

    def _add_single_annotation(self, node, text, offset):
        """Add a single text annotation to a node"""

        if hasattr(node, 'Proxy') and hasattr(node.Proxy, 'add_text'):
            node.Proxy.add_text(text)

    def _add_node_result_annotations(self, obj, base_node, node_data):
        """Add result annotations to the base node if enabled in solver properties"""
        # Check if node result display is enabled
        # Clear existing annotations
        base_node.Proxy.clear_texts()

        if hasattr(obj, 'ShowNodeResults') and obj.ShowNodeResults:
            dx = node_data.get('DX', 0.0).getValueAs('mm')
            dy = node_data.get('DY', 0.0).getValueAs('mm')
            dz = node_data.get('DZ', 0.0).getValueAs('mm')

            disp_text = f"D: ({dx.Value:.2f}, {dy.Value:.2f}, {dz.Value:.2f}) mm"
            self._add_single_annotation(base_node, disp_text, App.Vector(0, 10, 0))

        # Add reaction annotations if enabled
        if hasattr(obj, 'ShowReactions') and obj.ShowReactions:
            # Reaction forces
            fx = node_data.get('RXN_FX', 0.0).getValueAs('kN')
            fy = node_data.get('RXN_FY', 0.0).getValueAs('kN')
            fz = node_data.get('RXN_FZ', 0.0).getValueAs('kN')
            force_mag = (fx ** 2 + fy ** 2 + fz ** 2) ** 0.5
            if force_mag > 0.1:  # Only show if significant
                force_text = f"F: ({fx.Value:.1f}, {fy.Value:.1f}, {fz.Value:.1f}) kN"
                self._add_single_annotation(base_node, force_text, App.Vector(0, 20, 0))

            # Reaction moments
            mx = node_data.get('RXN_MX', 0.0).getValueAs('kN*m')
            my = node_data.get('RXN_MY', 0.0).getValueAs('kN*m')
            mz = node_data.get('RXN_MZ', 0.0).getValueAs('kN*m')
            moment_mag = (mx ** 2 + my ** 2 + mz ** 2) ** 0.5

            if moment_mag > 0.1:  # Only show if significant
                moment_text = f"M: ({mx.Value:.1f}, {my.Value:.1f}, {mz.Value:.1f}) kN·m"
                self._add_single_annotation(base_node, moment_text, App.Vector(0, 30, 0))

    def _update_beam_vis(self, obj, members_data):
        key = DIAGRAM_TYPE_MAP.get(obj.DiagramType)
        if not key:
            grp = App.ActiveDocument.getObject("BeamsResult")
            if grp:
                for b in grp.Group: b.Proxy.clear_diagram(b)
            return

        # Mapping key to target display units
        target_unit = "N"  # Fallback
        if "moment" in key:
            target_unit = "kN*m"
        elif "shear" in key or "axial" in key:
            target_unit = "kN"
        elif "deflection" in key:
            target_unit = "mm"
        elif "unity_check" in key:
            target_unit = ""

        # Get max value for scaling
        max_q = obj.Results.get_max_diagram_value(obj.LoadCase, key)
        # Ensure max_q is treated as a Quantity and converted to target unit
        # print("max q",max_q)
        if not key=="unity_check":
            max_val_float = max_q.getValueAs(target_unit).Value if hasattr(max_q, 'getValueAs') else float(max_q)
        else:
            max_val_float=max_q
        grp = App.ActiveDocument.getObject("BeamsResult")
        if not grp: return

        for b in grp.Group:
            if b.BaseBeam.Name in members_data and key in members_data[b.BaseBeam.Name]:
                d = members_data[b.BaseBeam.Name][key]

                # Get Values (Quantities)
                raw_quantities = d['values'][1]

                # Calculate scale
                scale_denom = max_val_float
                if scale_denom == 0: scale_denom = 1.0
                if key=="unity_check":
                    float_values=[q / scale_denom for q in raw_quantities]
                else:
                    float_values = [q.getValueAs(target_unit).Value / scale_denom for q in raw_quantities]

                if 'positions' in d:
                    vis_positions = d['positions']
                else:
                    # d['values'][0] is [0.0, ..., Length]
                    abs_pos = d['values'][0]
                    if len(abs_pos) > 0:
                        beam_len = abs_pos[-1]
                        if beam_len > 1e-9:
                            vis_positions = [p / beam_len for p in abs_pos]
                        else:
                            vis_positions = [0.0] * len(abs_pos)
                    else:
                        vis_positions = []

                unit_str = target_unit.replace('*', '·') if target_unit else ""  # Pretty formatting for UI
                # Pass to beam proxy (adding the unit string for the UI)
                print('float_values', float_values)

                b.Proxy.set_diagram(
                    vis_positions,
                    float_values,
                    max_val_float,
                    unit_str
                )
    def update_visualization(self, obj):
        for g in ["NodesResult", "BeamsResult"]:
            grp = App.ActiveDocument.getObject(g)
            if grp:
                for i in grp.Group:
                    if hasattr(i.ViewObject, "Proxy"):
                        i.ViewObject.Proxy.updateData(i, "ResultsUpdate")

    def onChanged(self, obj, prop):
        if not hasattr(self, 'flagInit') or self.flagInit or 'Restore' in obj.State:
            return
        elif prop in ["LoadCase", "DiagramType", "DiagramScale", "DeformationScale", "ShowNodeResults",
                      'ShowReactions']:
            # Only update visualization, don't recreate objects
            self._update_results(obj)
            self.update_visualization(obj)
        elif prop == "RunAnalysis" and obj.RunAnalysis:
            # Handle RunAnalysis property change
            self.run_analysis(obj)
            obj.RunAnalysis = False  # Reset after running

    def dumps(self):
        return None

    def loads(self, state):
        return None


class SolverViewProvider:
    def __init__(self, vobj):
        vobj.Proxy = self
        self.flagInit = True
        self.Object = vobj.Object
        self.setup_view_properties(vobj)
        self.flagInit = False

    def setup_view_properties(self, vobj):
        vobj.addProperty("App::PropertyColor", "DeformationColor", "Display", "Deformation color").DeformationColor = (
        0.0, 1.0, 0.0)
        vobj.addProperty("App::PropertyFloat", "NodeSize", "Display", "Node size").NodeSize = 2.0
        vobj.addProperty("App::PropertyBool", "ShowDeformedShape", "Display",
                         "Show deformed shape").ShowDeformedShape = True
        vobj.addProperty("App::PropertyBool", "ShowUndeformedShape", "Display",
                         "Show undeformed shape").ShowUndeformedShape = True

    def attach(self, vobj):
        from pivy import coin
        self.Object = vobj.Object
        self.root_node = coin.SoSeparator()
        vobj.addDisplayMode(self.root_node, "Default")

    def updateData(self, obj, prop):
        if prop in ["Results", "LoadCase", "DiagramType", "DiagramScale", "DeformationScale", "ResultsUpdate"]:
            if hasattr(obj.Proxy, "update_visualization"):
                obj.Proxy.update_visualization(obj)

    def getIcon(self):
        return SOLVER_ICON_PATH

    def onChanged(self, vobj, prop):
        if not hasattr(self, 'flagInit') or self.flagInit or not hasattr(self, "Object") or not self.Object:
            return
        if prop in ["DeformationColor", "NodeSize", "ShowDeformedShape", "ShowUndeformedShape"]:
            if hasattr(self.Object.Proxy, "update_visualization"):
                self.Object.Proxy.update_visualization(self.Object)

    def getDisplayModes(self, obj):
        return ["Default"]

    def getDefaultDisplayMode(self):
        return "Default"

    def setDisplayMode(self, mode):
        return mode

    def dumps(self):
        return None

    def loads(self, state):
        return None

    def canDragObjects(self):
        return False

    def canDropObjects(self):
        return False

    def setEdit(self, vobj, mode):
        """Called when the object is double-clicked in the tree view"""
        from ui.dialog_AnalysisSetup import show_analysis_setup
        show_analysis_setup()
        return True

    def unsetEdit(self, vobj, mode):
        """Called when editing is finished"""
        return False


def make_solver():
    doc = App.ActiveDocument
    if hasattr(doc, "Solver"): return doc.Solver
    sg = doc.addObject("App::DocumentObjectGroupPython", "Solver")
    Solver(sg)
    sg.Label = "Solver"
    from features.AnalysisGroup import get_analysis_group
    ag = get_analysis_group()
    if ag and sg not in ag.Group: ag.addObject(sg)
    if App.GuiUp: sg.ViewObject.Proxy = SolverViewProvider(sg.ViewObject)
    return sg


def run_analysis():
    """Trigger the analysis execution"""
    solver = make_solver()
    if solver:
        solver.RunAnalysis = True
        App.ActiveDocument.recompute()