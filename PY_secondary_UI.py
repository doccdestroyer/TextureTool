import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__)))

import os
import PySide6
from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtWidgets import QPushButton, QWidget, QApplication, QMainWindow, QPushButton, QWidget, QLineEdit, QLabel, QVBoxLayout, QHBoxLayout, QSlider, QRadioButton, QButtonGroup, QComboBox, QDial, QMenu, QMenuBar, QColorDialog, QDockWidget, QListWidget, QMessageBox
from PySide6.QtCore import Qt, Signal
import unreal
import math
###TODO ADJUST IMPORTS TO INCLUDE WHATS ONLY NECESARY
#from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget, QLineEdit, QLabel, QVBoxLayout, QHBoxLayout, QSlider, QRadioButton, QButtonGroup, QComboBox, QDial, QMenu, QMenuBar, QColorDialog
from PySide6.QtGui import QPainterPath,  QPolygon, QPolygonF, QAction, QImage, QColor, QPixmap, QAction, QTransform, QIcon


# from PySide6.QtGui import (QAction, QFont, QIcon, QKeySequence,
#                            QTextCharFormat, QTextCursor, QTextTableFormat)
#from PySide6.QtPrintSupport import QPrintDialog, QPrinter
# from PySide6.QtWidgets import (QApplication, QDialog, QDockWidget,
#                                QFileDialog, QListWidget, QMainWindow,
#                                QMessageBox, QTextEdit)

import time
import PIL 
from PIL import Image, ImageEnhance, ImageOps, ImageQt, ImageFilter

import PY_tools
from PY_tools import PenTool, MoveTool, LassoTool, PolygonalTool, RectangularTool, EllipticalTool, TransformTool, TextureLayer

###############################################################
#                   DELETION WINDOW                           # 
###############################################################
class DeleteConfirmationWindow(QWidget):
    def __init__(self, parent = None):
        super(DeleteConfirmationWindow, self).__init__(parent)

        self.mainWindow= QMainWindow()
        #self.mainWindow.setParent(parent)
        self.parent_window = parent

        # button
        self.accept_button = QPushButton("Yes")
        self.accept_button.clicked.connect(self.aceept_button_clicked)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_button_clicked)

        # label
        self.label = QLabel()
        self.label.setText("Are you sure you want to delete this layer?")

        # radio button
        self.dont_show_again_radio_button = QRadioButton()
        self.dont_show_again_radio_button.setText("Don't show this again")
        self.dont_show_again_radio_button.clicked.connect(self.dont_show_again_enabled)

        # combine all in a layout
        layout = QVBoxLayout()

        button_layouts= QHBoxLayout()
        button_layouts.addWidget(self.accept_button)
        button_layouts.addWidget(self.cancel_button)
        layout.addWidget(self.label)
        layout.addWidget(self.dont_show_again_radio_button)
        layout.addLayout(button_layouts)

        container = QWidget()
        container.setLayout(layout)

        self.setStyleSheet("""
            background-color: #252525;
            color: #ffffff;
            font-family: Segoe UI;
            font-size: 12px;                 
        """)  

        self.mainWindow.setCentralWidget(container)


    def aceept_button_clicked(self, checked):
        self.parent_window.will_delete = True
        self.parent_window.delete_current_layer()
        self.parent_window.update()
        self.mainWindow.close()
        self.mainWindow.deleteLater()

    def cancel_button_clicked(self, checked):
        self.parent_window.will_delete = False
        self.parent_window.update()
        self.parent_window.delete_current_layer()
        self.mainWindow.close()
        self.mainWindow.deleteLater()

    def dont_show_again_enabled(self, checked):
        self.parent_window.show_delete_message = False
        self.parent_window.update()



