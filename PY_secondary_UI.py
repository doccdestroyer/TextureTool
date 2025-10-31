import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__)))

import os
from PySide6 import QtCore
from PySide6.QtWidgets import QPushButton, QWidget, QMainWindow, QPushButton, QWidget, QLineEdit, QLabel, QVBoxLayout, QHBoxLayout, QSlider, QRadioButton, QButtonGroup
from PySide6.QtCore import Qt, Signal
import unreal
from PySide6.QtGui import QAction, QAction, QIcon

from PY_tools import PenTool, MoveTool, LassoTool, PolygonalTool, RectangularTool, EllipticalTool, TransformTool, TextureLayer

###############################################################
#                   DELETION WINDOW                           # 
###############################################################
# Window to confirm layer deletion
class DeleteConfirmationWindow(QWidget):
    def __init__(self, parent = None):
        # Setup window
        super(DeleteConfirmationWindow, self).__init__(parent)
        self.mainWindow= QMainWindow()
        # Establish Parent Window
        self.parent_window = parent

        # Establish buttons and effects
        self.accept_button = QPushButton("Yes")
        self.accept_button.clicked.connect(self.accept_button_clicked)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_button_clicked)

        # Estbalish text label
        self.label = QLabel()
        self.label.setText("Are you sure you want to delete this layer?")

        # Establish "Dont show this again button" and link effect
        self.dont_show_again_radio_button = QRadioButton()
        self.dont_show_again_radio_button.setText("Don't show this again")
        self.dont_show_again_radio_button.clicked.connect(self.dont_show_again_enabled)

        # Combine all in a layout and container
        layout = QVBoxLayout()
        button_layouts= QHBoxLayout()
        button_layouts.addWidget(self.accept_button)
        button_layouts.addWidget(self.cancel_button)
        layout.addWidget(self.label)
        layout.addWidget(self.dont_show_again_radio_button)
        layout.addLayout(button_layouts)
        container = QWidget()
        container.setLayout(layout)

        # Set dark mode
        self.setStyleSheet("""
            background-color: #252525;
            color: #ffffff;
            font-family: Segoe UI;
            font-size: 12px;                 
        """)  

        self.mainWindow.setCentralWidget(container)

    # Establish accept button effect to delete layer
    def accept_button_clicked(self, checked):
        self.parent_window.will_delete = True
        self.parent_window.delete_current_layer()
        self.parent_window.update()
        self.mainWindow.close()
        self.mainWindow.deleteLater()
    # Establish accept button effect to run deletion script without deleteinng layer    
    def cancel_button_clicked(self, checked):
        self.parent_window.will_delete = False
        self.parent_window.update()
        self.parent_window.delete_current_layer()
        self.mainWindow.close()
        self.mainWindow.deleteLater()
    # Establish don't show this again effect
    def dont_show_again_enabled(self, checked):
        self.parent_window.show_delete_message = False
        self.parent_window.update()



###############################################################
#                       RENAMER MENU                          # 
###############################################################
class ChooseNameWindow(QMainWindow):
    # Establish ChooseNameWindow
    def __init__(self):
        # Setup Window
        super().__init__()           
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        self.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint)

        # Add Apply Button and link effect
        self.button = QPushButton("Apply Name Change")
        self.button.setCheckable(True)
        self.button.clicked.connect(self.buttonClicked)

        self.label = QLabel()

        # Add Set Name line edit
        self.lineEdit = QLineEdit()
        self.lineEdit.textChanged.connect(self.label.setText)
        self.lineEdit.setText('')

        # Add widgets to layout
        layout = QVBoxLayout()
        layout.addWidget(self.button)
        layout.addWidget(self.lineEdit)
        layout.addWidget(self.label)
        container = QWidget()
        container.setLayout(layout)

        # Set dark mode
        self.setStyleSheet("""
            background-color: #262626;
            color: #ffffff;
            font-family: Segoe UI;
            font-size: 12px;
            selection-background-color: #424242;                  
        """)  
        self.setCentralWidget(container)

        # Establish Variables
        self.name = None
        self.button_clicked = False

    #Set LineText as name if pressed effect
    def buttonClicked(self, checked):
        self.button_clicked = True
        self.name = self.lineEdit.text() or "untitled"
        self.update()

    # Gets and returns the name
    def getName(self):
        return self.name

    # Launches Window
    def launchWindow(self):
        ChooseNameWindow.window = ChooseNameWindow()
        ChooseNameWindow.window.show()
        ChooseNameWindow.window.setWindowTitle("Choose File Name")
        ChooseNameWindow.window.setObjectName("ChooseNameWindow")
        unreal.parent_external_window_to_slate(ChooseNameWindow.window.winId())


