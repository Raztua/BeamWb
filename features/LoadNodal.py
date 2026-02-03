# LoadNodal.py
import FreeCAD as App


import os
from features.FEMVisualization import FEMVisualization

# Constants
WORKBENCH_DIR = os.path.dirname(os.path.dirname(__file__))
ICON_DIR = os.path.join(WORKBENCH_DIR, "icons")
NODAL_LOAD_ICON_PATH = os.path.join(ICON_DIR, "beam_nodal_load.svg")

class NodalLoad:
    def __init__(self, obj):
        self.flagInit = True
        try:
            obj.Proxy = self
            obj.addProperty("App::PropertyString", "Type", "Base", "Load Type").Type = "NodalLoad"
            #obj.addProperty("App::PropertyLink", "LoadID", "Base", "Parent Load ID")
            obj.addProperty("App::PropertyLinkList", "Nodes", "Base", "Applied Nodes")
            obj.addProperty("App::PropertyVector", "Force", "Load", "Force vector (N)")
            obj.addProperty("App::PropertyVector", "Moment", "Load", "Moment vector (Nm)")
            obj.Force=App.Vector(0,0,0)
            obj.Moment = App.Vector(0, 0, 0)
            self.flagInit = False
            self.execute(obj)
        except Exception as e:
            App.Console.PrintError(f"Failed to initialize NodalLoad: {str(e)}\n")

    def execute(self, obj):
        """Called on recompute"""
        if 'Restore' in obj.State:
            return  # or do some special thing
        if hasattr(obj,"Type") and obj.Type=="NodalLoad" :
            self.update_visualization(obj)

    def onChanged(self, obj, prop):
        """Called when properties change"""
        if 'Restore' in obj.State:
            return
        if not hasattr(self,"flagInit"):
            return
        if self.flagInit:
            return
        if prop in ["Force", "Moment", "Nodes"]:  #loadid removed
            if hasattr(obj, "ViewObject") and obj.ViewObject:
                self.execute(obj)

    def update_visualization(self, obj):
        """Trigger view provider update instead of direct manipulation"""
        if hasattr(obj, 'ViewObject') and obj.ViewObject is not None:
            if hasattr(obj.ViewObject, 'Proxy') and obj.ViewObject.Proxy is not None:
                if hasattr(obj.ViewObject.Proxy, 'updateVisualization'):
                    obj.ViewObject.Proxy.updateVisualization(obj)

    def dumps(self):
        return None

    def loads(self, state):
        return None


class NodalLoadViewProvider():
    def __init__(self, vobj):
        vobj.Proxy = self
        self.Object = vobj.Object
        self.ViewObject = vobj
        if not (hasattr(vobj, "NodalLoadColor")):
            vobj.addProperty("App::PropertyColor", "NodalLoadColor", "Style",
                             "Color for all nodes in this group").NodalLoadColor = (1.0, 1.0, 0.0)
            vobj.addProperty("App::PropertyFloat", "NodalLoadScale", "Style",
                             "Scale factor for all nodes in this group").NodalLoadScale = 10.0
            vobj.addProperty("App::PropertyBool", "ShowLoads", "Display",
                             "Show loads visualization").ShowLoads = True


    def attach(self, vobj):
        self.Object = vobj.Object
        self.ViewObject = vobj
        if not (hasattr(vobj, "NodalLoadColor")):
            vobj.addProperty("App::PropertyColor", "NodalLoadColor", "Style",
                             "Color for all nodes in this group").NodalLoadColor = (1.0, 1.0, 0.0)
            vobj.addProperty("App::PropertyFloat", "NodalLoadScale", "Style",
                             "Scale factor for all nodes in this group").NodalLoadScale = 1.0
            vobj.addProperty("App::PropertyBool", "ShowLoads", "Display",
                             "Show loads visualization").ShowLoads = True
        from pivy import coin
        #create default display mode
        self.default_node=coin.SoSeparator()
        self.default_node.setName("Default")
        # Add display modes to view object
        vobj.addDisplayMode(self.default_node, "Default")
        #vobj.Proxy = self
        self.updateVisualization(self.Object)

    def updateData(self, obj, prop):
        """Called when object data changes"""
        if prop in ["Force", "Moment", "Nodes"]:  #loadid removed
            if hasattr(obj, "ViewObject") and obj.ViewObject:
                self.updateVisualization(obj)

    def updateVisualization(self,obj):
        try:
            if not hasattr(self, "Object"):
                return
            if not hasattr(self, "ViewObject"):
                return
            if not hasattr(self.ViewObject, "ShowLoads"):
                return
            if not hasattr(self, "default_node"):
                return
            self.default_node.removeAllChildren()
            # Validate nodes
            if not hasattr(obj, "Nodes") or not isinstance(obj.Nodes, (list, tuple)):
                return

            if self.ViewObject.ShowLoads==False:
                return
            for node in obj.Nodes:
                if not hasattr(node, "X"):
                    continue
                #try:
                node_pos = App.Vector(node.X, node.Y, node.Z)
                # Force visualization
                if hasattr(obj, "Force") and hasattr(obj.Force, "Length"):
                    if obj.Force.Length > 1e-6:
                        force_arrow = FEMVisualization.create_force_arrow(
                            obj.Force,node_pos,
                            scale= self.ViewObject.NodalLoadScale/100,
                            color= self.ViewObject.NodalLoadColor[0:3])
                        self.default_node.addChild(force_arrow)

                    # Moment visualization
                    if hasattr(obj, "Moment") and hasattr(obj.Moment, "Length"):
                        if obj.Moment.Length > 1e-6:
                            moment_symbol = FEMVisualization.create_moment_symbol(
                                obj.Moment,node_pos,
                                scale=0.5 * self.ViewObject.NodalLoadScale/100,
                                color=self.ViewObject.NodalLoadColor[0:3])
                            self.default_node.addChild(moment_symbol)

        except Exception as e:
            App.Console.PrintError(f"Visualization update failed: {str(e)}\n")

    def getIcon(self):
        return NODAL_LOAD_ICON_PATH

    def onChanged(self, vobj, prop):
        """Called when view provider properties change"""
        if not hasattr(self,"Object"):
            return
        if prop in ["NodalLoadColor", "NodalLoadScale","ShowLoads"]:
            self.updateVisualization(self.Object)

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
    
    def doubleClicked(self, vobj):
        """Handle double-click event"""
        from ui.dialog_NodalLoad import show_nodal_load_creator
        show_nodal_load_creator(nodal_load_to_modify=vobj.Object)
        return True
    def canDragObjects(self):
        return False

    def canDropObjects(self):
        return False
