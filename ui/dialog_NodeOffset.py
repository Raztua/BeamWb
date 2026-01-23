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
        self.form.resize(500, 500)  # Increased height for new options
        
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

        # Advanced options
        advanced_group = QtGui.QGroupBox("Advanced Options")
        advanced_layout = QtGui.QVBoxLayout()

        # Use existing node option
        self.use_existing_check = QtGui.QCheckBox("Use existing node if at same location")
        self.use_existing_check.setToolTip("If a node already exists at the offset location, use it instead of creating a new node")
        advanced_layout.addWidget(self.use_existing_check)

        # Duplicate beams option
        self.duplicate_beams_check = QtGui.QCheckBox("Duplicate attached structural elements")
        self.duplicate_beams_check.setToolTip("If two original nodes are connected by a beam, create the same beam between their offset nodes")
        advanced_layout.addWidget(self.duplicate_beams_check)

        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)

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

    def find_existing_node_at_location(self, x, y, z, tolerance=1e-6):
        """Find an existing node at the specified location within tolerance"""
        doc = App.ActiveDocument
        if not doc or not hasattr(doc, "Nodes") or not hasattr(doc.Nodes, "Group"):
            return None
            
        for node in doc.Nodes.Group:
            if (hasattr(node, "Type") and node.Type == "NodeFeature" and
                abs(node.X.Value - x) < tolerance and
                abs(node.Y.Value - y) < tolerance and
                abs(node.Z.Value - z) < tolerance):
                return node
        return None

    def get_node_beams(self, node):
        """Get all beams connected to a node"""
        beams = []
        doc = App.ActiveDocument
        if not doc or not hasattr(doc, "Beams") or not hasattr(doc.Beams, "Group"):
            return beams
            
        for beam in doc.Beams.Group:
            if (hasattr(beam, "Type") and beam.Type == "BeamFeature" and
                hasattr(beam, "StartNode") and hasattr(beam, "EndNode")):
                if beam.StartNode == node or beam.EndNode == node:
                    beams.append(beam)
        return beams

    def beam_exists_between_nodes(self, node1, node2):
        """Check if a beam already exists between two nodes"""
        doc = App.ActiveDocument
        if not doc or not hasattr(doc, "Beams") or not hasattr(doc.Beams, "Group"):
            return False
            
        for beam in doc.Beams.Group:
            if (hasattr(beam, "Type") and beam.Type == "BeamFeature" and
                hasattr(beam, "StartNode") and hasattr(beam, "EndNode")):
                if ((beam.StartNode == node1 and beam.EndNode == node2) or
                    (beam.StartNode == node2 and beam.EndNode == node1)):
                    return True
        return False

    def create_beam_between_nodes(self, start_node, end_node, section):
        """Create a beam between two nodes"""
        try:
            # Import the beam creation function
            from features.beams import BeamFeature, BeamViewProvider
            
            # Create beam object
            doc = App.ActiveDocument
            beam_group = make_beams_group()
            beam = doc.addObject("App::FeaturePython", "Beam")
            BeamFeature(beam)
            BeamViewProvider(beam.ViewObject)
            
            # Set beam properties
            beam.StartNode = start_node
            beam.EndNode = end_node
            beam.Section = section
            
            beam.Label = f"Beam_{start_node.Label}_to_{end_node.Label}"
            beam_group.addObject(beam)
            
            return beam
        except Exception as e:
            App.Console.PrintError(f"Error creating beam: {str(e)}\n")
            return None

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
            use_existing = self.use_existing_check.isChecked()
            duplicate_beams = self.duplicate_beams_check.isChecked()
            selected_section = None
            
            if create_beams:
                selected_section = self.get_selected_section()
                if not selected_section:
                    QtGui.QMessageBox.warning(self.form, "Warning", "Please select a valid section for beam creation.")
                    return False

            # Create mapping from original nodes to new/offset nodes
            node_mapping = {}
            created_nodes = []
            existing_nodes_used = 0

            for node in self.selected_nodes:
                x = getattr(node, "X", 0.0).Value + x_offset
                y = getattr(node, "Y", 0.0).Value + y_offset
                z = getattr(node, "Z", 0.0).Value + z_offset
                
                # Check if we should use existing node
                new_node = None
                if use_existing:
                    existing_node = self.find_existing_node_at_location(x, y, z)
                    if existing_node:
                        new_node = existing_node
                        existing_nodes_used += 1
                        App.Console.PrintMessage(f"Using existing node: {existing_node.Label} at ({x:.1f}, {y:.1f}, {z:.1f})\n")
                
                # Create new node if no existing node found or option disabled
                if not new_node:
                    new_node = create_node(X=x, Y=y, Z=z)
                    if new_node:
                        # Use the same naming convention as normal nodes (N001, N002, etc.)
                        new_node.Label = self.get_next_node_name()
                        created_nodes.append(new_node)

                if new_node:
                    node_mapping[node] = new_node

            # Create beams between original and offset nodes if requested
            beam_count = 0
            existing_beams_skipped = 0
            if create_beams and selected_section and node_mapping:
                beam_group = make_beams_group()
                for original_node, offset_node in node_mapping.items():
                    # Check if beam already exists between original and offset nodes
                    if self.beam_exists_between_nodes(original_node, offset_node):
                        App.Console.PrintMessage(f"Beam already exists between {original_node.Label} and {offset_node.Label}, skipping creation\n")
                        existing_beams_skipped += 1
                    else:
                        beam = self.create_beam_between_nodes(original_node, offset_node, selected_section)
                        if beam:
                            beam_count += 1

            # Duplicate beams between offset nodes if requested
            duplicated_beam_count = 0
            existing_duplicated_beams_skipped = 0
            if duplicate_beams and len(node_mapping) >= 2:
                # Use a set to track processed beam pairs using node names (which are sortable)
                processed_pairs = set()
                
                for original_node1, offset_node1 in node_mapping.items():
                    beams1 = self.get_node_beams(original_node1)
                    for beam in beams1:
                        other_original_node = beam.StartNode if beam.EndNode == original_node1 else beam.EndNode
                        if other_original_node in node_mapping:
                            # Create a unique key for the pair using sorted node names
                            node_names = sorted([original_node1.Label, other_original_node.Label])
                            pair_key = tuple(node_names)
                            
                            if pair_key not in processed_pairs:
                                offset_node2 = node_mapping[other_original_node]
                                
                                # Check if beam already exists between offset nodes
                                if self.beam_exists_between_nodes(offset_node1, offset_node2):
                                    App.Console.PrintMessage(f"Beam already exists between {offset_node1.Label} and {offset_node2.Label}, skipping duplication\n")
                                    existing_duplicated_beams_skipped += 1
                                else:
                                    # Create beam between offset nodes using the same section
                                    if hasattr(beam, "Section") and beam.Section:
                                        new_beam = self.create_beam_between_nodes(offset_node1, offset_node2, beam.Section)
                                        if new_beam:
                                            duplicated_beam_count += 1
                                            new_beam.Label = f"Beam_{offset_node1.Label}_to_{offset_node2.Label}_copy"
                                processed_pairs.add(pair_key)

            
            if len(node_mapping) > 0:
                # Show success message
                new_nodes_count = len(created_nodes)
                message = f"Created {new_nodes_count} new node(s)"
                if existing_nodes_used > 0:
                    message += f", used {existing_nodes_used} existing node(s)"
                if beam_count > 0:
                    message += f", created {beam_count} connecting beam(s)"
                if existing_beams_skipped > 0:
                    message += f", skipped {existing_beams_skipped} existing beam(s)"
                if duplicated_beam_count > 0:
                    message += f", duplicated {duplicated_beam_count} beam(s)"
                if existing_duplicated_beams_skipped > 0:
                    message += f", skipped {existing_duplicated_beams_skipped} duplicated beam(s) (already exist)"
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
                App.ActiveDocument.recompute()
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