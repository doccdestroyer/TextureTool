
#TODO MAKE SELECTIONS SHARED
#TODO MAKE SELECTIONS LIMIT WHERE THE PEN CAN DRAW

#TODO MAKE MAGIC WAND
#TODO ADD TOLERANCE FOR WAND

#TODO MAKE COLOUR RANGE
#TODO ADD TOLERANCE FOR COLOUR RANGE

#TODO CTRL + SHIFT + I TO INVERT SELECTION

#TODO CHANGE ZOOM IN TO LOCK AT MIN AND MAX BASED ON TEXTURE SIZE



import os
import PySide6
from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtWidgets import QPushButton, QWidget, QApplication, QMainWindow, QPushButton, QWidget, QLineEdit, QLabel, QVBoxLayout, QHBoxLayout, QSlider, QRadioButton, QButtonGroup, QComboBox, QDial, QMenu, QMenuBar, QColorDialog, QDockWidget, QListWidget, QMessageBox
from PySide6.QtCore import Qt, Signal
import unreal
import math
###TODO ADJUST IMPORTS TO INCLUDE WHATS ONLY NECESARY
#from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget, QLineEdit, QLabel, QVBoxLayout, QHBoxLayout, QSlider, QRadioButton, QButtonGroup, QComboBox, QDial, QMenu, QMenuBar, QColorDialog
from PySide6.QtGui import QPainterPath,  QPolygon, QPolygonF, QAction, QImage, QColor, QPixmap, QAction, QTransform


# from PySide6.QtGui import (QAction, QFont, QIcon, QKeySequence,
#                            QTextCharFormat, QTextCursor, QTextTableFormat)
#from PySide6.QtPrintSupport import QPrintDialog, QPrinter
# from PySide6.QtWidgets import (QApplication, QDialog, QDockWidget,
#                                QFileDialog, QListWidget, QMainWindow,
#                                QMessageBox, QTextEdit)

import time
import PIL 
from PIL import Image, ImageEnhance, ImageOps, ImageQt




# selections = []

###############################################################
#                    INITIALISE TEXTURE                       # 
###############################################################
def export_texture_to_png(texture_asset):
    #ensures selection is a texture
    if not isinstance(texture_asset, unreal.Texture):
        unreal.log_error(f"{texture_asset.get_name()} is not a texture")
        return None

    #create temporary path
    temp_dir = os.path.join(unreal.Paths.project_intermediate_dir(), "TempExports")
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, f"{texture_asset.get_name()}.png")

    #create export task
    task = unreal.AssetExportTask()
    task.object = texture_asset
    task.filename = temp_path
    task.automated = True
    task.replace_identical = True
    task.prompt = False
    task.exporter = unreal.TextureExporterPNG()
    unreal.Exporter.run_asset_export_task(task)

    #ensure file is written
    if os.path.exists(temp_path):
        unreal.log(f"Exported texture to: {temp_path}")
        return temp_path
    else:
        unreal.log_error(f"Failed to export texture: {texture_asset.get_name()}")
        return None

###############################################################
#                       TEXTURE LAYERS                        # 
###############################################################
class TextureLayer:
    def __init__(self, pixmap: QtGui.QPixmap, position: QtCore.QPoint = QtCore.QPoint(0, 0)):
        self.pixmap = pixmap
        self.position = position
        self.selected = False
###############################################################
#                       RENAMER MENU                          # 
###############################################################
class ChooseNameWindow(QMainWindow):
    
    def __init__(self):
        super().__init__()           
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

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
            font-family: Consolas;
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
        if QApplication.instance():
            for win in (QApplication.allWindows()):
                if 'toolWindow' in win.objectName(): 
                    win.destroy()
        else:
            QApplication(sys.argv)

        ChooseNameWindow.window = ChooseNameWindow()
        ChooseNameWindow.window.show()
        ChooseNameWindow.window.setWindowTitle("WINDOW Demo")
        ChooseNameWindow.window.setObjectName("ToolWindow")
        unreal.parent_external_window_to_slate(ChooseNameWindow.window.winId())

class TestWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_window = parent

        im = Image.new("RGBA", (600, 600), 0x04030201)
        data = im.tobytes('raw', 'RGBA')
        #color_box = QColorDialog.getColor()
        image = QImage(data, im.size[0], im.size[1], QImage.Format_ARGB32)
        pix = QPixmap.fromImage(image)
        lbl = QLabel()
        lbl.setPixmap(pix)
        # lbl.show()

        layout = QVBoxLayout()
        layout.addWidget(lbl) 
        self.setLayout(layout)

