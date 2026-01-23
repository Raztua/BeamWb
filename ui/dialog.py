# ui/dialog.py
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtGui, QtCore
from pivy import coin
import os
import random

# Task panel manager functions
def show_node_creator():
    from ui.dialog_NodeManager import NodeManagerTaskPanel
    panel = NodeManagerTaskPanel()
    Gui.Control.showDialog(panel)

def show_code_check_results(feature_obj):
    from ui.dialog_CodeCheckResults import show_code_check_results
    show_code_check_results(feature_obj)

def show_beam_colorizer():
    from ui.dialog_BeamColorizer import show_beam_colorizer
    panel = show_beam_colorizer()
    return panel

def show_bc_creator():
    from ui.dialog_BoundaryConditionCreator import BoundaryConditionCreatorTaskPanel
    panel = BoundaryConditionCreatorTaskPanel()
    Gui.Control.showDialog(panel)

def show_section_creator():
    from ui.dialog_SectionCreator import SectionCreatorTaskPanel
    panel = SectionCreatorTaskPanel()
    Gui.Control.showDialog(panel)

def show_beam_creator():
    from ui.dialog_BeamCreator import BeamCreatorTaskPanel
    panel = BeamCreatorTaskPanel()
    Gui.Control.showDialog(panel)

def show_load_group_creator():
    from ui.dialog_LoadID import LoadIDTaskPanel
    panel = LoadIDTaskPanel()
    Gui.Control.showDialog(panel)

def show_nodal_load_creator(selected_nodes=None, nodal_load_to_modify=None):
    from ui.dialog_NodalLoad import show_nodal_load_creator
    panel = show_nodal_load_creator(selected_nodes=selected_nodes, nodal_load_to_modify=nodal_load_to_modify)
    return panel

def show_member_load_creator(selected_beams=None, member_load_to_modify=None):
    from ui.dialog_MemberLoad import show_member_load_creator
    panel = show_member_load_creator(selected_beams=selected_beams, member_load_to_modify=member_load_to_modify)
    return panel
    
def show_item_labeling():
    from ui.dialog_ItemLabeling import show_item_labeling
    panel = show_item_labeling()
    return panel
    
def show_acceleration_load_creator(selected_beams=None, acceleration_load_to_modify=None):
    from ui.dialog_AccelerationLoad import show_acceleration_load_creator
    panel = show_acceleration_load_creator(selected_beams=selected_beams, acceleration_load_to_modify=acceleration_load_to_modify)
    return panel

def show_load_combination_creator(combination=None):
    from ui.dialog_LoadCombination import LoadCombinationTaskPanel
    panel = LoadCombinationTaskPanel(combination=combination)
    Gui.Control.showDialog(panel)