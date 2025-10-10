#TODO MAKE LASSO CANCEL IF NOT CLOSED
#TODO MAKE LASSO DELETE EXCESSIVE LINES IF THEY DO NOT MERGE
#TODO MAKE LASSO SEAL EVEN IF OVERLAPPING

#TODO MAKE POLYGONAL TOOL

#TODO MAKE RECTANGLULAR SELECTION

#TODO MAKE ELLIPSUS SELECTION

#TODO MAKE MAGIC WAND
#TODO ADD TOLERANCE FOR WAND

#TODO MAKE COLOUR RANGE
#TODO ADD TOLERANCE FOR COLOUR RANGE

#TODO ADD ABILITY TO ADD MORE LASSO AND MERGE THEM
#TODO ADD ABILITY TO TAKE AWAY LASSO AND MERGE THEM
#TODO CTRL + SHIFT + I TO INVERT SELECTION

#TODO ADD ABILITY TO DELETE PARTS IN SELECTION

#TODO ADD ABILITY TO ZOOM IN/OUT WITH MOUSE WHEEL

#TODO ADD PEN TOOL, ABILITY TO ADD WITHIN SELECTION BOUNDS ON A MASK

#TODO REORGANISE CLASSES ONCE 2 SELECTION TYPES ARE IMPLEMENTED TO EMBDED CLASSES


import os
import PySide6
from PySide6 import QtWidgets, QtGui, QtCore
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
#CreateLassoTool
###############################################################
class SelectionTools():
    def __init__(self):
        self.current_points = []

        pass
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

    class PolygonalTool(QtWidgets.QLabel):
        def __init__(self, image_path):
            super().__init__()
            self.image = QtGui.QPixmap(image_path)
            self.is_first_click_of_selection = True
            self.current_points=[]

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

            self.setWindowTitle("Polygonal Tool")


        def mousePressEvent(self, event):
            if event.button() == QtCore.Qt.LeftButton:
                if self.is_first_click_of_selection == True:
                    self.drawing = True
                    self.initial_point = event.position().toPoint()
                    self.points = [event.position().toPoint()]
                    self.is_first_click_of_selection = False
                    self.update()
                    self.current_point =  event.position().toPoint()
                else:
                    self.current_point =  event.position().toPoint()
                    if (self.current_point.x() - self.initial_point.x()) < 30 and (self.current_point.y() - self.initial_point.y() < 30) and (self.current_point.x() - self.initial_point.x()) > -30 and (self.current_point.y() - self.initial_point.y() > -30):
                        print("THIS HAS OCCURED")
                        self.points.append(self.initial_point)
                        self.drawing = False
                        self.update()

                    else:
                        self.points.append(event.position().toPoint())
                        self.update()

    

        def mouseMoveEvent(self, event):
            if self.drawing:
        #         self.points.append(event.pos())

                self.hovered_point =  event.position().toPoint()

                vector_distance_between_points = math.dist(self.initial_point,self.hovered_point)
                #vector_distance_between_points = ((self.initial_point.x()-self.hovered_point.x()+self.initial_point.y()-self.hovered_point.y())/2)
                for i in range (0, (vector_distance_between_points/10)):
                    self.current_points.append(QtCore.QPoint((self.initial_point.x()+(i*(vector_distance_between_points/10), (self.initial_point.y()+(i*(vector_distance_between_points/10)))))))

                    #self.current_points.append((self.initial_point.x()+(i*(vector_distance_between_points/10))))
                #self.current_points.append(event.pos())
                self.update()

        def mouseReleaseEvent(self, event):
            if event.button() == QtCore.Qt.LeftButton:
        #         #self.drawing = False
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

                if len(self.current_points) > 0:
                    temporary_pen = QtGui.QPen(QtCore.Qt.red, QtGui.Color(255, 0, 0, 150), QtCore.Qt.DashLine)
                    painter.setPen(temporary_pen)
                    line = QtGui.QPolygon(self.current_points)
                    painter.drawPolyline(line(self.current_points))
                    print("Hello hello hello")

                if not self.drawing:
                    print("NOT DRAWING")
                    painter.setBrush(QtGui.QColor(255, 0, 0, 50))  # translucent fill
                    painter.drawPolygon(polygon)
                    self.is_first_click_of_selection = True

# ---- Main execution ----
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