"""
This script duplicates a mesh and creates a blend shape deformer for each duplicate. 
The duplicates are then parented to a control circle. 
The script also creates a camera and a master group for showcase purposes.

Created by Bonny Baez
LinkedIn: https://www.linkedin.com/in/bonnybaez/

"""

from PySide6 import QtWidgets, QtCore
import maya.cmds as cmds
from maya import OpenMayaUI as omui
import maya.app.general.mayaMixin as mayaMixin

# This function returns a pointer to the main Maya window
def maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return mayaMixin.wrapInstance(int(main_window_ptr), QtWidgets.QWidget)

def remove_duplicates():
    # Delete all duplicated meshes and control circles along with their blend shape nodes and group nodes
    all_duplicated_meshes = cmds.ls("*BB_Duplicate_Mesh*dup*", type="transform")
    all_ctrl_circles = cmds.ls("*BB_Duplicate_Mesh*ctrl*", type="transform")
    all_blend_shape_nodes = cmds.ls("*BB_Duplicate_Mesh*bs*", type="blendShape")
    cmds.delete(all_duplicated_meshes, all_ctrl_circles, all_blend_shape_nodes)
    cmds.delete(cmds.ls("BB_Duplicates_Grp", "BB_Duplicate_Showcase_Grp"))

# This function calculates the bounding box of the selected mesh
def calculate_bounding_box(meshes):
    x_min = y_min = z_min = float('inf')
    x_max = y_max = z_max = float('-inf')

    for mesh in meshes:
        bbox = cmds.exactWorldBoundingBox(mesh)
        x_min = min(x_min, bbox[0])
        y_min = min(y_min, bbox[1])
        z_min = min(z_min, bbox[2])
        x_max = max(x_max, bbox[3])
        y_max = max(y_max, bbox[4])
        z_max = max(z_max, bbox[5])

    # Calculate the width, height, and depth of the bounding box and return them
    width = x_max - x_min
    height = y_max - y_min
    depth = z_max - z_min

    return width, height, depth

