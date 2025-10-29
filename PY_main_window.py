

import unreal
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

import PY_secondary_UI
from PY_secondary_UI import ToolSectionMenu, Slider, DeleteConfirmationWindow, ChooseNameWindow, TextureLayer, MoveTool
#from PY_secondary_UI import ToolSectionMenu, Slider, DeleteConfirmationWindow, ChooseNameWindow, TextureLayer

# import PY_tools
# from PY_tools import PenTool, MoveTool, LassoTool, PolygonalTool, RectangularTool, EllipticalTool, TransformTool


class MainWindow(QMainWindow):
    def __init__(self, image_path):
        super().__init__()
        # import PY_secondary_UI
        # from PY_secondary_UI import ToolSectionMenu, Slider, DeleteConfirmationWindow, ChooseNameWindow, TextureLayer
        self.layers = ""
        self.received_value = 100
        self.pen_size = 2
        self.color = PySide6.QtGui.QColor.fromRgbF(0.000000, 0.000000, 0.000000, 1.000000)
        #self.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint)

        self.setWindowTitle("Selection Tools")
        self.image_path = image_path
        self.active_tool_widget = None

        self.scale_factor = 1.0
        self.pan_offset = QtCore.QPoint(0,0)
        self.texture_layers = []
        self.translucent_texture_layers = []

        self.pixmap = None

        # Load base image as first layer
        base_pixmap = QtGui.QPixmap(self.image_path)
        self.base_pixmap = QtGui.QPixmap(self.image_path)


        self.merged_selection_path = QPainterPath()
        self.selections_paths = []

        # self.image_label = QLabel()
        # self.image_label.setAlignment(Qt.AlignCenter)
        # self.image_label.setPixmap(base_pixmap)

        # base_pixmap = base_pixmap.scaled(base_pixmap)
        base_layer = TextureLayer(base_pixmap, QtCore.QPoint(0, 0))
        self.base_layer = TextureLayer(base_pixmap, QtCore.QPoint(0, 0))
        self.selected_layer = base_layer
        self.current_image = self.selected_layer.pixmap.toImage()
        self.selected_layer_index = 0

        self.original_image_location = self.selected_layer.position
        self.texture_layers.append(base_layer)
        self.translucent_texture_layers.append(base_layer)

        self.pen_overlay = QtGui.QPixmap(self.texture_layers[0].pixmap.size())
        self.pen_overlay.fill(QtCore.Qt.transparent)

        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setFocus()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)


        self.layout = QVBoxLayout(central_widget)
        self.setLayout(self.layout)

        self.active_tool_widget = MoveTool(parent_window=self)
        #self.layout.addWidget(self.active_tool_widget)
        #self.layout.insertWidget(0,self.active_tool_widget)
        #self.setFixedSize((self.active_tool_widget.size())*2)
        self.setFixedSize(1600,850)

        self.chosen_name = None
        self.never_rotated = True
        # self.saturation_panel = Slider(parent = self, name = "Saturation Slider", min = 0, max =100, default =100)
        # self.saturation_panel.show()
        # self.saturation_panel.value_changed.connect(self.adjust_saturation)

        # self.brightness_panel = Slider(self, "Brightness Slider" , 0, 199, 100)
        # self.brightness_panel.show()
        # self.brightness_panel.value_changed.connect(self.adjust_brightness)

        # self.tool_panel = ToolSectionMenu(parent=self)
        # self.tool_panel.show()



        # self.cyan_red_panel = Slider(self, "Colour Balance - Red " , 1, 100, 50)
        # self.cyan_red_panel.show()
        # self.cyan_red_panel.value_changed.connect(self.adjust_redness)

        # self.magenta_green_panel = Slider(self, "Colour Balance - Green " , 1, 100, 50)
        # self.magenta_green_panel.show()
        # self.magenta_green_panel.value_changed.connect(self.adjust_greenness)



        # #debug buttons

        # self.add_texture_button = QPushButton("Add Texture")
        # self.add_texture_button.clicked.connect(self.prompt_add_texture)
        # self.layout.insertWidget(1,self.add_texture_button)

        # self.export_flat_button = QPushButton("Export Flattened Image")
        # self.export_flat_button.clicked.connect(lambda: self.export_flattened_image(str(self.prompt_add_folder_path())))
        # self.layout.addWidget(self.export_flat_button)


        # self.export_addtions_button = QPushButton("Export Additons as PNG")
        # self.export_addtions_button.clicked.connect(lambda: self.export_flattened_additions(str(self.prompt_add_folder_path())))
        # self.layout.addWidget(self.export_addtions_button)

        # self.create_decal_button = QPushButton("Create Decal")
        # #self.create_decal_button.clicked.connect(lambda: self.export_flattened_additions(str(self.prompt_add_folder_path())))
        # self.create_decal_button.clicked.connect(lambda: self.create_decal(self.prompt_add_folder_path(), "M_DecalTest69"))
        # self.layout.addWidget(self.create_decal_button)


        self.tool_description = None

        self.CreateToolBar()

        self.base_image = self.base_pixmap.toImage()
        self.altered_image = self.base_image

        self.use_low_res = True
        self.resolution = 16

        self.saturation_value = 100
        self.brightness_value = 100
        self.contrast_value = 100
        self.redness_value = 0
        self.greenness_value = 0
        self.blueness_value = 0
        #self.gaussian_value = 0
        self.exposure_value = 0
        self.opacity_value = 255
        self.create_dock_windows()
        self.use_low_res = True
        self.active_tool_widget.setCursor(QtCore.Qt.CrossCursor)

        self.item = None

        item = self.layers.item(self.selected_layer_index)
        self.layers.setCurrentItem(item)

        self.layer_opacities = [255]

        self.setStyleSheet(f"""
            background-color: #2c2c2c;
            color: #ffffff;
            font-family: Segoe UI;
            font-size: 12px;
            border: 1px solid #434343;
        """) 

        QtGui.QShortcut(QtGui.QKeySequence("Ctrl++"), self, activated=self.zoom_in)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+="), self, activated=self.zoom_in)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+-"), self, activated=self.zoom_out)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+0"), self, activated=self.reset_zoom)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Shift+i"), self, activated=self.invert_selections)
        #QtGui.QShortcut(QtGui.QKeySequence("Space"), self, activated=self.start_panning)

    # def keyPressEvent(self, event):
    #     if event.key() == 16777216:
    #         self.clear_selections()


        self.will_delete = False
        self.show_delete_message = True
        self.resetting = False
    #def start_panning(self):
        
                            
    def change_layer(self, item):
        if self.opacity_value != self.layer_opacities[self.selected_layer_index]:
            self.layer_opacities[self.selected_layer_index] = self.opacity_value
        self.apply_full_resolution_adjustments()
        # self.item = item        
        print("LAYER CHANGED")
        print("item: ", item)
        for i in range (1, len(self.texture_layers)):
            if item.text() == "Base Layer":
                self.selected_layer = self.translucent_texture_layers[0]
                self.selected_layer_index = 0
                self.item = item
                print(item)
            else:
                if item.text() == ("Layer " + str(i)):
                    self.selected_layer = self.translucent_texture_layers[i]
                    self.selected_layer_index = i
        self.current_image = self.selected_layer.pixmap.toImage()
        self.altered_image = self.current_image

        #self.opacity_slider.reset(self.layer_opacities[self.selected_layer_index])
        self.never_rotated = True
        self.opacity_value = self.layer_opacities[self.selected_layer_index]

        #self.adjust_opacity(self.opacity_value)

        self.apply_full_resolution_adjustments()
        #self.use_low_res = True
    def color_dialog(self):
        self.color = QColorDialog.getColor()


        self.color_name = self.color.name()
        self.color_button.setStyleSheet(f"""
            background-color: {self.color_name};
            color: #ffffff;
            font-family: Segoe UI;
            font-size: 12px;
        """) 
        self.active_tool_widget.update_overlay()
        self.update()


    def create_dock_windows(self):
        self.color_button = QPushButton("Pick Color")
        self.color_button.setCheckable(True)
        self.color_button.clicked.connect(self.color_dialog)
        dock = QDockWidget("Colour", self)
        dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea
                             | Qt.DockWidgetArea.RightDockWidgetArea
                             | Qt.DockWidgetArea.TopDockWidgetArea)
        self.setDockOptions(QMainWindow.DockOption.AllowNestedDocks)
        self.color_button.setFixedSize(330,100)

        self.setStyleSheet("""
            background-color: #2c2c2c;
            color: #ffffff;
            font-family: Segoe UI;
            font-size: 12px;
            selection-background-color: #424242;                  
        """)  

        self.color_button.setStyleSheet(f"""
            background-color: #000000;
            color: #ffffff;
            font-family: Segoe UI;
            font-size: 12px;
        """) 


        # central_widget = QWidget()
        # layout = QVBoxLayout(central_widget)

        dock.setWidget(self.color_button)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)

        # #stackedLayout = QStackedLayout()

        self.clr_label = QLabel()
        self.clr_label.setText(self.color.name())


        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)

        dock = QDockWidget("Colour Balance", self)
        self.cyan_red_panel = Slider(self, "Colour Balance - Red " , -80, 80, 0)
        self.cyan_red_panel.value_changed.connect(self.adjust_redness)
        self.cyan_red_panel.has_released_slider.connect(self.apply_1k_resolution_adjustments)

        dock.setLayout(layout)


        self.cyan_red_panel.setStyleSheet("""
                QSlider::groove:horizontal {
                    border: 1px solid #999999;
                    height: 5px;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00FFFF, stop:1 #FF0000);

                }

                QSlider::handle:horizontal {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b4b4b4, stop:1 #8f8f8f);
                    border: 1px solid #5c5c5c;
                    width: 10px;
                    margin: -2px 0;
                    border-radius: 3px;
                }
            """)


        # self.cyan_red_panel.setStyleSheet("""
        #     background-color: #252525;
        #     color: #ffffff;
        #     font-family: Segoe UI;
        #     background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00FFFF, stop:1 #FF0000);
        #     font-size: 12px;
                                          
        #     QSlider::groove:horizontal {
        #         border: 1px solid #999999;
        #         height: 8px;
        #         background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00FFFF, stop:1 #00FFFF);
        #         margin: 2px 0;
        #     }
        # """)  
 

        # self.cyan_red_panel.setStyleSheet("""
        #     QSlider::groove:horizontal {
        #         border: 1px solid #999999;
        #         height: 8px;
        #         background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00FFFF, stop:1 #FF0000);
        #         margin: 2px 0;
        #     }
        # """)


        self.magenta_green_panel = Slider(self, "Colour Balance - Green " , -80, 80, 0)
        self.magenta_green_panel.value_changed.connect(self.adjust_greenness)
        self.magenta_green_panel.has_released_slider.connect(self.apply_1k_resolution_adjustments)

        # self.magenta_green_panel = Slider(self, "Colour Balance - Green " , -90, 90, 0)
        # self.magenta_green_panel.value_changed.connect(self.adjust_magneta)


        self.magenta_green_panel.setStyleSheet("""
                QSlider::groove:horizontal {
                    border: 1px solid #999999;
                    height: 5px;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FF00FF, stop:1 #00FF00);

                }

                QSlider::handle:horizontal {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b4b4b4, stop:1 #8f8f8f);
                    border: 1px solid #5c5c5c;
                    width: 10px;
                    margin: -2px 0;
                    border-radius: 3px;
                }
            """)
        self.yellow_blue_panel = Slider(self, "Colour Balance - Blue " , -80, 80, 0)
        self.yellow_blue_panel.value_changed.connect(self.adjust_blueness)
        self.yellow_blue_panel.has_released_slider.connect(self.apply_1k_resolution_adjustments)

        self.yellow_blue_panel.setStyleSheet("""
                QSlider::groove:horizontal {
                    border: 1px solid #999999;
                    height: 5px;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FFFF00, stop:1 #0000FF);

                }

                QSlider::handle:horizontal {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b4b4b4, stop:1 #8f8f8f);
                    border: 1px solid #5c5c5c;
                    width: 10px;
                    margin: -2px 0;
                    border-radius: 3px;
                }
            """)
        
        layout.addWidget(self.cyan_red_panel)
        layout.addWidget(self.magenta_green_panel)
        layout.addWidget(self.yellow_blue_panel)

        # self.setCentralWidget(central_widget)
        dock.setWidget(central_widget)
        #dock.setLayout(layout)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)

        internal_layout = QHBoxLayout(central_widget)

        dock = QDockWidget("Layer Opacity", self)
        self.opacity_slider = Slider(self, "Opacity", 0,255,255)
        self.opacity_slider.value_changed.connect(self.adjust_opacity)
        self.opacity_slider.has_released_slider.connect(self.apply_full_resolution_adjustments)
        self.opacity_slider.setFixedSize(320, 25)
        #layout.addWidget(self.opacity_slider)
        dock.setWidget(self.opacity_slider)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)


        dock = QDockWidget("Layers", self)

        self.new_layer_button = QPushButton("Add New Layer")
        self.new_layer_button.setCheckable(True)
        self.new_layer_button.clicked.connect(self.add_layer)
        internal_layout.addWidget(self.new_layer_button)

        self.delete_layer_button = QPushButton("Delete Current Layer")
        self.delete_layer_button.setCheckable(True)
        self.delete_layer_button.clicked.connect(self.show_delete_box)
        internal_layout.addWidget(self.delete_layer_button)


        self.layers = QListWidget(dock)
        self.layers.setFocus()
        i = 0
        for layer in self.texture_layers:
            if i == 0:
                self.layers.addItem("Base Layer")
            else:
                self.layers.addItem("Layer "+ str(i))
            i+=1

        # self.layers.addItems((
        #     "Layer 2",
        #     "Layer 1",
        #     "Base Layer"))
        self.layers.itemClicked.connect(self.change_layer)

        layout.addLayout(internal_layout)
        layout.addWidget(self.layers)

        dock.setWidget(central_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)



        descript_dock = QDockWidget("Tool User Guide", self)
        self.tool_description_label = QLabel(self.tool_description)
        descript_dock.setWidget(self.tool_description_label)
        descript_dock.setFixedSize(225,1000)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, descript_dock)

        descript_zoom_dock = QDockWidget("Zoom/Pan User Guide", self)
        self.tool_zoom_label = QLabel(
        "\n  Pan                       -      Space and Drag\n\n" \
        "  Zoom In              -      Ctrl +\n\n" \
        "  Zoom Out           -      Ctrl -\n\n" \
        "  Reset Zoom        -      Ctrl 0\n\n"\
        "  Invert Selection  -      Ctrl Shift i"\
        "\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\nn\n\n\n")
        descript_zoom_dock.setWidget(self.tool_zoom_label)
        descript_zoom_dock.setFixedSize(225,300)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, descript_zoom_dock)

        tool_dock = QDockWidget("Tools", self)
        self.tool_panel = ToolSectionMenu(parent=self)
        tool_dock.setFixedSize(32,500)
        #dock.setWidget(self.tool_panel)
        #self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)

        tool_dock.setWidget(self.tool_panel)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, tool_dock)


        # Split dock1 to the right to show dock2 beside it
        self.splitDockWidget(descript_dock, tool_dock, Qt.Horizontal)



        dock = QDockWidget("Saturation", self)
        self.saturation_panel = Slider(parent = self, name = "Saturation Slider", min = 0, max =200, default =100)
        self.saturation_panel.value_changed.connect(self.adjust_saturation)
        self.saturation_panel.has_released_slider.connect(self.apply_1k_resolution_adjustments)



        dock.setWidget(self.saturation_panel)
        self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, dock)

        self.saturation_panel.setStyleSheet("""
                QSlider::groove:horizontal {
                    border: 1px solid #999999;
                    height: 5px;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #818181, stop:1 #FF0000);

                }

                QSlider::handle:horizontal {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b4b4b4, stop:1 #8f8f8f);
                    border: 1px solid #5c5c5c;
                    width: 10px;
                    margin: -2px 0;
                    border-radius: 3px;
                }
            """)

        dock = QDockWidget("Exposure", self)
        self.exposure_panel = Slider(self, "Expsure Slider" , -100, 100, 0)
        self.exposure_panel.value_changed.connect(self.adjust_exposure)
        self.exposure_panel.has_released_slider.connect(self.apply_1k_resolution_adjustments)
        dock.setWidget(self.exposure_panel)
        self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, dock)


        self.exposure_panel.setStyleSheet("""
                QSlider::groove:horizontal {
                    border: 1px solid #999999;
                    height: 5px;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #000000, stop:1 #FFFFFF);

                }

                QSlider::handle:horizontal {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b4b4b4, stop:1 #8f8f8f);
                    border: 1px solid #5c5c5c;
                    width: 10px;
                    margin: -2px 0;
                    border-radius: 3px;
                }
            """)


        dock = QDockWidget("Brightness", self)
        self.brightness_panel = Slider(self, "Brightness Slider" , 0, 199, 100)
        self.brightness_panel.value_changed.connect(self.adjust_brightness)
        self.brightness_panel.has_released_slider.connect(self.apply_1k_resolution_adjustments)
        dock.setWidget(self.brightness_panel)
        self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, dock)


        self.brightness_panel.setStyleSheet("""
                QSlider::groove:horizontal {
                    border: 1px solid #999999;
                    height: 5px;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #000000, stop:1 #FFFFFF);

                }

                QSlider::handle:horizontal {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b4b4b4, stop:1 #8f8f8f);
                    border: 1px solid #5c5c5c;
                    width: 10px;
                    margin: -2px 0;
                    border-radius: 3px;
                }
            """)

 
        dock = QDockWidget("Contrast", self)
        self.contrast_panel = Slider(self, "Contrast Slider" , 0, 199, 100)
        self.contrast_panel.value_changed.connect(self.adjust_contrast)
        self.contrast_panel.has_released_slider.connect(self.apply_1k_resolution_adjustments)

        dock.setWidget(self.contrast_panel)
        self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, dock)


        self.contrast_panel.setStyleSheet("""
                QSlider::groove:horizontal {
                    border: 1px solid #999999;
                    height: 5px;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #818181, stop:1 #000000);

                }

                QSlider::handle:horizontal {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b4b4b4, stop:1 #8f8f8f);
                    border: 1px solid #5c5c5c;
                    width: 10px;
                    margin: -2px 0;
                    border-radius: 3px;
                }
            """)


        # dock = QDockWidget("Gaussian Blur", self)
        # self.gaussian_panel = Slider(self, "Gaussian Slider" , 0, 100, 0)
        # self.gaussian_panel.value_changed.connect(self.adjust_gaussian)
        # dock.setWidget(self.gaussian_panel)
        # self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, dock)

        # self.gaussian_panel.setStyleSheet("""
        #         QSlider::groove:horizontal {
        #             border: 1px solid #999999;
        #             height: 5px;
        #             background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #000000, stop:1 #FFFFFF);

        #         }

        #         QSlider::handle:horizontal {
        #             background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b4b4b4, stop:1 #8f8f8f);
        #             border: 1px solid #5c5c5c;
        #             width: 10px;
        #             margin: -2px 0;
        #             border-radius: 3px;
        #         }
        #     """)





        dock = QDockWidget("Apply Sliders", self)
        self.apply_button = QPushButton("Apply")
        self.apply_button.setCheckable(True)
        self.apply_button.clicked.connect(self.apply_full_resolution_adjustments)
        self.apply_button.setFixedSize(157,25)
        dock.setWidget(self.apply_button)
        self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, dock)

        dock = QDockWidget("Reset Sliders", self)
        self.reset_button = QPushButton("Reset")
        self.reset_button.setCheckable(True)
        self.reset_button.clicked.connect(self.reset_sliders)
        self.reset_button.setFixedSize(157,25)
        dock.setWidget(self.reset_button)
        self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, dock)
    # def update_tool_description(self):
    #     self.tool_description = self.get_tool_description()
    #     unreal.log(self.tool_description)
    #     self.update()
    #     return self.tool_description

    # def get_tool_description(self):
    #     if self.active_tool_widget == PenTool(self.image_path, self):
    #         print("pen selected")
    #         unreal.log("pem selected")
    #         return ("THIS IS A PEN DESCRIPTION I BEG PLEASE WORK")
    #     if self.active_tool_widget == MoveTool(parent_window=self):
    #         print("penMOVE selected")
    #         unreal.log("move selected")
    #         return ("THIS IS A MOOOOOVE DESCRIPTION I BEG PLEASE WORK")
    #     else:
    #         return ("LOL")
    #     unreal.log("UPDATED")

    def add_layer(self):
        new_pixmap = QtGui.QPixmap(self.base_image.size())
        new_pixmap.fill(QtCore.Qt.transparent)
        #new_pixmap = QtGui.QPixmap()
        new_layer = TextureLayer(new_pixmap, QtCore.QPoint(0, 0))
        self.texture_layers.append(new_layer)
        self.translucent_texture_layers.append(new_layer)

        if self.active_tool_widget:
            self.active_tool_widget.update()

        self.layers.addItem("Layer "+ str(len(self.texture_layers)-1))
        self.layer_opacities.append(255)
        self.update()

    def delete_current_layer(self):
        if self.will_delete == True:
            self.texture_layers.remove(self.texture_layers[self.selected_layer_index])
            self.layer_opacities.remove(self.layer_opacities[self.selected_layer_index])
            self.translucent_texture_layers.remove(self.translucent_texture_layers[self.selected_layer_index])

            self.rewrite_layers()

            self.selected_layer = self.texture_layers[self.selected_layer_index-1]
            self.selected_layer_index = self.selected_layer_index-1
            item = self.layers.item(self.selected_layer_index)
            self.layers.setCurrentItem(item)
            self.will_delete = False
            self.update()

            
    def show_delete_box(self):
        if self.selected_layer_index != 0:
            if self.show_delete_message == True:
                self.show_delete_confirmation()
            else:
                self.will_delete = True
                self.delete_current_layer()


        else:
            self.show_cannot_delete_message()

    def show_delete_confirmation(self):
        self.window = DeleteConfirmationWindow(self)
        self.window.mainWindow.show()
        self.window.setWindowTitle("Delete Confirmation")
        self.window.setObjectName("deleteConfirmationWindow")
        #unreal.parent_external_window_to_slate(DeleteConfirmationWindow.window.winId())




    def show_cannot_delete_message(self):
        QMessageBox.about(self, "Error",
                          "You canno delete the base layer!\n\n"
                          "If you wish to export without the base layer,"
                          "select File > Export > Export Flattened Additons.")
        
    def adjust_all_but_self(self, current_adjustment):
        sliders_changed = 1
        self.adjust_resolution(sliders_changed)



        if current_adjustment != "rednesss" and self.redness_value != 0:
            self.adjust_redness(self.redness_value)
            sliders_changed += 1
            self.adjust_resolution(sliders_changed)

        if current_adjustment != "greenness" and self.greenness_value != 0:
            self.adjust_greenness(self.greenness_value)
            sliders_changed += 1
            self.adjust_resolution(sliders_changed)

        if current_adjustment != "blueness" and self.blueness_value != 0:
            self.adjust_blueness(self.blueness_value)
            sliders_changed += 1
            self.adjust_resolution(sliders_changed)

        if current_adjustment != "brightness" and self.brightness_value != 100:
            self.adjust_brightness(self.brightness_value)
            sliders_changed += 1
            self.adjust_resolution(sliders_changed)

        if current_adjustment != "saturation" and self.saturation_value != 100:
            self.adjust_saturation(self.saturation_value)
            sliders_changed += 1
            self.adjust_resolution(sliders_changed)
        
        if current_adjustment != "exposure" and self.exposure_value != 0:
            self.adjust_exposure(self.exposure_value)
            sliders_changed += 1
            self.adjust_resolution(sliders_changed)

        if current_adjustment != "contrast" and self.contrast_value != 100:
            self.adjust_contrast(self.contrast_value)
            sliders_changed += 1
            self.adjust_resolution(sliders_changed)

        if current_adjustment != "opacity":
            self.adjust_opacity(self.opacity_value)
        self.tool_panel.refresh_tool()
        # self.altered_image = self.current_image

    def adjust_resolution(self,sliders_changed):

        if sliders_changed > 6:
            self.resolution = 16
        elif sliders_changed > 4:
            self.resolution = 32
        elif sliders_changed > 2:
            self.resolution = 32
        elif sliders_changed > 1:
            self.resolution = 32
        else:
            self.resolution = 64
        self.adjust_apply_button_colour(sliders_changed)

    def adjust_apply_button_colour(self, sliders_changed_amount):
        if sliders_changed_amount > 0:
            self.apply_button.setStyleSheet("""
                background-color: #7A7A7A;
                color: #ffffff;
                font-family: Segoe UI;
                font-size: 12px;
                selection-background-color: #424242;                  
            """)    

        else:
            self.apply_button.setStyleSheet("""
                background-color: #2c2c2c;
                color: #ffffff;
                font-family: Segoe UI;
                font-size: 12px;
                selection-background-color: #424242;                  
            """)   
        self.update()          





    def adjust_greenness(self,value):
            factor = abs(value)/100
            if self.use_low_res:
                #original_image = self.base_image.convertToFormat(QImage.Format_ARGB32)
                self.original_image_location = self.selected_layer.position
                #original_image = self.base_image.convertToFormat(QImage.Format_ARGB32)

                self.low_res_image = self.altered_image.scaled(self.resolution, self.resolution, Qt.KeepAspectRatio, Qt.SmoothTransformation)


                #image = self.low_res_image.convertToFormat(QImage.Format_ARGB32)


                altered_image = self.low_res_image.convertToFormat(QImage.Format_ARGB32)

                pillow_image = ImageQt.fromqimage(altered_image)

                # for pixelY in range(altered_image.height()):
                #     for pixelX in range (altered_image.width()):
                #         pixel_color = QColor(altered_image.pixel(pixelX,pixelY))
                #         H,S,L,A = pixel_color.getHsl()



                if value < 0:
                    colorize_ops = ImageOps.colorize(pillow_image.convert('L'), mid = 'magenta', black = 'black', white = 'white').convert('RGBA')
                    #coloured_image = ImageQt.ImageQt(colorize_ops)
                    colorize_ops = colorize_ops.convert('RGBA')
                    pillow_image = pillow_image.convert('RGBA')
                    pillow_image = Image.blend(pillow_image,colorize_ops,factor)
                    #pillow_image = colorize_ops

                elif value >0:
                    colorize_ops = ImageOps.colorize(pillow_image.convert('L'), mid = 'green', black = 'black', white = 'white')
                    colorize_ops = colorize_ops.convert('RGBA')
                    pillow_image = pillow_image.convert('RGBA')
                    #coloured_image = ImageQt.ImageQt(colorize_ops)
                    pillow_image = Image.blend(pillow_image,colorize_ops,factor) 
                    #pillow_image = colorize_ops


                # pillow_image = Image.blend(pillow_image,coloured_image,factor) 






                new_qimage = ImageQt.ImageQt(pillow_image).convertToFormat(QImage.Format_ARGB32)

                display_size = self.current_image.size()  # QImage.size() gives QSize
                new_qimage = new_qimage.scaled(display_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)


                #self.base_pixmap = QPixmap.fromImage(image)
                self.altered_pixmap = QPixmap.fromImage(new_qimage)

                updated_texture = TextureLayer(QPixmap.fromImage(new_qimage), self.original_image_location)
                #update textures
                #index = self.texture_layers.index(self.selected_layer)
                self.texture_layers[self.selected_layer_index] = updated_texture
                self.translucent_texture_layers[self.selected_layer_index] = updated_texture

                #self.active_tool_widget.texture_layers[0] = updated_texture
                self.active_tool_widget.update_overlay()
                

                self.altered_image = new_qimage

                if value != self.greenness_value:
                    self.adjust_all_but_self("greenness")
                    self.altered_image = self.current_image

                self.greenness_value= value

                #self.base_image = self.base_pixmap.toImage()
                ########################
                ####self.altered_image = self.altered_pixmap.toImage()
                #####self.adjust_saturation(self.saturation_value)
                self.update()
            else:
                self.setCursor(QtCore.Qt.ForbiddenCursor)
                self.original_image_location = self.selected_layer.position

                #image = self.base_image.convertToFormat(QImage.Format_ARGB32)
                altered_image = self.altered_image.convertToFormat(QImage.Format_ARGB32)
                pillow_image = ImageQt.fromqimage(altered_image)

                # for pixelY in range(altered_image.height()):
                #     for pixelX in range (altered_image.width()):
                #         pixel_color = QColor(altered_image.pixel(pixelX,pixelY))
                #         H,S,L,A = pixel_color.getHsl()


                if value < 0:
                    colorize_ops = ImageOps.colorize(pillow_image.convert('L'), mid = 'magenta', black = 'black', white = 'white').convert('RGBA')
                    #coloured_image = ImageQt.ImageQt(colorize_ops)
                    colorize_ops = colorize_ops.convert('RGBA')
                    pillow_image = pillow_image.convert('RGBA')
                    pillow_image = Image.blend(pillow_image,colorize_ops,factor)
                    #pillow_image = colorize_ops

                elif value >0:
                    colorize_ops = ImageOps.colorize(pillow_image.convert('L'), mid = 'green', black = 'black', white = 'white')
                    colorize_ops = colorize_ops.convert('RGBA')
                    pillow_image = pillow_image.convert('RGBA')
                    #coloured_image = ImageQt.ImageQt(colorize_ops)
                    pillow_image = Image.blend(pillow_image,colorize_ops,factor) 
                    #pillow_image = colorize_ops


                new_qimage = ImageQt.ImageQt(pillow_image).convertToFormat(QImage.Format_ARGB32)


                #self.base_pixmap = QPixmap.fromImage(image)
                self.altered_pixmap = QPixmap.fromImage(new_qimage)

                updated_texture = TextureLayer(QPixmap.fromImage(new_qimage), self.original_image_location)
                #update textures
                #index = self.texture_layers.index(self.selected_layer)
                self.texture_layers[self.selected_layer_index] = updated_texture
                self.translucent_texture_layers[self.selected_layer_index] = updated_texture

                #self.active_tool_widget.texture_layers[0] = updated_texture
                self.active_tool_widget.update_overlay()

                #self.base_image = self.base_pixmap.toImage()
                ########################
                self.altered_image = self.altered_pixmap.toImage()
                #self.adjust_saturation(self.saturation_value)
                self.magenta_green_panel.reset(0)
                self.greenness_value = 0
                self.update()

    def adjust_blueness(self,value):
            factor = abs(value)/100
            if self.use_low_res:
                #original_image = self.base_image.convertToFormat(QImage.Format_ARGB32)
                self.original_image_location = self.selected_layer.position
                #original_image = self.base_image.convertToFormat(QImage.Format_ARGB32)

                self.low_res_image = self.altered_image.scaled(self.resolution, self.resolution, Qt.KeepAspectRatio, Qt.SmoothTransformation)


                #image = self.low_res_image.convertToFormat(QImage.Format_ARGB32)


                altered_image = self.low_res_image.convertToFormat(QImage.Format_ARGB32)

                pillow_image = ImageQt.fromqimage(altered_image)

                # for pixelY in range(altered_image.height()):
                #     for pixelX in range (altered_image.width()):
                #         pixel_color = QColor(altered_image.pixel(pixelX,pixelY))
                #         H,S,L,A = pixel_color.getHsl()



                if value < 0:
                    colorize_ops = ImageOps.colorize(pillow_image.convert('L'), mid = 'yellow', black = 'black', white = 'white').convert('RGBA')
                    #coloured_image = ImageQt.ImageQt(colorize_ops)
                    colorize_ops = colorize_ops.convert('RGBA')
                    pillow_image = pillow_image.convert('RGBA')
                    pillow_image = Image.blend(pillow_image,colorize_ops,factor)
                    #pillow_image = colorize_ops

                elif value >0:
                    colorize_ops = ImageOps.colorize(pillow_image.convert('L'), mid = 'blue', black = 'black', white = 'white')
                    colorize_ops = colorize_ops.convert('RGBA')
                    pillow_image = pillow_image.convert('RGBA')
                    #coloured_image = ImageQt.ImageQt(colorize_ops)
                    pillow_image = Image.blend(pillow_image,colorize_ops,factor) 
                    #pillow_image = colorize_ops


                # pillow_image = Image.blend(pillow_image,coloured_image,factor) 






                new_qimage = ImageQt.ImageQt(pillow_image).convertToFormat(QImage.Format_ARGB32)

                display_size = self.current_image.size()  # QImage.size() gives QSize
                new_qimage = new_qimage.scaled(display_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)


                #self.base_pixmap = QPixmap.fromImage(image)
                self.altered_pixmap = QPixmap.fromImage(new_qimage)

                updated_texture = TextureLayer(QPixmap.fromImage(new_qimage), self.original_image_location)
                #update textures
                #index = self.texture_layers.index(self.selected_layer)
                self.texture_layers[self.selected_layer_index] = updated_texture
                self.translucent_texture_layers[self.selected_layer_index] = updated_texture
                self.active_tool_widget.update_overlay()
                #self.base_image = self.base_pixmap.toImage()
                ########################
                ####self.altered_image = self.altered_pixmap.toImage()
                #####self.adjust_saturation(self.saturation_value)

                self.altered_image = new_qimage

                if value != self.blueness_value:

                    self.adjust_all_but_self("blueness")
                    self.altered_image = self.current_image


                self.blueness_value = value

                self.update()
            else:
                self.setCursor(QtCore.Qt.ForbiddenCursor)
                self.original_image_location = self.selected_layer.position

                #image = self.base_image.convertToFormat(QImage.Format_ARGB32)
                altered_image = self.altered_image.convertToFormat(QImage.Format_ARGB32)
                pillow_image = ImageQt.fromqimage(altered_image)

                # for pixelY in range(altered_image.height()):
                #     for pixelX in range (altered_image.width()):
                #         pixel_color = QColor(altered_image.pixel(pixelX,pixelY))
                #         H,S,L,A = pixel_color.getHsl()


                if value < 0:
                    colorize_ops = ImageOps.colorize(pillow_image.convert('L'), mid = 'yellow', black = 'black', white = 'white').convert('RGBA')
                    #coloured_image = ImageQt.ImageQt(colorize_ops)
                    colorize_ops = colorize_ops.convert('RGBA')
                    pillow_image = pillow_image.convert('RGBA')
                    pillow_image = Image.blend(pillow_image,colorize_ops,factor)
                    #pillow_image = colorize_ops

                elif value >0:
                    colorize_ops = ImageOps.colorize(pillow_image.convert('L'), mid = 'blue', black = 'black', white = 'white')
                    colorize_ops = colorize_ops.convert('RGBA')
                    pillow_image = pillow_image.convert('RGBA')
                    #coloured_image = ImageQt.ImageQt(colorize_ops)
                    pillow_image = Image.blend(pillow_image,colorize_ops,factor) 
                    #pillow_image = colorize_ops


                new_qimage = ImageQt.ImageQt(pillow_image).convertToFormat(QImage.Format_ARGB32)


                #self.base_pixmap = QPixmap.fromImage(image)
                self.altered_pixmap = QPixmap.fromImage(new_qimage)

                updated_texture = TextureLayer(QPixmap.fromImage(new_qimage), self.original_image_location)
                #update textures
                #index = self.texture_layers.index(self.selected_layer)
                self.texture_layers[self.selected_layer_index] = updated_texture
                self.translucent_texture_layers[self.selected_layer_index] = updated_texture
                self.active_tool_widget.update_overlay()

                #self.base_image = self.base_pixmap.toImage()
                ########################
                self.altered_image = self.altered_pixmap.toImage()
                #self.adjust_saturation(self.saturation_value)
                self.yellow_blue_panel.reset(0)
                self.blueness_value = 0
                self.update()

    def adjust_gaussian(self,value):
            factor = value/10
            if self.use_low_res:
                #original_image = self.base_image.convertToFormat(QImage.Format_ARGB32)
                self.original_image_location = self.selected_layer.position
                #original_image = self.base_image.convertToFormat(QImage.Format_ARGB32)

                self.low_res_image = self.altered_image.scaled(self.resolution, self.resolution, Qt.KeepAspectRatio, Qt.SmoothTransformation)


                #image = self.low_res_image.convertToFormat(QImage.Format_ARGB32)


                altered_image = self.low_res_image.convertToFormat(QImage.Format_ARGB32)

                pillow_image = ImageQt.fromqimage(altered_image)


                image_gaussblur = pillow_image.filter(ImageFilter.GaussianBlur(radius = factor))
                new_qimage = ImageQt.ImageQt(image_gaussblur).convertToFormat(QImage.Format_ARGB32)

                display_size = self.current_image.size()  # QImage.size() gives QSize
                new_qimage = new_qimage.scaled(display_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)


                #self.base_pixmap = QPixmap.fromImage(image)
                self.altered_pixmap = QPixmap.fromImage(new_qimage)

                updated_texture = TextureLayer(QPixmap.fromImage(new_qimage), self.original_image_location)
                #update textures
                #index = self.texture_layers.index(self.selected_layer)
                self.texture_layers[self.selected_layer_index] = updated_texture
                #self.active_tool_widget.texture_layers[0] = updated_texture
                self.active_tool_widget.update_overlay()



                self.altered_image = new_qimage

                if value != self.gaussian_value:
                    self.adjust_all_but_self("gaussian")
                    self.altered_image = self.base_image


                self.gaussian_value = value
                #self.base_image = self.base_pixmap.toImage()
                ########################
                ####self.altered_image = self.altered_pixmap.toImage()
                #####self.adjust_saturation(self.saturation_value)
                self.update()
            else:
                self.setCursor(QtCore.Qt.ForbiddenCursor)

                #image = self.base_image.convertToFormat(QImage.Format_ARGB32)
                altered_image = self.altered_image.convertToFormat(QImage.Format_ARGB32)
                pillow_image = ImageQt.fromqimage(altered_image)

                image_gaussblur = pillow_image.filter(ImageFilter.GaussianBlur(radius = factor))
                new_qimage = ImageQt.ImageQt(image_gaussblur).convertToFormat(QImage.Format_ARGB32)


                #self.base_pixmap = QPixmap.fromImage(image)
                self.altered_pixmap = QPixmap.fromImage(new_qimage)

                updated_texture = TextureLayer(QPixmap.fromImage(new_qimage), self.original_image_location)
                #update textures
                #index = self.texture_layers.index(self.selected_layer)
                self.texture_layers[self.selected_layer_index] = updated_texture
                #self.active_tool_widget.texture_layers[0] = updated_texture
                self.active_tool_widget.update_overlay()

                #self.base_image = self.base_pixmap.toImage()
                ########################
                self.altered_image = self.altered_pixmap.toImage()
                #self.adjust_saturation(self.saturation_value)
                self.gaussian_panel.reset(0)
                self.gaussian_value = 0
                self.tool_panel.refresh_tool()

                self.update()

    def adjust_redness(self,value):
            factor = abs(value)/100
            if self.use_low_res:
                #original_image = self.base_image.convertToFormat(QImage.Format_ARGB32)
                self.original_image_location = self.selected_layer.position
                #original_image = self.base_image.convertToFormat(QImage.Format_ARGB32)

                self.low_res_image = self.altered_image.scaled(self.resolution, self.resolution, Qt.KeepAspectRatio, Qt.SmoothTransformation)


                #image = self.low_res_image.convertToFormat(QImage.Format_ARGB32)


                altered_image = self.low_res_image.convertToFormat(QImage.Format_ARGB32)

                pillow_image = ImageQt.fromqimage(altered_image)

                # for pixelY in range(altered_image.height()):
                #     for pixelX in range (altered_image.width()):
                #         pixel_color = QColor(altered_image.pixel(pixelX,pixelY))
                #         H,S,L,A = pixel_color.getHsl()



                if value < 0:
                    colorize_ops = ImageOps.colorize(pillow_image.convert('L'), mid = 'aqua', black = 'black', white = 'white').convert('RGBA')
                    #coloured_image = ImageQt.ImageQt(colorize_ops)
                    colorize_ops = colorize_ops.convert('RGBA')
                    pillow_image = pillow_image.convert('RGBA')
                    pillow_image = Image.blend(pillow_image,colorize_ops,factor)
                    #pillow_image = colorize_ops

                elif value >0:
                    colorize_ops = ImageOps.colorize(pillow_image.convert('L'), mid = 'red', black = 'black', white = 'white')
                    colorize_ops = colorize_ops.convert('RGBA')
                    pillow_image = pillow_image.convert('RGBA')
                    #coloured_image = ImageQt.ImageQt(colorize_ops)
                    pillow_image = Image.blend(pillow_image,colorize_ops,factor) 
                    #pillow_image = colorize_ops


                # pillow_image = Image.blend(pillow_image,coloured_image,factor) 






                new_qimage = ImageQt.ImageQt(pillow_image).convertToFormat(QImage.Format_ARGB32)

                display_size = self.current_image.size()  # QImage.size() gives QSize
                new_qimage = new_qimage.scaled(display_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)


                #self.base_pixmap = QPixmap.fromImage(image)
                self.altered_pixmap = QPixmap.fromImage(new_qimage)

                updated_texture = TextureLayer(QPixmap.fromImage(new_qimage), self.original_image_location)
                #update textures
                #index = self.texture_layers.index(self.selected_layer)
                self.texture_layers[self.selected_layer_index] = updated_texture
                self.translucent_texture_layers[self.selected_layer_index] = updated_texture
                self.active_tool_widget.update_overlay()


                self.altered_image = new_qimage


                if value != self.redness_value:
                    self.adjust_all_but_self("redness")
                    self.altered_image = self.current_image


                self.redness_value = value

                #self.base_image = self.base_pixmap.toImage()
                ########################
                ####self.altered_image = self.altered_pixmap.toImage()
                #####self.adjust_saturation(self.saturation_value)
                self.update()
            else:
                self.setCursor(QtCore.Qt.ForbiddenCursor)
                self.original_image_location = self.selected_layer.position

                #image = self.base_image.convertToFormat(QImage.Format_ARGB32)
                altered_image = self.altered_image.convertToFormat(QImage.Format_ARGB32)
                pillow_image = ImageQt.fromqimage(altered_image)

                # for pixelY in range(altered_image.height()):
                #     for pixelX in range (altered_image.width()):
                #         pixel_color = QColor(altered_image.pixel(pixelX,pixelY))
                #         H,S,L,A = pixel_color.getHsl()


                if value < 0:
                    colorize_ops = ImageOps.colorize(pillow_image.convert('L'), mid = 'aqua', black = 'black', white = 'white').convert('RGBA')
                    #coloured_image = ImageQt.ImageQt(colorize_ops)
                    colorize_ops = colorize_ops.convert('RGBA')
                    pillow_image = pillow_image.convert('RGBA')
                    pillow_image = Image.blend(pillow_image,colorize_ops,factor)
                    #pillow_image = colorize_ops

                elif value >0:
                    colorize_ops = ImageOps.colorize(pillow_image.convert('L'), mid = 'red', black = 'black', white = 'white')
                    colorize_ops = colorize_ops.convert('RGBA')
                    pillow_image = pillow_image.convert('RGBA')
                    #coloured_image = ImageQt.ImageQt(colorize_ops)
                    pillow_image = Image.blend(pillow_image,colorize_ops,factor) 
                    #pillow_image = colorize_ops


                new_qimage = ImageQt.ImageQt(pillow_image).convertToFormat(QImage.Format_ARGB32)


                #self.base_pixmap = QPixmap.fromImage(image)
                self.altered_pixmap = QPixmap.fromImage(new_qimage)

                updated_texture = TextureLayer(QPixmap.fromImage(new_qimage), self.original_image_location)
                #update textures
                #index = self.texture_layers.index(self.selected_layer)
                self.texture_layers[self.selected_layer_index] = updated_texture
                self.translucent_texture_layers[self.selected_layer_index] = updated_texture
                self.active_tool_widget.update_overlay()

                #self.base_image = self.base_pixmap.toImage()
                ########################
                self.altered_image = self.altered_pixmap.toImage()
                #self.adjust_saturation(self.saturation_value)
                self.cyan_red_panel.reset(0)
                self.redness_value = 0
                self.update()

    def adjust_contrast(self,value):
            factor = value/100
            if self.use_low_res:
                #original_image = self.base_image.convertToFormat(QImage.Format_ARGB32)
                self.original_image_location = self.selected_layer.position
                #original_image = self.base_image.convertToFormat(QImage.Format_ARGB32)
                print(self.original_image_location)
                self.low_res_image = self.altered_image.scaled(self.resolution, self.resolution, Qt.KeepAspectRatio, Qt.SmoothTransformation)


                #image = self.low_res_image.convertToFormat(QImage.Format_ARGB32)


                altered_image = self.low_res_image.convertToFormat(QImage.Format_ARGB32)

                pillow_image = ImageQt.fromqimage(altered_image)

                # for pixelY in range(altered_image.height()):
                #     for pixelX in range (altered_image.width()):
                #         pixel_color = QColor(altered_image.pixel(pixelX,pixelY))
                #         H,S,L,A = pixel_color.getHsl()

                contrast_enhancer = ImageEnhance.Contrast(pillow_image)
                pillow_image = contrast_enhancer.enhance(factor)

                new_qimage = ImageQt.ImageQt(pillow_image).convertToFormat(QImage.Format_ARGB32)

                display_size = self.current_image.size()  # QImage.size() gives QSize
                new_qimage = new_qimage.scaled(display_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)


                #self.base_pixmap = QPixmap.fromImage(image)
                self.altered_pixmap = QPixmap.fromImage(new_qimage)

                updated_texture = TextureLayer(QPixmap.fromImage(new_qimage), self.original_image_location)
                #update textures
                #index = self.texture_layers.index(self.selected_layer)
                self.texture_layers[self.selected_layer_index] = updated_texture
                self.translucent_texture_layers[self.selected_layer_index] = updated_texture
                self.active_tool_widget.update_overlay()


                self.altered_image = new_qimage

                if value != self.contrast_value:
                    self.adjust_all_but_self("contrast")
                    self.altered_image = self.current_image


                self.contrast_value = value
                #self.base_image = self.base_pixmap.toImage()
                ########################
                ####self.altered_image = self.altered_pixmap.toImage()
                #####self.adjust_saturation(self.saturation_value)
                self.update()
            else:
                self.setCursor(QtCore.Qt.ForbiddenCursor)
                self.original_image_location = self.selected_layer.position

                #image = self.base_image.convertToFormat(QImage.Format_ARGB32)
                altered_image = self.altered_image.convertToFormat(QImage.Format_ARGB32)
                pillow_image = ImageQt.fromqimage(altered_image)

                # for pixelY in range(altered_image.height()):
                #     for pixelX in range (altered_image.width()):
                #         pixel_color = QColor(altered_image.pixel(pixelX,pixelY))
                #         H,S,L,A = pixel_color.getHsl()

                contrast_enhancer = ImageEnhance.Contrast(pillow_image)
                pillow_image = contrast_enhancer.enhance(factor)

                new_qimage = ImageQt.ImageQt(pillow_image).convertToFormat(QImage.Format_ARGB32)


                #self.base_pixmap = QPixmap.fromImage(image)
                self.altered_pixmap = QPixmap.fromImage(new_qimage)

                updated_texture = TextureLayer(QPixmap.fromImage(new_qimage), self.original_image_location)
                #update textures
                #index = self.texture_layers.index(self.selected_layer)
                self.texture_layers[self.selected_layer_index] = updated_texture
                self.translucent_texture_layers[self.selected_layer_index] = updated_texture
                self.active_tool_widget.update_overlay()

                #self.base_image = self.base_pixmap.toImage()
                ########################
                self.altered_image = self.altered_pixmap.toImage()
                #self.adjust_saturation(self.saturation_value)
                self.contrast_panel.reset(100)
                self.contrast_value = 100
                self.tool_panel.refresh_tool()
                self.update()

    def adjust_saturation(self,value):
            factor = value/100
            if self.use_low_res:
                #original_image = self.base_image.convertToFormat(QImage.Format_ARGB32)
                self.original_image_location = self.selected_layer.position
                #original_image = self.base_image.convertToFormat(QImage.Format_ARGB32)

                self.low_res_image = self.altered_image.scaled(self.resolution, self.resolution, Qt.KeepAspectRatio, Qt.SmoothTransformation)


                #image = self.low_res_image.convertToFormat(QImage.Format_ARGB32)


                altered_image = self.low_res_image.convertToFormat(QImage.Format_ARGB32)

                pillow_image = ImageQt.fromqimage(altered_image)

                # for pixelY in range(altered_image.height()):
                #     for pixelX in range (altered_image.width()):
                #         pixel_color = QColor(altered_image.pixel(pixelX,pixelY))
                #         H,S,L,A = pixel_color.getHsl()

                color_enhancer = ImageEnhance.Color(pillow_image)
                pillow_image = color_enhancer.enhance(factor)

                new_qimage = ImageQt.ImageQt(pillow_image).convertToFormat(QImage.Format_ARGB32)

                display_size = self.current_image.size()  # QImage.size() gives QSize
                new_qimage = new_qimage.scaled(display_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)


                #self.base_pixmap = QPixmap.fromImage(image)
                self.altered_pixmap = QPixmap.fromImage(new_qimage)

                updated_texture = TextureLayer(QPixmap.fromImage(new_qimage), self.original_image_location)
                #update textures
                #index = self.texture_layers.index(self.selected_layer)
                self.texture_layers[self.selected_layer_index] = updated_texture
                self.translucent_texture_layers[self.selected_layer_index] = updated_texture
                self.active_tool_widget.update_overlay()



                self.altered_image = new_qimage

                if value != self.saturation_value:
                    self.adjust_all_but_self("saturation")
                    self.altered_image = self.current_image


                self.saturation_value = value
                #self.base_image = self.base_pixmap.toImage()
                ########################
                ####self.altered_image = self.altered_pixmap.toImage()
                #####self.adjust_saturation(self.saturation_value)
                self.update()
            else:
                self.setCursor(QtCore.Qt.ForbiddenCursor)
                self.original_image_location = self.selected_layer.position

                #image = self.base_image.convertToFormat(QImage.Format_ARGB32)
                altered_image = self.altered_image.convertToFormat(QImage.Format_ARGB32)
                pillow_image = ImageQt.fromqimage(altered_image)

                # for pixelY in range(altered_image.height()):
                #     for pixelX in range (altered_image.width()):
                #         pixel_color = QColor(altered_image.pixel(pixelX,pixelY))
                #         H,S,L,A = pixel_color.getHsl()

                color_enhancer = ImageEnhance.Color(pillow_image)
                pillow_image = color_enhancer.enhance(factor)

                new_qimage = ImageQt.ImageQt(pillow_image).convertToFormat(QImage.Format_ARGB32)


                #self.base_pixmap = QPixmap.fromImage(image)
                self.altered_pixmap = QPixmap.fromImage(new_qimage)

                updated_texture = TextureLayer(QPixmap.fromImage(new_qimage), self.original_image_location)
                #update textures
                #index = self.texture_layers.index(self.selected_layer)
                self.texture_layers[self.selected_layer_index] = updated_texture
                self.translucent_texture_layers[self.selected_layer_index] = updated_texture
                self.active_tool_widget.update_overlay()

                #self.base_image = self.base_pixmap.toImage()
                ########################
                self.altered_image = self.altered_pixmap.toImage()
                #self.adjust_saturation(self.saturation_value)
                self.saturation_panel.reset(100)
                self.saturation_value = 100
                self.tool_panel.refresh_tool()

                self.update()

    def adjust_opacity(self,value):
            factor = value/255
            if factor <0.001:
                factor = 0.001
            if self.use_low_res:
                #previous_res = self.resolution

                #self.resolution = max(self.selected_layer.pixmap.width(),self.selected_layer.pixmap.height())


                #original_image = self.base_image.convertToFormat(QImage.Format_ARGB32)
                self.original_image_location = self.selected_layer.position
                #original_image = self.base_image.convertToFormat(QImage.Format_ARGB32)

                self.low_res_image = self.altered_image.scaled(self.resolution, self.resolution, Qt.KeepAspectRatio, Qt.SmoothTransformation)


                #image = self.low_res_image.convertToFormat(QImage.Format_ARGB32)


                altered_image = self.low_res_image.convertToFormat(QImage.Format_ARGB32)

                pillow_image = ImageQt.fromqimage(altered_image).convert("RGBA")

                # for pixelY in range(altered_image.height()):
                #     for pixelX in range (altered_image.width()):
                #         pixel_color = QColor(altered_image.pixel(pixelX,pixelY))
                #         H,S,L,A = pixel_color.getHsl()



                # alpha_mask = Image.new("L", pillow_image.size, int(factor)) 
                # pillow_image.putalpha(alpha_mask)

                r, g, b, a = pillow_image.split()
                new_alpha = a.point(lambda point: point*factor)
                pillow_image.putalpha(new_alpha)




                new_qimage = ImageQt.ImageQt(pillow_image).convertToFormat(QImage.Format_ARGB32)

                display_size = self.current_image.size()  # QImage.size() gives QSize
                new_qimage = new_qimage.scaled(display_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)


                #self.base_pixmap = QPixmap.fromImage(image)

                self.altered_pixmap = QPixmap.fromImage(new_qimage)

                updated_texture = TextureLayer(QPixmap.fromImage(new_qimage), self.original_image_location)
                #update textures
                #index = self.texture_layers.index(self.selected_layer)
                self.translucent_texture_layers[self.selected_layer_index] = updated_texture
                #self.active_tool_widget.texture_layers[0] = updated_texture
                self.active_tool_widget.update_overlay()


                self.altered_image = new_qimage

                if value != self.opacity_value:
                    self.adjust_all_but_self("opacity")
                    self.altered_image = self.current_image


                self.opacity_value = value
                #self.base_image = self.base_pixmap.toImage()
                ########################
                ####self.altered_image = self.altered_pixmap.toImage()
                #####self.adjust_saturation(self.saturation_value)


                # self.current_image = self.selected_layer.pixmap.toImage()
                # self.altered_image = self.current_image

                
                #self.resolution = previous_res

                self.update()
            else:
                self.original_image_location = self.selected_layer.position
                self.setCursor(QtCore.Qt.ForbiddenCursor)

                #image = self.base_image.convertToFormat(QImage.Format_ARGB32)
                altered_image = self.altered_image.convertToFormat(QImage.Format_ARGB32)
                pillow_image = ImageQt.fromqimage(altered_image)


                # for pixelY in range(altered_image.height()):
                #     for pixelX in range (altered_image.width()):
                #         pixel_color = QColor(altered_image.pixel(pixelX,pixelY))
                #         H,S,L,A = pixel_color.getHsl()


                # alpha_mask = Image.new("L", pillow_image.size, factor) 
                # pillow_image.putalpha(alpha_mask)


                r, g, b, a = pillow_image.split()
                new_alpha = a.point(lambda point: point*factor)
                pillow_image.putalpha(new_alpha)


                new_qimage = ImageQt.ImageQt(pillow_image).convertToFormat(QImage.Format_ARGB32)

                #self.base_pixmap = QPixmap.fromImage(image)
                self.altered_pixmap = QPixmap.fromImage(new_qimage)

                updated_texture = TextureLayer(QPixmap.fromImage(new_qimage), self.original_image_location)
                #update textures
                #index = self.texture_layers.index(self.selected_layer)
                self.translucent_texture_layers[self.selected_layer_index] = updated_texture
                #self.active_tool_widget.texture_layers[0] = updated_texture
                self.active_tool_widget.update_overlay()

                #self.base_image = self.base_pixmap.toImage()
                ########################
                self.altered_image = self.altered_pixmap.toImage()
                #self.adjust_saturation(self.saturation_value)
                # self.opacity_slider.reset(255)
                # self.opacity_value = 255
                self.tool_panel.refresh_tool()
                self.layer_opacities[self.selected_layer_index] = value

                # self.current_image = self.selected_layer.pixmap.toImage()
                # self.altered_image = self.current_image
                self.update()



    def adjust_brightness(self,value):
            #factor = 2**(value/100)
            factor = (value/100)
            if self.use_low_res:
                #original_image = self.base_image.convertToFormat(QImage.Format_ARGB32)
                self.original_image_location = self.selected_layer.position
                #original_image = self.base_image.convertToFormat(QImage.Format_ARGB32)

                self.low_res_image = self.altered_image.scaled(self.resolution, self.resolution, Qt.KeepAspectRatio, Qt.SmoothTransformation)


                #image = self.low_res_image.convertToFormat(QImage.Format_ARGB32)


                altered_image = self.low_res_image.convertToFormat(QImage.Format_ARGB32)

                pillow_image = ImageQt.fromqimage(altered_image)

                # for pixelY in range(altered_image.height()):
                #     for pixelX in range (altered_image.width()):
                #         pixel_color = QColor(altered_image.pixel(pixelX,pixelY))
                #         H,S,L,A = pixel_color.getHsl()

                brightness_enhancer = ImageEnhance.Brightness(pillow_image)
                pillow_image = brightness_enhancer.enhance(factor)

                new_qimage = ImageQt.ImageQt(pillow_image).convertToFormat(QImage.Format_ARGB32)

                display_size = self.current_image.size() 
                new_qimage = new_qimage.scaled(display_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)






                #self.base_pixmap = QPixmap.fromImage(image)
                self.altered_pixmap = QPixmap.fromImage(new_qimage)

                updated_texture = TextureLayer(QPixmap.fromImage(new_qimage), self.original_image_location)
                #update textures
                #index = self.texture_layers.index(self.selected_layer)
                self.texture_layers[self.selected_layer_index] = updated_texture
                self.translucent_texture_layers[self.selected_layer_index] = updated_texture
                self.active_tool_widget.update_overlay()



                self.altered_image = new_qimage

                if value != self.brightness_value:
                    self.adjust_all_but_self("brightness")
                    self.altered_image = self.current_image


                self.brightness_value = value

                #self.base_image = self.base_pixmap.toImage()
                ########################
                ####self.altered_image = self.altered_pixmap.toImage()
                #####self.adjust_saturation(self.saturation_value)
                self.update()
            else:          
                self.setCursor(QtCore.Qt.ForbiddenCursor)
                self.original_image_location = self.selected_layer.position

                #image = self.base_image.convertToFormat(QImage.Format_ARGB32)
                altered_image = self.altered_image.convertToFormat(QImage.Format_ARGB32)
                pillow_image = ImageQt.fromqimage(altered_image)

                # for pixelY in range(altered_image.height()):
                #     for pixelX in range (altered_image.width()):
                #         pixel_color = QColor(altered_image.pixel(pixelX,pixelY))
                #         H,S,L,A = pixel_color.getHsl()

                brightness_enhancer = ImageEnhance.Brightness(pillow_image)



                pillow_image = brightness_enhancer.enhance(factor)

                new_qimage = ImageQt.ImageQt(pillow_image).convertToFormat(QImage.Format_ARGB32)


                #self.base_pixmap = QPixmap.fromImage(image)
                self.altered_pixmap = QPixmap.fromImage(new_qimage)

                updated_texture = TextureLayer(QPixmap.fromImage(new_qimage), self.original_image_location)
                #update textures
                #index = self.texture_layers.index(self.selected_layer)
                self.texture_layers[self.selected_layer_index] = updated_texture
                self.translucent_texture_layers[self.selected_layer_index] = updated_texture
                self.active_tool_widget.update_overlay()

                #self.base_image = self.base_pixmap.toImage()
                ########################
                self.altered_image = self.altered_pixmap.toImage()
                #self.adjust_saturation(self.saturation_value)
                self.brightness_panel.reset(100)
                self.brightness_value = 100
                self.tool_panel.refresh_tool()

                self.update()

    def adjust_exposure(self,value):
            factor = 2**(value/100)
            if self.use_low_res:
                #original_image = self.base_image.convertToFormat(QImage.Format_ARGB32)
                self.original_image_location = self.selected_layer.position
                #original_image = self.base_image.convertToFormat(QImage.Format_ARGB32)

                self.low_res_image = self.altered_image.scaled(self.resolution, self.resolution, Qt.KeepAspectRatio, Qt.SmoothTransformation)


                #image = self.low_res_image.convertToFormat(QImage.Format_ARGB32)


                altered_image = self.low_res_image.convertToFormat(QImage.Format_ARGB32)

                pillow_image = ImageQt.fromqimage(altered_image)

                # for pixelY in range(altered_image.height()):
                #     for pixelX in range (altered_image.width()):
                #         pixel_color = QColor(altered_image.pixel(pixelX,pixelY))
                #         H,S,L,A = pixel_color.getHsl()
                exposure_enhancer = ImageEnhance.Brightness(pillow_image)
                pillow_image = exposure_enhancer.enhance(factor)

                new_qimage = ImageQt.ImageQt(pillow_image).convertToFormat(QImage.Format_ARGB32)

                display_size = self.current_image.size() 
                new_qimage = new_qimage.scaled(display_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)






                #self.base_pixmap = QPixmap.fromImage(image)
                self.altered_pixmap = QPixmap.fromImage(new_qimage)

                updated_texture = TextureLayer(QPixmap.fromImage(new_qimage), self.original_image_location)
                #update textures
                #index = self.texture_layers.index(self.selected_layer)
                self.texture_layers[self.selected_layer_index] = updated_texture
                self.translucent_texture_layers[self.selected_layer_index] = updated_texture
                self.active_tool_widget.update_overlay()



                self.altered_image = new_qimage

                if value != self.exposure_value:
                    self.adjust_all_but_self("exposure")
                    print("adjusting  all but exposure")
                    self.altered_image = self.current_image


                self.exposure_value = value

                #self.base_image = self.base_pixmap.toImage()
                ########################
                ####self.altered_image = self.altered_pixmap.toImage()
                #####self.adjust_saturation(self.saturation_value)
                self.update()
            else:          
                self.setCursor(QtCore.Qt.ForbiddenCursor)
                self.original_image_location = self.selected_layer.position

                #image = self.base_image.convertToFormat(QImage.Format_ARGB32)
                altered_image = self.altered_image.convertToFormat(QImage.Format_ARGB32)
                pillow_image = ImageQt.fromqimage(altered_image)

                # for pixelY in range(altered_image.height()):
                #     for pixelX in range (altered_image.width()):
                #         pixel_color = QColor(altered_image.pixel(pixelX,pixelY))
                #         H,S,L,A = pixel_color.getHsl()

                if value != 0:
                    exposure_enhancer = ImageEnhance.Brightness(pillow_image)
                    pillow_image = exposure_enhancer.enhance(factor)


                new_qimage = ImageQt.ImageQt(pillow_image).convertToFormat(QImage.Format_ARGB32)


                #self.base_pixmap = QPixmap.fromImage(image)
                self.altered_pixmap = QPixmap.fromImage(new_qimage)

                updated_texture = TextureLayer(QPixmap.fromImage(new_qimage), self.original_image_location)
                #update textures
                #index = self.texture_layers.index(self.selected_layer)
                self.texture_layers[self.selected_layer_index] = updated_texture
                self.translucent_texture_layers[self.selected_layer_index] = updated_texture
                self.active_tool_widget.update_overlay()

                #self.base_image = self.base_pixmap.toImage()
                ########################
                self.altered_image = self.altered_pixmap.toImage()
                #self.adjust_saturation(self.saturation_value)
                self.exposure_panel.reset(0)
                self.exposure_value = 0
                self.tool_panel.refresh_tool()

                self.update()

    def reset_sliders(self):
        # self.resolution = 1024
        self.magenta_green_panel.reset(0)
        self.cyan_red_panel.reset(0)
        self.yellow_blue_panel.reset(0)
        self.saturation_panel.reset(100)
        self.contrast_panel.reset(100)
        self.brightness_panel.reset(100)
        # self.gaussian_panel.reset(0)
        self.exposure_panel.reset(0)
        #self.opacity_slider.reset(255)
        self.adjust_apply_button_colour(0)
        self.resetting = True
        self.apply_full_resolution_adjustments()
        self.resetting = False
        self.update()


        self.tool_panel.refresh_tool()

    def apply_full_resolution_adjustments(self):
        #self.resolution = self.base_image.height()
        self.use_low_res = False
        self.setCursor(QtCore.Qt.ForbiddenCursor)


        any_value_changed = False
        if self.redness_value != 0 or self.resetting:
            self.adjust_redness(self.redness_value)
            any_value_changed = True
        if self.greenness_value != 0 or self.resetting:
            self.adjust_greenness(self.greenness_value)
            any_value_changed = True
        if self.blueness_value != 0 or self.resetting:
            self.adjust_blueness(self.blueness_value)
            any_value_changed = True
        if self.saturation_value != 100 or self.resetting:
            self.adjust_saturation(self.saturation_value)
            any_value_changed = True
        if self.brightness_value != 100 or self.resetting:
            self.adjust_brightness(self.brightness_value)
            any_value_changed = True
        if self.exposure_value != 0 or self.resetting:
            self.adjust_exposure(self.exposure_value)
            any_value_changed = True
        if self.contrast_value != 100 or self.resetting:
            self.adjust_contrast(self.contrast_value)
            any_value_changed = True



        self.current_image = self.altered_image
        #self.setCursor(QtCore.Qt.ArrowCursor)


        self.selected_layer = self.texture_layers[self.selected_layer_index]

        self.tool_panel.refresh_tool()
        

        if self.opacity_value != self.layer_opacities[self.selected_layer_index] or self.resetting or any_value_changed:
            self.adjust_opacity(self.opacity_value)
        #self.adjust_opacity(self.opacity_value)
 
        self.tool_panel.refresh_tool()
        
        self.adjust_apply_button_colour(0)

        self.selected_layer = self.texture_layers[self.selected_layer_index]

        self.current_image = self.selected_layer.pixmap.toImage()
        self.altered_image = self.current_image

        self.opacity_slider.reset(self.layer_opacities[self.selected_layer_index])
        self.use_low_res = True
        self.tool_panel.refresh_tool()

    def apply_1k_resolution_adjustments(self, bool):
        self.use_low_res = bool
        #self.setCursor(QtCore.Qt.ForbiddenCursor)
        self.resolution = 256

  

        if self.redness_value != 0 or self.resetting:
            self.adjust_redness(self.redness_value)

        if self.greenness_value != 0 or self.resetting:
            self.adjust_greenness(self.greenness_value)

        if self.blueness_value != 0 or self.resetting:
            self.adjust_blueness(self.blueness_value)

        if self.saturation_value != 100 or self.resetting:
            self.adjust_saturation(self.saturation_value)
 
        if self.brightness_value != 100 or self.resetting:
            self.adjust_brightness(self.brightness_value)

        if self.exposure_value != 0 or self.resetting:
            self.adjust_exposure(self.exposure_value)

        if self.contrast_value != 100 or self.resetting:
            self.adjust_contrast(self.contrast_value)

        # updated_texture = TextureLayer(self.altered_pixmap, self.original_image_location)
        # self.texture_layers[self.selected_layer_index] = updated_texture

        self.adjust_opacity(self.opacity_value)
        self.altered_image = self.current_image


        #self.setCursor(QtCore.Qt.ArrowCursor)
        self.tool_panel.refresh_tool()

        # Optionally update the full-res altered_image
        #self.altered_image = self.altered_pixmap.toImage()


    ##########################################
    #                 TOOL BAR               #
    ##########################################
    def clear_selections(self):
        self.selections_paths.clear()
        self.active_tool_widget.clear_overlay()

    def select_all(self):
        self.selections_paths.clear()
        layer = self.texture_layers[0]
        rectangle = QtCore.QRect(layer.position, layer.pixmap.size())
        polygon = QPolygonF(QPolygon(rectangle))
        path = QPainterPath()
        path.addPolygon(polygon)
        self.selections_paths.append(path)
        self.active_tool_widget.update_overlay()

    def invert_selections(self):
        entire_image_rectangle = QtCore.QRect(self.base_layer.position, self.base_layer.pixmap.size())
        entire_image_polygon = QPolygonF(QPolygon(entire_image_rectangle))
        entire_image_path = QPainterPath()
        entire_image_path.addPolygon(entire_image_polygon)
        entire_image_selection = entire_image_path

        for i, path in enumerate(list(self.selections_paths)):
                subtraction_path = entire_image_path.subtracted(path)
                self.selections_paths[i] = subtraction_path

                changed = True
                while changed:
                    changed = False
                    for k, other_path in enumerate(list(self.selections_paths)):
                        if k == i:
                            continue
                        if self.selections_paths[i].intersects(other_path):
                            self.selections_paths[i] = self.selections_paths[i].subtracted(other_path)
                            changed = True
                            break

        self.active_tool_widget.update_overlay()
        self.update()
        
    def contract_selections(self):
        self.alter_selections_scale(9/10)

    def expand_selections(self):
        self.alter_selections_scale(10/9)
        # self.merged_selection_path = parent_window.merged_selection_path
        # self.selections_paths = parent_window.selections_paths



    def alter_selections_scale(self,scale_factor):
        new_selections_paths = []
        for path in self.selections_paths:
            all_polys = path.toFillPolygons()
            for poly_f in all_polys:
                transform = QTransform()
                center = poly_f.boundingRect().center()
                transform.translate(center.x(), center.y())
                transform.scale(scale_factor, scale_factor)
                transform.translate(-center.x(), -center.y())

                new_poly_f = transform.map(poly_f)

                new_path = QPainterPath()
                new_path.addPolygon(new_poly_f)

                new_selections_paths.append(new_path)

        self.selections_paths = new_selections_paths
        
        self.update()
        self.active_tool_widget.update_overlay()
        self.tool_panel.refresh_tool()

    def queue_flattened_image(self):
        chosen_name = None
        folder_path = None
        chosen_name = self.change_name()
        while folder_path == None:
            if chosen_name == None:
                pass
            else:
                break
        folder_path = self.prompt_add_folder_path()
        self.export_flattened_image(folder_path, chosen_name)


    def queue_flattened_additions(self):
        chosen_name = None
        folder_path = None
        chosen_name = self.change_name()
        while folder_path == None:
            if chosen_name == None:
                pass
            else:
                break
        folder_path = self.prompt_add_folder_path()
        self.export_flattened_additions(folder_path, chosen_name)


    def CreateToolBar(self):
        print("CreateToolBar is running inside:", type(self))
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("File")

        #import button
        import_action = QAction("Import", self)
        import_action.triggered.connect(self.prompt_add_texture)
        file_menu.addAction(import_action)




        #export menu
        export_menu = QMenu("Export", self)

        export_flat_all = QAction("Export Flattened Image", self)
        export_flat_additions = QAction("Export Flattened Additions", self)
        create_decal = QAction("Create Decal", self)

        export_menu.addAction(export_flat_all)
        export_menu.addAction(export_flat_additions)
        export_menu.addAction(create_decal)
    
        export_flat_all.triggered.connect(lambda:self.queue_flattened_image())
        export_flat_additions.triggered.connect(lambda: self.queue_flattened_additions())
        create_decal.triggered.connect((lambda: self.create_decal(self.prompt_add_folder_path(), (self.chosen_name + "_Decal"))))
        file_menu.addMenu(export_menu)    

        self.chosen_name = "untitled"
        #change name button
        change_name_action = QAction("Change File Name", self)
        file_menu.addAction(change_name_action)
        change_name_action.triggered.connect(self.change_name)




        edit_menu = menu_bar.addMenu("Edit")

        flip_horizontal = QAction("Flip Current Layer Horizontal", self)
        flip_vertical = QAction("Flip Current Layer Vertical", self)

        edit_menu.addAction(flip_horizontal)
        edit_menu.addAction(flip_vertical)


        flip_horizontal.triggered.connect(lambda: self.flip_horizontal())
        flip_vertical.triggered.connect(lambda: self.flip_vertical())


        flip_all_horizontal = QAction("Flip All Layers Horizontal", self)
        flip_all_vertical = QAction("Flip All Layers Vertical", self)

        edit_menu.addAction(flip_all_horizontal)
        edit_menu.addAction(flip_all_vertical)


        flip_all_horizontal.triggered.connect(lambda: self.flip_all_horizontal())
        flip_all_vertical.triggered.connect(lambda: self.flip_all_horizontal())



        select_menu = menu_bar.addMenu("Select")

        select_all_action = QAction("Select All", self)
        clear_selections_action = QAction("Clear Selections", self)
        invert_selections_action = QAction("Invert Selections", self)

        select_menu.addAction(select_all_action)
        select_menu.addAction(clear_selections_action)
        select_menu.addAction(invert_selections_action)

        clear_selections_action.triggered.connect(lambda: self.clear_selections())
        select_all_action.triggered.connect(lambda: self.select_all())
        invert_selections_action.triggered.connect(lambda: self.invert_selections())

        modify_menu = QMenu("Modify", self)

        expand_action = QAction("Expand", self)
        contract_action = QAction("Contract", self)

        modify_menu.addAction(expand_action)
        modify_menu.addAction(contract_action)

        select_menu.addMenu(modify_menu)

        expand_action.triggered.connect(lambda: self.expand_selections())
        contract_action.triggered.connect(lambda: self.contract_selections())


        help_menu = menu_bar.addMenu("Help")
        help_action = QAction("Show Help", self)
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)

        menu_bar.setStyleSheet("""
            background-color: #252525;
            color: #ffffff;
            font-family: Segoe UI;
            font-size: 12px;
            selection-background-color: #424242;                  
        """)  
 
        modify_menu.setStyleSheet("""
            background-color: #252525;
            color: #ffffff;
            font-family: Segoe UI;
            font-size: 12px;
            selection-background-color: #424242;                  
        """)  

        export_menu.setStyleSheet("""
            background-color: #252525;
            color: #ffffff;
            font-family: Segoe UI;
            font-size: 12px;
            selection-background-color: #424242;                  
        """)  
 

    def flip_horizontal(self):
        self.flip_selected_layer(self.selected_layer, -1,1, self.texture_layers)
        self.flip_selected_layer(self.translucent_texture_layers[self.selected_layer_index], -1,1, self.translucent_texture_layers)

    def flip_vertical(self):
        self.flip_selected_layer(self.selected_layer, 1,-1, self.texture_layers)
        self.flip_selected_layer(self.translucent_texture_layers[self.selected_layer_index], 1,-1, self.translucent_texture_layers)

    def flip_selected_layer(self, layer ,x,y, destination):
        layer_pixmap = layer.pixmap
        layer_position = layer.position

        flipped_pixmap = layer_pixmap.transformed(QTransform().scale(x, y))
        flipped_position = QtCore.QPoint(layer_position.x()*x, layer_position.y()*y)

        new_layer = TextureLayer(flipped_pixmap, flipped_position)
        destination[self.selected_layer_index] = new_layer

        self.tool_panel.refresh_tool()
        self.apply_full_resolution_adjustments()

    def flip_all_layers(self,x,y, layer_group):
        for layer in layer_group:
            layer_pixmap = layer.pixmap
            layer_position = layer.position

            index = layer_group.index(layer)
            flipped_pixmap = layer_pixmap.transformed(QTransform().scale(x, y))
            flipped_position = QtCore.QPoint(layer_position.x()*x, layer_position.y()*y)

            new_layer = TextureLayer(flipped_pixmap, flipped_position)
            layer_group[index] = new_layer

        layer_pixmap = self.pen_overlay
        flipped_pixmap = layer_pixmap.transformed(QTransform().scale(x, y))
        new_layer = flipped_pixmap
        self.pen_overlay = new_layer
        self.tool_panel.refresh_tool()
        self.active_tool_widget.update_overlay()

        self.tool_panel.refresh_tool()
        self.apply_full_resolution_adjustments()

    def flip_all_horizontal(self):
        self.flip_all_layers(-1,1, self.texture_layers)
        self.flip_all_layers(-1,1, self.translucent_texture_layers)


    def flip_all_vertical(self):
        self.flip_all_layers(1,-1, self.texture_layers)
        self.flip_all_layers(1,-1, self.translucent_texture_layers)


    def show_help(self):
        QMessageBox.about(self, "About Texture Editor",
                          "This Texture Editor allows for the editting of "
                          "textures within Unreal. Select a tool for further "
                          "information regarding your selected tool. Press 'file' to "
                          "import and export textures.")
        

    def change_name(self):
        name_window = ChooseNameWindow()
        #name_window.launchWindow()
        name_window.show()
        name_window.setWindowTitle("Name File")
        name_window.setObjectName("NamerWindow")
        looping = True
        while looping:
            QApplication.processEvents()
            if name_window.button_clicked:
                self.chosen_name = name_window.getName()
                looping = False
        return self.chosen_name
            

    def prompt_add_texture(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select Texture",
            "",
            "Images (*.png *.jpg *.jpeg)"
        )
        if file_path:
            self.add_new_texture_layer(file_path)


    def prompt_add_folder_path(self):

        file_path = QtWidgets.QFileDialog.getExistingDirectory(
    self,
    "Select Folder for Texture",
    "/Game/",
    QtWidgets.QFileDialog.ShowDirsOnly
    )
        print (f"file path = {file_path}")

        split_path = file_path.split("/")
        print (split_path.index("Content"))

        new_path = "/Game/"

        for item in split_path[split_path.index("Content")+1:]:
            print (item)
            new_path += str(item)
            new_path += ("/")
            
        # print(new_path)

        if new_path:
            return new_path
        else:
            print("FILE DIRECTORY NOT FOUND NOT FOUND NOT FOUND")

    def add_new_texture_layer(self, texture_path):
        self.pixmap = QtGui.QPixmap(texture_path)
        
        if self.pixmap.isNull():
            print(f"Failed to load texture: {texture_path}")
            return
        
        self.layer_opacities.append(255)

        print(f"Loaded new texture: {texture_path}")
        new_layer = TextureLayer(self.pixmap, QtCore.QPoint(0, 0))
        self.texture_layers.append(new_layer)
        self.translucent_texture_layers.append(new_layer)

        if self.active_tool_widget:
            self.active_tool_widget.update()

        self.layers.addItem("Layer "+ str(len(self.texture_layers)-1))
        self.update()

    def rewrite_layers(self):
        self.layers.clear()
        i = 0
        for layer in self.texture_layers:
            if i == 0:
                self.layers.addItem("Base Layer")
            else:
                self.layers.addItem("Layer "+ str(i))
            i+=1


    def zoom_changed(self, value):
        if self.active_tool_widget:
            self.active_tool_widget.set_scale_factor(value / 100.0)
            self.tool_panel.refresh_tool()

    def zoom_in(self):
        self._apply_zoom(10/9)
        self.zoom_changed(self.scale_factor * 100)

    def zoom_out(self):
        self._apply_zoom(0.9)
        self.zoom_changed(self.scale_factor * 100)

    def reset_zoom(self):
        self.scale_factor = 1.0
        self.zoom_changed(self.scale_factor * 100)

    #CHANGE TO LOCK AT MAX ZOOMED IN BASED ON SIZE OF TEXTRE
    def _apply_zoom(self, factor: float):
        new_scale = self.scale_factor * factor
        if 0.1 <= new_scale <= 10.0:
            self.scale_factor = new_scale


    def export_flattened_image(self, unreal_folder,name):
        temp_dir = os.path.join(unreal.Paths.project_intermediate_dir(), "TempExports")
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, (name + ".png"))

        base_size = self.texture_layers[0].pixmap.size()
        final_image = QtGui.QImage(base_size, QtGui.QImage.Format_ARGB32)
        final_image.fill(QtCore.Qt.transparent)

        pen_layer = TextureLayer(self.pen_overlay, QtCore.QPoint(0, 0))
        self.texture_layers.append(pen_layer)

        painter = QtGui.QPainter(final_image)
        for layer in self.texture_layers:
            painter.drawPixmap(layer.position, layer.pixmap)


        painter.end()

        QtGui.QPixmap.fromImage(final_image).save(temp_path, "PNG")

        import_task = unreal.AssetImportTask()
        import_task.filename = temp_path
        import_task.destination_path = unreal_folder
        import_task.destination_name = name          
        import_task.automated = True
        import_task.save = True
        import_task.replace_existing = True

        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        asset_tools.import_asset_tasks([import_task])

        imported_asset_path = f"{unreal_folder}/{name}.{name}"

        if unreal.EditorAssetLibrary.does_asset_exist(imported_asset_path):
            unreal.log("Successfully imported into Unreal")
            texture_generated = unreal.EditorAssetLibrary.load_asset(imported_asset_path)
            texture_generated.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_DEFAULT)
            unreal.EditorAssetLibrary.save_asset(imported_asset_path)
        else:
            unreal.log_error("Failed to import into Unreal")

    def export_flattened_additions(self, unreal_folder, name):
        temp_dir = os.path.join(unreal.Paths.project_intermediate_dir(), "TempExports")
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, (name + ".png"))

        base_size = self.texture_layers[0].pixmap.size()
        final_image = QtGui.QImage(base_size, QtGui.QImage.Format_ARGB32)
        final_image.fill(QtCore.Qt.transparent)


        pen_layer = TextureLayer(self.pen_overlay, QtCore.QPoint(0, 0))
        self.texture_layers.append(pen_layer)

        painter = QtGui.QPainter(final_image)
        for layer in self.texture_layers[1:]:
            painter.drawPixmap(layer.position, layer.pixmap)

        painter.end()

        QtGui.QPixmap.fromImage(final_image).save(temp_path, "PNG")

        import_task = unreal.AssetImportTask()
        import_task.filename = temp_path
        import_task.destination_path = unreal_folder
        import_task.destination_name = name          
        import_task.automated = True
        import_task.save = True
        import_task.replace_existing = True

        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        asset_tools.import_asset_tasks([import_task])

        imported_asset_path = f"{unreal_folder}/{name}.{name}"

        if unreal.EditorAssetLibrary.does_asset_exist(imported_asset_path):
            unreal.log("Successfully imported into Unreal")
            texture_generated = unreal.EditorAssetLibrary.load_asset(imported_asset_path)
            texture_generated.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_DEFAULT)
            unreal.EditorAssetLibrary.save_asset(imported_asset_path)
            return imported_asset_path
        else:
            unreal.log_error("Failed to import into Unreal")

        time.sleep(1)
        self.close()

    def create_decal(self, unreal_folder, material_name, name = "DECAL"):

        name = self.chosen_name

        temp_dir = os.path.join(unreal.Paths.project_intermediate_dir(), "TempExports")
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, (name + ".png"))

        base_size = self.texture_layers[0].pixmap.size()
        final_image = QtGui.QImage(base_size, QtGui.QImage.Format_ARGB32)
        final_image.fill(QtCore.Qt.transparent)


        pen_layer = TextureLayer(self.pen_overlay, QtCore.QPoint(0, 0))
        self.texture_layers.append(pen_layer)

        painter = QtGui.QPainter(final_image)
        for layer in self.texture_layers[1:]:
            painter.drawPixmap(layer.position, layer.pixmap)

        painter.end()

        QtGui.QPixmap.fromImage(final_image).save(temp_path, "PNG")

        import_task = unreal.AssetImportTask()
        import_task.filename = temp_path
        import_task.destination_path = unreal_folder
        import_task.destination_name = name          
        import_task.automated = True
        import_task.save = True
        import_task.replace_existing = True

        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        asset_tools.import_asset_tasks([import_task])

        imported_asset_path = f"{unreal_folder}{name}.{name}"

        if unreal.EditorAssetLibrary.does_asset_exist(imported_asset_path):
            unreal.log("Successfully imported into Unreal")
            texture_generated = unreal.EditorAssetLibrary.load_asset(imported_asset_path)
            texture_generated.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_DEFAULT)
            unreal.EditorAssetLibrary.save_asset(imported_asset_path)
        else:
            unreal.log_error("Failed to import into Unreal")

        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        material_factory = unreal.MaterialFactoryNew()
        package_path = unreal_folder
        decal_name = material_name

        #texture_path = merged_texture_path
        unreal.log(imported_asset_path)
        unreal.log(imported_asset_path)
        unreal.log(imported_asset_path)
        unreal.log(imported_asset_path)

        texture = unreal.load_asset(str(imported_asset_path))
        if texture:
            print ("TEXTURE LOADED")

        material = asset_tools.create_asset(decal_name, package_path, unreal.Material, material_factory)
        if material:
            print ("MATERIAL LOADED")
        mat_editor = unreal.MaterialEditingLibrary

        material.set_editor_property("material_domain", unreal.MaterialDomain.MD_DEFERRED_DECAL)
        material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)

        texture_sample = mat_editor.create_material_expression(material, unreal.MaterialExpressionTextureSample, -400, 0)
        texture_sample.set_editor_property("texture", texture)

        mat_editor.connect_material_property(texture_sample, "rgb", unreal.MaterialProperty.MP_BASE_COLOR)
        mat_editor.connect_material_property(texture_sample, "a", unreal.MaterialProperty.MP_OPACITY)

        mat_editor.recompile_material(material)
        unreal.EditorAssetLibrary.save_loaded_asset(material)