###############################################################
#                       RENAMER MENU                          # 
###############################################################
class ChooseNameWindow(QMainWindow):
    
    def __init__(self):
        super().__init__()           
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        self.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint)
        #self.mainWindow= QMainWindow()
        #self.mainWindow.setParent(self)
        self.button = QPushButton("Apply Name Change")
        self.button.setCheckable(True)
        self.button.clicked.connect(self.buttonClicked)

        self.label = QLabel()

        self.lineEdit = QLineEdit()
        self.lineEdit.textChanged.connect(self.label.setText)
        self.lineEdit.setText('')


        layout = QVBoxLayout()
        layout.addWidget(self.button)
        layout.addWidget(self.lineEdit)
        layout.addWidget(self.label)

        container = QWidget()
        container.setLayout(layout)

        self.setStyleSheet("""
            background-color: #262626;
            color: #ffffff;
            font-family: Segoe UI;
            font-size: 12px;
            selection-background-color: #424242;                  
        """)  
 
        self.setCentralWidget(container)

        self.name = None
        self.button_clicked = False

    def buttonClicked(self, checked):
        self.button_clicked = True
        self.name = self.lineEdit.text() or "untitled"
        self.update()

    def getName(self):
        print("internal name", self.name)
        return self.name

    def launchWindow(self):
        ChooseNameWindow.window = ChooseNameWindow()
        ChooseNameWindow.window.show()
        ChooseNameWindow.window.setWindowTitle("WINDOW Demo")
        ChooseNameWindow.window.setObjectName("ToolWindow")
        unreal.parent_external_window_to_slate(ChooseNameWindow.window.winId())



class Slider(QWidget):
    value_changed = Signal(int)
    has_released_slider = Signal(bool)
    def __init__(self, parent, name, min, max, default):
        super().__init__(parent)
        self.parent_window = parent
 

        self.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setFixedSize(320, 25)
        self.setWindowTitle(name)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(min)
        self.slider.setMaximum(max)
        self.slider.setSliderPosition(default)
        self.slider.valueChanged.connect(self.sliderChanged)
        self.slider.sliderReleased.connect(self.slider_been_released)
        # self.slider.sliderReleased.connect(self.slider_released)

        self.texture_layers = parent.texture_layers

        self.setStyleSheet("""
            background-color: #252525;
            color: #ffffff;
            font-family: Segoe UI;
            font-size: 12px;
        """)  
 
        # self.setStyleSheet("""
        #     QSlider::groove:horizontal {
        #         border: 1px solid #999999;
        #         height: 8px;
        #         background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00FFFF, stop:1 #FF0000);

        #     }

        #     QSlider::handle:horizontal {
        #         background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b4b4b4, stop:1 #8f8f8f);
        #         border: 1px solid #5c5c5c;
        #         width: 10px;
        #         margin: -2px 0;
        #         border-radius: 3px;
        #     }
        # """)


        ################for layer in self.texture_layers: ADD ONCE LAYER SELECTION IS A THING
        self.original_pixmap = self.parent_window.base_pixmap
        self.original_image = self.original_pixmap.toImage()

        self.image_label = QLabel()
        
        
        #self.image_label.setPixmap(self.original_pixmap) #####################################################


        layout = QVBoxLayout()
        layout.addWidget(self.slider)
        #layout.addWidget(self.image_label) ##################################################################

        self.setLayout(layout)

    def reset(self,default):
        self.slider.setSliderPosition(default)

    def sliderChanged(self,value):
        # factor = value/100
        # image = self.original_image.convertToFormat(QImage.Format_ARGB32)
        
        # for pixelY in range(image.height()):
        #     for pixelX in range(image.width()):
        #         pixel_color = QColor(image.pixel(pixelX,pixelY))
        #         H,S,L,A = pixel_color.getHsl()
        #         S = int(S*factor)
        #         pixel_color.setHsl(H,S,L,A)
        #         image.setPixelColor(pixelX,pixelY,pixel_color)
        
        # self.image_label.setPixmap(QPixmap.fromImage(image))
        # #texture_layer = TextureLayer(self.image_label, QtCore.QPoint(100,100))
        # texture_layer2 = TextureLayer(QPixmap.fromImage(image), QtCore.QPoint(0,0))

        # self.parent_window.texture_layers[0] = texture_layer2
        # #self.parent_window.base_layer = texture_layer2

        # #move_tool_class = MoveTool(parent=parent_window)
        # self.parent_window.active_tool_widget.texture_layers[0] = texture_layer2

        #self.parent_window.active_tool_widget.update_overlay()
        # print("base texture layer updated")
        # self.parent_window.update()
        self.value_changed.emit(value)
    
    def slider_been_released(self):
        unreal.log(print("hi"))
        # self.setCursor(QtCore.Qt.ForbiddenCursor)
        # self.parent_window.use_low_res = False
        self.has_released_slider.emit(True)

        #self.has_released_slider.emit(True)

    
