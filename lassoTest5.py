
#TODO ADD PEN TOOL, ABILITY TO ADD WITHIN SELECTION BOUNDS ON A MASK

#TODO MAKE LASSO ACTUALLY SELECET

#TODO MAKE POLYGONAL TOOL WORK

#TODO MAKE RECTANGLULAR SELECTION
#TODO MAKE ELLIPSUS SELECTION SQUARE WITH ALT OR WHATVER
#TODO MAKE RECTANGLULAR SELECTION WORK

#TODO MAKE ELLIPSUS SELECTION
#TODO MAKE ELLIPSUS SELECTION CIRCLE WITH ALT OR WHATVER
#TODO MAKE ELLIPSUS SELECTION WORK

#TODO MAKE MAGIC WAND
#TODO ADD TOLERANCE FOR WAND

#TODO MAKE COLOUR RANGE
#TODO ADD TOLERANCE FOR COLOUR RANGE

#TODO ADD ABILITY TO ADD MORE LASSO AND MERGE THEM
#TODO ADD ABILITY TO TAKE AWAY LASSO AND MERGE THEM
#TODO CTRL + SHIFT + I TO INVERT SELECTION

#TODO ADD ABILITY TO DELETE PARTS IN SELECTION

#TODO ADD ABILITY TO ZOOM IN/OUT WITH MOUSE WHEEL

#TODO REORGANISE CLASSES ONCE 2 SELECTION TYPES ARE IMPLEMENTED TO EMBDED CLASSES


import os
import PySide6
from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtCore import Qt
import unreal
import math

#TODO 
###############################################################
#Creates Temporary PNG for Texture to be Viewed
###############################################################
def export_texture_to_png(texture_asset):
    #ensures selection is a texture
    if not isinstance(texture_asset, unreal.Texture):
        unreal.log_error(f"{texture_asset.get_name()} is not a texture!")
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

is_first_click_of_selection = True

###############################################################
#CreatePenDebugTool
###############################################################
class SelectionTools():
    def __init__(self):
        self.current_points = []

        pass
class PenTool(QtWidgets.QLabel):
    def __init__(self,image_path):
        super().__init__()
        self.image = QtGui.QPixmap(image_path)
        self.isDrawingWithPen = False
        if self.image.isNull():
            unreal.log_error("Failed to load image")
            self.setText("Image failed to load")
            self.setAlignment(QtCore.Qt.AlignCenter)
            return      
        
        self.setPixmap(self.image)
        self.points = []
        self.drawing = False

        self.setFixedSize(self.image.size())
        self.setWindowTitle("Selection Tools")

    # def altPressEvent(self, event):
    #     if event.key() == Qt.Key_Alt:
    #         self.isDrawingWithPen = True
    #         self.update()
            
    # def altReleaseEvent(self,event):
    #     if event.key() == Qt.Key_Alt:
    #         self.isDrawingWithPen = False
    #         self.update()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.drawing = True
            self.points = [event.position().toPoint()]
            self.update()
    
    def mouseMoveEvent(self, event):
        if event.buttons() & QtCore.Qt.LeftButton and self.drawing:
            self.points.append(event.position().toPoint())
            self.update()

    def mouseReleaseEvent(self,event):
        if event.button() == QtCore.Qt.LeftButton:
            self.drawing = False
            self.update()
    
    def paintEvent(self,event):
        painter = QtGui.QPainter(self)
        painter.drawPixmap(0,0,self.image)

        if len(self.points) > 1:
            painter.setPen(QtGui.QPen(QtCore.Qt.black, 3))
            painter.drawPolyline(QtGui.QPolygon(self.points))

        if len(self.points) > 1:
            pen = QtGui.QPen(QtCore.Qt.black, 3)
            painter.setPen(pen)
            polygon = QtGui.QPolygon(self.points)
            painter.drawPolyline(polygon)

###############################################################
#CreateLassoTool
###############################################################
class LassoTool(QtWidgets.QLabel):
    def __init__(self, image_path):
        super().__init__()
        self.image = QtGui.QPixmap(image_path)

        if self.image.isNull():
            unreal.log_error(f"Failed to load image: {image_path}")
            self.setText("Image failed to load")
            self.setAlignment(QtCore.Qt.AlignCenter)
            return

        self.setPixmap(self.image)
        self.points = []
        self.drawing = False

        # Make window match image size
        self.setFixedSize(self.image.size())
        self.setWindowTitle("Lasso Tool")

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.drawing = True
            self.points = [event.position().toPoint()]

            self.update()

    def mouseMoveEvent(self, event):
        if self.drawing:
            self.points.append(event.position().toPoint())
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.drawing = False
            if len(self.points) > 2:
                self.points.append(self.points[0])
            self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.drawPixmap(0, 0, self.image)
        if len(self.points) > 1:
            painter.setPen(QtGui.QPen(QtCore.Qt.red, 2))
            painter.drawPolyline(QtGui.QPolygon(self.points))

        if len(self.points) > 1:
            pen = QtGui.QPen(QtCore.Qt.red, 2)
            painter.setPen(pen)
            polygon = QtGui.QPolygon(self.points)
            painter.drawPolyline(polygon)

            if not self.drawing:
                print("NOT DRAWING")
                painter.setBrush(QtGui.QColor(255, 0, 0, 50))  # translucent fill
                painter.drawPolygon(polygon)
                self.is_first_click_of_selection = True
###############################################################
#CreatePolygonalLassoTool
###############################################################
class PolygonalTool(QtWidgets.QLabel):
    def __init__(self, image_path):
        super().__init__()
        self.image = QtGui.QPixmap(image_path)
        if self.image.isNull():
            self.setText("Image failed to load")
            self.setAlignment(QtCore.Qt.AlignCenter)
            return

        self.setPixmap(self.image)
        self.points = []
        self.hover_point = None
        self.drawing = False
        self.is_first_click = True

        self.setMouseTracking(True)
        self.setFixedSize(self.image.size())
        self.setWindowTitle("Polygonal Tool")

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            point = event.position().toPoint()
            if self.is_first_click:
                # start polygon
                self.points = [point]
                self.drawing = True
                self.is_first_click = False
            else:
                # close polygon if near first point
                if (point - self.points[0]).manhattanLength() < 20:
                    self.points.append(self.points[0])
                    self.drawing = False  # polygon finished
                    self.is_first_click = True
                    print("Polygon closed!")
                else:
                    # add new vertex
                    self.points.append(point)
            self.update()

    def mouseMoveEvent(self, event):
        self.hover_point = event.position().toPoint()
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.drawPixmap(0, 0, self.image)

        if len(self.points) > 1:
            painter.setPen(QtGui.QPen(QtCore.Qt.red, 2))
            polygon = QtGui.QPolygon(self.points)
            painter.drawPolyline(polygon)

        if self.drawing and self.hover_point and self.points:
            painter.setPen(QtGui.QPen(QtCore.Qt.red, 1, QtCore.Qt.DashLine))
            painter.drawLine(self.points[-1], self.hover_point)

        if not self.drawing and len(self.points) > 2:
            painter.setBrush(QtGui.QColor(255, 0, 0, 50))
            polygon = QtGui.QPolygon(self.points)
            painter.drawPolygon(polygon)
    
###############################################################
#MAIN SCRIPT
###############################################################
assets = unreal.EditorUtilityLibrary.get_selected_assets()
is_first_click_of_selection = True
for tex in assets:
    if isinstance(tex, unreal.Texture):
        if __name__ == "__main__":
            png_path = export_texture_to_png(tex)
            app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
            win = PolygonalTool(png_path)
            win.show()
            app.exec()