###############################################################
#                        MAIN WINDOW                          #
###############################################################
class MainWindow(QMainWindow):
    def __init__(self, image_path):
        super().__init__()
        self.received_value = 100
        
        self.color = PySide6.QtGui.QColor.fromRgbF(0.000000, 0.000000, 0.000000, 1.000000)

        self.setWindowTitle("Selection Tools")
        self.image_path = image_path
        self.active_tool_widget = None

        self.scale_factor = 1.0
        self.pan_offset = QtCore.QPoint(0,0)
        self.texture_layers = []

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

        self.texture_layers.append(base_layer)

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

        # self.saturation_panel = Slider(parent = self, name = "Saturation Slider", min = 0, max =100, default =100)
        # self.saturation_panel.show()
        # self.saturation_panel.value_changed.connect(self.adjust_saturation)

        # self.brightness_panel = Slider(self, "Brightness Slider" , 0, 199, 100)
        # self.brightness_panel.show()
        # self.brightness_panel.value_changed.connect(self.adjust_brightness)

        # self.tool_panel = ToolSectionMenu(parent=self)
        # self.tool_panel.show()

        QtGui.QShortcut(QtGui.QKeySequence("Ctrl++"), self, activated=self.zoom_in)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+="), self, activated=self.zoom_in)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+-"), self, activated=self.zoom_out)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+0"), self, activated=self.reset_zoom)


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

        self.create_decal_button = QPushButton("Create Decal")
        #self.create_decal_button.clicked.connect(lambda: self.export_flattened_additions(str(self.prompt_add_folder_path())))
        self.create_decal_button.clicked.connect(lambda: self.create_decal(self.prompt_add_folder_path(), "M_DecalTest69"))
        self.layout.addWidget(self.create_decal_button)


        self.tool_description = None

        self.CreateToolBar()

        self.base_image = self.base_pixmap.toImage()
        self.altered_image = self.base_image

        self.saturation_value = 100
        self.green_value = 50
        self.blue_value = 50
        self.red_value = 50
        self.brightness_value = 100
        self.contrast_value = 100
        self.create_dock_windows()
        self.use_low_res = True
        self.active_tool_widget.setCursor(QtCore.Qt.CrossCursor)


    def color_dialog(self):
        self.color = QColorDialog.getColor()


        self.color_name = self.color.name()
        self.color_button.setStyleSheet(f"""
            background-color: {self.color_name};
            color: #ffffff;
            font-family: Consolas;
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
        self.color_button.setFixedSize(320,200)

        self.setStyleSheet("""
            background-color: #2c2c2c;
            color: #ffffff;
            font-family: Consolas;
            font-size: 12px;
            selection-background-color: #424242;                  
        """)  
 

        self.color_button.setStyleSheet(f"""
            background-color: #000000;
            color: #ffffff;
            font-family: Consolas;
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
        self.cyan_red_panel = Slider(self, "Colour Balance - Red " , -180, 180, 0)
        self.cyan_red_panel.value_changed.connect(self.adjust_cyan)
        #dock.setWidget(self.cyan_red_panel)
        dock.setLayout(layout)

        self.magenta_green_panel = Slider(self, "Colour Balance - Green " , 0, 100, 50)
        self.magenta_green_panel.value_changed.connect(self.adjust_greenness)

        # self.magenta_green_panel = Slider(self, "Colour Balance - Green " , -90, 90, 0)
        # self.magenta_green_panel.value_changed.connect(self.adjust_magneta)


        self.yellow_blue_panel = Slider(self, "Colour Balance - Blue " , 0, 100, 50)
        self.yellow_blue_panel.value_changed.connect(self.adjust_blueness)

        layout.addWidget(self.cyan_red_panel)
        layout.addWidget(self.magenta_green_panel)
        layout.addWidget(self.yellow_blue_panel)

        # self.setCentralWidget(central_widget)
        dock.setWidget(central_widget)
        #dock.setLayout(layout)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)



        dock = QDockWidget("Layers", self)
        self.layers = QListWidget(dock)
        self.layers.addItems((
            "ADD TOP LAYER",
            "ADD IN BETWEEN LAYERS",
            "ADD BASE LAYER"))
        dock.setWidget(self.layers)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)



        descript_dock = QDockWidget("Tool User Guide", self)
        self.tool_description_label = QLabel(self.tool_description)
        descript_dock.setWidget(self.tool_description_label)
        descript_dock.setFixedSize(225,420)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, descript_dock)

        descript_zoom_dock = QDockWidget("Zoom/Pan User Guide", self)
        self.tool_zoom_label = QLabel("  Space    -  Hold, Drag to Pan\n\n" \
        "  Ctrl +   -  Zoom In\n\n" \
        "  Ctrl -   -  Zoom Out\n\n" \
        "  Ctrl 0   -  Reset Zoom"\
        "\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\nn\n\n\n")
        descript_zoom_dock.setWidget(self.tool_zoom_label)
        descript_zoom_dock.setFixedSize(225,500)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, descript_zoom_dock)

        tool_dock = QDockWidget("Tools", self)
        self.tool_panel = ToolSectionMenu(parent=self)
        #dock.setWidget(self.tool_panel)
        #self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)

        tool_dock.setWidget(self.tool_panel)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, tool_dock)


        # Split dock1 to the right to show dock2 beside it
        self.splitDockWidget(descript_dock, tool_dock, Qt.Horizontal)



        dock = QDockWidget("Saturation", self)
        self.saturation_panel = Slider(parent = self, name = "Saturation Slider", min = 0, max =100, default =100)
        self.saturation_panel.value_changed.connect(self.adjust_saturation)
        dock.setWidget(self.saturation_panel)
        self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, dock)



        dock = QDockWidget("Brightness", self)
        self.brightness_panel = Slider(self, "Brightness Slider" , 0, 199, 100)
        self.brightness_panel.value_changed.connect(self.adjust_brightness)
        dock.setWidget(self.brightness_panel)
        self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, dock)

        dock = QDockWidget("Contrast", self)
        self.contrast_panel = Slider(self, "Contrast Slider" , 0, 199, 100)
        self.contrast_panel.value_changed.connect(self.adjust_contrast)
        dock.setWidget(self.contrast_panel)
        self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, dock)




        dock = QDockWidget("Gamma DOES NOT WORK YET", self)
        self.gamma_panel = Slider(self, "Gamma Slider" , 0, 199, 100)
        self.gamma_panel.value_changed.connect(self.adjust_contrast)
        dock.setWidget(self.gamma_panel)
        self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, dock)






        dock = QDockWidget("Apply Sliders", self)
        self.apply_button = QPushButton("APPLY")
        self.apply_button.setCheckable(True)
        self.apply_button.clicked.connect(self.apply_full_resolution_adjustments)
        self.apply_button.setFixedSize(320,50)


        dock.setWidget(self.apply_button)
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

    def adjust_cyan(self,value):
        factor = value/10
        image = self.base_image.convertToFormat(QImage.Format_ARGB32) 
        altered_image = self.altered_image.convertToFormat(QImage.Format_ARGB32)

        for pixelY in range(image.height()):
            for pixelX in range(image.width()):
                pixel_color = QColor(image.pixel(pixelX,pixelY))
                pixel_color_alt = QColor(altered_image.pixel(pixelX,pixelY))
                
                original_hue, original_saturation, original_value, original_alpha = pixel_color.getHsv()
                # new_hue, new_saturation, new_value, new_alpha = pixel_color_alt.getHsv()

                # # difference_in_hue = new_hue - original_hue

                new_hue = original_hue

                if value<0:  #becoming more cyan
                    if original_hue == 180:
                        pass
                    elif original_hue < 180:
                        new_hue = original_hue - value
                        if new_hue > 180:
                            new_hue = 180
                    elif original_hue > 180:
                        new_hue = original_hue + value
                        if new_hue < 180:
                            new_hue = 180

                elif value > 0: # becoming more red
                    if original_value == 0 or original_value == 360: 
                        pass
                    elif original_hue > 180:
                        new_hue = original_hue + value
                        if new_hue > 360:
                            new_hue = 360
                    elif original_hue <= 180:
                        new_hue = original_hue - value
                        if new_hue < 0:
                            new_hue = 0
                    
                if new_hue < 0:
                    if value > 0:
                        new_hue = 0
                    elif value <0:
                        new_hue = 360 - new_hue
                elif new_hue > 360:
                    if value > 0:
                        new_hue = 360
                    elif value < 0:
                        new_hue = new_hue - 360

                pixel_color_alt.setHsv(new_hue,original_saturation, original_value, original_alpha)

                altered_image.setPixelColor(pixelX,pixelY,pixel_color_alt)

                previous_cyan_value = value

        self.cyan_red_panel.image_label.setPixmap(QPixmap.fromImage(altered_image))

        #self.base_pixmap = QPixmap.fromImage(altered_image)
        self.altered_pixmap = QPixmap.fromImage(altered_image)

        updated_texture = TextureLayer(QPixmap.fromImage(altered_image), QtCore.QPoint(0,0))
        self.texture_layers[0] = updated_texture
        self.active_tool_widget.texture_layers[0] = updated_texture
        self.active_tool_widget.update_overlay()

        #self.altered_image = self.base_pixmap.toImage()
        #self.altered_image = self.altered_pixmap.toImage()


        self.update()


    # def adjust_magneta(self,value):
    #     factor = value/10
    #     image = self.base_image.convertToFormat(QImage.Format_ARGB32) 
    #     altered_image = self.altered_image.convertToFormat(QImage.Format_ARGB32)

    #     for pixelY in range(image.height()):
    #         for pixelX in range(image.width()):
    #             pixel_color = QColor(image.pixel(pixelX,pixelY))
    #             pixel_color_alt = QColor(altered_image.pixel(pixelX,pixelY))
                
    #             original_hue, original_saturation, original_value, original_alpha = pixel_color.getHsv()
    #             # new_hue, new_saturation, new_value, new_alpha = pixel_color_alt.getHsv()

    #             # # difference_in_hue = new_hue - original_hue

    #             new_hue = original_hue

    #             if value>0:  #becoming more magenta
    #                 if original_hue == 300:
    #                     pass
    #                 elif original_hue > 300:
    #                     new_hue = 300
    #                 elif original_hue > 120:
    #                     new_hue = original_hue + value
    #                     if new_hue > 300:
    #                         new_hue = 300
    #                 elif original_hue < 120:
    #                     new_hue = original_hue - value
    #                     if new_hue <0:
    #                         new_hue = 360 - new_hue
    #                         if new_hue < 300:
    #                             new_hue = 300

    #             elif value > 0: # becoming more green
    #                 pass
    #             pixel_color_alt.setHsv(new_hue,original_saturation, original_value, original_alpha)

    #             altered_image.setPixelColor(pixelX,pixelY,pixel_color_alt)

    #             previous_magenta_value = value

    #     self.magenta_green_panel.image_label.setPixmap(QPixmap.fromImage(altered_image))

    #     #self.base_pixmap = QPixmap.fromImage(altered_image)
    #     self.altered_pixmap = QPixmap.fromImage(altered_image)

    #     updated_texture = TextureLayer(QPixmap.fromImage(altered_image), QtCore.QPoint(0,0))
    #     self.texture_layers[0] = updated_texture
    #     self.active_tool_widget.texture_layers[0] = updated_texture
    #     self.active_tool_widget.update_overlay()

    #     #self.altered_image = self.base_pixmap.toImage()
    #     #self.altered_image = self.altered_pixmap.toImage()


    #     self.update()

    # def adjust_cyan(self,value):
    #     factor = value/100
    #     image = self.base_image.convertToFormat(QImage.Format_ARGB32) 
    #     altered_image = self.altered_image.convertToFormat(QImage.Format_ARGB32)
    #     for pixelY in range(image.height()):
    #         for pixelX in range(image.width()):
    #             pixel_color = QColor(image.pixel(pixelX,pixelY))
    #             pixel_color_alt = QColor(altered_image.pixel(pixelX,pixelY))


    #             C_ORIGINAL,M,Y,K,A = pixel_color.getCmyk()
    #             if value == 0:
    #                 pass 
    #             else:
    #                 C_ORIGINAL = 255- ((C_ORIGINAL + (255-int(C_ORIGINAL))) * factor)
    #                 # if C_ORIGINAL>255:
    #                 #     C_ORIGINAL = 255  
    #             pixel_color.setCmyk(C_ORIGINAL,M,Y,K,A)
    #             altered_image.setPixelColor(pixelX,pixelY,pixel_color)

    #         self.cyan_red_panel.image_label.setPixmap(QPixmap.fromImage(altered_image))

    #         #self.base_pixmap = QPixmap.fromImage(image)
    #         self.altered_pixmap = QPixmap.fromImage(altered_image)

    #         updated_texture = TextureLayer(QPixmap.fromImage(altered_image), QtCore.QPoint(0,0))
    #         #update textures
    #         self.texture_layers[0] = updated_texture
    #         #self.active_tool_widget.texture_layers[0] = updated_texture
    #         self.active_tool_widget.update_overlay()

    #         #self.base_image = self.base_pixmap.toImage()
    #         ########################
    #         self.altered_image = self.altered_pixmap.toImage()

    def adjust_redness(self,value):
        self.red_value = value
        factor = value/100
        image = self.base_image.convertToFormat(QImage.Format_ARGB32) 
        altered_image = self.altered_image.convertToFormat(QImage.Format_ARGB32)


        for pixelY in range(image.height()):
            for pixelX in range(image.width()):
                pixel_color = QColor(image.pixel(pixelX,pixelY))
                pixel_color_alt = QColor(altered_image.pixel(pixelX,pixelY))

                #R = pixel_color.red()
                if value == 50:
                    pass
                else:

                    B_OG_ORIGINAL = pixel_color.red()
                    if B_OG_ORIGINAL == 0:
                            B_OG_ORIGINAL = 1
                    B_OG_CHANGED = (B_OG_ORIGINAL + (255-int(B_OG_ORIGINAL))) * factor 
                    CHANGE = B_OG_CHANGED / B_OG_ORIGINAL


                    R = pixel_color_alt.red()
                    R = R * CHANGE
                    if R > 255:
                        R = 255

                    # R1,G1,B1,A1 = pixel_color_alt.getRgb()

                    # pixel_color_alt.setRgb(R,G1,B1,A1)

                    pixel_color_alt.setRed(R)

                    #do red logic tint
                altered_image.setPixelColor(pixelX,pixelY,pixel_color_alt)

        self.cyan_red_panel.image_label.setPixmap(QPixmap.fromImage(altered_image))

        #self.base_pixmap = QPixmap.fromImage(altered_image)
        self.altered_pixmap = QPixmap.fromImage(altered_image)

        updated_texture = TextureLayer(QPixmap.fromImage(altered_image), QtCore.QPoint(0,0))
        self.texture_layers[0] = updated_texture
        self.active_tool_widget.texture_layers[0] = updated_texture
        self.active_tool_widget.update_overlay()

        #self.altered_image = self.base_pixmap.toImage()
        #self.altered_image = self.altered_pixmap.toImage()


        self.update()

    def adjust_greenness(self,value):
        self.green_value = value
        factor = value/100
        image = self.base_image.convertToFormat(QImage.Format_ARGB32) 
        altered_image = self.altered_image.convertToFormat(QImage.Format_ARGB32)

        for pixelY in range(image.height()):
            for pixelX in range(image.width()):
                pixel_color = QColor(image.pixel(pixelX,pixelY))
                pixel_color_alt = QColor(altered_image.pixel(pixelX,pixelY))

                #R = pixel_color.red()
                if value == 50:
                    pass
                else:
                    #R,B_OG_ORIGINAL,B,A = pixel_color.getRgb()
                    B_OG_ORIGINAL = pixel_color.green()
                    if B_OG_ORIGINAL == 0:
                            B_OG_ORIGINAL = 1
                    B_OG_CHANGED = (B_OG_ORIGINAL + (255-int(B_OG_ORIGINAL))) * factor 
                    CHANGE = B_OG_CHANGED / B_OG_ORIGINAL


                    G = pixel_color_alt.green()
                    G = G * CHANGE
                    if G > 255:
                        G = 255

                    # R1,G1,B1,A1 = pixel_color_alt.getRgb()

                    # pixel_color_alt.setRgb(R1, G, B1, A1)

                    pixel_color_alt.setGreen(G)


                    # pixel_color_alt.setRgb(R,G,B,A)
                    #do red logic tint
                altered_image.setPixelColor(pixelX,pixelY,pixel_color_alt)

        self.magenta_green_panel.image_label.setPixmap(QPixmap.fromImage(altered_image))
        
        self.altered_pixmap = QPixmap.fromImage(altered_image)

        updated_texture = TextureLayer(QPixmap.fromImage(altered_image), QtCore.QPoint(0,0))
        self.texture_layers[0] = updated_texture
        self.active_tool_widget.texture_layers[0] = updated_texture
        self.active_tool_widget.update_overlay()

        #self.altered_image = self.base_pixmap.toImage()
        #self.altered_image = self.altered_pixmap.toImage()


        self.update()

    def adjust_blueness(self,value):
        self.blue_value = value
        factor = value/100
        image = self.base_image.convertToFormat(QImage.Format_ARGB32) 
        altered_image = self.altered_image.convertToFormat(QImage.Format_ARGB32)

        for pixelY in range(image.height()):
            for pixelX in range(image.width()):
                pixel_color = QColor(image.pixel(pixelX,pixelY))
                pixel_color_alt = QColor(altered_image.pixel(pixelX,pixelY))

                #R = pixel_color.red()
                if value == 50:
                    pass
                else:

                    B_OG_ORIGINAL = pixel_color.blue()
                    if B_OG_ORIGINAL == 0:
                            B_OG_ORIGINAL = 1
                    B_OG_CHANGED = (B_OG_ORIGINAL + (255-int(B_OG_ORIGINAL))) * factor 
                    CHANGE = B_OG_CHANGED / B_OG_ORIGINAL


                    B = pixel_color_alt.blue()
                    B = B * CHANGE
                    if B > 255:
                        B = 255


                    pixel_color_alt.setBlue(B)


                    
                    # R1,G1,B1,A1 = pixel_color_alt.getRgb()

                    # pixel_color_alt.setRgb(R1, G1, B, A1)

                    #do red logic tint
                altered_image.setPixelColor(pixelX,pixelY,pixel_color_alt)


        self.yellow_blue_panel.image_label.setPixmap(QPixmap.fromImage(altered_image))
        
        #self.base_pixmap = QPixmap.fromImage(altered_image)
        self.altered_pixmap = QPixmap.fromImage(altered_image)

        updated_texture = TextureLayer(QPixmap.fromImage(altered_image), QtCore.QPoint(0,0))
        self.texture_layers[0] = updated_texture
        self.active_tool_widget.texture_layers[0] = updated_texture
        self.active_tool_widget.update_overlay()

        #self.altered_image = self.base_pixmap.toImage()
        #self.altered_image = self.altered_pixmap.toImage()


        self.update()

    def adjust_contrast(self,value):
            factor = value/100
            if self.use_low_res:
                #original_image = self.base_image.convertToFormat(QImage.Format_ARGB32)

                self.low_res_image = self.base_image.scaled(800, 800, Qt.KeepAspectRatio, Qt.SmoothTransformation)


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

                display_size = self.base_image.size()  # QImage.size() gives QSize
                new_qimage = new_qimage.scaled(display_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)


                #self.base_pixmap = QPixmap.fromImage(image)
                self.altered_pixmap = QPixmap.fromImage(new_qimage)

                updated_texture = TextureLayer(QPixmap.fromImage(new_qimage), QtCore.QPoint(0,0))
                #update textures
                self.texture_layers[0] = updated_texture
                #self.active_tool_widget.texture_layers[0] = updated_texture
                self.active_tool_widget.update_overlay()
                self.contrast_value = value
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

                # for pixelY in range(altered_image.height()):
                #     for pixelX in range (altered_image.width()):
                #         pixel_color = QColor(altered_image.pixel(pixelX,pixelY))
                #         H,S,L,A = pixel_color.getHsl()

                contrast_enhancer = ImageEnhance.Contrast(pillow_image)
                pillow_image = contrast_enhancer.enhance(factor)

                new_qimage = ImageQt.ImageQt(pillow_image).convertToFormat(QImage.Format_ARGB32)


                #self.base_pixmap = QPixmap.fromImage(image)
                self.altered_pixmap = QPixmap.fromImage(new_qimage)

                updated_texture = TextureLayer(QPixmap.fromImage(new_qimage), QtCore.QPoint(0,0))
                #update textures
                self.texture_layers[0] = updated_texture
                #self.active_tool_widget.texture_layers[0] = updated_texture
                self.active_tool_widget.update_overlay()

                #self.base_image = self.base_pixmap.toImage()
                ########################
                self.altered_image = self.altered_pixmap.toImage()
                #self.adjust_saturation(self.saturation_value)
                self.contrast_panel.reset(100)
                self.contrast_value = 100
                self.tool_panel.radioButtonGroupChanged()
                self.update()

    def adjust_saturation(self,value):
            factor = value/100
            if self.use_low_res:
                #original_image = self.base_image.convertToFormat(QImage.Format_ARGB32)

                self.low_res_image = self.base_image.scaled(800, 800, Qt.KeepAspectRatio, Qt.SmoothTransformation)


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

                display_size = self.base_image.size()  # QImage.size() gives QSize
                new_qimage = new_qimage.scaled(display_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)


                #self.base_pixmap = QPixmap.fromImage(image)
                self.altered_pixmap = QPixmap.fromImage(new_qimage)

                updated_texture = TextureLayer(QPixmap.fromImage(new_qimage), QtCore.QPoint(0,0))
                #update textures
                self.texture_layers[0] = updated_texture
                #self.active_tool_widget.texture_layers[0] = updated_texture
                self.active_tool_widget.update_overlay()
                self.saturation_value = value
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

                # for pixelY in range(altered_image.height()):
                #     for pixelX in range (altered_image.width()):
                #         pixel_color = QColor(altered_image.pixel(pixelX,pixelY))
                #         H,S,L,A = pixel_color.getHsl()

                color_enhancer = ImageEnhance.Color(pillow_image)
                pillow_image = color_enhancer.enhance(factor)

                new_qimage = ImageQt.ImageQt(pillow_image).convertToFormat(QImage.Format_ARGB32)


                #self.base_pixmap = QPixmap.fromImage(image)
                self.altered_pixmap = QPixmap.fromImage(new_qimage)

                updated_texture = TextureLayer(QPixmap.fromImage(new_qimage), QtCore.QPoint(0,0))
                #update textures
                self.texture_layers[0] = updated_texture
                #self.active_tool_widget.texture_layers[0] = updated_texture
                self.active_tool_widget.update_overlay()

                #self.base_image = self.base_pixmap.toImage()
                ########################
                self.altered_image = self.altered_pixmap.toImage()
                #self.adjust_saturation(self.saturation_value)
                self.saturation_panel.reset(100)
                self.saturation_value = 100
                self.tool_panel.radioButtonGroupChanged()

                self.update()

    # def adjust_saturation(self,value):
    #     factor = value/100
    #     image = self.base_image.convertToFormat(QImage.Format_ARGB32)
    #     altered_image = self.altered_image.convertToFormat(QImage.Format_ARGB32)


    #     for pixelY in range(image.height()):
    #         for pixelX in range(image.width()):
    #             pixel_color_alter = QColor(altered_image.pixel(pixelX,pixelY))
    #             H,S,L,A = pixel_color_alter.getHsl()

    #             pixel_color = QColor(image.pixel(pixelX,pixelY))
    #             H1,S1,L1,A1 = pixel_color.getHsl()
    #             S1 = int(S1*factor)

    #             pixel_color_alter.setHsl(H1,S1,L,A)
    #             altered_image.setPixelColor(pixelX,pixelY,pixel_color_alter)
        
    #     self.saturation_panel.image_label.setPixmap(QPixmap.fromImage(altered_image))

    #     #self.base_pixmap = QPixmap.fromImage(image)
    #     self.altered_pixmap = QPixmap.fromImage(altered_image)

    #     updated_texture = TextureLayer(QPixmap.fromImage(altered_image), QtCore.QPoint(0,0))
    #     #update textures
    #     self.texture_layers[0] = updated_texture
    #     #self.active_tool_widget.texture_layers[0] = updated_texture
    #     self.active_tool_widget.update_overlay()

    #     #self.base_image = self.base_pixmap.toImage()
    #     ########################
    #     self.altered_image = self.altered_pixmap.toImage()

    #     self.saturation_value = value
    #     self.update()

    def adjust_brightness(self,value):
            factor = value/100
            if self.use_low_res:
                #original_image = self.base_image.convertToFormat(QImage.Format_ARGB32)

                self.low_res_image = self.base_image.scaled(800, 800, Qt.KeepAspectRatio, Qt.SmoothTransformation)


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

                display_size = self.base_image.size() 
                new_qimage = new_qimage.scaled(display_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)






                #self.base_pixmap = QPixmap.fromImage(image)
                self.altered_pixmap = QPixmap.fromImage(new_qimage)

                updated_texture = TextureLayer(QPixmap.fromImage(new_qimage), QtCore.QPoint(0,0))
                #update textures
                self.texture_layers[0] = updated_texture
                #self.active_tool_widget.texture_layers[0] = updated_texture
                self.active_tool_widget.update_overlay()
                self.brightness_value = value

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

                # for pixelY in range(altered_image.height()):
                #     for pixelX in range (altered_image.width()):
                #         pixel_color = QColor(altered_image.pixel(pixelX,pixelY))
                #         H,S,L,A = pixel_color.getHsl()

                brightness_enhancer = ImageEnhance.Brightness(pillow_image)



                pillow_image = brightness_enhancer.enhance(factor)

                new_qimage = ImageQt.ImageQt(pillow_image).convertToFormat(QImage.Format_ARGB32)


                #self.base_pixmap = QPixmap.fromImage(image)
                self.altered_pixmap = QPixmap.fromImage(new_qimage)

                updated_texture = TextureLayer(QPixmap.fromImage(new_qimage), QtCore.QPoint(0,0))
                #update textures
                self.texture_layers[0] = updated_texture
                #self.active_tool_widget.texture_layers[0] = updated_texture
                self.active_tool_widget.update_overlay()

                #self.base_image = self.base_pixmap.toImage()
                ########################
                self.altered_image = self.altered_pixmap.toImage()
                #self.adjust_saturation(self.saturation_value)
                self.brightness_panel.reset(100)
                self.brightness_value = 100
                self.tool_panel.radioButtonGroupChanged()

                self.update()


    def apply_full_resolution_adjustments(self):
        self.use_low_res = False
        self.setCursor(QtCore.Qt.ForbiddenCursor)
        if self.brightness_value != 100:
            self.adjust_brightness(self.brightness_value)
        if self.saturation_value != 100:
            self.adjust_saturation(self.saturation_value)
        if self.contrast_value != 100:
            self.adjust_contrast(self.contrast_value)
        self.tool_panel.radioButtonGroupChanged()
        self.use_low_res = True

        # Optionally update the full-res altered_image
        #self.altered_image = self.altered_pixmap.toImage()

    # def adjust_brightness(self,value):
    #         factor = value/100
    #         image = self.base_image.convertToFormat(QImage.Format_ARGB32)
    #         altered_image = self.altered_image.convertToFormat(QImage.Format_ARGB32)
    #         pil_img = ImageQt.fromqimage(altered_image)

    #         # for pixelY in range(altered_image.height()):
    #         #     for pixelX in range (altered_image.width()):
    #         #         pixel_color = QColor(altered_image.pixel(pixelX,pixelY))
    #         #         H,S,L,A = pixel_color.getHsl()

    #         brightness_enhancer = ImageEnhance.Brightness(pil_img)



    #         pil_img = brightness_enhancer.enhance(factor)

    #         new_qimage = ImageQt.ImageQt(pil_img).convertToFormat(QImage.Format_ARGB32)


    #         self.base_pixmap = QPixmap.fromImage(image)
    #         self.altered_pixmap = QPixmap.fromImage(new_qimage)

    #         updated_texture = TextureLayer(QPixmap.fromImage(new_qimage), QtCore.QPoint(0,0))
    #         #update textures
    #         self.texture_layers[0] = updated_texture
    #         #self.active_tool_widget.texture_layers[0] = updated_texture
    #         self.active_tool_widget.update_overlay()

    #         #self.base_image = self.base_pixmap.toImage()
    #         ########################
    #         self.altered_image = self.altered_pixmap.toImage()
    #         self.adjust_saturation(self.saturation_value)
    #         self.update()


    # def adjust_brightness(self,value):
    #         factor = value/100
    #         image = self.base_image.convertToFormat(QImage.Format_ARGB32)
    #         altered_image = self.altered_image.convertToFormat(QImage.Format_ARGB32)
            
    #         # for pixelY in range(altered_image.height()):
    #         #     for pixelX in range (altered_image.width()):
    #         #         pixel_color = QColor(altered_image.pixel(pixelX,pixelY))
    #         #         H,S,L,A = pixel_color.getHsl()


    #         for pixelY in range(image.height()):
    #             for pixelX in range (image.width()):

    #                 pixel_color_alter = QColor(altered_image.pixel(pixelX,pixelY))
    #                 H,S,L,A = pixel_color_alter.getHsl()


    #                 pixel_color = QColor(image.pixel(pixelX,pixelY))
    #                 H1,S1,L1,A1 = pixel_color.getHsl()
    #                 L1 = int(L1*factor)
    #                 if L1>255:
    #                     L1 = 255

    #                 pixel_color_alter.setHsl(H,S1,L1,A)
    #                 altered_image.setPixelColor(pixelX,pixelY,pixel_color_alter)

    #         self.brightness_panel.image_label.setPixmap(QPixmap.fromImage(altered_image))

    #         #self.base_pixmap = QPixmap.fromImage(image)
    #         self.altered_pixmap = QPixmap.fromImage(altered_image)

    #         updated_texture = TextureLayer(QPixmap.fromImage(altered_image), QtCore.QPoint(0,0))
    #         #update textures
    #         self.texture_layers[0] = updated_texture
    #         #self.active_tool_widget.texture_layers[0] = updated_texture
    #         self.active_tool_widget.update_overlay()

    #         #self.base_image = self.base_pixmap.toImage()
    #         ########################
    #         self.altered_image = self.altered_pixmap.toImage()
    #         self.adjust_saturation(self.saturation_value)
    #         self.update()


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
    
    def contract_selections(self):
        self.alter_selections_scale(9/10)

    def expand_selections(self):
        self.alter_selections_scale(10/9)

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
        self.tool_panel.radioButtonGroupChanged()

    def CreateToolBar(self):
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

        export_menu.addAction(export_flat_all)
        export_menu.addAction(export_flat_additions)

        export_flat_all.triggered.connect(lambda: self.export_flattened_image((str(self.prompt_add_folder_path())), self.chosen_name))
        export_flat_additions.triggered.connect(lambda: self.export_flattened_additions((str(self.prompt_add_folder_path())), self.chosen_name))
        file_menu.addMenu(export_menu)    

        self.chosen_name = "untitled"
        #change name button
        change_name_action = QAction("Change File Name", self)
        file_menu.addAction(change_name_action)
        change_name_action.triggered.connect(self.change_name)




        edit_menu = menu_bar.addMenu("Edit")

        flip_horizontal = QAction("Flip Base Layer Horizontal", self)
        flip_vertical = QAction("Flip Base Layer Vertcial", self)

        edit_menu.addAction(flip_horizontal)
        edit_menu.addAction(flip_vertical)


        flip_horizontal.triggered.connect(lambda: self.flip_horizontal())
        flip_vertical.triggered.connect(lambda: self.flip_vertical())


        flip_all_horizontal = QAction("Flip All Layers Horizontal", self)
        flip_all_vertical = QAction("Flip All Layers Vertcial", self)

        edit_menu.addAction(flip_all_horizontal)
        edit_menu.addAction(flip_all_vertical)


        flip_all_horizontal.triggered.connect(lambda: self.flip_all_horizontal())
        flip_all_vertical.triggered.connect(lambda: self.flip_all_horizontal())



        select_menu = menu_bar.addMenu("Select")

        select_all_action = QAction("Select All", self)
        clear_selections_action = QAction("Clear Selections", self)

        select_menu.addAction(select_all_action)
        select_menu.addAction(clear_selections_action)

        clear_selections_action.triggered.connect(lambda: self.clear_selections())
        select_all_action.triggered.connect(lambda: self.select_all())


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
            font-family: Consolas;
            font-size: 12px;
            selection-background-color: #424242;                  
        """)  
 
        modify_menu.setStyleSheet("""
            background-color: #252525;
            color: #ffffff;
            font-family: Consolas;
            font-size: 12px;
            selection-background-color: #424242;                  
        """)  

        export_menu.setStyleSheet("""
            background-color: #252525;
            color: #ffffff;
            font-family: Consolas;
            font-size: 12px;
            selection-background-color: #424242;                  
        """)  
 

    def flip_horizontal(self):
        self.flip_base_layer(-1,1)


    def flip_vertical(self):
        self.flip_base_layer(1,-1)

    def flip_base_layer(self,x,y):
        layer_pixmap = self.texture_layers[0].pixmap
        layer_position = self.texture_layers[0].position

        flipped_pixmap = layer_pixmap.transformed(QTransform().scale(x, y))
        flipped_position = QtCore.QPoint(layer_position.x()*x, layer_position.y()*y)

        new_layer = TextureLayer(flipped_pixmap, flipped_position)
        self.texture_layers[0] = new_layer

    def flip_all_layers(self,x,y):
        for layer in self.texture_layers:
            layer_pixmap = layer.pixmap
            layer_position = layer.position

            index = self.texture_layers.index(layer)
            flipped_pixmap = layer_pixmap.transformed(QTransform().scale(x, y))
            flipped_position = QtCore.QPoint(layer_position.x()*x, layer_position.y()*y)

            new_layer = TextureLayer(flipped_pixmap, flipped_position)
            self.texture_layers[index] = new_layer


        #flip pen overlay
        layer_pixmap = self.pen_overlay
        flipped_pixmap = layer_pixmap.transformed(QTransform().scale(x, y))
        new_layer = flipped_pixmap
        self.pen_overlay = new_layer
        self.tool_panel.radioButtonGroupChanged()
        self.active_tool_widget.update_overlay()


    def flip_all_horizontal(self):
        # for layer in self.texture_layers:
        #     layer_pixmap = layer.pixmap
        #     index = self.texture_layers.index(layer)
        #     flipped = layer_pixmap.transformed(QTransform().scale(-1, 1))
        #     new_layer = TextureLayer(flipped, QtCore.QPoint(0, 0))
        #     self.texture_layers[index] = new_layer
        self.flip_all_layers(-1,1)


    def flip_all_vertical(self):
        # for layer in self.texture_layers:
        #     layer_pixmap = layer.pixmap
        #     index = self.texture_layers.index(layer)
        #     flipped = layer_pixmap.transformed(QTransform().scale(1, -1))
        #     new_layer = TextureLayer(flipped, QtCore.QPoint(0, 0))
        #     self.texture_layers[index] = new_layer
        self.flip_all_layers(1,-1)


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
        unreal.parent_external_window_to_slate(name_window.winId())
        looping = True
        while looping:
            QApplication.processEvents()
            if name_window.button_clicked:
                self.chosen_name = name_window.getName()
                looping = False

            

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

        print(f"Loaded new texture: {texture_path}")
        new_layer = TextureLayer(self.pixmap, QtCore.QPoint(100, 100))
        self.texture_layers.append(new_layer)

        if self.active_tool_widget:
            self.active_tool_widget.update()
        self.update()


    def zoom_changed(self, value):
        if self.active_tool_widget:
            self.active_tool_widget.set_scale_factor(value / 100.0)
            self.tool_panel.radioButtonGroupChanged()

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

        pen_layer = TextureLayer(self.pen_overlay, QtCore.QPoint(100, 100))
        self.texture_layers.append(pen_layer)

        painter = QtGui.QPainter(final_image)
        for layer in self.texture_layers:
            painter.drawPixmap(layer.position, layer.pixmap)


        painter.end()

        QtGui.QPixmap.fromImage(final_image).save(temp_path, "PNG")

        import_task = unreal.AssetImportTask()
        import_task.filename = temp_path
        import_task.destination_path = unreal_folder
        import_task.automated = True
        import_task.save = True
        import_task.replace_existing = True

        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        asset_tools.import_asset_tasks([import_task])

        imported_asset_path = f"{unreal_folder}" + "/" + name + ".png"
        if unreal.EditorAssetLibrary.does_asset_exist(imported_asset_path):
            unreal.log("Succesfully imported into Unreal")
        else:
            unreal.log_error("Failed to import into Unreal")

    def export_flattened_additions(self, unreal_folder, name):
        temp_dir = os.path.join(unreal.Paths.project_intermediate_dir(), "TempExports")
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, (name + ".png"))

        base_size = self.texture_layers[0].pixmap.size()
        final_image = QtGui.QImage(base_size, QtGui.QImage.Format_ARGB32)
        final_image.fill(QtCore.Qt.transparent)


        pen_layer = TextureLayer(self.pen_overlay, QtCore.QPoint(100, 100))
        self.texture_layers.append(pen_layer)

        painter = QtGui.QPainter(final_image)
        for layer in self.texture_layers[1:]:
            painter.drawPixmap(layer.position, layer.pixmap)

        painter.end()

        QtGui.QPixmap.fromImage(final_image).save(temp_path, "PNG")

        import_task = unreal.AssetImportTask()
        import_task.filename = temp_path
        import_task.destination_path = unreal_folder
        import_task.automated = True
        import_task.save = True
        import_task.replace_existing = True

        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        asset_tools.import_asset_tasks([import_task])

        imported_asset_path = f"{unreal_folder}" + "/" + name + ".png"
        print("IMPORTED ASSET 1: ", imported_asset_path)

        time.sleep(1)
        unreal.AssetRegistryHelpers.get_asset_registry().scan_paths_synchronous([unreal_folder])

        if unreal.EditorAssetLibrary.does_asset_exist(imported_asset_path):
            unreal.log("Succesfully imported into Unreal")
            unreal.log(f"FIRST FUNCTION FILE PATH: ", imported_asset_path)
            return imported_asset_path
        else:
            unreal.log_error("Failed to import into Unreal")
            #return imported_asset_path
        
    def create_decal(self, unreal_folder, material_name):
        merged_texture_path = self.export_flattened_additions(str(self.prompt_add_folder_path()),"TESTTEST")
        print("MERGED TEXTURE PATH: ", merged_texture_path)

        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        material_factory = unreal.MaterialFactoryNew()
        package_path = unreal_folder
        decal_name = material_name

        #texture_path = merged_texture_path
        unreal.log(merged_texture_path)
        unreal.log(merged_texture_path)
        unreal.log(merged_texture_path)
        unreal.log(merged_texture_path)

        texture = unreal.load_asset(str(merged_texture_path))

        material = asset_tools.create_asset(decal_name, package_path, unreal.Material, material_factory)

        mat_editor = unreal.MaterialEditingLibrary

        material.set_editor_property("material_domain", unreal.MaterialDomain.MD_DEFERRED_DECAL)
        material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)

        texture_sample = mat_editor.create_material_expression(material, unreal.MaterialExpressionTextureSample, -400, 0)
        texture_sample.set_editor_property("texture", texture)

        mat_editor.connect_material_property(texture_sample, "rgb", unreal.MaterialProperty.MP_BASE_COLOR)
        mat_editor.connect_material_property(texture_sample, "a", unreal.MaterialProperty.MP_OPACITY)

        mat_editor.recompile_material(material)
        unreal.EditorAssetLibrary.save_loaded_asset(material)

###############################################################
#                         SLIDER                              #
###############################################################
class Slider(QWidget):
    value_changed = Signal(int)
    def __init__(self, parent, name, min, max, default):
        super().__init__(parent)
        self.parent_window = parent

        self.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setFixedSize(300, 45)
        self.setWindowTitle(name)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(min)
        self.slider.setMaximum(max)
        self.slider.setSliderPosition(default)
        self.slider.valueChanged.connect(self.sliderChanged)

        self.texture_layers = parent.texture_layers

        self.setStyleSheet("""
            background-color: #474747;
            color: #ffffff;
            font-family: Consolas;
            font-size: 12px;
            selection-background-color: #424242;                  
        """)  
 

        ################for layer in self.texture_layers: ADD ONCE LAYER SELECTION IS A THING
        self.original_pixmap = self.parent_window.base_pixmap
        self.original_image = self.original_pixmap.toImage()

        self.image_label = QLabel()
       # self.image_label.setPixmap(self.original_pixmap)


        layout = QVBoxLayout()
        layout.addWidget(self.slider)
        layout.addWidget(self.image_label) # <-- show preview REMOVE REMOVE REMOVE

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

    
###############################################################
#                    TOOL SELECTION MENU                      #
###############################################################
class ToolSectionMenu(QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.parent_window = parent

        self.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setFixedSize(150, 200)
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
        layout.addWidget(self.fill_tool)


        for button in [self.pen_tool, self.rectangle_tool, self.ellipse_tool, self.lasso_tool, self.polygonal_tool, self.move_tool, self.transform_tool, self.fill_tool]:
            self.radioButtonGroup.addButton(button)
            button.clicked.connect(self.radioButtonGroupChanged)

        self.setStyleSheet("""
            background-color: #262626;
            color: #ffffff;
            font-family: Consolas;
            font-size: 12px;
            selection-background-color: #424242;                  
        """)  
 
        self.pen_tool.setChecked(True)
        self.radioButtonGroupChanged()


    def radioButtonGroupChanged(self):
        button = self.radioButtonGroup.checkedButton()
        parent_layout = self.parent_window.layout

        if hasattr(self.parent_window, "active_tool_widget") and self.parent_window.active_tool_widget:
            parent_layout.removeWidget(self.parent_window.active_tool_widget)
            self.parent_window.active_tool_widget.deleteLater()
        #else:
            #parent_layout.removeWidget(self.parent_window.image_label)
            #self.parent_window.image_label.deleteLater()

        # self.parent_window.active_tool_widget = None

        if button == self.pen_tool:
            self.parent_window.active_tool_widget = PenTool(self.parent_window.image_path, parent_window=self.parent_window, color = self.parent_window.color)
            self.parent_window.tool_description =  "\n Pen Tool\n\n\n"\
                "  This Tool allows you to draw \n"\
                "  on the image. \n\n"\
                "  If you have had a prior \n"\
                "  selection, you will only be \n"\
                "  able to draw within that \n"\
                "  selection.\n"\
                "\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n"

        elif button == self.rectangle_tool:
            self.parent_window.active_tool_widget = RectangularTool(self.parent_window.image_path, parent_window=self.parent_window)
            self.parent_window.tool_description = "\n Rectangular Tool\n\n\n"\
                "  This tool allows you to draw \n"\
                "  rectangular selections by \n"\
                "  clicking and dragging. \n\n"\
                "  Press shift on initial click \n"\
                "  to do an additional selection. \n\n"\
                "  Press alt on initial click for \n"\
                "  a removal of your previous \n"\
                "  selection. \n\n"\
                "  Hold shift whilst drawing to \n"\
                "  lock the selection into a \n"\
                "  square. \n\n"\
                "  Hold alt whilst drawing to \n"\
                "  lock the selection around the \n"\
                "  starting point. \n\n"\
                "  Press delete to remove the \n"\
                "  entire selection.\n"\
                "\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n"

        elif button == self.ellipse_tool:
            self.parent_window.active_tool_widget = EllipticalTool(self.parent_window.image_path, parent_window=self.parent_window)
            self.parent_window.tool_description = "\n Ellipse Tool\n\n\n"\
                "  This tool allows you to draw \n"\
                "  elliptical selections by \n"\
                "  clicking and dragging. \n\n"\
                "  Press shift on initial click \n"\
                "  to do an additional selection. \n\n"\
                "  Press alt on initial click for \n"\
                "  a removal of your previous \n"\
                "  selection. \n\n"\
                "  Hold shift whilst drawing to \n"\
                "  lock the selection into a \n"\
                "  circle. \n\n"\
                "  Hold alt whilst drawing to \n"\
                "  lock the selection around the \n"\
                "  starting point. \n\n"\
                "  Press delete to remove the \n"\
                "  entire selection.\n"\
                "\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n"

        elif button == self.lasso_tool:
            self.parent_window.active_tool_widget = LassoTool(self.parent_window.image_path, parent_window=self.parent_window)
            self.parent_window.tool_description = "\n Lasso Tool\n\n\n"\
                "  This tool allows you to make \n"\
                "  freehand selections.\n\n"\
                "  Press shift on the initial click \n"\
                "  to do an additional selection.\n\n"\
                "  Press alt on initial click to do \n"\
                "  a removal of your previous \n"\
                "  selection. \n\n"\
                "  Press delete to remove the \n"\
                "  entire selection.\n"\
                "\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n"



        elif button == self.polygonal_tool:
            self.parent_window.active_tool_widget = PolygonalTool(self.parent_window.image_path, parent_window=self.parent_window)
            self.parent_window.tool_description = "\n Polygonal Lasso Tool \n\n\n"\
                "  This tool allows you to make \n"\
                "  polygonal selections by \n"\
                "  drawing point by point,\n"\
                "  ending the selection when \n"\
                "  you make contact with the \n"\
                "  original position.\n\n"\
                "  Press shift on the initial click \n"\
                "  to do an additional selection. \n\n"\
                "  Press alt on initial click to do \n"\
                "  a removal of your previous \n"\
                "  selection.\n\n"\
                "  Press delete to delete the \n"\
                "  previous point if applicable \n"\
                "  or to remove the entire \n"\
                "  selection\n"\
                "\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n"


        elif button == self.move_tool:
            self.parent_window.active_tool_widget = MoveTool(parent_window=self.parent_window)
            self.parent_window.tool_description = "\n Move Tool \n\n\n" \
                "  This tool allows you to \n"\
                "  select and move any layer.\n\n"\
                "  Left click and drag in\n"\
                "  the bounds of any image\n\n"\
                "  Left click and drag on the \n"\
                "  to move it \n"\
                "\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n"
        elif button == self.transform_tool:
            self.parent_window.active_tool_widget = TransformTool(parent_window=self.parent_window)
            self.parent_window.tool_description =  "\n Transform Tool\n\n\n"\
                "  This Tool allows you to  \n"\
                "  manipulate the selected  \n"\
                "  layer. \n\n"\
                "  Left click and drag in the  \n"\
                "  image to move it.\n\n"\
                "  Left click and drag on the  \n"\
                "  border of the image to scale  \n"\
                "  it. Go along the central point  \n"\
                "  of the image in order to flip  \n"\
                "  the image. \n\n"\
                "  eft click and drag on the  \n"\
                "  outside of the image to  \n"\
                "  rotate\n\n"\
                "\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n"
        elif button == self.fill_tool:
            self.parent_window.active_tool_widget = BucketTool(self.parent_window.image_path, parent_window=self.parent_window)
            self.parent_window.tool_description = "\n Bucket Tool\n\n\n"\

        if self.parent_window.active_tool_widget:
            parent_layout.insertWidget(0,self.parent_window.active_tool_widget)
            #parent_layout.insertWidget(1,self.parent_window.add_texture_button)
            self.parent_window.active_tool_widget.show()
            if self.parent_window.active_tool_widget == self.move_tool or  self.parent_window.active_tool_widget == self.transform_tool:
                self.parent_window.setCursor(QtCore.Qt.ArrowCursor)
            else: 
                self.parent_window.active_tool_widget.setCursor(QtCore.Qt.CrossCursor)

        self.parent_window.tool_description_label.setText(self.parent_window.tool_description)

        #self.parent_window.get_tool_description()
        self.parent_window.update()

###############################################################
#                     PEN DEBUG TOOL                          #
###############################################################
class MoveTool(QtWidgets.QWidget):
    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window

        #base_layer = self.parent_window.texture_layers[0]
        #self.setFixedSize((base_layer.pixmap.size())*0.8)
        self.texture_layers = parent_window.texture_layers

        self.panning = False
        self.last_pan_point = None

        self.dragging_layer = None
        self.drag_start_offset = QtCore.QPoint()

        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setFocus()

    def get_scaled_point(self, pos):
        scale = self.parent_window.scale_factor
        pan = self.parent_window.pan_offset
        return QtCore.QPoint(int((pos.x() - pan.x()) / scale), int((pos.y() - pan.y()) / scale))

    def set_scale_factor(self, scale):
        self.parent_window.scale_factor = scale
        base_size = self.parent_window.texture_layers[0].pixmap.size()
        new_size = base_size * scale
        self.resize(new_size)
        self.update()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            if self.panning:
                self.last_pan_point = event.position().toPoint()
                self.setCursoe(QtCore.Qt.ClosedHandCursor)
            else:
                point = self.get_scaled_point(event.position())
                for layer in reversed(self.parent_window.texture_layers):
                    rectangle = QtCore.QRect(layer.position, layer.pixmap.size())
                    if rectangle.contains(point):
                        if layer == self.parent_window.texture_layers[0]:
                            break #NEW NEW NEW  
                        else:
                            layer.selected = True
                            self.dragging_layer = layer
                            self.drag_start_offset = point - layer.position
                            break
    
    def mouseMoveEvent(self,event):
        if self.panning and self.last_pan_point:
            change = event.position().toPoint() - self.last_pan_point
            self.parent_window.pan_offset += change
            self.last_pan_point = event.position().toPoint()
            self.update()
        elif self.dragging_layer:
            new_position = self.get_scaled_point(event.position()) - self.drag_start_offset
            self.dragging_layer.position = new_position
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            if self.panning:
                self.panning = False
                self.setCursor(QtCore.Qt.ArrowCursor)
            if self.dragging_layer:
                self.dragging_layer.selected = False
                self.dragging_layer = None

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            self.panning = True
            self.setCursor(QtCore.Qt.OpenHandCursor)

    def keyReleaseEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            self.panning = False
            self.setCursor(QtCore.Qt.ArrowCursor)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.translate(self.parent_window.pan_offset)
        painter.scale(self.parent_window.scale_factor, self.parent_window.scale_factor)

        for layer in self.texture_layers[0:]:
            painter.drawPixmap(layer.position, layer.pixmap)
        painter.drawPixmap(QtCore.QPoint(0,0), self.parent_window.pen_overlay)
        
    def update_overlay(self):
        self.update()


###############################################################
#                     PEN DEBUG TOOL                          #
###############################################################
class PenTool(QtWidgets.QWidget):
    def __init__(self, image_path, parent_window=None, color=QtGui.QColor.fromRgbF(0.000000, 0.000000, 0.000000, 1.000000)):
        super().__init__()

        self.pen_color = color

        self.parent_window = parent_window


        self.texture_layers = parent_window.texture_layers

        self.image = self.parent_window.texture_layers[0].pixmap
        if self.image.isNull():
            raise ValueError("Failed to load image")

        self.original_image = self.image.copy()
        self.overlay = QtGui.QPixmap(self.image.size())
        self.overlay.fill(QtCore.Qt.transparent)

        self.pen_overlay = parent_window.pen_overlay
        
        self.points = []
        self.drawing = False

        self.panning = False
        self.last_pan_point = None

        self.in_selection = False

        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setFocus()
        self.resize(self.image.size()) 

        self.merged_selection_path = parent_window.merged_selection_path
        self.selections_paths = parent_window.selections_paths
        self.update_overlay()

    def get_scaled_point(self, pos):         
        scale = self.parent_window.scale_factor
        pan = self.parent_window.pan_offset
        return QtCore.QPoint(int((pos.x() - pan.x()) / scale), int((pos.y() - pan.y()) / scale))

    def set_scale_factor(self, scale):
        self.parent_window.scale_factor = scale
        new_size = self.original_image.size() * scale
        self.resize(new_size)
        self.update()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            self.panning = True
            self.setCursor(QtCore.Qt.OpenHandCursor)
        if event.key() == QtCore.Qt.Key_Delete:
            self.clear_overlay()

    def keyReleaseEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            self.panning = False
            self.setCursor(QtCore.Qt.CrossCursor)
        
    def paintEvent(self, event):
        unreal.log("is painting")
        painter = QtGui.QPainter(self)
        painter.translate(self.parent_window.pan_offset)     
        painter.scale(self.parent_window.scale_factor, self.parent_window.scale_factor)
        #painter.drawPixmap(0, 0, self.image)
        #painter.drawPixmap(0, 0, self.overlay)

        for layer in self.parent_window.texture_layers[0:]:
            painter.drawPixmap(layer.position, layer.pixmap)

        painter.drawPixmap(0,0, self.overlay)
        painter.drawPixmap(0,0, self.pen_overlay)

        #self.update_overlay()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
                        
            point = self.get_scaled_point(event.position())
            for i, path in enumerate(list(self.selections_paths)):
                    if path.contains(point):
                        self.in_selection = True
                    else:
                        self.in_selection = False

            if (len(self.selections_paths) > 0 and self.in_selection) or len(self.selections_paths)==0:
                if self.panning:
                    self.last_pan_point = event.position().toPoint()
                    self.setCursor(QtCore.Qt.ClosedHandCursor)
                else:
                    point = self.get_scaled_point(event.position())
                    self.drawing = True
                    self.points = [point]
                    self.update_overlay()
            else:
                return

    def mouseMoveEvent(self, event):
        if self.drawing and not self.panning:
            point = self.get_scaled_point(event.position())
            # self.points.append(point)
            # self.update_overlay()

            if len(self.selections_paths) > 0:
                for i, path in enumerate(list(self.selections_paths)):
                    if path.contains(point):
                        self.in_selection = True
                        self.points.append(point)
    
                        self.update_overlay()

                    else:
                        self.in_selection = False
                        self.update_overlay()
            else:
                self.points.append(point)
                self.update_overlay()

        if self.panning and self.last_pan_point:
            change = event.position().toPoint() - self.last_pan_point 
            self.parent_window.pan_offset += change                    
            self.last_pan_point = event.position().toPoint()
            self.update()
        self.update()
            


    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            if self.drawing:
                self.drawing = False
                self.update_overlay()

            if self.panning:
                self.panning = False
                self.setCursor(QtCore.Qt.CrossCursor)
        

    def update_overlay(self):
        self.overlay.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(self.overlay)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        outline_pen = QtGui.QPen(QtCore.Qt.red, 2)
        fill_brush = QtGui.QBrush(QtGui.QColor(255, 0, 0, 50))

        if self.in_selection or len(self.selections_paths)<1:
            if len(self.points) > 1:
                pen = QtGui.QPen(QtCore.Qt.black, 3)
                painter.setPen(pen)
                painter.drawPolyline(QtGui.QPolygon(self.points))
                self.commit_line_to_image(QtGui.QPolygon(self.points))

        #elif not self.in_selection and len(self.selections_paths)>0:
            #self.drawing = False

        for path in self.selections_paths:
            all_polys = path.toFillPolygons()
            for poly_f in all_polys:
                poly_q = QtGui.QPolygon([QtCore.QPoint(int(round(p.x())), int(round(p.y()))) for p in poly_f])
                painter.setPen(outline_pen)
                painter.setBrush(QtCore.Qt.NoBrush)
                painter.drawPolygon(poly_q)
                painter.setPen(QtCore.Qt.NoPen)
                painter.setBrush(fill_brush)
                painter.drawPolygon(poly_q)

        self.pen_color = self.parent_window.color
        painter.end()
        self.update()

    def clear_overlay(self):
        self.pen_overlay.fill(QtCore.Qt.transparent)
        self.image = self.original_image.copy()
        self.points.clear()
        self.update()

    def commit_line_to_image(self, line):
        painter = QtGui.QPainter(self.pen_overlay)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(QtGui.QPen(self.pen_color, 2))
        painter.drawPolyline(line)
        painter.end()
        self.update()


###############################################################
#                       LASSO TOOL                            # 
###############################################################
class LassoTool(QtWidgets.QWidget):
    def __init__(self, image_path, parent_window):
        print("lasso initializing")
        super().__init__()
        #self.scale_factor = 1.0

        self.parent_window = parent_window

        self.texture_layers = parent_window.texture_layers

        self.image = QtGui.QPixmap(image_path)

        if self.image.isNull():
            unreal.log_error(f"Failed to load image: {image_path}")
            #self.setText("Image failed to load")
            #self.setAlignment(QtCore.Qt.AlignCenter)
            return


        #self.setPixmap(self.image)
        self.points = []
        self.drawing = False
        self.making_additional_selection = False
        self.making_removal = False

        self.original_image = self.image.copy()
        self.overlay = QtGui.QPixmap(self.image.size())
        self.overlay.fill(QtCore.Qt.transparent)

        #self.setFixedSize(self.image.size())
        self.setWindowTitle("Lasso Tool")

        self.merged_selection_path = parent_window.merged_selection_path
        self.selections_paths = parent_window.selections_paths

        self.panning = False
        self.last_pan_point = None

        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setFocus()

        self.update_overlay()



    def get_scaled_point(self, pos):         
        scale = self.parent_window.scale_factor
        pan = self.parent_window.pan_offset
        return QtCore.QPoint(int((pos.x() - pan.x()) / scale), int((pos.y() - pan.y()) / scale))

    def set_scale_factor(self, scale):
        self.parent_window.scale_factor = scale
        new_size = self.original_image.size() * scale
        self.resize(new_size)
        self.update()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            self.panning = True
            self.setCursor(QtCore.Qt.OpenHandCursor)
        if event.key() == QtCore.Qt.Key_Delete:
            self.clear_overlay()
            self.drawing = False
            self.selections_paths.clear()
            self.points = []

    def keyReleaseEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            self.panning = False
            self.setCursor(QtCore.Qt.CrossCursor)


    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            if self.panning:
                self.last_pan_point = event.position().toPoint()
                self.setCursor(QtCore.Qt.ClosedHandCursor)
            else:
                self.points = []
                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    self.making_additional_selection = True
                    self.making_removal = False
                elif event.modifiers() & Qt.KeyboardModifier.AltModifier:
                    self.making_removal = True
                    self.making_additional_selection = False
                else:
                    self.making_additional_selection = False
                    self.making_removal = False
                    self.selections_paths.clear()
                    #selections.clear()
                    self.merged_selection_path = QPainterPath()
                    #self.image = self.original_image.copy()
                    self.clear_overlay()
                self.drawing = True
                self.points = [(self.get_scaled_point(event.position()))]
                self.update_overlay()

    def mouseMoveEvent(self, event):
        if self.drawing and not self.panning:
            self.points.append(self.get_scaled_point(event.position()))
            self.update_overlay()
        #self.update()

        if self.panning and self.last_pan_point:
            change = event.position().toPoint() - self.last_pan_point 
            self.parent_window.pan_offset += change                    
            self.last_pan_point = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            if self.panning:
                self.panning = False
                self.setCursor(QtCore.Qt.CrossCursor)
            else:
                self.drawing = False
                if len(self.points) <= 2:
                    self.points = []
                    self.update_overlay()
                    return 

                self.points.append(self.points[0])
                new_polygon_f = QPolygonF(QPolygon(self.points))
                new_path = QPainterPath()
                new_path.addPolygon(new_polygon_f)

                if not self.making_removal and not self.making_additional_selection:
                    self.selections_paths.clear()
                    self.selections_paths.append(new_path)
                else:
                    removed_from_merge = False

                    #remove polygons if overlapping
                    for i, path in enumerate(list(self.selections_paths)):
                        if path.intersects(new_path):
                            subtraction_path = path.subtracted(new_path)

                            self.selections_paths[i] = subtraction_path
                            removed_from_merge = True

                            changed = True
                            while changed:
                                changed = False
                                for k, other_path in enumerate(list(self.selections_paths)):
                                    if k == i:
                                        continue
                                    if self.selections_paths[i].intersects(other_path):
                                        self.selections_paths[i] = self.selections_paths[i].subtracted(other_path)
                                        self.selections_paths.pop(j)
                                        changed = True
                                        break
                        if not removed_from_merge:
                            self.selections_paths.append(new_path)

                if not self.making_additional_selection and not self.making_removal:
                    self.selections_paths.clear()
                    self.selections_paths.append(new_path)
                elif not self.making_removal:
                    merged_any_polygons = False

                    #merge polygons if overlapping
                    for i, path in enumerate(list(self.selections_paths)):
                        if path.intersects(new_path):
                            merge_path = path.united(new_path)

                            self.selections_paths[i] = merge_path
                            merged_any_polygons = True

                            changed = True
                            while changed:
                                changed = False
                                for j, other_path in enumerate(list(self.selections_paths)):
                                    if j == i:
                                        continue
                                    if self.selections_paths[i].intersects(other_path):
                                        self.selections_paths[i] = self.selections_paths[i].united(other_path)
                                        self.selections_paths.pop(j)
                                        changed = True
                                        break
                            break
                        if not merged_any_polygons:
                            self.selections_paths.append(new_path)
                self.points = []
                self.update_overlay()
                self.update()


    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.translate(self.parent_window.pan_offset)     
        painter.scale(self.parent_window.scale_factor, self.parent_window.scale_factor)
        # painter.drawPixmap(0, 0, self.image)
        # painter.drawPixmap(0, 0, self.overlay)

        for layer in self.texture_layers[0:]:
            painter.drawPixmap(layer.position, layer.pixmap)

        painter.drawPixmap(QtCore.QPoint(0,0), self.parent_window.pen_overlay)
        painter.drawPixmap(0, 0, self.overlay)
        
    def clear_overlay(self):
        self.overlay.fill(QtCore.Qt.transparent)
        #self.points.clear()
        self.update()


    def update_overlay(self):
        self.overlay.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(self.overlay)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        outline_pen = QtGui.QPen(QtCore.Qt.red, 2)
        fill_brush = QtGui.QBrush(QtGui.QColor(255, 0, 0, 50))

        for path in self.selections_paths:
            all_polys = path.toFillPolygons()
            for poly_f in all_polys:
                poly_q = QtGui.QPolygon([QtCore.QPoint(int(round(p.x())), int(round(p.y()))) for p in poly_f])
                painter.setPen(outline_pen)
                painter.setBrush(QtCore.Qt.NoBrush)
                painter.drawPolygon(poly_q)
                painter.setPen(QtCore.Qt.NoPen)
                painter.setBrush(fill_brush)
                painter.drawPolygon(poly_q)

        if len(self.points) > 1:
            painter.setPen(outline_pen)
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.drawPolyline(QtGui.QPolygon(self.points))


        painter.end()
        self.update()

    # def commit_polygon_to_image(self,polygon):
    #     painter = QtGui.QPainter(self.image)
    #     painter.setRenderHint(QtGui.QPainter.Antialiasing)
    #     painter.setBrush(QtGui.QColor(255, 0, 0, 50))
    #     painter.setPen(QtGui.QPen(QtCore.Qt.red, 2))
    #     painter.drawPolygon(polygon)
    #     painter.end()
    #     self.update()

###############################################################
#CreatePolygonalLassoTool
###############################################################
class PolygonalTool(QtWidgets.QLabel):
    def __init__(self, image_path, parent_window=None):
        super().__init__()
        self.image = QtGui.QPixmap(image_path)

        self.parent_window = parent_window
        self.texture_layers = parent_window.texture_layers

        if self.image.isNull():
            self.setText("Image failed to load")
            self.setAlignment(QtCore.Qt.AlignCenter)
            return

        self.original_image = self.image.copy()
        self.overlay = QtGui.QPixmap(self.image.size())
        self.overlay.fill(QtCore.Qt.transparent)

        #self.setPixmap(self.image)
        self.points = []
        self.hover_point = None
        self.drawing = False
        self.is_first_click = True
        self.making_additional_selection = False
        self.making_removal = False

        #self.parent_window.scale_factor = scale_factor
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setFocus()

        self.setMouseTracking(True)
        #self.setFixedSize(self.image.size())
        self.setWindowTitle("Polygonal Tool")

        self.panning = False
        self.last_pan_point = None

        self.merged_selection_path = parent_window.merged_selection_path
        self.selections_paths = parent_window.selections_paths

        self.update_overlay()


    def get_scaled_point(self, pos):         
        scale = self.parent_window.scale_factor
        pan = self.parent_window.pan_offset
        return QtCore.QPoint(int((pos.x() - pan.x()) / scale), int((pos.y() - pan.y()) / scale))
    
    def set_scale_factor(self, scale):
        self.parent_window.scale_factor = scale
        new_size = self.original_image.size() * scale
        self.resize(new_size)
        self.update()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            self.panning = True
            self.setCursor(QtCore.Qt.OpenHandCursor)
        if event.key() == QtCore.Qt.Key_Delete:
            if self.drawing:
                if len(self.points)>0:
                    self.points.remove(self.points[-1])
                else:
                    self.clear_overlay()
                    self.drawing = False
                    self.selections_paths.clear()
                    self.points = []
                    self.is_first_click = True
            else:   
                self.clear_overlay()
                self.drawing = False
                self.selections_paths.clear()
                self.points = []
                self.is_first_click = True

    def keyReleaseEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            self.panning = False
            self.setCursor(QtCore.Qt.CrossCursor)

    def mousePressEvent(self, event):
        global selections
        isComplete = False
        new_path = QPainterPath()

        if event.button() == QtCore.Qt.LeftButton:
            if self.panning:
                self.last_pan_point = event.position().toPoint()
                self.setCursor(QtCore.Qt.ClosedHandCursor)
            else:
                point = self.get_scaled_point(event.position()) 
                if self.is_first_click:
                    isComplete = False
                    self.points = [point]
                    self.drawing = True
                    self.is_first_click = False
                    if event.modifiers() & QtCore.Qt.ShiftModifier:
                        self.making_additional_selection = True
                        self.making_removal = False
                    elif event.modifiers() & Qt.KeyboardModifier.AltModifier:
                        self.making_removal = True
                        self.making_additional_selection = False
                    else:
                        self.making_additional_selection = False
                        self.making_removal = False
                        self.selections_paths.clear()
                        self.merged_selection_path = QPainterPath()
                        self.image = self.original_image.copy()

                        self.clear_overlay()
                        self.update()

                else: #Check if polygon has completed
                    if (point - self.points[0]).manhattanLength() < 20:
                        isComplete = True
                        self.points.append(self.points[0])
                        self.drawing = False 
                        self.is_first_click = True
                        if self.making_additional_selection:
                            selections.append(QtGui.QPolygon(self.points))
                        else:
                            selections = [QtGui.QPolygon(self.points)]

                        new_polygon_f = QPolygonF(QPolygon(self.points))
                        new_path = QPainterPath()
                        new_path.addPolygon(new_polygon_f)

                        if not self.making_removal and not self.making_additional_selection and isComplete:
                            self.selections_paths.clear()
                            self.selections_paths.append(new_path)
                        elif self.making_removal and isComplete:
                            removed_from_merge = False

                            #remove polygons if overlapping
                            for i, path in enumerate(list(self.selections_paths)):
                                if path.intersects(new_path):
                                    subtraction_path = path.subtracted(new_path)

                                    self.selections_paths[i] = subtraction_path
                                    removed_from_merge = True

                                    changed = True
                                    while changed:
                                        changed = False
                                        for k, other_path in enumerate(list(self.selections_paths)):
                                            if k == i:
                                                continue
                                            if self.selections_paths[i].intersects(other_path):
                                                self.selections_paths[i] = self.selections_paths[i].subtracted(other_path)
                                                self.selections_paths.pop(j)
                                                changed = True
                                                break
                                    
                                if not removed_from_merge:
                                    self.selections_paths.append(new_path)

                        if not self.making_additional_selection and not self.making_removal:
                            self.selections_paths.clear()
                            self.selections_paths.append(new_path)
                        elif not self.making_removal:
                            print("merging polygons function")
                            merged_any_polygons = False
                            for i, path in enumerate(list(self.selections_paths)):
                                if path.intersects(new_path):
                                    merge_path = path.united(new_path)

                                    self.selections_paths[i] = merge_path
                                    merged_any_polygons = True

                                    changed = True
                                    while changed:
                                        changed = False
                                        for j, other_path in enumerate(list(self.selections_paths)):
                                            if j == i:
                                                continue
                                            if self.selections_paths[i].intersects(other_path):
                                                self.selections_paths[i] = self.selections_paths[i].united(other_path)
                                                self.selections_paths.pop(j)
                                                changed = True
                                                break
                                    break
                                if not merged_any_polygons:
                                    self.selections_paths.append(new_path)
                            self.clear_overlay()
                    else:
                        self.points.append(point)
                self.update_overlay()

    def mouseMoveEvent(self, event):
        # if not self.panning:
        #     self.hover_point = self.get_scaled_point(event.position())
        #     if self.drawing:
        #         self.update_overlay()
        #     self.update()
        if self.panning and self.last_pan_point:
            change = event.position().toPoint() - self.last_pan_point 
            self.parent_window.pan_offset += change
            self.last_pan_point = event.position().toPoint()
            self.update()
        else:
            self.hover_point = self.get_scaled_point(event.position())
            if self.drawing:
                self.update_overlay()
            self.update()

    def mouseReleaseEvent(self,event):
        if event.button() == QtCore.Qt.LeftButton:
            if self.panning:
                self.panning = False
                self.last_pan_point = None
                self.setCursor(QtCore.Qt.CrossCursor)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.translate(self.parent_window.pan_offset)     
        painter.scale(self.parent_window.scale_factor, self.parent_window.scale_factor)
        # painter.drawPixmap(0, 0, self.image)   
        # painter.drawPixmap(0, 0, self.overlay)

        for layer in self.parent_window.texture_layers[0:]:
            painter.drawPixmap(layer.position, layer.pixmap)
        painter.drawPixmap(QtCore.QPoint(0,0), self.parent_window.pen_overlay)
        painter.drawPixmap(0, 0, self.overlay)
        
    ###HERE NEEDS TO BE REMOVED
    def clear_overlay(self):
        self.overlay.fill(QtCore.Qt.transparent)
        self.update()
        

    def update_overlay(self):
        self.overlay.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(self.overlay)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        outline_pen = QtGui.QPen(QtCore.Qt.red, 2)
        fill_brush = QtGui.QBrush(QtGui.QColor(255, 0, 0, 50))

        for path in self.selections_paths:
            all_polys = path.toFillPolygons()
            for poly_f in all_polys:
                poly_q = QtGui.QPolygon([QtCore.QPoint(int(round(p.x())), int(round(p.y()))) for p in poly_f])
                painter.setPen(outline_pen)
                painter.setBrush(QtCore.Qt.NoBrush)
                painter.drawPolygon(poly_q)
                painter.setPen(QtCore.Qt.NoPen)
                painter.setBrush(fill_brush)
                painter.drawPolygon(poly_q)

        if len(self.points) > 1 and self.drawing:
            painter.setPen(outline_pen)
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.drawPolyline(QtGui.QPolygon(self.points))

        #add guide line
        if self.drawing and self.hover_point and self.points:
            painter.setPen(QtGui.QPen(QtCore.Qt.red, 1, QtCore.Qt.DashLine))
            painter.drawLine(self.points[-1], self.hover_point)

        painter.end()
        self.update()

    # def commit_polygon_to_image(self, polygon):
    #     painter = QtGui.QPainter(self.image)
    #     painter.setRenderHint(QtGui.QPainter.Antialiasing)
    #     painter.setBrush(QtGui.QColor(255, 0, 0, 50))
    #     painter.setPen(QtGui.QPen(QtCore.Qt.red, 2))
    #     painter.drawPolygon(polygon)
    #     painter.end()
    #     self.update()

###############################################################
#                    MAGIC WAND TOOL                          #
###############################################################
class MagicWandTool(QtWidgets.QLabel):
    def __init__(self, image_path, parent_window):
        self.image = QtGui.QPixmap(image_path)

        self.parent_window = parent_window

        self.texture_layers = parent_window.texture_layers     

        self.points = []
        if self.image.isNull():
            unreal.log_error(f"Failed to load image.")
            self.setText("Image failed to load")
            self.setAlignment(QtCore.Qt.AlignCenter)
            return
        
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setFocus()

        self.making_additional_selection = False
        self.making_removal = False

        self.resize(self.image.size())

        self.panning = False
        self.last_pan_point = None

        self.merged_selection_path = parent_window.merged_selection_path
        self.selections_paths = parent_window.selections_paths

        self.update_overlay()

    def get_scaled_point(self, pos):         
        scale = self.parent_window.scale_factor
        pan = self.parent_window.pan_offset
        return QtCore.QPoint(int((pos.x() - pan.x()) / scale), int((pos.y() - pan.y()) / scale))

    def set_scale_factor(self, scale):
        self.parent_window.scale_factor = scale
        new_size = self.original_image.size() * scale
        self.resize(new_size)
        self.update()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            self.panning = True
            self.setCursor(QtCore.Qt.OpenHandCursor)
        if event.key() == QtCore.Qt.Key_Delete:
            self.clear_overlay()
            self.drawing = False
            self.selections_paths.clear()
            self.points = []

    def keyReleaseEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            self.panning = False
            self.setCursor(QtCore.Qt.CrossCursor)

    def mousePressEvent(self,event):
        if event.button() == QtCore.Qt.LeftButton:
            if self.panning:
                self.last_pan_point = event.position().toPoint()
                self.setCursor(QtCore.Qt.ClosedHandCursor)
            else:
                if event.modifiers() & QtCore.Qt.ShiftModifier:
                    self.making_additional_selection = True
                    self.making_removal = False
                elif event.modifiers() & Qt.KeyboardModifier.AltModifier:
                    self.making_removal = True
                    self.making_additional_selection = False
                else:
                    self.making_additional_selection = False
                    self.making_removal = False
                    self.selections_paths.clear()

                    self.merged_selection_path = QPainterPath()
                    self.image = self.original_image.copy()
                    self.clear_overlay()

                self.start_point = self.get_scaled_point(event.position())
                #magic wand logic goes here

###############################################################
#                     RECTANGLE TOOL                          #
###############################################################
class RectangularTool(QtWidgets.QLabel):
    def __init__(self, image_path, parent_window):
        super().__init__()
        self.image = QtGui.QPixmap(image_path)

        self.parent_window = parent_window

        self.texture_layers = parent_window.texture_layers

        self.points = []
        if self.image.isNull():
            unreal.log_error(f"Failed to load image.")
            self.setText("Image failed to load")
            self.setAlignment(QtCore.Qt.AlignCenter)
            return
        
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setFocus()

        self.original_image = self.image.copy()
        self.overlay = QtGui.QPixmap(self.image.size())
        self.overlay.fill(QtCore.Qt.transparent)

        self.release_point = QtCore.QPoint(0, 0)
        self.start_point = QtCore.QPoint(0, 0)
        self.hover_point = QtCore.QPoint(0, 0)
        self.setMouseTracking(True)
        self.setPixmap(self.image)
        self.drawing = False
        self.drawing_square = False
        self.drawing_in_place = False

        self.making_additional_selection = False
        self.making_removal = False

        self.resize(self.image.size())

        self.panning = False
        self.last_pan_point = None

        #self.setFixedSize(self.image.size())
        self.setWindowTitle("Rectangle Tool")

        self.merged_selection_path = parent_window.merged_selection_path
        self.selections_paths = parent_window.selections_paths

        self.update_overlay()


    def get_scaled_point(self, pos):         
        scale = self.parent_window.scale_factor
        pan = self.parent_window.pan_offset
        return QtCore.QPoint(int((pos.x() - pan.x()) / scale), int((pos.y() - pan.y()) / scale))

    def set_scale_factor(self, scale):
        self.parent_window.scale_factor = scale
        new_size = self.original_image.size() * scale
        self.resize(new_size)
        self.update()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            self.panning = True
            self.setCursor(QtCore.Qt.OpenHandCursor)
        if event.key() == QtCore.Qt.Key_Delete:
            self.clear_overlay()
            self.drawing = False
            self.selections_paths.clear()
            self.points = []

    def keyReleaseEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            self.panning = False
            self.setCursor(QtCore.Qt.CrossCursor)


    def mousePressEvent(self,event):
        if event.button() == QtCore.Qt.LeftButton:
            if self.panning:
                self.last_pan_point = event.position().toPoint()
                self.setCursor(QtCore.Qt.ClosedHandCursor)
            else:
                if event.modifiers() & QtCore.Qt.ShiftModifier:
                    self.making_additional_selection = True
                    self.making_removal = False
                elif event.modifiers() & Qt.KeyboardModifier.AltModifier:
                    self.making_removal = True
                    self.making_additional_selection = False
                else:
                    self.making_additional_selection = False
                    self.making_removal = False
                    self.selections_paths.clear()
                    #selections.clear()
                    self.merged_selection_path = QPainterPath()
                    self.image = self.original_image.copy()
                    self.clear_overlay()

                    #self.update()
                self.release_point = QtCore.QPoint(0, 0)
                self.start_point = QtCore.QPoint(0, 0)
                self.drawing = True
                self.start_point = self.get_scaled_point(event.position())
                self.update_overlay()




    def mouseMoveEvent(self, event):
        if self.drawing and not self.panning:
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.drawing_square = True
            else:
                self.drawing_square = False

            if event.modifiers() & Qt.KeyboardModifier.AltModifier:
                self.drawing_in_place = True
            else:
                self.drawing_in_place = False

            self.hover_point = self.get_scaled_point(event.position())
            self.update_overlay()
            self.update()

        if self.panning and self.last_pan_point:
            change = event.position().toPoint() - self.last_pan_point 
            self.parent_window.pan_offset += change                    
            self.last_pan_point = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self,event):
        if event.button() == QtCore.Qt.LeftButton:
            if self.panning:
                self.panning = False
                self.last_pan_point = None
                self.setCursor(QtCore.Qt.CrossCursor)
            else:            
                if self.drawing:
                    self.release_point = self.get_scaled_point(event.position())

                if self.drawing_square:
                    self.drawing_square = False
                    self.x_difference = (self.release_point.x()-self.start_point.x())
                    self.y_difference = (self.release_point.y()-self.start_point.y())

                    variance = min(abs(self.x_difference), abs(self.y_difference))

                    if self.x_difference <0:
                        directionX = -1
                    else:
                        directionX = 1

                    if self.y_difference <0:
                        directionY = -1
                    else:
                        directionY = 1

                    self.release_point.setY(self.start_point.y() + variance * directionY)
                    self.release_point.setX(self.start_point.x() + variance * directionX)
                    self.update_overlay()

                else:
                    self.release_point = self.get_scaled_point(event.position())
                    self.drawing = False
                    self.update()

                    

                if self.drawing_in_place:
                    self.drawing_in_place

                    self.central_point = self.start_point
                    self.start_point = self.hover_point

                    self.x_difference = (self.hover_point.x()-self.central_point.x())
                    self.y_difference = (self.hover_point.y()-self.central_point.y())
                    #self.release_point = -1 * self.hover_point
                    self.release_point.setY(self.central_point.y()-self.y_difference)
                    self.release_point.setX(self.central_point.x()-self.x_difference)



                    #self.commit_rectanlge_to_image()
                    self.update()

                elif not self.drawing_square:
                    #self.release_point = event.position().toPoint()
                    #self.drawing = False
                    #self.commit_rectanlge_to_image()
                    self.update()
                


            new_polygon_f = QPolygonF(QPolygon(QtCore.QRect(self.start_point, self.release_point)))
            new_path = QPainterPath()
            new_path.addPolygon(new_polygon_f)
                
            if self.making_additional_selection and self.drawing:
                #selections.append((QtCore.QRect(self.start_point, self.release_point)))
                self.selections_paths.append(new_path)
            #elif self.drawing:
                # #selections.clear()
                # #self.selection = QtCore.QRect(self.start_point, self.release_point)
                # self.selections_paths.clear()
                # self.selections_paths.append(new_path)
                # self.image = self.original_image.copy()
            self.drawing = False
            self.update_overlay()

            #convert rectanlge into polygon
            # new_polygon_f = QPolygonF(QPolygon(QtCore.QRect(self.start_point, self.release_point)))
            # new_path = QPainterPath()
            # new_path.addPolygon(new_polygon_f)
                
            if not self.making_removal and not self.making_additional_selection:
                self.selections_paths.clear()
                self.selections_paths.append(new_path)
            elif self.making_removal:
                removed_from_merge = False

                #remove polygons if overlapping
                for i, path in enumerate(list(self.selections_paths)):
                    if path.intersects(new_path):
                        subtraction_path = path.subtracted(new_path)

                        self.selections_paths[i] = subtraction_path
                        removed_from_merge = True

                        changed = True
                        while changed:
                            changed = False
                            for k, other_path in enumerate(list(self.selections_paths)):
                                if k == i:
                                    continue
                                if self.selections_paths[i].intersects(other_path):
                                    self.selections_paths[i] = self.selections_paths[i].subtracted(other_path)
                                    print ("section removed")
                                    self.selections_paths.pop(k)
                                    changed = True
                                    break
                        
                    if not removed_from_merge:
                        self.selections_paths.append(new_path)


            elif not self.making_additional_selection:
                self.selections_paths.clear()
                self.selections_paths.append(new_path)

            else:
                merged_any_polygons = False

                #merge polygons if overlapping
                for i, path in enumerate(list(self.selections_paths)):
                    if path.intersects(new_path):
                        merge_path = path.united(new_path)

                        self.selections_paths[i] = merge_path
                        merged_any_polygons = True

                        changed = True
                        while changed:
                            changed = False
                            for l, other_path in enumerate(list(self.selections_paths)):
                                if l == i:
                                    continue
                                if self.selections_paths[i].intersects(other_path):
                                    self.selections_paths[i] = self.selections_paths[i].united(other_path)
                                    self.selections_paths.pop(l)
                                    changed = True
                                    break
                        break
                    if not merged_any_polygons:
                        self.selections_paths.append(new_path)
            self.points = []
            self.update_overlay()
            self.update()


    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.translate(self.parent_window.pan_offset)     
        painter.scale(self.parent_window.scale_factor, self.parent_window.scale_factor)
        # painter.drawPixmap(0, 0, self.image)
        # painter.drawPixmap(0, 0, self.overlay)

        for layer in self.parent_window.texture_layers[0:]:
            painter.drawPixmap(layer.position, layer.pixmap)
        painter.drawPixmap(QtCore.QPoint(0,0), self.parent_window.pen_overlay)
        painter.drawPixmap(0, 0, self.overlay)

    def clear_overlay(self):
        self.overlay.fill(QtCore.Qt.transparent)
        self.update()

    def update_overlay(self):
        self.overlay.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(self.overlay)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        self.isDrawn = False
        

        # if self.start_point != QtCore.QPoint(0, 0) and self.release_point != QtCore.QPoint(0, 0 and self.drawing):
                    
        #     painter.setPen(QtGui.QPen(QtCore.Qt.red, 2))
        #     rectangle = QtCore.QRect(self.start_point, self.release_point)
        #     painter.drawRect(rectangle)
        #     self.isDrawn = True

        if self.start_point != QtCore.QPoint(0, 0) and self.hover_point != QtCore.QPoint(0, 0) and self.drawing:
            if self.drawing_square and self.drawing:

                self.x_difference = (self.hover_point.x()-self.start_point.x())
                self.y_difference = (self.hover_point.y()-self.start_point.y())
                variance = min(abs(self.x_difference), abs(self.y_difference))

                if self.x_difference <0:
                    directionX = -1
                else:
                    directionX = 1

                if self.y_difference <0:
                    directionY = -1
                else:
                    directionY = 1

                self.hover_point.setY(self.start_point.y() + variance * directionY)
                self.hover_point.setX(self.start_point.x() + variance * directionX)
            

                rectangle = QtCore.QRect(self.start_point, self.hover_point)
                if not self.drawing_in_place:
                    painter.setPen(QtGui.QPen(QtCore.Qt.red, 1, QtCore.Qt.DashLine))
                    painter.drawRect(rectangle)
                self.update()

            if self.drawing_in_place and self.drawing:
                self.central_point = self.start_point
                self.inital_point = self.hover_point
                #self.start_point = self.hover_point
                self.x_difference = (self.inital_point.x()-self.central_point.x())
                self.y_difference = (self.inital_point.y()-self.central_point.y())     

                self.temporary_release_point =  QtCore.QPoint(0, 0)

                self.temporary_release_point.setY(self.central_point.y()-self.y_difference)
                self.temporary_release_point.setX(self.central_point.x()-self.x_difference)

                painter.setPen(QtGui.QPen(QtCore.Qt.red, 1, QtCore.Qt.DashLine))
                rectangle = QtCore.QRect(self.inital_point, self.temporary_release_point)
                painter.drawRect(rectangle)
                #self.isDrawn = True

                

            elif self.drawing and not self.isDrawn and not self.drawing_square:
                painter.setPen(QtGui.QPen(QtCore.Qt.red, 1, QtCore.Qt.DashLine))
                rectangle = QtCore.QRect(self.start_point, self.hover_point)
                painter.drawRect(rectangle)
            



#if self.isDrawn:
            #painter.setBrush(QtGui.QColor(255,0,0,50))
            #self.commit_rectanlge_to_image(rectangle)
            #selections.append()

        if not self.drawing:
            self.clear_overlay()
            
        outline_pen = QtGui.QPen(QtCore.Qt.red, 2)
        fill_brush = QtGui.QBrush(QtGui.QColor(255, 0, 0, 50))

        for path in self.selections_paths:
            all_polys = path.toFillPolygons()
            for poly_f in all_polys:
                poly_q = QtGui.QPolygon([QtCore.QPoint(int(round(p.x())), int(round(p.y()))) for p in poly_f])
                painter.setPen(outline_pen)
                painter.setBrush(QtCore.Qt.NoBrush)
                painter.drawPolygon(poly_q)
                painter.setPen(QtCore.Qt.NoPen)
                painter.setBrush(fill_brush)
                painter.drawPolygon(poly_q)

    # def commit_rectanlge_to_image(self,rectangle):
    #     painter = QtGui.QPainter(self.image)
    #     painter.setRenderHint(QtGui.QPainter.Antialiasing)
    #     painter.setBrush(QtGui.QColor(255, 0, 0, 50))
    #     painter.setPen(QtGui.QPen(QtCore.Qt.red, 2))
    #     painter.drawRect(rectangle)
    #     painter.end()
    #     self.update()
###############################################################
#                       ELLIPSE TOOL                          #
###############################################################
class EllipticalTool(QtWidgets.QLabel):
    def __init__(self, image_path, parent_window):

        self.parent_window = parent_window

        self.texture_layers = parent_window.texture_layers

        super().__init__()
        self.image = QtGui.QPixmap(image_path)
        self.points = []
        if self.image.isNull():
            unreal.log_error(f"Failed to load image.")
            self.setText("Image failed to load")
            self.setAlignment(QtCore.Qt.AlignCenter)
            return
        
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setFocus()

        
        self.overlay = QtGui.QPixmap(self.image.size())
        self.overlay.fill(QtCore.Qt.transparent)
        self.original_image = self.image.copy()

        self.release_point = QtCore.QPoint(0, 0)
        self.start_point = QtCore.QPoint(0, 0)
        self.hover_point = QtCore.QPoint(0, 0)
        self.setMouseTracking(True)
        self.setPixmap(self.image)
        self.drawing = False
        self.drawing_circle = False
        self.drawing_in_place = False

        self.making_additional_selection = False
        self.making_removal = False

        #self.setFixedSize(self.image.size())
        self.setWindowTitle("Ellipse Tool")

        self.merged_selection_path = parent_window.merged_selection_path
        self.selections_paths = parent_window.selections_paths

        self.panning = False
        self.last_pan_point = None

        self.update_overlay()

    def set_scale_factor(self, scale):
        self.parent_window.scale_factor = scale
        new_size = self.original_image.size() * scale
        self.resize(new_size)
        self.update()

    def get_scaled_point(self, pos):         
        scale = self.parent_window.scale_factor
        pan = self.parent_window.pan_offset
        return QtCore.QPoint(int((pos.x() - pan.x()) / scale), int((pos.y() - pan.y()) / scale))

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            self.panning = True
            self.setCursor(QtCore.Qt.OpenHandCursor)
        if event.key() == QtCore.Qt.Key_Delete:
            self.clear_overlay()
            self.drawing = False
            self.selections_paths.clear()
            self.points = []

    def keyReleaseEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            self.panning = False
            self.setCursor(QtCore.Qt.CrossCursor)


    def mousePressEvent(self,event):
        if event.button() == QtCore.Qt.LeftButton:
            if self.panning:
                self.last_pan_point = event.position().toPoint()
                self.setCursor(QtCore.Qt.ClosedHandCursor)
            else:
                if event.modifiers() & QtCore.Qt.ShiftModifier:
                    self.making_additional_selection = True
                    self.making_removal = False
                elif event.modifiers() & Qt.KeyboardModifier.AltModifier:
                    self.making_removal = True
                    self.making_additional_selection = False
                else:
                    self.making_additional_selection = False
                    self.making_removal = False
                    self.selections_paths.clear()
                    #selections.clear()
                    self.merged_selection_path = QPainterPath()
                    self.image = self.original_image.copy()
                    self.clear_overlay()
                    #self.update()
                self.release_point = QtCore.QPoint(0, 0)
                self.start_point = QtCore.QPoint(0, 0)
                self.drawing = True
                self.start_point = self.get_scaled_point(event.position())
                self.update_overlay()




    def mouseMoveEvent(self, event):
        if self.drawing and not self.panning:
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.drawing_circle = True
            else:
                self.drawing_circle = False

            if event.modifiers() & Qt.KeyboardModifier.AltModifier:
                self.drawing_in_place = True
            else:
                self.drawing_in_place = False

            self.hover_point = self.get_scaled_point(event.position())
            self.update_overlay()
            self.update()

        if self.panning and self.last_pan_point:
            change = event.position().toPoint() - self.last_pan_point 
            self.parent_window.pan_offset += change                    
            self.last_pan_point = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self,event):
        if event.button() == QtCore.Qt.LeftButton:
            if self.panning:
                self.panning = False
                self.last_pan_point = None
                self.setCursor(QtCore.Qt.CrossCursor)
            else:               
                if self.drawing:
                    self.release_point = self.get_scaled_point(event.position())

                if self.drawing_circle:
                    self.drawing_circle = False
                    self.x_difference = (self.release_point.x()-self.start_point.x())
                    self.y_difference = (self.release_point.y()-self.start_point.y())

                    variance = min(abs(self.x_difference), abs(self.y_difference))

                    if self.x_difference <0:
                        directionX = -1
                    else:
                        directionX = 1

                    if self.y_difference <0:
                        directionY = -1
                    else:
                        directionY = 1

                    self.release_point.setY(self.start_point.y() + variance * directionY)
                    self.release_point.setX(self.start_point.x() + variance * directionX)
                    self.update_overlay()

                else:
                    self.release_point = self.get_scaled_point(event.position())
                    self.drawing = False
                    self.update()

                    

                if self.drawing_in_place:
                    #self.drawing_in_place

                    self.central_point = self.start_point
                    self.start_point = self.hover_point

                    self.x_difference = (self.hover_point.x()-self.central_point.x())
                    self.y_difference = (self.hover_point.y()-self.central_point.y())
                    #self.release_point = -1 * self.hover_point
                    self.release_point.setY(self.central_point.y()-self.y_difference)
                    self.release_point.setX(self.central_point.x()-self.x_difference)
                    ellipse = QtCore.QRect(self.start_point, self.release_point)



                    #self.commit_rectanlge_to_image()
                    self.update()

                elif not self.drawing_circle:
                    #self.release_point = event.position().toPoint()
                    #self.drawing = False
                    #self.commit_rectanlge_to_image()
                    self.update()
                    ellipse = QtCore.QRect(self.start_point, self.hover_point)



            #convert rectanlge into polygon
            painter = QtGui.QPainter(self)
            ellipse_path = QtGui.QPainterPath()
            ellipse_path.addEllipse(ellipse)
            ellipse_polygon = ellipse_path.toFillPolygon()

            new_polygon_f = QtGui.QPolygonF(map_points_of_polygon(ellipse_polygon, 100))
            new_path = QPainterPath()
            new_path.addPolygon(new_polygon_f)
                
            if self.making_additional_selection:
                self.selections_paths.append(new_path)
            # else:
            #     selections.clear()
            #     self.selection = QtCore.QRect(self.start_point, self.release_point)
            #     self.image = self.original_image.copy()
            self.drawing = False
            self.update_overlay()




                
            if not self.making_removal and not self.making_additional_selection:
                self.selections_paths.clear()
                self.selections_paths.append(new_path)

            elif self.making_removal:
                print ("is making removal")
                removed_from_merge = False

                #remove polygons if overlapping
                for i, path in enumerate(list(self.selections_paths)):
                    if path.intersects(new_path):
                        subtraction_path = path.subtracted(new_path)

                        self.selections_paths[i] = subtraction_path
                        removed_from_merge = True

                        changed = True
                        while changed:
                            changed = False
                            for k, other_path in enumerate(list(self.selections_paths)):
                                if k == i:
                                    continue
                                if self.selections_paths[i].intersects(other_path):
                                    self.selections_paths[i] = self.selections_paths[i].subtracted(other_path)
                                    print ("section removed")
                                    self.selections_paths.pop(k)
                                    changed = True
                                    break
                    if not removed_from_merge:
                        self.selections_paths.append(new_path)







            elif not self.making_additional_selection:
                self.selections_paths.clear()
                self.selections_paths.append(new_path)

            else:
                merged_any_polygons = False

                #merge polygons if overlapping
                for i, path in enumerate(list(self.selections_paths)):
                    if path.intersects(new_path):
                        merge_path = path.united(new_path)

                        self.selections_paths[i] = merge_path
                        merged_any_polygons = True

                        changed = True
                        while changed:
                            changed = False
                            for l, other_path in enumerate(list(self.selections_paths)):
                                if l == i:
                                    continue
                                if self.selections_paths[i].intersects(other_path):
                                    self.selections_paths[i] = self.selections_paths[i].united(other_path)
                                    self.selections_paths.pop(l)
                                    changed = True
                                    break
                        break
                    if not merged_any_polygons:
                        self.selections_paths.append(new_path)
            self.points = []
            self.update_overlay()
            self.update()



    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.translate(self.parent_window.pan_offset)     
        painter.scale(self.parent_window.scale_factor, self.parent_window.scale_factor)
        # painter.drawPixmap(0, 0, self.image)
        # painter.drawPixmap(0, 0, self.overlay)

        for layer in self.parent_window.texture_layers[0:]:
            painter.drawPixmap(layer.position, layer.pixmap)
        painter.drawPixmap(QtCore.QPoint(0,0), self.parent_window.pen_overlay)
        painter.drawPixmap(0, 0, self.overlay)
        
    def clear_overlay(self):
        self.overlay.fill(QtCore.Qt.transparent)
        self.update()

    def update_overlay(self):
        self.overlay.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(self.overlay)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        self.isDrawn = False
        

        if self.start_point != QtCore.QPoint(0, 0) and self.release_point != QtCore.QPoint(0, 0 and self.drawing):
                    
            painter.setPen(QtGui.QPen(QtCore.Qt.red, 2))
            ellipse = QtCore.QRect(self.start_point, self.release_point)
            painter.drawEllipse(ellipse)
            self.isDrawn = True

        if self.start_point != QtCore.QPoint(0, 0) and self.hover_point != QtCore.QPoint(0, 0) and self.drawing:
            
            if self.drawing_circle and self.drawing:

                self.x_difference = (self.hover_point.x()-self.start_point.x())
                self.y_difference = (self.hover_point.y()-self.start_point.y())
                variance = min(abs(self.x_difference), abs(self.y_difference))

                if self.x_difference <0:
                    directionX = -1
                else:
                    directionX = 1

                if self.y_difference <0:
                    directionY = -1
                else:
                    directionY = 1

                self.hover_point.setY(self.start_point.y() + variance * directionY)
                self.hover_point.setX(self.start_point.x() + variance * directionX)
            

                ellipse = QtCore.QRect(self.start_point, self.hover_point)
                if not self.drawing_in_place:
                    painter.setPen(QtGui.QPen(QtCore.Qt.red, 1, QtCore.Qt.DashLine))
                    painter.drawEllipse(ellipse)
                self.update()

            if self.drawing_in_place and self.drawing:
                self.central_point = self.start_point
                self.inital_point = self.hover_point
                #self.start_point = self.hover_point
                self.x_difference = (self.inital_point.x()-self.central_point.x())
                self.y_difference = (self.inital_point.y()-self.central_point.y())     

                self.temporary_release_point =  QtCore.QPoint(0, 0)

                self.temporary_release_point.setY(self.central_point.y()-self.y_difference)
                self.temporary_release_point.setX(self.central_point.x()-self.x_difference)

                painter.setPen(QtGui.QPen(QtCore.Qt.red, 1, QtCore.Qt.DashLine))
                ellipse = QtCore.QRect(self.inital_point, self.temporary_release_point)
                painter.drawEllipse(ellipse)
                #self.isDrawn = True

                

            elif self.drawing and not self.isDrawn and not self.drawing_circle:
                painter.setPen(QtGui.QPen(QtCore.Qt.red, 1, QtCore.Qt.DashLine))
                ellipse = QtCore.QRect(self.start_point, self.hover_point)
                painter.drawEllipse(ellipse)

        # if self.isDrawn:
        #     #painter.setBrush(QtGui.QColor(255,0,0,50))
        #     #self.commit_rectanlge_to_image(rectangle)
        #     self.selections_paths.append(ellipse)

        if not self.drawing:
            self.clear_overlay()
            
        outline_pen = QtGui.QPen(QtCore.Qt.red, 2)
        fill_brush = QtGui.QBrush(QtGui.QColor(255, 0, 0, 50))

        for path in self.selections_paths:
            all_polys = path.toFillPolygons()
            for poly_f in all_polys:
                poly_q = QtGui.QPolygon([QtCore.QPoint(int(round(p.x())), int(round(p.y()))) for p in poly_f])
                painter.setPen(outline_pen)
                painter.setBrush(QtCore.Qt.NoBrush)
                painter.drawPolygon(poly_q)
                painter.setPen(QtCore.Qt.NoPen)
                painter.setBrush(fill_brush)
                painter.drawPolygon(poly_q)
###############################################################
#                        BUCKET TOOL                          #
###############################################################
class BucketTool(QWidget):
    pass
    # def __init__(self, image_path, parent_window=None):
    #     super().__init__()
    #     self.parent_window = parent_window

    #     self.panning = False
    #     self.last_pan_point = None

    #     self.setFocusPolicy(QtCore.Qt.StrongFocus)
    #     self.setFocus()

    #     self.texture_layers = parent_window.texture_layers

    #     self.in_selection = False

    #     self.point = None
    #     self.drawing = False

    #     self.image = self.parent_window.texture_layers[0].pixmap
    #     if self.image.isNull():
    #         raise ValueError("Failed to load image")
    #     self.original_image = self.image.copy()
    #     self.overlay = QtGui.QPixmap(self.image.size())
    #     self.overlay.fill(QtCore.Qt.transparent)
    #     self.pen_overlay = parent_window.pen_overlay

    #     self.original_image = self.image.copy()
    #     self.overlay = QtGui.QPixmap(self.image.size())
    #     self.overlay.fill(QtCore.Qt.transparent)

    #     self.merged_selection_path = parent_window.merged_selection_path
    #     self.selections_paths = parent_window.selections_paths
    #     self.update_overlay()

    # def get_scaled_point(self, pos):         
    #     scale = self.parent_window.scale_factor
    #     pan = self.parent_window.pan_offset
    #     return QtCore.QPoint(int((pos.x() - pan.x()) / scale), int((pos.y() - pan.y()) / scale))

    # def set_scale_factor(self, scale):
    #     self.parent_window.scale_factor = scale
    #     new_size = self.original_image.size() * scale
    #     self.resize(new_size)
    #     self.update()

    # def paintEvent(self, event):
    #     unreal.log("is painting")
    #     painter = QtGui.QPainter(self)
    #     painter.translate(self.parent_window.pan_offset)     
    #     painter.scale(self.parent_window.scale_factor, self.parent_window.scale_factor)
    #     #painter.drawPixmap(0, 0, self.image)
    #     #painter.drawPixmap(0, 0, self.overlay)

    #     for layer in self.parent_window.texture_layers[0:]:
    #         painter.drawPixmap(layer.position, layer.pixmap)

    #     painter.drawPixmap(0,0, self.overlay)
    #     painter.drawPixmap(0,0, self.pen_overlay) 

    # def mousePressEvent(self, event):
    #     if event.button() == QtCore.Qt.LeftButton:
    #         point = self.get_scaled_point(event.position())
    #         for i, path in enumerate(list(self.selections_paths)):
    #                 if path.contains(point):
    #                     self.in_selection = True
    #                 else:
    #                     self.in_selection = False
    #         if (len(self.selections_paths) > 0 and self.in_selection) or len(self.selections_paths)==0:
    #             if self.panning:
    #                 self.last_pan_point = event.position().toPoint()
    #                 self.setCursor(QtCore.Qt.ClosedHandCursor)
    #                 self.drawing = False
    #             else:
    #                 point = self.get_scaled_point(event.position())
    #                 self.drawing = True
    #                 if self.selections_paths == []:
    #                     self.parent_window.select_all()




    #                 self.commit_line_to_image(QtGui.QPolygon(self.point))
    #                 self.update_overlay()
    #                 self.drawing = False
    #         else:
    #             return
        


        
    # def update_overlay(self):
    #     self.overlay.fill(QtCore.Qt.transparent)
    #     painter = QtGui.QPainter(self.overlay)
    #     painter.setRenderHint(QtGui.QPainter.Antialiasing)
    #     outline_pen = QtGui.QPen(QtCore.Qt.red, 2)
    #     fill_brush = QtGui.QBrush(QtGui.QColor(255, 0, 0, 50))

    #     if self.in_selection or len(self.selections_paths)<1:
    #         if self.point:
    #             pen = QtGui.QPen(QtCore.Qt.black, 3)
    #             painter.setPen(pen)
    #             painter.drawPolyline(QtGui.QPolygon(self.points))
    #             self.commit_line_to_image(QtGui.QPolygon(self.points))

    #     #elif not self.in_selection and len(self.selections_paths)>0:
    #         #self.drawing = False

    #     for path in self.selections_paths:
    #         all_polys = path.toFillPolygons()
    #         for poly_f in all_polys:
    #             poly_q = QtGui.QPolygon([QtCore.QPoint(int(round(p.x())), int(round(p.y()))) for p in poly_f])
    #             painter.setPen(outline_pen)
    #             painter.setBrush(QtCore.Qt.NoBrush)
    #             painter.drawPolygon(poly_q)
    #             painter.setPen(QtCore.Qt.NoPen)
    #             painter.setBrush(fill_brush)
    #             painter.drawPolygon(poly_q)

    #     if self.drawing:
    #         for path in self.selections_paths:
    #             all_polys = path.toFillPolygons()
    #             for poly_f in all_polys:
    #                 poly_q = QtGui.QPolygon([QtCore.QPoint(int(round(p.x())), int(round(p.y()))) for p in poly_f])
    #                 painter.setPen(outline_pen)
    #                 painter.setBrush(QtCore.Qt.NoBrush)
    #                 painter.drawPolygon(poly_q)
    #                 painter.setBrush(outline_pen)
    #                 painter.drawPolygon(poly_q)

    #     self.pen_color = self.parent_window.color
    #     painter.end()
    #     self.update()

    # def clear_overlay(self):
    #     self.pen_overlay.fill(QtCore.Qt.transparent)
    #     self.image = self.original_image.copy()
    #     self.points.clear()
    #     self.update()

    # def commit_line_to_image(self, line):
    #     painter = QtGui.QPainter(self.pen_overlay)
    #     outline_pen = QtGui.QPen(QtCore.Qt.red, 2)


    #     for path in self.selections_paths:
    #         all_polys = path.toFillPolygons()
    #         for poly_f in all_polys:
    #             poly_q = QtGui.QPolygon([QtCore.QPoint(int(round(p.x())), int(round(p.y()))) for p in poly_f])
    #             painter.setPen(outline_pen)
    #             painter.setBrush(QtCore.Qt.NoBrush)
    #             painter.drawPolygon(poly_q)
    #             painter.setBrush(outline_pen)
    #             painter.drawPolygon(poly_q)

    #     painter.setRenderHint(QtGui.QPainter.Antialiasing)
    #     painter.setPen(QtGui.QPen(self.pen_color, 2))
    #     painter.drawPolyline(line)
    #     painter.end()
    #     self.update()

###############################################################
#                     TRANSFORM TOOL                          #
###############################################################
class TransformTool(QWidget):
    def __init__(self,parent_window):
        super().__init__()
        self.parent_window = parent_window

        self.panning = False
        self.last_pan_point = None

        self.dragging_layer = None
        self.drag_start_offset = QtCore.QPoint()

        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setFocus()

        self.texture_layers = parent_window.texture_layers

        self.inSelection = True

        #self.merged_selection_path = parent_window.merged_selection_path

        self.image = self.parent_window.texture_layers[0].pixmap

        self.overlay = QtGui.QPixmap(self.image.size())
        self.overlay.fill(QtCore.Qt.transparent)

        self.dragging_pixmap = QtGui.QPixmap(self.image.size())
        #self.overlay = QtGui.QPixmap()
        #self.overlay.fill(QtCore.Qt.transparent)
        self.scaling = False
        self.rotating = False

        self.update_overlay()

        self.rectangle = None

        self.point = None

    def get_scaled_point(self, pos):
        scale = self.parent_window.scale_factor
        pan = self.parent_window.pan_offset
        return QtCore.QPoint(int((pos.x() - pan.x()) / scale), int((pos.y() - pan.y()) / scale))

    def set_scale_factor(self, scale):
        self.parent_window.scale_factor = scale
        base_size = self.parent_window.texture_layers[0].pixmap.size()
        new_size = base_size * scale
        self.resize(new_size)
        self.update()
    
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and self.inSelection:
            if self.panning:
                self.last_pan_point = event.position().toPoint()
                self.setCursoe(QtCore.Qt.ClosedHandCursor)
            else:
                self.point = self.get_scaled_point(event.position())
                for layer in reversed(self.parent_window.texture_layers):
                    self.rectangle = QtCore.QRect(layer.position, layer.pixmap.size())
                    expanded_rectangle = self.expand_rectangle(self.rectangle, 2)
                    # expanded_rectangle = QtCore.QRect(layer.position, layer.pixmap.size())
                    # expanded_rectangle.setWidth(expanded_rectangle.width()*2)
                    # expanded_rectangle.setHeight(expanded_rectangle.height()*2)
                    self.center_point = self.rectangle.center()

                    if self.rectangle.contains(self.point):

                        if layer == self.parent_window.texture_layers[0]:
                            break #NEW NEW NEW  
                        else:
                            layer.selected = True
                            # if self.dragging_layer != layer:
                            #     self.clear_dragging_layer()
                            self.dragging_layer = layer
                            self.drag_start_offset = self.point - layer.position
                            self.overlay = QtGui.QPixmap(self.dragging_layer.pixmap.size())
                            self.dragging_pixmap = self.dragging_layer.pixmap
                            self.scaling = False
                            self.rotating = False

                            self.update_overlay()
                            break
                    elif expanded_rectangle.contains(self.point):
                        unreal.log ("YOU DID IT YOU DID IT")
                        self.scaling = True
                        self.rotating = False
                    else: #currently set to scaling settings which will need ot be changed once ui and indication is clearer
                        unreal.log ("ROTATION")
                        self.scaling = False
                        self.rotating = True

                            
    def mouseMoveEvent(self,event):
        if self.panning and self.last_pan_point:
            change = event.position().toPoint() - self.last_pan_point
            self.parent_window.pan_offset += change
            self.last_pan_point = event.position().toPoint()
            self.update()
        if self.scaling:
            hover_point = self.get_scaled_point(event.position())

            self.x_hover_difference = (self.center_point.x()-hover_point.x())
            self.y_hover_difference = (self.center_point.y()-hover_point.y())
            hover_variance = max(abs(self.x_hover_difference), abs(self.y_hover_difference))

            self.x_main_difference = (self.center_point.x()-self.point.x())
            self.y_main_difference = (self.center_point.y()-self.point.y())
            main_variance = max(abs(self.x_main_difference), abs(self.y_main_difference))

            self.image_scale_factor = hover_variance/main_variance
            


            height_difference = self.dragging_pixmap.height()*self.image_scale_factor - self.dragging_pixmap.height()
            width_difference =  self.dragging_pixmap.width()*self.image_scale_factor -  self.dragging_pixmap.width()
            
            
            


            base_image = self.dragging_pixmap.toImage()
            convert = base_image.convertToFormat(QImage.Format_ARGB32)
            pillow_image = ImageQt.fromqimage(convert)            
        
            resized_image = pillow_image.resize((int(pillow_image.size[0]*self.image_scale_factor), int(pillow_image.size[1]*self.image_scale_factor)))
            unreal.log(print("image scaled"))


            new_qimage = ImageQt.ImageQt(resized_image).convertToFormat(QImage.Format_ARGB32)
            new_image = QPixmap.fromImage(new_qimage)


            #self.dragging_pixmap = self.dragging_pixmap.scaled(self.dragging_pixmap.width()*self.image_scale_factor,self.dragging_pixmap.height()*self.image_scale_factor)
            self.dragging_pixmap = new_image




            bounds_rectangle = QtCore.QRect(self.dragging_layer.position, self.dragging_pixmap.size())

            new_position = QtCore.QPoint(self.center_point.x() - width_difference/2, self.center_point.y() - height_difference/2)


            new_layer = TextureLayer(self.dragging_pixmap, new_position)

            self.parent_window.texture_layers[(self.parent_window.texture_layers.index(self.dragging_layer))] = new_layer
            self.dragging_layer = self.parent_window.texture_layers[(self.parent_window.texture_layers.index(new_layer))]

            self.update_overlay()
            # for layer in self.parent_window.texture_layers:
            #     if self.dragging_layer == layer:

        elif self.rotating:
            hover_point = self.get_scaled_point(event.position())
            a = self.point.x(), self.point.y()
            b = self.center_point.x(), self.center_point.y()
            c = hover_point.x(), hover_point.y()
            rotation_angle = math.degrees(math.atan2(c[1]-b[1], c[0]-b[0]) - math.atan2(a[1]-b[1], a[0]-b[0]))
            if rotation_angle <0:
                rotation_angle += 360
            
            base_image = self.dragging_pixmap.toImage()
            convert = base_image.convertToFormat(QImage.Format_ARGB32)
            pillow_image = ImageQt.fromqimage(convert)            
        
            rotated_image = pillow_image.rotate(360 - rotation_angle, expand = True)
            unreal.log(print("image rotated"))
            unreal.log(print(rotation_angle))

            new_qimage = ImageQt.ImageQt(rotated_image).convertToFormat(QImage.Format_ARGB32)
            new_image = QPixmap.fromImage(new_qimage)

            
            new_layer = TextureLayer(new_image, self.dragging_layer.position)

            self.parent_window.texture_layers[(self.parent_window.texture_layers.index(self.dragging_layer))] = new_layer
            self.dragging_layer = self.parent_window.texture_layers[(self.parent_window.texture_layers.index(new_layer))]
            self.update_overlay()

                    
        elif self.dragging_layer:
            new_position = self.get_scaled_point(event.position()) - self.drag_start_offset
            self.dragging_layer.position = new_position
            self.update()

    def mouseReleaseEvent(self, event):
        # if self.selections_paths == 0:
        #     pass
        # else:
        if event.button() == QtCore.Qt.LeftButton:
            if self.panning:
                self.panning = False
                self.setCursor(QtCore.Qt.ArrowCursor)
            if self.scaling:
                # print (self.dragging_pixmap.height())
                # height_difference = self.dragging_pixmap.height()*self.image_scale_factor - self.dragging_pixmap.height()
                # width_difference =  self.dragging_pixmap.width()*self.image_scale_factor -  self.dragging_pixmap.width()
                # self.dragging_pixmap = self.dragging_pixmap.scaled(self.dragging_pixmap.width()*self.image_scale_factor,self.dragging_pixmap.height()*self.image_scale_factor)
                # # print (self.dragging_pixmap.height())
                # # transform = QTransform()
                # bounds_rectangle = QtCore.QRect(self.dragging_layer.position, self.dragging_pixmap.size())

                # center = bounds_rectangle.center()
                # #new_position = QtCore.QPoint(self.dragging_layer.position.x() + (width_difference/2), self.dragging_layer.position.y() +(height_difference/2))
                # new_position = QtCore.QPoint(center.x() + width_difference/2, center.y() + height_difference/2)
                # # transform.translate(center.x(), center.y())
                # # transform.scale(self.scale_factor, self.scale_factor)
                # # transform.translate(-center.x(), -center.y())

                # # self.dragging_pixmap = transform.map(self.dragging_pixmap)
                # #print("INDEX: ", (self.parent_window.texture_layers.index(self.dragging_layer)))
                # unreal.log(print("NEW POSITION: ", new_position))

                # new_layer = TextureLayer(self.dragging_pixmap, new_position)

                # self.parent_window.texture_layers[(self.parent_window.texture_layers.index(self.dragging_layer))] = new_layer
                # self.dragging_layer = self.parent_window.texture_layers[(self.parent_window.texture_layers.index(new_layer))]
                print("NEW LAYER DELT WITH")
                self.scaling = False
                self.rectangle = None
                self.point = None
                self.center_point = None
                self.update_overlay()
            # elif self.rotating:


 

            # elif self.dragging_layer:
            #     self.dragging_layer.selected = False
            #     self.dragging_layer = None
            #     self.clear_overlay()
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            self.panning = True
            self.setCursor(QtCore.Qt.OpenHandCursor)

    def keyReleaseEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            self.panning = False
            self.setCursor(QtCore.Qt.ArrowCursor)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.translate(self.parent_window.pan_offset)
        painter.scale(self.parent_window.scale_factor, self.parent_window.scale_factor)

        # painter.drawPixmap(0, 0, self.image)
        # painter.drawPixmap(0, 0, self.overlay)

        for layer in self.parent_window.texture_layers[0:]:
            painter.drawPixmap(layer.position, layer.pixmap)
        painter.drawPixmap(QtCore.QPoint(0,0), self.parent_window.pen_overlay)
        #painter.drawPixmap(0, 0, self.overlay)
        
    def clear_overlay(self):
        self.overlay.fill(QtCore.Qt.transparent)
        self.update()

    def clear_dragging_layer(self):
        self.dragging_pixmap.fill(QtCore.Qt.transparent)
        self.update()

    def expand_rectangle(self,rectangle,scale_factor):
        transform = QTransform()
        center = rectangle.center()
        transform.translate(center.x(), center.y())
        transform.scale(scale_factor, scale_factor)
        transform.translate(-center.x(), -center.y())
        new_rectangle = QPolygon.boundingRect(transform.map(rectangle))
        return new_rectangle

        # self.active_tool_widget.update_overlay()
        # self.tool_panel.radioButtonGroupChanged()

    def update_overlay(self):
        self.overlay.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(self.overlay)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        outline_pen = QtGui.QPen(QtCore.Qt.blue, 5)

        if self.dragging_layer:
            painter = QtGui.QPainter(self.dragging_layer.pixmap)
            painter.setPen(QtGui.QPen(outline_pen))
            rect = QtCore.QRect(0, 0, self.dragging_layer.pixmap.width()-1, self.dragging_layer.pixmap.height()-1)
            painter.drawRect(rect)
            painter.end()


        painter.end()
        self.update()


###############################################################
#                   SELECTION MANAGEMENT                      #
###############################################################
class SelectionManagement():
    pass


def map_points_of_polygon(polygon, n):
    path = QPainterPath()
    path.addPolygon(polygon)
    return [path.pointAtPercent(i/(n-1)) for i in range (n)]


    
def check_if_selections_intersect(previous_polygon, current_polygon):
    # previous_poly_points = map_n_points_of_polygon(previous_polygon, 100)
    # previous_poly_points = map_n_points_of_polygon(current_polygon, 100)

    previous_poly_path = QPainterPath()
    previous_poly_path.addPolygon(previous_polygon)

    current_polygon_path = QPainterPath()
    current_polygon_path.addPolygon(current_polygon)

    if previous_poly_path.intersects(current_polygon_path):
        print ("does intersect")
        #return previous_poly_path, current_polygon_path, True
        return True
    else:
        print ("NO INTERESCTION")
        #return previous_poly_path, current_polygon_path, False
        return False
    
###############################################################
#                      MAIN SCRIPT                            #
###############################################################
assets = unreal.EditorUtilityLibrary.get_selected_assets()
is_first_click_of_selection = True
for tex in assets:
    if isinstance(tex, unreal.Texture):
        if __name__ == "__main__":
            main_png_path = export_texture_to_png(tex)
            win = MainWindow(main_png_path)
            win.show()