# ui/dialog_BaseLoadCreator.py
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtGui, QtCore
from features.LoadIDManager import create_load_id

class BaseLoadTaskPanel:
    """Base task panel for all load types with common functionality"""
    
    def __init__(self, title, load_type):
        self.form = QtGui.QWidget()
        self.form.setWindowTitle(title)
        self.selected_items = []
        self.selection_callback = None
        self.is_picking = False
        self.load_type = load_type
        
        self.setup_common_ui()
        self.update_load_id_combo()
        
    def setup_common_ui(self):
        layout = QtGui.QVBoxLayout(self.form)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Title
        title = QtGui.QLabel(f"Create {self.load_type} Load")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)

        # Load ID Section
        load_id_group = QtGui.QGroupBox("Load ID")
        load_id_layout = QtGui.QHBoxLayout()
        
        self.load_id_combo = QtGui.QComboBox()
        load_id_layout.addWidget(self.load_id_combo)
        
        self.new_load_id_btn = QtGui.QPushButton("New Load ID")
        self.new_load_id_btn.clicked.connect(self.create_new_load_id)
        load_id_layout.addWidget(self.new_load_id_btn)
        
        load_id_group.setLayout(load_id_layout)
        layout.addWidget(load_id_group)

    def update_load_id_combo(self):
        self.load_id_combo.clear()
        doc = App.ActiveDocument
        if doc:
            for obj in doc.Objects:
                if hasattr(obj, "Type") and obj.Type == "LoadIDFeature":
                    self.load_id_combo.addItem(obj.Label, obj)
        
        if self.load_id_combo.count() == 0:
            self.load_id_combo.addItem("No Load IDs - Create one first", None)

    def create_new_load_id(self):
        """Create a new Load ID"""
        try:
            load_id = create_load_id()
            if load_id:
                self.update_load_id_combo()
                # Select the newly created Load ID
                for i in range(self.load_id_combo.count()):
                    if self.load_id_combo.itemData(i) == load_id:
                        self.load_id_combo.setCurrentIndex(i)
                        break
        except Exception as e:
            QtGui.QMessageBox.critical(self.form, "Error", f"Failed to create Load ID:\n{str(e)}")

    def setup_item_selection(self, item_type, item_label):
        """Setup item selection section (nodes, beams, etc.)"""
        self.item_type = item_type
        self.item_label = item_label
        
        item_group = QtGui.QGroupBox(f"{item_label} Selection")
        item_layout = QtGui.QVBoxLayout()

        # Selection info
        self.selection_info = QtGui.QLabel(f"No {item_label.lower()} selected")
        self.selection_info.setStyleSheet("font-weight: bold; color: blue;")
        item_layout.addWidget(self.selection_info)

        # Item list
        self.item_list = QtGui.QListWidget()
        self.item_list.setSelectionMode(QtGui.QListWidget.ExtendedSelection)
        self.item_list.setMaximumHeight(120)
        self.item_list.itemSelectionChanged.connect(self.on_item_selection_changed)
        item_layout.addWidget(self.item_list)

        # Selection buttons
        button_layout = QtGui.QHBoxLayout()
        self.pick_button = QtGui.QPushButton(f"Pick {item_label}")
        self.pick_button.clicked.connect(self.toggle_picking)
        self.clear_button = QtGui.QPushButton("Clear Selection")
        self.clear_button.clicked.connect(self.clear_selection)

        button_layout.addWidget(self.pick_button)
        button_layout.addWidget(self.clear_button)
        item_layout.addLayout(button_layout)

        item_group.setLayout(item_layout)
        
        # Find the Load ID group and insert after it
        layout = self.form.layout()
        for i in range(layout.count()):
            widget = layout.itemAt(i).widget()
            if widget and isinstance(widget, QtGui.QGroupBox) and widget.title() == "Load ID":
                layout.insertWidget(i + 1, item_group)
                break

    def toggle_picking(self):
        """Toggle picking mode on/off"""
        if self.is_picking:
            self.stop_picking()
        else:
            self.start_picking()

    def start_picking(self):
        """Start picking items using FreeCAD selection"""
        Gui.Selection.clearSelection()
        
        # Add already selected items to FreeCAD selection for visual feedback
        for item in self.selected_items:
            Gui.Selection.addSelection(item)
        
        self.pick_button.setStyleSheet("font-weight: bold; background-color: lightgreen")
        self.pick_button.setText("Finish Selection")
        self.is_picking = True
        
        # Set up selection callback
        self.selection_callback = LoadSelectionCallback(self)
        Gui.Selection.addObserver(self.selection_callback)

    def stop_picking(self):
        """Stop picking items and process the selection"""
        if self.selection_callback:
            Gui.Selection.removeObserver(self.selection_callback)
            self.selection_callback = None

        # Get current FreeCAD selection and update our item list
        current_selection = Gui.Selection.getSelection()
        self.selected_items = []
        
        for obj in current_selection:
            if self.is_valid_item(obj):
                if obj not in self.selected_items:
                    self.selected_items.append(obj)
        
        self.update_display()

        self.pick_button.setStyleSheet("")
        self.pick_button.setText(f"Pick {self.item_label}")
        self.is_picking = False

    def is_valid_item(self, obj):
        """Check if object is valid for this load type - to be overridden by subclasses"""
        return True

    def process_selection(self, doc_name, obj_name):
        """Process individual selection events"""
        try:
            doc = App.getDocument(doc_name)
            if not doc:
                return

            obj = doc.getObject(obj_name)
            if not obj:
                return

            if self.is_valid_item(obj):
                # During picking, we only update the visual selection in FreeCAD
                # The actual selection is only updated when user clicks "Finish Selection"
                pass

        except Exception as e:
            print(f"Error processing selection: {e}")

    def on_item_selection_changed(self):
        """Handle item list selection changes"""
        selected_items = self.item_list.selectedItems()
        if selected_items:
            # Update FreeCAD selection to match list widget selection
            Gui.Selection.clearSelection()
            for item in selected_items:
                item_label = item.text().split(" - ")[0]
                item_obj = self.find_item_by_label(item_label)
                if item_obj:
                    Gui.Selection.addSelection(item_obj)

    def find_item_by_label(self, label):
        """Find item object by label - to be overridden by subclasses"""
        doc = App.ActiveDocument
        if not doc:
            return None
        return doc.getObject(label)

    def update_display(self):
        """Update the display based on current selection"""
        self.item_list.clear()
        for item in self.selected_items:
            if hasattr(item, "X") and hasattr(item, "Y") and hasattr(item, "Z"):
                x = getattr(item, "X", 0.0)
                y = getattr(item, "Y", 0.0)
                z = getattr(item, "Z", 0.0)
                
                if hasattr(x, "Value"):  # Handle Quantity objects
                    item_text = f"{item.Label} - ({x.Value:.1f}, {y.Value:.1f}, {z.Value:.1f}) mm"
                else:
                    item_text = f"{item.Label} - ({x:.1f}, {y:.1f}, {z:.1f}) mm"
            else:
                item_text = item.Label
                
            item = QtGui.QListWidgetItem(item_text)
            self.item_list.addItem(item)

        # Update selection info
        count = len(self.selected_items)
        self.selection_info.setText(f"{count} {self.item_label.lower()}(s) selected")

    def clear_selection(self):
        """Clear the item selection"""
        self.selected_items = []
        Gui.Selection.clearSelection()
        self.update_display()

    def get_current_load_id(self):
        """Get the currently selected Load ID"""
        if self.load_id_combo.currentData():
            return self.load_id_combo.currentData()
        else:
            QtGui.QMessageBox.warning(self.form, "Error", "Please select or create a Load ID first.")
            return None

    def cleanup(self):
        """Clean up resources"""
        if self.is_picking:
            self.stop_picking()

    def reject(self):
        """Cancel operation"""
        self.cleanup()
        return True

    def getStandardButtons(self):
        """Return standard buttons for task panel"""
        return QtGui.QDialogButtonBox.Apply | QtGui.QDialogButtonBox.Close

    def clicked(self, button):
        """Handle button clicks"""
        if button == QtGui.QDialogButtonBox.Apply:
            self.apply_changes()
            App.ActiveDocument.recompute()
        elif button == QtGui.QDialogButtonBox.Close:
            self.cleanup()
            Gui.Control.closeDialog()


class LoadSelectionCallback:
    """Callback class for handling load selection events"""

    def __init__(self, task_panel):
        self.task_panel = task_panel

    def addSelection(self, doc_name, obj_name, sub_name, pos):
        """Called when an object is selected"""
        self.task_panel.process_selection(doc_name, obj_name)