
import os
import unreal

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


import PY_main_window 
from PY_main_window import MainWindow as MainWindow



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
    

    
def main():
    assets = unreal.EditorUtilityLibrary.get_selected_assets()
    is_first_click_of_selection = True
    for tex in assets:
        if isinstance(tex, unreal.Texture):
            # if __name__ == "__main__":
            main_png_path = export_texture_to_png(tex)
            win = MainWindow(main_png_path)
            win.show()


main()