# ui/dialog_NodeOffset.py
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtGui, QtCore
from features.nodes import create_node, get_all_nodes
from features.beams import make_beams_group
import re


class NodeOffsetTaskPanel:
    """Task panel for creating offset nodes"""

    def __init__(self):
        self.form = QtGui.QWidget()
        self.form.setWindowTitle("Offset Nodes")
        self.form.resize(500, 450)  # Increased height for new options
        
        self.selected_nodes = []
        self.selection_callback = None
        self.is_picking = False
        self.available_sections = []
        
        self.setup_ui()
        self.load_available_sections()

    def setup_ui(self):
        layout = QtGui.QVBoxLayout(self.form)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Title
        title = QtGui.QLabel("Create Offset Nodes")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)

        # Node selection
        selection_group = QtGui.QGroupBox("Base Nodes Selection")
        selection_layout = QtGui.QVBoxLayout()

        # Selection info
        self.selection_info = QtGui.QLabel("No nodes selected")
        self.selection_info.setStyleSheet("font-weight: bold; color: blue;")
        selection_layout.addWidget(self.selection_info)

        # Node list
        self.node_list = QtGui.QListWidget()
        self.node_list.setSelectionMode(QtGui.QListWidget.ExtendedSelection)
        selection_layout.addWidget(self.node_list)

        # Selection buttons
        button_layout = QtGui.QHBoxLayout()
        self.pick_button = QtGui.QPushButton("Pick Base Nodes")
        self.pick_button.clicked.connect(self.toggle_picking)
        self.clear_button = QtGui.QPushButton("Clear Selection")
        self.clear_button.clicked.connect(self.clear_selection)
        self.select_all_btn = QtGui.QPushButton("Select All")
        self.select_all_btn.clicked.connect(self.select_all_nodes)

        button_layout.addWidget(self.pick_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.select_all_btn)
        selection_layout.addLayout(button_layout)

        selection_group.setLayout(selection_layout)
        layout.addWidget(selection_group)

        # Offset settings
        offset_group = QtGui.QGroupBox("Offset Settings (mm)")
        offset_layout = QtGui.QGridLayout()

        offset_layout.addWidget(QtGui.QLabel("X Offset:"), 0, 0)
        self.x_offset = QtGui.QLineEdit()
        self.x_offset.setPlaceholderText("Offset in X direction")
        self.x_offset.setText("0.0")
        offset_layout.addWidget(self.x_offset, 0, 1)

        offset_layout.addWidget(QtGui.QLabel("Y Offset:"), 1, 0)
        self.y_offset = QtGui.QLineEdit()
        self.y_offset.setPlaceholderText("Offset in Y direction")
        self.y_offset.setText("0.0")
        offset_layout.addWidget(self.y_offset, 1, 1)

        offset_layout.addWidget(QtGui.QLabel("Z Offset:"), 2, 0)
        self.z_offset = QtGui.QLineEdit()
        self.z_offset.setPlaceholderText("Offset in Z direction")
        self.z_offset.setText("0.0")
        offset_layout.addWidget(self.z_offset, 2, 1)

        offset_group.setLayout(offset_layout)
        layout.addWidget(offset_group)

        # Beam creation options
        self.beam_group = QtGui.QGroupBox("Beam Creation")
        beam_layout = QtGui.QGridLayout()

        # Checkbox for beam creation
        self.create_beams_check = QtGui.QCheckBox("Create beams between original and offset nodes")
        self.create_beams_check.stateChanged.connect(self.on_beam_creation_toggled)
        beam_layout.addWidget(self.create_beams_check, 0, 0, 1, 2)

        # Section selection
        beam_layout.addWidget(QtGui.QLabel("Section:"), 1, 0)
        self.section_combo = QtGui.QComboBox()
        self.section_combo.setEnabled(False)
        beam_layout.addWidget(self.section_combo, 1, 1)

        self.beam_group.setLayout(beam_layout)
        layout.addWidget(self.beam_group)

        layout.addStretch()

    def load_available_sections(self):
        """Load available sections from the document"""
        self.available_sections = []
        self.section_combo.clear()
        
        doc = App.ActiveDocument
        if not doc:
            return
            
        # Check if sections group exists
        if hasattr(doc, "Sections") and hasattr(doc.Sections, "Group"):
            for obj in doc.Sections.Group:
                if hasattr(obj, "Label"):
                    self.available_sections.append(obj)
                    # Store section object in combo box using user data
                    self.section_combo.addItem(obj.Label)
        
        # Enable/disable beam creation based on available sections
        has_sections = len(self.available_sections) > 0
        self.create_beams_check.setEnabled(has_sections)
        
        if not has_sections:
            self.create_beams_check.setToolTip("No sections available in the document. Create sections first.")
            self.section_combo.addItem("No sections available")
            self.section_combo.setEnabled(False)
        else:
            self.create_beams_check.setToolTip("")
            self.section_combo.setEnabled(False)  # Will be enabled when checkbox is checked

        # Debug output to verify sections are loaded
        App.Console.PrintMessage(f"Loaded {len(self.available_sections)} sections\n")
        for i, section in enumerate(self.available_sections):
            App.Console.PrintMessage(f"  {i}: {section.Label}\n")

    def on_beam_creation_toggled(self, state):
        """Enable/disable section selection based on checkbox state"""
        has_sections = len(self.available_sections) > 0
        self.section_combo.setEnabled(state == QtCore.Qt.Checked and has_sections)

    def get_selected_section(self):
        """Get the currently selected section object"""
        if not self.available_sections:
            return None
            
        index = self.section_combo.currentIndex()
        if 0 <= index < len(self.available_sections):
            return self.available_sections[index]
        return None

    def get_next_node_name(self):
        """Generate the next available node name (N001, N002, etc.)"""
        existing_names = []
        doc = App.ActiveDocument
        
        if doc and hasattr(doc, "Nodes") and hasattr(doc.Nodes, "Group"):
            for obj in doc.Nodes.Group:
                if hasattr(obj, "Label") and obj.Label:
                    existing_names.append(obj.Label)

        # Find the highest existing number
        max_number = 0
        pattern = re.compile(r'^N(\d+)$', re.IGNORECASE)

        for name in existing_names:
            match = pattern.match(name)
            if match:
                number = int(match.group(1))
                if number > max_number:
                    max_number = number

        return f"N{max_number + 1:03d}"

    def toggle_picking(self):
        """Toggle picking mode on/off"""
        if self.is_picking:
            self.stop_picking()
        else:
            self.start_picking()

    def start_picking(self):
        """Start picking nodes"""
        if self.selection_callback:
            Gui.Selection.removeObserver(self.selection_callback)

        self.pick_button.setStyleSheet("font-weight: bold; background-color: lightgreen")
        self.pick_button.setText("Picking... Click to stop")
        self.is_picking = True

        self.selection_callback = NodeSelectionCallback(self)
        Gui.Selection.addObserver(self.selection_callback)
        Gui.Selection.clearSelection()

    def stop_picking(self):
        """Stop picking nodes"""
        if self.selection_callback:
            Gui.Selection.removeObserver(self.selection_callback)
            self.selection_callback = None

        self.pick_button.setStyleSheet("")
        self.pick_button.setText("Pick Base Nodes")
        self.is_picking = False

    def process_selection(self, doc_name, obj_name):
        """Process the selected object"""
        try:
            doc = App.getDocument(doc_name)
            if not doc:
                return

            obj = doc.getObject(obj_name)
            if not obj:
                return

            # Check if it's a node feature
            if hasattr(obj, "Type") and obj.Type == "NodeFeature":
                if obj not in self.selected_nodes:
                    self.selected_nodes.append(obj)
                    self.update_display()
            else:
                print("Selected object is not a NodeFeature")

        except Exception as e:
            print(f"Error processing selection: {e}")

    def clear_selection(self):
        """Clear the node selection"""
        self.selected_nodes = []
        self.update_display()

    def select_all_nodes(self):
        """Select all nodes in the document"""
        self.selected_nodes = get_all_nodes()
        self.update_display()

    def update_display(self):
        """Update the display based on current selection"""
        # Update node list
        self.node_list.clear()
        for node in self.selected_nodes:
            x = getattr(node, "X", 0.0)
            y = getattr(node, "Y", 0.0)
            z = getattr(node, "Z", 0.0)
            
            item_text = f"{node.Label} - ({x.Value:.1f}, {y.Value:.1f}, {z.Value:.1f}) mm"
            self.node_list.addItem(item_text)

        # Update selection info
        count = len(self.selected_nodes)
        self.selection_info.setText(f"{count} base node(s) selected")

    def create_beam_between_nodes(self, start_node, end_node, section):
        """Create a beam between two nodes"""
        try:
            # Import the beam creation function
            from features.beams import create_beam
            
            # Create the beam
            beam = create_beam(start_node, end_node, section)
            if beam:
                beam.Label = f"Beam_{start_node.Label}_to_{end_node.Label}"
                return beam
            return None
        except Exception as e:
            App.Console.PrintError(f"Error creating beam: {str(e)}\n")
            return None

    def create_offset_nodes(self):
        """Create offset nodes from selected base nodes"""
        if not self.selected_nodes:
            QtGui.QMessageBox.warning(self.form, "Warning", "Please select at least one base node.")
            return False

        try:
            x_offset = float(self.x_offset.text()) if self.x_offset.text() else 0.0
            y_offset = float(self.y_offset.text()) if self.y_offset.text() else 0.0
            z_offset = float(self.z_offset.text()) if self.z_offset.text() else 0.0
            
            create_beams = self.create_beams_check.isChecked()
            selected_section = None
            
            if create_beams:
                selected_section = self.get_selected_section()
                if not selected_section:
                    QtGui.QMessageBox.warning(self.form, "Warning", "Please select a valid section for beam creation.")
                    return False

            created_nodes = []
            for node in self.selected_nodes:
                x = getattr(node, "X", 0.0).Value + x_offset
                y = getattr(node, "Y", 0.0).Value + y_offset
                z = getattr(node, "Z", 0.0).Value + z_offset
                
                new_node = create_node(X=x, Y=y, Z=z)
                if new_node:
                    # Use the same naming convention as normal nodes (N001, N002, etc.)
                    new_node.Label = self.get_next_node_name()
                    created_nodes.append((node, new_node))  # Store original and new node

            # Create beams if requested
            beam_count = 0
            if create_beams and selected_section and created_nodes:
                beam_group = make_beams_group()
                for original_node, new_node in created_nodes:
                    beam = self.create_beam_between_nodes(original_node, new_node, selected_section)
                    if beam:
                        beam_count += 1

            
            if len(created_nodes) > 0:
                # Show success message
                message = f"Created {len(created_nodes)} offset node(s)"
                if beam_count > 0:
                    message += f" and {beam_count} beam(s)"
                message += " successfully!"
                QtGui.QMessageBox.information(self.form, "Success", message)
                
                # Clear selection after successful creation
                self.clear_selection()
                return True
            else:
                return False

        except ValueError:
            QtGui.QMessageBox.warning(self.form, "Input Error", 
                                    "Please enter valid numeric values for offsets.")
            return False

    def apply_changes(self):
        """Apply button handler - create offset nodes"""
        return self.create_offset_nodes()

    def getStandardButtons(self):
        """Return standard buttons for task panel"""
        return QtGui.QDialogButtonBox.Apply | QtGui.QDialogButtonBox.Close

    def clicked(self, button):
        """Handle button clicks"""
        if button == QtGui.QDialogButtonBox.Apply:
            if self.apply_changes():
                # Keep the dialog open for creating more offset nodes
                pass
        elif button == QtGui.QDialogButtonBox.Close:
            self.stop_picking()
            Gui.Control.closeDialog()

    def reject(self):
        """Cancel operation"""
        self.stop_picking()
        return True

    def accept(self):
        """Apply changes and close"""
        self.stop_picking()
        if self.apply_changes():
            Gui.Control.closeDialog()
            return True
        return False


class NodeSelectionCallback:
    """Callback class for handling node selection events"""

    def __init__(self, task_panel):
        self.task_panel = task_panel

    def addSelection(self, doc_name, obj_name, sub_name, pos):
        """Called when an object is selected"""
        self.task_panel.process_selection(doc_name, obj_name)


def show_node_offset():
    """Show the node offset task panel"""
    # Close any existing task dialog first
    if Gui.Control.activeDialog():
        Gui.Control.closeDialog()
    
    panel = NodeOffsetTaskPanel()
    Gui.Control.showDialog(panel)