###############################################################
#                    TOOL SELECTION MENU                      #
###############################################################
class ToolSectionMenu(QMainWindow):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.parent_window = parent
        self.parent_layout = self.parent_window.layout

        self.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setFixedSize(32, 1000)
        self.setWindowTitle("Tool Menu")

        layout = QVBoxLayout(self)

        self.pen_tool = QRadioButton()
        self.pen_tool.setText('Pen')
        self.lasso_tool = QRadioButton()
        self.lasso_tool.setText('Lasso')
        self.rectangle_tool = QRadioButton()
        self.rectangle_tool.setText('Rectangle')
        self.ellipse_tool = QRadioButton()
        self.ellipse_tool.setText('Ellipse')
        self.polygonal_tool = QRadioButton()
        self.polygonal_tool.setText('Polygonal')
        self.move_tool = QRadioButton()
        self.move_tool.setText('Move')
        self.transform_tool = QRadioButton()
        self.transform_tool.setText('Transform')
        self.fill_tool = QRadioButton()
        self.fill_tool.setText('Fill')


        self.radioButtonGroup = QButtonGroup()
        self.radioButtonGroup.addButton(self.pen_tool)
        self.radioButtonGroup.addButton(self.lasso_tool)
        self.radioButtonGroup.addButton(self.rectangle_tool)
        self.radioButtonGroup.addButton(self.ellipse_tool)
        self.radioButtonGroup.addButton(self.polygonal_tool)
        self.radioButtonGroup.addButton(self.move_tool)
        self.radioButtonGroup.addButton(self.transform_tool)
        self.radioButtonGroup.addButton(self.fill_tool)

        layout.addWidget(self.pen_tool)
        layout.addWidget(self.lasso_tool)
        layout.addWidget(self.rectangle_tool)
        layout.addWidget(self.ellipse_tool)
        layout.addWidget(self.polygonal_tool)
        layout.addWidget(self.move_tool)
        layout.addWidget(self.transform_tool)
        # layout.addWidget(self.fill_tool)


        # for button in [self.pen_tool, self.rectangle_tool, self.ellipse_tool, self.lasso_tool, self.polygonal_tool, self.move_tool, self.transform_tool, self.fill_tool]:
        #     self.radioButtonGroup.addButton(button)
        #     button.clicked.connect(self.radioButtonGroupChanged)

        self.setStyleSheet("""
            background-color: #262626;
            color: #ffffff;
            font-family: Segoe UI;
            font-size: 12px;
            selection-background-color: #424242;                  
        """)  
 
        #self.pen_tool.setChecked(True)
        #self.radioButtonGroupChanged()
        # self.parent_window.active_tool_widget =  PenTool(self.image_path, self)
        self.selected_tool = "Pen"
        self.previous_selected_tool = None
        self.refresh_tool()

        # self._text_edit = QTextEdit()
        # self.setCentralWidget(self._text_edit)

        self.create_actions()
        self.create_tool_bars()

        self.setStyleSheet("""
            background-color: #2c2c2c;
            color: #ffffff;
            font-family: Segoe UI;
            font-size: 12px;
            selection-background-color: #424242;                  
        """)  
 
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



    def update_tool(self):
        if self.parent_window.active_tool_widget:
            self.parent_layout.insertWidget(0,self.parent_window.active_tool_widget)
            #parent_layout.insertWidget(1,self.parent_window.add_texture_button)
            self.parent_window.active_tool_widget.show()
            # if self.parent_window.active_tool_widget == self.move_tool or  self.parent_window.active_tool_widget == self.transform_tool:
            #     self.parent_window.setCursor(QtCore.Qt.ArrowCursor)
            # else: 
            #     self.parent_window.active_tool_widget.setCursor(QtCore.Qt.CrossCursor)

        self.parent_window.tool_description_label.setText(self.parent_window.tool_description)
        #self.parent_window.get_tool_description()
        self.parent_window.update()

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
        #self.parent_window.get_tool_description()
        # self.parent_window.update()


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
        if self.previous_selected_tool == self.selected_tool:
            self.previous_selected_tool = "Pen"


        
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