###############################################################
#                          SLIDER                             #
###############################################################
# Establishes Slider class to be used for all sliders
class Slider(QWidget):
    # Estalish Signals to communicate with other classes
    value_changed = Signal(int)
    has_released_slider = Signal(bool)
    def __init__(self, parent, name, min, max, default):
        # Set Up Slider
        super().__init__(parent)
        self.parent_window = parent
        self.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setFixedSize(320, 25)
        self.setWindowTitle(name)

        # Set up slider values and connections
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(min)
        self.slider.setMaximum(max)
        self.slider.setSliderPosition(default)
        self.slider.valueChanged.connect(self.sliderChanged)
        self.slider.sliderReleased.connect(self.slider_been_released)

        # Set dark mode
        self.setStyleSheet("""
            background-color: #252525;
            color: #ffffff;
            font-family: Segoe UI;
            font-size: 12px;
        """)  

        # Set textures and get base pixmap/image
        self.texture_layers = parent.texture_layers
        self.original_pixmap = self.parent_window.base_pixmap
        self.original_image = self.original_pixmap.toImage()

        # Add slider to widget
        self.image_label = QLabel()
        layout = QVBoxLayout()
        layout.addWidget(self.slider)
        self.setLayout(layout)

    # Reset slider poistion to default
    def reset(self,default):
        self.slider.setSliderPosition(default)

    # Emit new value when slider is changed
    def sliderChanged(self,value):
        self.value_changed.emit(value)
    
    # Emit boolean to say if the slider has been released
    def slider_been_released(self):
        self.has_released_slider.emit(True)

