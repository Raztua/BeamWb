# ui/dialog_ItemLabeling.py
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtGui, QtCore
from features.nodes import get_all_nodes
from features.beams import get_all_beams

class ItemLabelingTaskPanel:
    """Task panel for labeling nodes and beams"""

    def __init__(self):
        self.form = QtGui.QWidget()
        self.form.setWindowTitle("Item Labeling")
        self.form.resize(500, 500)
        
        self.setup_ui()

    def setup_ui(self):
        layout = QtGui.QVBoxLayout(self.form)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Title
        title = QtGui.QLabel("Item Labeling - Nodes and Beams")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)

        # Beam labeling section
        beam_group = QtGui.QGroupBox("Beam Labeling")
        beam_layout = QtGui.QVBoxLayout()

        # Beam label options combobox
        beam_options_layout = QtGui.QVBoxLayout()
        
        beam_options_layout.addWidget(QtGui.QLabel("Select information to display:"))
        self.beam_combobox = QtGui.QComboBox()
        self.beam_combobox.addItem("None", "none")
        self.beam_combobox.addItem("Beam Name", "name")
        self.beam_combobox.addItem("Material Group Name", "material")
        self.beam_combobox.addItem("Section Name", "section")
        self.beam_combobox.addItem("Release Name", "release")
        self.beam_combobox.addItem("Buckling Length (m)", "buckling")
        self.beam_combobox.addItem("Effective Length (m)", "effective")
        self.beam_combobox.addItem("All Information", "all")
        
        beam_options_layout.addWidget(self.beam_combobox)
        beam_options_layout.addStretch()
        beam_group.setLayout(beam_options_layout)
        layout.addWidget(beam_group)

        # Node labeling section
        node_group = QtGui.QGroupBox("Node Labeling")
        node_layout = QtGui.QVBoxLayout()
        
        # Node label options combobox
        node_options_layout = QtGui.QVBoxLayout()
        
        node_options_layout.addWidget(QtGui.QLabel("Select information to display:"))
        self.node_combobox = QtGui.QComboBox()
        self.node_combobox.addItem("None", "none")
        self.node_combobox.addItem("Node Label", "label")
        self.node_combobox.addItem("Node Position (X,Y,Z in m)", "position")
        self.node_combobox.addItem("Boundary Condition Label", "boundary")

        
        node_options_layout.addWidget(self.node_combobox)
        node_options_layout.addStretch()
        node_group.setLayout(node_options_layout)
        layout.addWidget(node_group)

        # Text size and styling
        style_group = QtGui.QGroupBox("Text Style")
        style_layout = QtGui.QGridLayout()
        
        style_layout.addWidget(QtGui.QLabel("Text Size:"), 0, 0)
        self.text_size = QtGui.QDoubleSpinBox()
        self.text_size.setRange(0, 500.0)
        self.text_size.setValue(100.0)
        self.text_size.setSuffix(" mm")
        style_layout.addWidget(self.text_size, 0, 1)
        
        style_layout.addWidget(QtGui.QLabel("Text Offset:"), 1, 0)
        self.text_offset = QtGui.QDoubleSpinBox()
        self.text_offset.setRange(-1000.0, 1000.0)
        self.text_offset.setValue(50.0)
        self.text_offset.setSuffix(" mm")
        style_layout.addWidget(self.text_offset, 1, 1)
        
        style_group.setLayout(style_layout)
        layout.addWidget(style_group)

        # Action buttons
        button_layout = QtGui.QHBoxLayout()
        
        self.apply_button = QtGui.QPushButton("Apply Labels")
        self.apply_button.clicked.connect(self.apply_labels)
        self.apply_button.setStyleSheet("font-weight: bold;")
        
        self.clear_button = QtGui.QPushButton("Clear All Labels")
        self.clear_button.clicked.connect(self.clear_labels)
        
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.clear_button)
        layout.addLayout(button_layout)

        layout.addStretch()

    def get_beam_text(self, beam):
        """Generate text for beam based on selected option"""
        option = self.beam_combobox.currentData()
        
        if option == "none":
            return ""
        elif option == "name":
            return f"{beam.Label}"
        elif option == "material":
            return f"{beam.Material.Label}" if beam.Material else ""
        elif option == "section":
            return f"{beam.Section.Label}" if beam.Section else ""
        elif option == "release":
            return f"{beam.MemberRelease.Label}" if beam.MemberRelease else ""
        elif option == "buckling":
            buckling_y = beam.BucklingLengthY.Value / 1000.0  # Convert to meters
            buckling_z = beam.BucklingLengthZ.Value / 1000.0  # Convert to meters
            return f"Buckling L: Y={buckling_y:.2f}m, Z={buckling_z:.2f}m"
        elif option == "effective":
            effective_y = beam.EffectiveLengthY.Value / 1000.0  # Convert to meters
            effective_z = beam.EffectiveLengthZ.Value / 1000.0  # Convert to meters
            return f"Effective L: Y={effective_y:.2f}m, Z={effective_z:.2f}m"
        elif option == "all":
            texts = []
            texts.append(f"{beam.Label}")
            
            if beam.Material:
                texts.append(f"{beam.Material.Label}")
            
            if beam.Section:
                texts.append(f"{beam.Section.Label}")
            
            if beam.MemberRelease:
                texts.append(f"{beam.MemberRelease.Label}")
            
            buckling_y = beam.BucklingLengthY.Value / 1000.0
            buckling_z = beam.BucklingLengthZ.Value / 1000.0
            texts.append(f"Buckling L: Y={buckling_y:.2f}m, Z={buckling_z:.2f}m")
            
            effective_y = beam.EffectiveLengthY.Value / 1000.0
            effective_z = beam.EffectiveLengthZ.Value / 1000.0
            texts.append(f"Effective L: Y={effective_y:.2f}m, Z={effective_z:.2f}m")
            
            return "\n".join(texts)
        
        return ""

    def get_node_text(self, node):
        """Generate text for node based on selected option"""
        option = self.node_combobox.currentData()
        if option == "none":
            return ""
        elif option == "label":
            return f"{node.Label}"
        elif option == "position":
            x = node.X.Value / 1000.0  # Convert to meters
            y = node.Y.Value / 1000.0  # Convert to meters
            z = node.Z.Value / 1000.0  # Convert to meters
            return f"({x:.2f}, {y:.2f}, {z:.2f}) m"
        elif option == "boundary":
            bc_text = self.get_node_boundary_conditions(node)
            return f"{bc_text}" if bc_text else ""

        elif option == "all":
            texts = []
            texts.append(f"{node.Label}")
            
            x = node.X.Value / 1000.0
            y = node.Y.Value / 1000.0
            z = node.Z.Value / 1000.0
            texts.append(f"({x:.2f}, {y:.2f}, {z:.2f}) m")
            
            bc_text = self.get_node_boundary_conditions(node)
            if bc_text:
                texts.append(f"{bc_text}")
            
            return "\n".join(texts)
        
        return ""

    def get_node_boundary_conditions(self, node):
        """Get boundary condition information for a node"""
        doc = App.ActiveDocument
        if not doc or not hasattr(doc, "BoundaryConditions"):
            return ""
        
        bc_group = doc.BoundaryConditions
        if not bc_group:
            return ""
        
        bc_labels = []
        for bc in bc_group.Group:
            if hasattr(bc, "Nodes") and node in bc.Nodes:
                bc_labels.append(bc.Label)
        
        return ", ".join(bc_labels) if bc_labels else "None"

    def apply_labels(self):
        """Apply labels to all beams and nodes"""
        #try:
        # Get all beams and nodes
        beams = get_all_beams()
        nodes = get_all_nodes()
        text_size = self.text_size.value()
        text_offset_val = self.text_offset.value()

        # Apply beam labels
        for beam in beams:
            if hasattr(beam, "Proxy") and hasattr(beam.Proxy, "clear_texts"):
                beam.Proxy.clear_texts(beam)
            text_content = self.get_beam_text(beam)
            if text_content:
                # Add text at center of beam with offset
                offset = App.Vector(0, 0, text_offset_val)
                if text_content and hasattr(beam, "Proxy") and hasattr(beam.Proxy, "add_text"):
                    beam.Proxy.add_text(beam, text_content, 0.5, offset)
                    beam.TextSize = text_size

        
        # Apply node labels
        for node in nodes:
            if hasattr(node, "Proxy") and hasattr(node.Proxy, "clear_texts"):
                node.Proxy.clear_texts()
            text_content = self.get_node_text(node)
            if text_content and hasattr(node.Proxy, "add_text"):
                # For nodes, we'll add the text above the node
                node.Proxy.add_text(text_content)
                node.TextSize=text_size

        
        #except Exception as e:
        #    QtGui.QMessageBox.critical(self.form, "Error", f"Failed to apply labels: {str(e)}")

    def clear_labels(self):
        """Clear all labels from beams and nodes"""
        try:
            beams = get_all_beams()
            nodes = get_all_nodes()
            
            beam_count = 0
            node_count = 0
            
            # Clear beam labels
            for beam in beams:
                if hasattr(beam, "Proxy") and hasattr(beam.Proxy, "clear_texts"):
                    beam.Proxy.clear_texts(beam)
                    beam_count += 1
            
            # Clear node labels
            for node in nodes:
                if hasattr(node, "clear_texts"):
                    node.Proxy.clear_texts()
                    node_count += 1

            QtGui.QMessageBox.information(self.form, "Success", 
                                        f"Labels cleared from {beam_count} beams and {node_count} nodes.")
            
        except Exception as e:
            QtGui.QMessageBox.critical(self.form, "Error", f"Failed to clear labels: {str(e)}")

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


def show_item_labeling():
    """Show the item labeling task panel"""
    # Close any existing task panel first
    if hasattr(Gui, 'Control') and Gui.Control.activeDialog():
        Gui.Control.closeDialog()
    
    panel = ItemLabelingTaskPanel()
    Gui.Control.showDialog(panel)
    return panel