class BeamWB:
    def __init__(self):
        pass

    def Initialize(self):
        # This will be called when the workbench is loaded
        pass

    def GetClassName(self):
        return "Gui::PythonWorkbench"

# The workbench will be created when FreeCAD starts
FreeCAD.addImportType("Beam Workbench", "*")