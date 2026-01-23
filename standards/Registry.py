import FreeCAD as App

class StandardsRegistry:
    _standards = {}

    @classmethod
    def register(cls, standard_class):
        """Register a new standard class"""
        if hasattr(standard_class, 'name'):
            cls._standards[standard_class.name] = standard_class
            App.Console.PrintMessage(f"CodeCheck: Registered '{standard_class.name}'\n")

    @classmethod
    def get_standard(cls, name):
        """Get the class for a specific standard name"""
        return cls._standards.get(name)

    @classmethod
    def get_available_names(cls):
        """Get list of registered names"""
        return list(cls._standards.keys())

# Global instance not strictly needed as we use class methods,
# but good for ensuring import runs