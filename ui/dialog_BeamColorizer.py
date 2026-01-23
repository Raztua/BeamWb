# ui/dialog_BeamColorizer.py
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtGui, QtCore
from features.beams import get_all_beams
import random

class BeamColorizerTaskPanel:
    """Task panel for coloring beams based on properties"""
    
    def __init__(self):
        self.form = QtGui.QWidget()
        self.form.setWindowTitle("Beam Colorizer")
        self.form.resize(600, 700)
        
        # Store color mappings
        self.color_mappings = {}
        self.color_pickers = {}  # Store references to color picker widgets
        
        self.setup_ui()
        self.load_beams()
        
    def setup_ui(self):
        # Main layout
        main_layout = QtGui.QVBoxLayout(self.form)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # Title
        title = QtGui.QLabel("Beam Colorizer - Color Beams by Property")
        title.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        main_layout.addWidget(title)

        # Property selection section
        prop_group = QtGui.QGroupBox("Property Selection")
        prop_layout = QtGui.QVBoxLayout(prop_group)
        
        prop_layout.addWidget(QtGui.QLabel("Select property to color by:"))
        self.property_combobox = QtGui.QComboBox()
        self.property_combobox.addItem("Section", "section")
        self.property_combobox.addItem("Material", "material") 
        self.property_combobox.addItem("Member Releases", "releases")
        self.property_combobox.addItem("Buckling Length", "buckling")
        self.property_combobox.addItem("Effective Length", "effective")
        self.property_combobox.addItem("Member Type", "member_type")
        
        self.property_combobox.currentIndexChanged.connect(self.on_property_changed)
        prop_layout.addWidget(self.property_combobox)
        
        # Buckling length precision
        buckling_layout = QtGui.QHBoxLayout()
        buckling_layout.addWidget(QtGui.QLabel("Rounding precision (meters):"))
        self.buckling_precision = QtGui.QDoubleSpinBox()
        self.buckling_precision.setRange(0.01, 10.0)
        self.buckling_precision.setValue(0.1)
        self.buckling_precision.setSingleStep(0.1)
        buckling_layout.addWidget(self.buckling_precision)
        buckling_layout.addStretch()
        
        # Create a widget to contain the buckling layout for easy show/hide
        self.buckling_widget = QtGui.QWidget()
        self.buckling_widget.setLayout(buckling_layout)
        prop_layout.addWidget(self.buckling_widget)
        
        main_layout.addWidget(prop_group)

        # Color mapping section
        self.mapping_group = QtGui.QGroupBox("Color Mapping")
        mapping_layout = QtGui.QVBoxLayout(self.mapping_group)
        
        # Instructions
        instructions = QtGui.QLabel("Click on color buttons to customize colors for each property value:")
        instructions.setStyleSheet("color: gray; font-size: 11px;")
        mapping_layout.addWidget(instructions)
        
        # Scroll area for color mappings
        self.scroll_area = QtGui.QScrollArea()
        self.scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scroll_widget = QtGui.QWidget()
        self.scroll_layout = QtGui.QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setContentsMargins(5, 5, 5, 5)
        self.scroll_layout.setSpacing(3)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setMinimumHeight(300)
        
        mapping_layout.addWidget(self.scroll_area)
        main_layout.addWidget(self.mapping_group)

        # Action buttons
        button_layout = QtGui.QHBoxLayout()
        
        self.generate_colors_btn = QtGui.QPushButton("Generate Colors")
        self.generate_colors_btn.clicked.connect(self.generate_colors)
        
        self.apply_colors_btn = QtGui.QPushButton("Apply Colors")
        self.apply_colors_btn.clicked.connect(self.apply_colors)
        self.apply_colors_btn.setStyleSheet("font-weight: bold;")
        
        self.reset_colors_btn = QtGui.QPushButton("Reset to Original")
        self.reset_colors_btn.clicked.connect(self.reset_colors)
        
        button_layout.addWidget(self.generate_colors_btn)
        button_layout.addWidget(self.apply_colors_btn)
        button_layout.addWidget(self.reset_colors_btn)
        main_layout.addLayout(button_layout)

        # Status
        self.status_label = QtGui.QLabel("Select a property to begin")
        self.status_label.setStyleSheet("color: gray; font-style: italic;")
        main_layout.addWidget(self.status_label)

        main_layout.addStretch()
        
        # Hide buckling precision by default
        self.buckling_widget.setVisible(False)

    def on_property_changed(self):
        """Handle property selection change"""
        prop = self.property_combobox.currentData()
        
        # Show/hide buckling precision
        show_precision = prop in ["buckling", "effective"]
        self.buckling_widget.setVisible(show_precision)
        
        self.load_beams()

    def load_beams(self):
        """Load beams and extract unique values for selected property"""
        beams = get_all_beams()
        if not beams:
            self.status_label.setText("No beams found in the document")
            self.create_empty_mapping_ui()
            return
            
        prop = self.property_combobox.currentData()
        unique_values = self.extract_unique_values(beams, prop)
        
        self.create_color_mapping_ui(unique_values)
        self.status_label.setText(f"Found {len(unique_values)} unique values for {prop}")

    def create_empty_mapping_ui(self):
        """Create empty mapping UI when no beams found"""
        self.clear_scroll_layout()
        
        no_beams_label = QtGui.QLabel("No beams found in the document")
        no_beams_label.setStyleSheet("color: gray; font-style: italic; padding: 20px;")
        no_beams_label.setAlignment(QtCore.Qt.AlignCenter)
        self.scroll_layout.addWidget(no_beams_label)

    def clear_scroll_layout(self):
        """Properly clear the scroll layout"""
        # Clear color pickers dictionary
        self.color_pickers.clear()
        
        # Remove all items from layout
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                # Recursively clear sub-layouts
                self.clear_sublayout(item.layout())

    def clear_sublayout(self, layout):
        """Clear a sub-layout recursively"""
        if layout:
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                elif item.layout():
                    self.clear_sublayout(item.layout())

    def extract_unique_values(self, beams, property_type):
        """Extract unique values for the selected property"""
        unique_values = set()
        
        for beam in beams:
            try:
                if property_type == "section":
                    value = beam.Section.Label if beam.Section else "No Section"
                    unique_values.add(value)
                    
                elif property_type == "material":
                    value = beam.Material.Label if beam.Material else "No Material"
                    unique_values.add(value)
                    
                elif property_type == "releases":
                    value = beam.MemberRelease.Label if beam.MemberRelease else "No Releases"
                    unique_values.add(value)
                    
                elif property_type == "buckling":
                    # Round buckling length to reduce number of unique values
                    precision = self.buckling_precision.value()
                    by = round(beam.BucklingLengthY.Value / 1000.0 / precision) * precision  # Convert to meters
                    bz = round(beam.BucklingLengthZ.Value / 1000.0 / precision) * precision
                    value = f"Y={by:.2f}m, Z={bz:.2f}m"
                    unique_values.add(value)
                    
                elif property_type == "effective":
                    # Round effective length to reduce number of unique values
                    precision = self.buckling_precision.value()
                    ey = round(beam.EffectiveLengthY.Value / 1000.0 / precision) * precision  # Convert to meters
                    ez = round(beam.EffectiveLengthZ.Value / 1000.0 / precision) * precision
                    value = f"Y={ey:.2f}m, Z={ez:.2f}m"
                    unique_values.add(value)
                    
                elif property_type == "member_type":
                    value = getattr(beam, 'MemberType', 'normal')
                    unique_values.add(value)
                    
            except Exception as e:
                App.Console.PrintWarning(f"Error processing beam {beam.Label}: {str(e)}\n")
                continue
        
        return sorted(list(unique_values))

    def create_color_mapping_ui(self, unique_values):
        """Create the color mapping UI for unique values"""
        # Clear existing layout properly
        self.clear_scroll_layout()
        self.color_mappings.clear()
        self.color_pickers.clear()
        
        if not unique_values:
            no_data_label = QtGui.QLabel("No unique values found for selected property")
            no_data_label.setStyleSheet("color: gray; font-style: italic; padding: 20px;")
            no_data_label.setAlignment(QtCore.Qt.AlignCenter)
            self.scroll_layout.addWidget(no_data_label)
            return
        
        # Create header
        header_widget = QtGui.QWidget()
        header_layout = QtGui.QHBoxLayout(header_widget)
        header_layout.setContentsMargins(5, 2, 5, 2)
        
        header_layout.addWidget(QtGui.QLabel("Property Value"), 2)
        header_layout.addWidget(QtGui.QLabel("Color"), 1)
        header_layout.addWidget(QtGui.QLabel("Count"), 1)
        
        header_widget.setStyleSheet("font-weight: bold; background-color: #f0f0f0; padding: 5px;")
        self.scroll_layout.addWidget(header_widget)
        
        # Add separator
        separator = QtGui.QFrame()
        separator.setFrameShape(QtGui.QFrame.HLine)
        separator.setFrameShadow(QtGui.QFrame.Sunken)
        self.scroll_layout.addWidget(separator)
        
        # Create color pickers for each unique value
        beams = get_all_beams()
        
        for value in unique_values:
            value_widget = QtGui.QWidget()
            value_layout = QtGui.QHBoxLayout(value_widget)
            value_layout.setContentsMargins(5, 3, 5, 3)
            
            # Value label
            value_label = QtGui.QLabel(str(value))
            value_label.setToolTip(str(value))
            value_label.setWordWrap(True)
            value_layout.addWidget(value_label, 2)
            
            # Color picker
            color_picker = QtGui.QPushButton()
            color_picker.setFixedSize(60, 25)
            
            # Generate initial random color
            initial_color = self.generate_random_color()
            color_picker.setStyleSheet(f"background-color: {initial_color.name()}; border: 1px solid #666;")
            
            # FIX: Use partial instead of lambda to avoid argument issues
            from functools import partial
            color_picker.clicked.connect(partial(self.choose_color, color_picker, value))
            
            value_layout.addWidget(color_picker, 1)
            
            # Store the color picker reference
            self.color_pickers[value] = color_picker
            
            # Count of beams with this value
            count = self.count_beams_with_value(beams, value)
            count_label = QtGui.QLabel(str(count))
            count_label.setAlignment(QtCore.Qt.AlignCenter)
            value_layout.addWidget(count_label, 1)
            
            self.scroll_layout.addWidget(value_widget)
            
            # Store the mapping
            self.color_mappings[value] = initial_color
        
        # Add stretch at the end
        self.scroll_layout.addStretch()

    def count_beams_with_value(self, beams, target_value):
        """Count how many beams have the target value"""
        prop = self.property_combobox.currentData()
        count = 0
        
        for beam in beams:
            try:
                current_value = self.get_beam_property_value(beam, prop)
                if current_value == target_value:
                    count += 1
            except:
                continue
                
        return count

    def get_beam_property_value(self, beam, property_type):
        """Get the property value for a beam"""
        if property_type == "section":
            return beam.Section.Label if beam.Section else "No Section"
        elif property_type == "material":
            return beam.Material.Label if beam.Material else "No Material"
        elif property_type == "releases":
            return beam.MemberRelease.Label if beam.MemberRelease else "No Releases"
        elif property_type == "buckling":
            precision = self.buckling_precision.value()
            by = round(beam.BucklingLengthY.Value / 1000.0 / precision) * precision
            bz = round(beam.BucklingLengthZ.Value / 1000.0 / precision) * precision
            return f"Y={by:.2f}m, Z={bz:.2f}m"
        elif property_type == "effective":
            precision = self.buckling_precision.value()
            ey = round(beam.EffectiveLengthY.Value / 1000.0 / precision) * precision
            ez = round(beam.EffectiveLengthZ.Value / 1000.0 / precision) * precision
            return f"Y={ey:.2f}m, Z={ez:.2f}m"
        elif property_type == "member_type":
            return getattr(beam, 'MemberType', 'normal')
            
        return "Unknown"

    def generate_random_color(self):
        """Generate a random color"""
        return QtGui.QColor(
            random.randint(50, 255),
            random.randint(50, 255), 
            random.randint(50, 255)
        )

    def choose_color(self, color_picker, value):
        """Let user choose a color for a value"""
        current_color = self.color_mappings.get(value, self.generate_random_color())
        color = QtGui.QColorDialog.getColor(current_color, self.form)
        if color.isValid():
            color_picker.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #666;")
            self.color_mappings[value] = color

    def generate_colors(self):
        """Generate new random colors for all values"""
        for value in self.color_mappings:
            new_color = self.generate_random_color()
            self.color_mappings[value] = new_color
        
        # Update all color picker buttons
        for value, color_picker in self.color_pickers.items():
            if value in self.color_mappings:
                color = self.color_mappings[value]
                color_picker.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #666;")
        
        self.status_label.setText("New colors generated - click 'Apply Colors' to update beams")

    def apply_colors(self):
        """Apply the color mapping to all beams"""
        try:
            beams = get_all_beams()
            prop = self.property_combobox.currentData()
            
            colored_count = 0
            for beam in beams:
                try:
                    value = self.get_beam_property_value(beam, prop)
                    if value in self.color_mappings:
                        color = self.color_mappings[value]
                        
                        # Convert QColor to FreeCAD color tuple (0-1 range)
                        fc_color = (color.red()/255.0, color.green()/255.0, color.blue()/255.0)
                        
                        # Set beam color
                        if hasattr(beam, 'ViewObject') and beam.ViewObject:
                            beam.ViewObject.ShapeColor = fc_color
                            colored_count += 1
                except Exception as e:
                    App.Console.PrintWarning(f"Could not color beam {beam.Label}: {str(e)}\n")
                    continue

            self.status_label.setText(f"Colors applied to {colored_count} beams successfully")
            
        except Exception as e:
            self.status_label.setText(f"Error applying colors: {str(e)}")
            QtGui.QMessageBox.critical(self.form, "Error", f"Failed to apply colors: {str(e)}")

    def reset_colors(self):
        """Reset all beams to their original colors"""
        try:
            beams = get_all_beams()
            reset_count = 0
            
            for beam in beams:
                if hasattr(beam, 'ViewObject') and beam.ViewObject:
                    # Reset to default beam color (reddish)
                    beam.ViewObject.ShapeColor = (0.8, 0.2, 0.2)
                    reset_count += 1

            self.status_label.setText(f"Reset {reset_count} beams to original colors")
            
        except Exception as e:
            self.status_label.setText(f"Error resetting colors: {str(e)}")
            QtGui.QMessageBox.critical(self.form, "Error", f"Failed to reset colors: {str(e)}")

    def getStandardButtons(self):
        """Return standard buttons for task panel"""
        return QtGui.QDialogButtonBox.Close

    def clicked(self, button):
        """Handle button clicks"""
        App.ActiveDocument.recompute()
        if button == QtGui.QDialogButtonBox.Close:
            Gui.Control.closeDialog()

    def reject(self):
        """Cancel operation"""
        return True

    def accept(self):
        """Apply changes and close"""
        Gui.Control.closeDialog()
        return True


def show_beam_colorizer():
    """Show the beam colorizer task panel"""
    # Close any existing task panel first
    if hasattr(Gui, 'Control') and Gui.Control.activeDialog():
        Gui.Control.closeDialog()
    
    panel = BeamColorizerTaskPanel()
    Gui.Control.showDialog(panel)
    return panel