###############################################################
#                    TOOL SELECTION MENU                      #
###############################################################
# Tool Selection Menu
class ToolSelectionMenu(QMainWindow):
    def __init__(self, parent = None):
        super().__init__(parent)
        # Establish parent and parent layout
        self.parent_window = parent
        self.parent_layout = self.parent_window.layout
        # Esablish window
        self.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setFixedSize(32, 1000)
        self.setWindowTitle("Tool Menu")

        # Set dark mode
        self.setStyleSheet("""
            background-color: #262626;
            color: #ffffff;
            font-family: Segoe UI;
            font-size: 12px;
            selection-background-color: #424242;                  
        """)  
 
        # Set intial tool as pen
        self.selected_tool = "Pen"
        self.refresh_tool()

        self.create_actions()
        self.create_tool_bars()

        self.setStyleSheet("""
            background-color: #2c2c2c;
            color: #ffffff;
            font-family: Segoe UI;
            font-size: 12px;
            selection-background-color: #424242;                  
        """)  
    # Add Tool bar actions to corresponding Icon
    def create_tool_bars(self):
        self.tool_bar = self.addToolBar("File")
        self.tool_bar.setOrientation(Qt.Vertical)
        self.tool_bar.addAction(self.move_action)
        self.tool_bar.addAction(self.pen_action)
        self.tool_bar.addAction(self.lasso_action)
        self.tool_bar.addAction(self.polygonal_action)
        self.tool_bar.addAction(self.rectangle_action)
        self.tool_bar.addAction(self.ellipse_action)
        self.tool_bar.addAction(self.transform_action)

    # Create Actions for tool bars with icons
    def create_actions(self):
        icon = QIcon(os.path.join(os.path.dirname(__file__), "icon_images", "move.png"))
        self.move_action = QAction(icon, "Move Tool",
                                       self,
                                       statusTip="Move Tool",
                                       triggered=self.enable_move_tool)

        icon = QIcon(os.path.join(os.path.dirname(__file__), "icon_images", "pen.png"))
        self.pen_action = QAction(icon, "Pen Tool", self,
                                  statusTip="Print the current form letter",
                                  triggered=self.enable_pen_tool)

        icon = QIcon(os.path.join(os.path.dirname(__file__), "icon_images", "lasso.png"))
        self.lasso_action = QAction(icon, "Lasso Tool", self,
                                  statusTip="Print the current form letter",
                                  triggered=self.enable_lasso_tool)

        icon = QIcon(os.path.join(os.path.dirname(__file__), "icon_images", "polylasso.png"))
        self.polygonal_action = QAction(icon, "Polygonal Lasso", self,
                                 statusTip="Save the current form letter",
                                 triggered=self.enable_polygonal_tool)

        icon = QIcon(os.path.join(os.path.dirname(__file__), "icon_images", "rectangle.png"))
        self.rectangle_action = QAction(icon, "Rectanlge Tool", self,
                                  statusTip="Print the current form letter",
                                  triggered=self.enable_rectanlge_tool)
        
        icon = QIcon(os.path.join(os.path.dirname(__file__), "icon_images", "ellipse.png"))
        self.ellipse_action = QAction(icon, "Ellipse Tool", self,
                                  statusTip="Print the current form letter",
                                  triggered=self.enable_ellipse_tool)
        
        icon = QIcon(os.path.join(os.path.dirname(__file__), "icon_images", "transform.png"))
        self.transform_action = QAction(icon, "Transform Tool", self,
                                  statusTip="Print the current form letter",
                                  triggered=self.enable_transform_tool)


    # Update the current tool
    def update_tool(self):
        if self.parent_window.active_tool_widget:
            self.parent_layout.insertWidget(0,self.parent_window.active_tool_widget)
            self.parent_window.active_tool_widget.show()
        self.parent_window.tool_description_label.setText(self.parent_window.tool_description)
        self.parent_window.update()

    # Refresh the tool
    def refresh_tool(self):
        if self.selected_tool == "Move":
            self.enable_move_tool()
        elif self.selected_tool == "Pen":
            self.enable_pen_tool()
        elif self.selected_tool == "Lasso":
            self.enable_lasso_tool()
        elif self.selected_tool == "Polygon":
            self.enable_polygonal_tool()
        elif self.selected_tool == "Rectangle":
            self.enable_rectanlge_tool()
        elif self.selected_tool == "Ellipse":
            self.enable_ellipse_tool()
        elif self.selected_tool == "Transform":
            self.enable_transform_tool()
        self.parent_window.tool_description_label.setText(self.parent_window.tool_description)

    # Enable move tool
    def enable_move_tool(self):
        if hasattr(self.parent_window, "active_tool_widget") and self.parent_window.active_tool_widget:
            self.parent_layout.removeWidget(self.parent_window.active_tool_widget)
            self.parent_window.active_tool_widget.deleteLater()
        self.parent_window.active_tool_widget = MoveTool(parent_window=self.parent_window)
        self.parent_window.tool_description = "\n  Move Tool \n\n\n" \
            "  This tool allows you to select and \n"\
            "  move any layer\n\n"\
            "  Select Layer - click on the contents \n"\
            "  of a layer\n\n"\
            "  Move Layer - click and drag on the \n"\
            "  contents of a layer\n\n"\
            "\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n"
        self.setCursor(QtCore.Qt.ArrowCursor)
        self.update_tool()

    # Enable pen tool
    def enable_pen_tool(self):
        if hasattr(self.parent_window, "active_tool_widget") and self.parent_window.active_tool_widget:
            self.parent_layout.removeWidget(self.parent_window.active_tool_widget)
            self.parent_window.active_tool_widget.deleteLater()

        self.parent_window.active_tool_widget = PenTool(self.parent_window.image_path, parent_window=self.parent_window, color = self.parent_window.color)
        self.parent_window.tool_description =  "\n  Pen Tool\n\n\n"\
            "  This tool allows you to draw on the \n"\
            "  selected layer within its bounds. \n\n"\
            "  If there was a prior selection you \n"\
            "  will only be able to draw within the \n"\
            "  selection.\n\n"\
            "  Decrease Pen Size - press [\n\n"\
            "  Increase Pen Size - press ] \n\n"\
            "\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n"
        self.selected_tool = "Pen"
        self.parent_window.setCursor(QtCore.Qt.CrossCursor)
        self.update_tool()

    # Enable lasso tool
    def enable_lasso_tool(self):
        if hasattr(self.parent_window, "active_tool_widget") and self.parent_window.active_tool_widget:
            self.parent_layout.removeWidget(self.parent_window.active_tool_widget)
            self.parent_window.active_tool_widget.deleteLater()
        self.parent_window.active_tool_widget = LassoTool(self.parent_window.image_path, parent_window=self.parent_window)
        self.parent_window.tool_description = "\n  Lasso Tool\n\n\n"\
            "  This tool allows you to make \n"\
            "  freehand selections \n\n"\
            "  Add Selection- hold shift on initial \n"\
            "  click then draw desired addition \n\n"\
            "  Subtract Selection- hold alt on \n"\
            "  initial click then draw desired \n"\
            "  removal \n\n"\
            "  Remove All Selections - press \n"\
            "  escape to remove the entire \n"\
            "  selection. \n\n"\
            "\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n"
        self.selected_tool = "Lasso"
        self.setCursor(QtCore.Qt.CrossCursor)
        self.update_tool()

    # Enable rectangle tool
    def enable_rectanlge_tool(self):
        if hasattr(self.parent_window, "active_tool_widget") and self.parent_window.active_tool_widget:
            self.parent_layout.removeWidget(self.parent_window.active_tool_widget)
            self.parent_window.active_tool_widget.deleteLater()
        self.parent_window.active_tool_widget = RectangularTool(self.parent_window.image_path, parent_window=self.parent_window)
        self.parent_window.tool_description = "\n  Rectangular Tool\n\n\n"\
            "  This tool allows you to draw \n"\
            "  rectangular selections\n\n"\
            "  Draw Rectangle - click and drag\n\n"\
            "  Add Rectangle - hold shift on initial \n"\
            "  click then drag to desired addition\n\n"\
            "  Subtract Rectangle - hold alt on \n"\
            "  initial click then drag to desired \n"\
            "  removal\n\n"\
            "  Lock to Square - whilst drawing, \n"\
            "  hold shift to lock rectangle into a \n"\
            "  square\n\n"\
            "  Lock around Point - whilst \n"\
            "  drawing, hold alt to lock rectangle \n"\
            "  around initial point\n"\
            "  Remove All Selections - press \n"\
            "  escape to remove the entire \n"\
            "  selection.\n\n"\
            "\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n"
        self.selected_tool = "Rectanlge"
        self.parent_window.setCursor(QtCore.Qt.CrossCursor)
        self.update_tool()

    # Enable ellipse tool
    def enable_ellipse_tool(self):
        if hasattr(self.parent_window, "active_tool_widget") and self.parent_window.active_tool_widget:
            self.parent_layout.removeWidget(self.parent_window.active_tool_widget)
            self.parent_window.active_tool_widget.deleteLater()
        self.parent_window.active_tool_widget = EllipticalTool(self.parent_window.image_path, parent_window=self.parent_window)
        self.parent_window.tool_description = "\n  Ellipse Tool\n\n\n"\
            "  This tool allows you to draw \n"\
            "  elliptical selections.\n\n"\
            "  Draw Ellipse - click and drag\n\n"\
            "  Add Ellipse - hold shift on initial \n"\
            "  click then drag to desired addition\n\n"\
            "  Subtract Ellipse - hold alt on initial \n"\
            "  click then drag to desired removal\n\n"\
            "  Lock to Circle- whilst drawing, hold \n"\
            "  shift to lock rectangle into a circle\n\n"\
            "  Lock around Point - whilst \n"\
            "  drawing, hold alt to lock ellipse \n"\
            "  around initial point.\n\n"\
            "  Remove All Selections - press \n"\
            "  escape to remove the entire \n"\
            "  selection.\n\n"\
            "\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n"
        self.selected_tool = "Ellipse"
        self.parent_window.setCursor(QtCore.Qt.CrossCursor)
        self.update_tool()

    # Enable polygonal tool
    def enable_polygonal_tool(self):
        if hasattr(self.parent_window, "active_tool_widget") and self.parent_window.active_tool_widget:
            self.parent_layout.removeWidget(self.parent_window.active_tool_widget)
            self.parent_window.active_tool_widget.deleteLater()
        self.parent_window.active_tool_widget = PolygonalTool(self.parent_window.image_path, parent_window=self.parent_window)
        self.parent_window.tool_description = "\n  Polygonal Lasso Tool \n\n\n"\
            "  This tool allows you to make \n"\
            "  polygonal selections by \n"\
            "  drawing point by point,\n"\
            "  ending the selection when \n"\
            "  you make contact with the \n"\
            "  original position.\n\n"\
            "  to do an additional selection. \n\n"\
            "  Press alt on initial click to do \n"\
            "  a removal of your previous \n"\
            "  selection.\n\n"\
            "  Press delete to delete the \n"\
            "  previous point if applicable \n"\
            "  or to remove the entire \n"\
            "  selection\n"\
            "\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n"
        self.selected_tool = "Polygon"
        self.parent_window.setCursor(QtCore.Qt.ArrowCursor)
        self.update_tool()
    
    # Enable transform tool
    def enable_transform_tool(self):
        if hasattr(self.parent_window, "active_tool_widget") and self.parent_window.active_tool_widget:
            self.parent_layout.removeWidget(self.parent_window.active_tool_widget)
            self.parent_window.active_tool_widget.deleteLater()
        self.parent_window.active_tool_widget = TransformTool(parent_window=self.parent_window)
        self.parent_window.tool_description =  "\n  Transform Tool\n\n\n"\
            "  This Tool allows you to \n"\
            "  manipulate the selected \n"\
            "  layer. \n\n"\
            "  Move - left click and drag\n\n"\
            "  Scale - left click and drag on the\n"\
            "  border of the image to scale it.\n\n"\
            "  Rotate - left click and drag on the \n"\
            "  outside of the image to rotate\n\n"\
            "\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n"
        self.selected_tool = "Transform"
        self.parent_window.setCursor(QtCore.Qt.SizeAllCursor)
        self.update_tool()