# Main duplicate function
def duplicate_and_deform(num_copies, scale_factor, showcase_setup):
    
    # Save the initial selection and get the selected mesh. Also, check if either a mesh or a nurbs surface is selected
    initial_selection = cmds.ls(sl=True)
    selected_meshes = cmds.ls(sl=True, dag=True, leaf=True, noIntermediate=True, objectsOnly=True, shapes=True) 
    selected_meshes = [node for node in selected_meshes if cmds.nodeType(node) in {"mesh", "nurbsSurface"}]

    # Check if a mesh is selected if not then show a warning message
    if not selected_meshes:
        QtWidgets.QMessageBox.warning(None, "Warning", "Please select a mesh.")
        return

    width, height, depth = calculate_bounding_box(selected_meshes)

    # Warning if the number of copies is greater than 10
    if num_copies > 10:
        reply = QtWidgets.QMessageBox.question(None, "Confirmation", "You're about to create a large number of duplicates. Are you sure you want to do this?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.No:
            return
    # remove duplicate if BB_Duplicate_grp exists
    if cmds.objExists("BB_Duplicates_Grp"):
        remove_duplicates()

    # Create parent group
    parent_group = cmds.group(empty=True, name="BB_Duplicates_Grp")

    # Create camera and showcase group
    if showcase_setup:
        cmds.delete(cmds.ls("renderCam"))
        camera = cmds.camera(name="renderCam")[0]
        cmds.move(0, 0.5 * height, 6 * depth, camera)
        cmds.group(empty=True, name="BB_Duplicate_Showcase_Grp")
        cmds.parent(camera, "BB_Duplicate_Showcase_Grp")
        cmds.parent(parent_group, camera)

        # Create a new modelPanel and parent it under a new layout
        if cmds.window("newWindow", exists=True):
            cmds.deleteUI("newWindow", window=True)
        new_window = cmds.window("Showcase", title="Showcase", iconName='Short Name', widthHeight=(800, 600))
        cmds.paneLayout()
        panel = cmds.modelPanel(label='Camera View')
        cmds.modelPanel(panel, edit=True, camera=camera)

        # Set the modelPanel to display the mesh and turn off the grid turn on curves
        cmds.modelEditor(panel, edit=True, allObjects=False)
        cmds.modelEditor(panel, edit=True, polymeshes=True)
        cmds.modelEditor(panel, edit=True, motionTrails=True)
        cmds.modelEditor(panel, edit=True, grid=False)  # Turn off the grid
        cmds.modelEditor(panel, edit=True, displayAppearance='smoothShaded', displayTextures=True)
        cmds.modelEditor(panel, edit=True, nurbsCurves=False)

        cmds.showWindow(new_window)

        # Set the camera to the mesh
        cmds.lookThru(camera)

        # Select the initial selection
        cmds.select(initial_selection)
        
        # Fit the camera to the mesh
        cmds.viewFit(f=0.5)


    # Duplicate meshes and create blend shape deformer for each duplicate
    for i in range(num_copies):
        group_node = cmds.group(empty=True, name="BB_Duplicate_Mesh_{:02d}".format(i+1))

        for mesh in selected_meshes:
            duplicated_mesh = cmds.duplicate(mesh)[0]
            mesh_name = mesh.split(":")[-1]
            duplicated_mesh = cmds.rename(duplicated_mesh, "dup_" + mesh_name + "_{:02d}".format(i+1))
            blend_shape_node = cmds.blendShape(mesh, duplicated_mesh, name=group_node + "_BS", frontOfChain=True)[0]
            cmds.setAttr(blend_shape_node + "." + mesh_name, 1)
            cmds.parent(duplicated_mesh, group_node)

        circle_control = cmds.circle(name=group_node + "_ctrl", normal=(0, 1, 0), radius=width/2.0)[0]
        cmds.scale(scale_factor, scale_factor, scale_factor, circle_control)

        # Set control circle color to yellow
        cmds.setAttr(circle_control + ".overrideEnabled", 1)
        cmds.setAttr(circle_control + ".overrideRGBColors", 1)
        cmds.setAttr(circle_control + ".overrideColorRGB", 1, 1, 0)  # RGB for yellow

        # Position and parent control circle
        if showcase_setup and num_copies == 4:
            offset_positions = [(1.0, 0.7), (-1.0, 0.7), (1.0, 0.0), (-1.0, 0.0)]
            rotation_values = [(0, 90, 0), (0, -90, 0), (0, 0, 0), (0, 180, 0)]
            
            # Rotate and move control circle and group node to their respective positions using offset and rotation values
            cmds.rotate(rotation_values[i][0], rotation_values[i][1], rotation_values[i][2], circle_control)
            cmds.move(offset_positions[i][0] * width, offset_positions[i][1] * height, -2 * depth, circle_control, localSpace=True)
        else:
            # Rotate and move control circle and group node to their respective positions
            cmds.move(1.1 * width * (i+1), 0, 0, circle_control, localSpace=True)

        # Parent group node to control circle
        cmds.parentConstraint(circle_control, group_node)
        cmds.scaleConstraint(circle_control, group_node)
        cmds.parent(circle_control, parent_group)
        cmds.parent(group_node, parent_group)

    # Parent showcase group to parent group
    cmds.select(initial_selection)

# Main window class
class MainWindow(mayaMixin.MayaQWidgetBaseMixin, QtWidgets.QMainWindow):
    def __init__(self, parent=maya_main_window()):
        super(MainWindow, self).__init__(parent)

        # Set window title and size
        self.setWindowTitle("BB MultiMesh Showcase")
        self.setFixedSize(300, 200)

        # Create main widget and layout
        main_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(main_widget)
        layout = QtWidgets.QVBoxLayout(main_widget)

        # Input fields for number of duplicates and scale
        duplicates_label = QtWidgets.QLabel("Number of duplicates:")
        self.num_copies_field = QtWidgets.QLineEdit()
        self.num_copies_field.setPlaceholderText("Enter number of duplicates")
        self.num_copies_field.setText("1")
        
        scale_label = QtWidgets.QLabel("Scale:")
        self.scale_field = QtWidgets.QLineEdit()
        self.scale_field.setPlaceholderText("Enter scale")
        self.scale_field.setText("1")

        # Checkbox for showcase setup
        self.showcase_checkbox = QtWidgets.QCheckBox("Create Showcase setup")
        self.showcase_checkbox.stateChanged.connect(self.on_checkbox_state_changed)

        # Create a QHBoxLayout for the buttons
        button_layout = QtWidgets.QHBoxLayout()

        # Duplicate button
        duplicate_button = QtWidgets.QPushButton("Duplicate")
        duplicate_button.clicked.connect(self.on_duplicate_clicked)
        button_layout.addWidget(duplicate_button)

        # Delete duplicates button
        delete_button = QtWidgets.QPushButton("Delete Duplicates")
        delete_button.clicked.connect(self.on_delete_clicked)
        button_layout.addWidget(delete_button)

        # Slider for scaling duplicates
        scale_duplicates_label = QtWidgets.QLabel("Scale Duplicates:")
        self.scale_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.scale_slider.setMinimum(1)
        self.scale_slider.setMaximum(150)
        self.scale_slider.setValue(50)
        self.scale_slider.valueChanged.connect(self.on_scale_changed)
        
        # Add widgets to layout
        layout.addWidget(duplicates_label)
        layout.addWidget(self.num_copies_field)
        layout.addWidget(scale_label)
        layout.addWidget(self.scale_field)
        layout.addWidget(self.showcase_checkbox)        
        layout.addLayout(button_layout) # Add the button layout here
        layout.addWidget(scale_duplicates_label)
        layout.addWidget(self.scale_slider)

    # Checkbox state changed
    def on_checkbox_state_changed(self, state):
        if state == QtCore.Qt.Checked:
            self.num_copies_field.setText("4")
            self.num_copies_field.setEnabled(False)
            self.scale_field.setText("0.5")            
        else:
            self.num_copies_field.setEnabled(True)

    # Duplicate button clicked
    def on_duplicate_clicked(self):
        num_copies = int(self.num_copies_field.text())
        scale_factor = float(self.scale_field.text())
        showcase_setup = self.showcase_checkbox.isChecked()
        
        # Set the slider's value
        self.scale_slider.setValue(scale_factor * 50)  # Assuming scale_factor is in the range [0, 2]
        
        duplicate_and_deform(num_copies, scale_factor, showcase_setup)

    # Delete button clicked
    def on_delete_clicked(self):
        remove_duplicates()
            
    # Scale slider changed
    def on_scale_changed(self, value):
        # Scale all control circles by the slider's value (in the range [1, 100]) divided by 50 in order to get a value in the range [0.02, 2]
        scale_factor = value / 50.0
        all_ctrl_circles = cmds.ls("*BB_Duplicate_Mesh*ctrl*", type="transform")
        for ctrl_circle in all_ctrl_circles:
            cmds.scale(scale_factor, scale_factor, scale_factor, ctrl_circle)

# Run the script   
if __name__ == "__main__":
    try:
        BB_Mesh_Duplicator.close()
        BB_Mesh_Duplicator.deleteLater()
    except:
        pass

    BB_Mesh_Duplicator = MainWindow()
    BB_Mesh_Duplicator.show()
