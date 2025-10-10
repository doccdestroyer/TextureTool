#TODO ADD PEN TOOL, ABILITY TO ADD WITHIN SELECTION BOUNDS ON A MASK

#TODO MAKE LASSO ACTUALLY SELECET

#TODO MAKE POLYGONAL TOOL WORK

#TODO MAKE RECTANGULAR AND SQUARE EXPANSION AROUND A POINT
#TODO MAKE RECTANGLULAR SELECTION WORK

#TODO MAKE ELLIPTICAL AND CIRCULAR EXPANSION AROUND A POINT
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

####drop down menu = ComboBox

import os
import PySide6
from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtWidgets import QPushButton, QWidget
from PySide6.QtCore import Qt
import unreal
import math
###TODO ADJUST IMPORTS TO INCLUDE WHATS ONLY NECESARY
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget, QLineEdit, QLabel, QVBoxLayout, QSlider, QRadioButton, QButtonGroup, QComboBox, QDial


selections = []


###############################################################
#Creates Temporary PNG for Texture to be Viewed
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

is_first_click_of_selection = True

###############################################################
#CreateMainWindow
###############################################################
class CreateWindow(QtWidgets.QWidget):
    def __init__(self, image_path):
        super().__init__()
        self.setWindowTitle("Selection Tools")
        self.image_path = image_path
        self.active_tool_widget = None 

        layout = QVBoxLayout(self)

        self.image_label = QLabel()
        self.image_label.setPixmap(QtGui.QPixmap(self.image_path))
        layout.addWidget(self.image_label)

        self.setFixedSize(self.image_label.pixmap().size())

        self.tool_panel = ToolSectionMenu(parent=self)
        self.tool_panel.show()


###############################################################
#CreateToolSectionWindow
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
        self.pen_tool.setText('Pen Tool')
        self.lasso_tool = QRadioButton()
        self.lasso_tool.setText('Lasso Tool')
        self.rectangle_tool = QRadioButton()
        self.rectangle_tool.setText('Rectangle Tool')
        self.ellipse_tool = QRadioButton()
        self.ellipse_tool.setText('Ellipse Tool')
        self.polygonal_tool = QRadioButton()
        self.polygonal_tool.setText('Polygonal Tool')
        self.radioButtonGroup = QButtonGroup()
        self.radioButtonGroup.addButton(self.pen_tool)
        self.radioButtonGroup.addButton(self.lasso_tool)
        self.radioButtonGroup.addButton(self.rectangle_tool)
        self.radioButtonGroup.addButton(self.ellipse_tool)
        self.radioButtonGroup.addButton(self.polygonal_tool)

        layout.addWidget(self.pen_tool)
        layout.addWidget(self.lasso_tool)
        layout.addWidget(self.rectangle_tool)
        layout.addWidget(self.ellipse_tool)
        layout.addWidget(self.polygonal_tool)

        for btn in [self.pen_tool, self.rectangle_tool, self.ellipse_tool, self.lasso_tool, self.polygonal_tool]:
            self.radioButtonGroup.addButton(btn)
            btn.clicked.connect(self.radioButtonGroupChanged)

        self.setStyleSheet("""
            background-color: #262626;
            color: #ffffff;
            font-family: Consolas;
            font-size: 12px;
        """)
        self.pen_tool.setChecked(True)
        self.radioButtonGroupChanged()


    def radioButtonGroupChanged(self):
        button = self.radioButtonGroup.checkedButton()
        parent_layout = self.parent_window.layout()

        if hasattr(self.parent_window, "active_tool_widget") and self.parent_window.active_tool_widget:
            parent_layout.removeWidget(self.parent_window.active_tool_widget)
            self.parent_window.active_tool_widget.deleteLater()
        else:
            parent_layout.removeWidget(self.parent_window.image_label)
            self.parent_window.image_label.deleteLater()

        self.parent_window.active_tool_widget = None

        if button == self.pen_tool:
            self.parent_window.active_tool_widget = PenTool(self.parent_window.image_path)
        elif button == self.rectangle_tool:
            self.parent_window.active_tool_widget = RectangularTool(self.parent_window.image_path)
        elif button == self.ellipse_tool:
            self.parent_window.active_tool_widget = EllipticalTool(self.parent_window.image_path)
        elif button == self.lasso_tool:
            self.parent_window.active_tool_widget = LassoTool(self.parent_window.image_path)
        elif button == self.polygonal_tool:
            self.parent_window.active_tool_widget = PolygonalTool(self.parent_window.image_path)


        if self.parent_window.active_tool_widget:
            parent_layout.addWidget(self.parent_window.active_tool_widget)
            self.parent_window.active_tool_widget.show()


###############################################################
#                   CreatePenDebugTool
###############################################################
class PenTool(QtWidgets.QLabel):
    def __init__(self,image_path):
        super().__init__()
        self.image = QtGui.QPixmap(image_path)

        if self.image.isNull():
            unreal.log_error("Failed to load image")
            self.setText("Image failed to load")
            self.setAlignment(QtCore.Qt.AlignCenter)
            return      

        self.original_image = self.image.copy()
        self.overlay = QtGui.QPixmap(self.image.size())
        self.overlay.fill(QtCore.Qt.transparent)

        self.isDrawingWithPen = False
        self.points = []
        self.drawing = False
        
        self.setFocusPolicy(QtCore.Qt.StrongFocus) 
        self.setFocus() 


    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            #############TEST
            self.setPixmap(self.overlay)
            print("mouse pressed")
            self.drawing = True
            self.points = [event.position().toPoint()]
            self.update_overlay()

   
    def mouseMoveEvent(self, event):
        if event.buttons() & QtCore.Qt.LeftButton and self.drawing:
            self.points.append(event.position().toPoint())
            self.update_overlay()
        else:
            self.update()

    def mouseReleaseEvent(self,event):
        if event.button() == QtCore.Qt.LeftButton:
            self.drawing = False
            self.update_overlay()

    def keyPressEvent(self,event):
        if event.key() == QtCore.Qt.Key_Delete:
            self.clear_overlay()
            print ("delete pressed and cleared")

    def paintEvent(self,event):
        painter = QtGui.QPainter(self)
        painter.drawPixmap(0,0,self.image)
        painter.drawPixmap(0,0,self.overlay)

    def clear_overlay(self):
            self.image = self.original_image.copy()
            self.overlay.fill(QtCore.Qt.transparent)
            self.update()

    def update_overlay(self):
        self.overlay.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(self.overlay)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        if len(self.points) > 1:
            pen = QtGui.QPen(QtCore.Qt.black, 3)
            painter.setPen(pen)
            line = QtGui.QPolygon(self.points)
            painter.drawPolyline(line)
            self.commit_line_to_image(QtGui.QPolygon(self.points))
        painter.end()
        self.update()


    def commit_line_to_image(self, line):
        painter = QtGui.QPainter(self.image)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        #painter.setBrush(QtGui.QColor(255, 0, 0, 50))
        painter.setPen(QtGui.QPen(QtCore.Qt.black, 2))
        painter.drawPolyline(line)
        painter.end()
        self.update()

###############################################################
#                    CreateLassoTool
###############################################################
class LassoTool(QtWidgets.QLabel):
    def __init__(self, image_path):
        print("lasso initializing")
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
        self.making_additional_selection = False


        self.original_image = self.image.copy()
        self.overlay = QtGui.QPixmap(self.image.size())
        self.overlay.fill(QtCore.Qt.transparent)

        self.setFixedSize(self.image.size())
        self.setWindowTitle("Lasso Tool")

        self.merged_selection_path = QPainterPath()
        self.selections_paths = []

    def mousePressEvent(self, event):
            if event.button() == QtCore.Qt.LeftButton:
                self.points = []
                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    self.making_additional_selection = True
                else:
                    self.making_additional_selection = False
                    self.selections_paths = []
                    selections.clear()
                    self.merged_selection_path = QPainterPath()
                    self.image = self.original_image.copy()
                    self.clear_overlay()
                self.drawing = True
                self.points = [event.position().toPoint()]
                self.update_overlay()

    def mouseMoveEvent(self, event):
        if self.drawing:
            self.points.append(event.position().toPoint())
            self.update_overlay()
        self.update()


    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.drawing = False
            if len(self.points) > 2:
                self.points.append(self.points[0])
                new_polygon_f = QPolygonF(QPolygon(self.points))
                new_path = QPainterPath()
                new_path.addPolygon(new_polygon_f)

            if not self.making_additional_selection:
                self.selections_paths = [new_path]
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
        painter.drawPixmap(0, 0, self.image)
        painter.drawPixmap(0, 0, self.overlay)


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

        if len(self.points) > 1:
            painter.setPen(outline_pen)
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.drawPolyline(QtGui.QPolygon(self.points))


        painter.end()
        self.update()

    def commit_polygon_to_image(self,polygon):
        painter = QtGui.QPainter(self.image)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setBrush(QtGui.QColor(255, 0, 0, 50))
        painter.setPen(QtGui.QPen(QtCore.Qt.red, 2))
        painter.drawPolygon(polygon)
        painter.end()
        self.update()

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

        self.original_image = self.image.copy()

        self.overlay = QtGui.QPixmap(self.image.size())
        self.overlay.fill(QtCore.Qt.transparent)

        self.setPixmap(self.image)
        self.points = []
        self.hover_point = None
        self.drawing = False
        self.is_first_click = True
        self.making_additional_selection = False
        self.setMouseTracking(True)
        self.setFixedSize(self.image.size())
        self.setWindowTitle("Polygonal Tool")

        self.merged_selection_path = QPainterPath()
        self.selections_paths = []


    def mousePressEvent(self, event):
        global selections
        if event.button() == QtCore.Qt.LeftButton:
            point = event.position().toPoint()
            if self.is_first_click:
                self.points = [point]
                self.drawing = True
                self.is_first_click = False
                if event.modifiers() & QtCore.Qt.ShiftModifier:
                    self.making_additional_selection = True
                else:
                    self.making_additional_selection = False
                    self.selections_paths = []
                    selections.clear()
                    self.merged_selection_path = QPainterPath()
                    self.image = self.original_image.copy()
                    self.clear_overlay()
                    self.update()




            else: #MouseReleaseEvent Equivalent
                if (point - self.points[0]).manhattanLength() < 20:
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

                    if not self.making_additional_selection:
                        self.selections_paths = [new_path]
                    else:
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


                    #self.commit_polygon_to_image(QtGui.QPolygon(self.points))
                    self.clear_overlay()
                else:
                    self.points.append(point)



                
            self.update_overlay()

    def mouseMoveEvent(self, event):
        self.hover_point = event.position().toPoint()
        if self.drawing:
            self.update_overlay()
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.drawPixmap(0, 0, self.image)   
        painter.drawPixmap(0, 0, self.overlay)
    ###HERE NEEDS TO BE REMOVED
    def clear_overlay(self):
        self.overlay.fill(QtCore.Qt.transparent)
        self.update()

    def update_overlay(self):
        self.overlay.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(self.overlay)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # for selection in selections:
        #     painter.setBrush(QtGui.QColor(255, 0, 0, 50))
        #     painter.setPen(QtGui.QPen(QtCore.Qt.red, 2))
        #     painter.drawPolygon(selection)
        #     painter.drawPolyline(selection)

        #COPY AND PASTED FROM LASSO

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


        # #add new polygon drawn
        # if len(self.points) > 1:
        #     painter.setPen(QtGui.QPen(QtCore.Qt.red, 2))
        #     polygon = QtGui.QPolygon(self.points)
        #     painter.drawPolyline(polygon)

        if len(self.points) > 1:
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
#RECTANGLE TOOL
###############################################################
class RectangularTool(QtWidgets.QLabel):
    def __init__(self, image_path):
        super().__init__()
        self.image = QtGui.QPixmap(image_path)
        self.points = []
        if self.image.isNull():
            unreal.log_error(f"Failed to load image.")
            self.setText("Image failed to load")
            self.setAlignment(QtCore.Qt.AlignCenter)
            return
        
        self.overlay = QtGui.QPixmap(self.image.size())
        self.overlay.fill(QtCore.Qt.transparent)
        self.original_image = self.image.copy()

        self.release_point = QtCore.QPoint(0, 0)
        self.start_point = QtCore.QPoint(0, 0)
        self.hover_point = QtCore.QPoint(0, 0)
        self.setMouseTracking(True)
        self.setPixmap(self.image)
        self.drawing = False
        self.drawing_square = False
        self.drawing_in_place = False

        self.making_additional_selection = False

        self.setFixedSize(self.image.size())
        self.setWindowTitle("Rectangle Tool")



    def mousePressEvent(self,event):
        if event.button() == QtCore.Qt.LeftButton:
            if event.modifiers() & QtCore.Qt.ShiftModifier:
                self.making_additional_selection = True
            else:
                self.making_additional_selection = False
                selections.clear()
                self.image = self.original_image.copy()
                self.clear_overlay()
                #self.update()
            self.release_point = QtCore.QPoint(0, 0)
            self.start_point = QtCore.QPoint(0, 0)
            self.drawing = True
            self.start_point = event.position().toPoint()
            self.update_overlay()
            self.update()

    def mouseMoveEvent(self, event):
        if self.drawing:
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.drawing_square = True
            else:
                self.drawing_square = False

            if event.modifiers() & Qt.KeyboardModifier.AltModifier:
                self.drawing_in_place = True
            else:
                self.drawing_in_place = False

            self.hover_point = event.position().toPoint()
            self.update_overlay()

            self.update()

    def mouseReleaseEvent(self,event):
        if event.button() == QtCore.Qt.LeftButton:
            if self.drawing:
                self.release_point = event.position().toPoint()

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

            else:
                #### add to else of next one???? FIX FIX FIX
                self.release_point = event.position().toPoint()
                self.drawing = False
                self.update()

                

            if self.drawing_in_place:
                self.drawing_in_place

                print ("Drawing self in place")

                self.central_point = self.start_point
                self.start_point = self.hover_point

                self.x_difference = (self.hover_point.x()-self.central_point.x())
                self.y_difference = (self.hover_point.y()-self.central_point.y())
                #self.release_point = -1 * self.hover_point
                self.release_point.setY(self.central_point.y()-self.y_difference)
                self.release_point.setX(self.central_point.x()-self.x_difference)

            else:
                self.release_point = event.position().toPoint()
                self.drawing = False
                self.update()



            
        if self.making_additional_selection:
            selections.append((QtCore.QRect(self.start_point, self.release_point)))
        else:
            selections.clear()
            self.selection = QtCore.QRect(self.start_point, self.release_point)
            self.image = self.original_image.copy()
        self.drawing = False
        self.update_overlay()


    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.drawPixmap(0,0, self.image)
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
            rectangle = QtCore.QRect(self.start_point, self.release_point)
            painter.drawRect(rectangle)
            self.isDrawn = True

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
            

                painter.setPen(QtGui.QPen(QtCore.Qt.red, 1, QtCore.Qt.DashLine))
                rectangle = QtCore.QRect(self.start_point, self.hover_point)
                painter.drawRect(rectangle)

            # if self.drawing_in_place and self.drawing:
            #     self.central_point = self.start_point
            #     self.start_point = self.hover_point

            #     self.x_difference = (self.hover_point.x()-self.central_point.x())
            #     self.y_difference = (self.hover_point.y()-self.central_point.y())
            #     #self.release_point = -1 * self.hover_point
            #     self.release_point.setY(self.central_point.y()-self.y_difference)
            #     self.release_point.setX(self.central_point.x()-self.x_difference)

                

            # painter.setPen(QtGui.QPen(QtCore.Qt.red, 1, QtCore.Qt.DashLine))
            # rectangle = QtCore.QRect(self.start_point, self.release_point)
            # painter.drawRect(rectangle)

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

            elif self.drawing:
                painter.setPen(QtGui.QPen(QtCore.Qt.red, 1, QtCore.Qt.DashLine))
                rectangle = QtCore.QRect(self.start_point, self.hover_point)
                painter.drawRect(rectangle)
        


        if self.isDrawn:
            painter.setBrush(QtGui.QColor(255,0,0,50))
            self.commit_rectanlge_to_image(rectangle)
            
        if len(selections) > 0:
            for selection in selections:
                painter.drawRect(selection)
                painter.drawPolyline(selection)
            if not self.drawing:
                painter.drawRect(rectangle)
                self.is_first_click_of_selection = True

    def commit_rectanlge_to_image(self,rectangle):
        painter = QtGui.QPainter(self.image)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setBrush(QtGui.QColor(255, 0, 0, 50))
        painter.setPen(QtGui.QPen(QtCore.Qt.red, 2))
        painter.drawRect(rectangle)
        painter.end()
        self.update()
###############################################################
#                       ELLIPSE TOOL                          #
###############################################################
class EllipticalTool(QtWidgets.QLabel):
    def __init__(self, image_path):
        super().__init__()
        self.image = QtGui.QPixmap(image_path)
        self.points = []
        if self.image.isNull():
            unreal.log_error(f"Failed to load image.")
            self.setText("Image failed to load")
            self.setAlignment(QtCore.Qt.AlignCenter)
            return
        
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

        self.setFixedSize(self.image.size())
        self.setWindowTitle("Elliptical Tool")

    def mousePressEvent(self,event):
        if event.button() == QtCore.Qt.LeftButton:
            if event.modifiers() & QtCore.Qt.ShiftModifier:
                self.making_additional_selection = True
            else:
                self.making_additional_selection = False
                selections.clear()
                self.image = self.original_image.copy()
                self.clear_overlay()
                #self.update()
            self.release_point = QtCore.QPoint(0, 0)
            self.start_point = QtCore.QPoint(0, 0)
            self.drawing = True
            self.start_point = event.position().toPoint()
            self.update_overlay()
            self.update()

    def mouseMoveEvent(self, event):
        if self.drawing:
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.drawing_circle = True
            else:
                self.drawing_circle = False
            if event.modifiers() & Qt.KeyboardModifier.AltModifier:
                self.drawing_in_place = True
            else:
                self.drawing_in_place = False
            self.hover_point = event.position().toPoint()
            self.update_overlay()

    def mouseReleaseEvent(self,event):
        if event.button() == QtCore.Qt.LeftButton:
            if self.drawing:
                self.release_point = event.position().toPoint()
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

            else:
                self.release_point = event.position().toPoint()
                self.drawing = False
                self.update()

            if self.drawing_in_place:
                self.drawing_in_place

                print ("Drawing self in place")

                self.central_point = self.start_point
                self.start_point = self.hover_point

                self.x_difference = (self.hover_point.x()-self.central_point.x())
                self.y_difference = (self.hover_point.y()-self.central_point.y())
                #self.release_point = -1 * self.hover_point
                self.release_point.setY(self.central_point.y()-self.y_difference)
                self.release_point.setX(self.central_point.x()-self.x_difference)

            else:
                self.release_point = event.position().toPoint()
                self.drawing = False
                self.update()


        if self.making_additional_selection:
            selections.append((QtCore.QRect(self.start_point, self.release_point)))
        else:
            selections.clear()
            self.selection = QtCore.QRect(self.start_point, self.release_point)
            self.image = self.original_image.copy()
        self.drawing = False
        self.update_overlay()


    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.drawPixmap(0,0, self.image)


        painter.drawPixmap(0, 0, self.overlay)


    def clear_overlay(self):
        self.overlay.fill(QtCore.Qt.transparent)
        self.update()

    def update_overlay(self):
        print ("is updating overlay")
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

                if not self.drawing_in_place:
                    painter.setPen(QtGui.QPen(QtCore.Qt.red, 1, QtCore.Qt.DashLine))
                    ellipse = QtCore.QRect(self.start_point, self.hover_point)
                    painter.drawEllipse(ellipse)



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

            elif self.drawing:
                painter.setPen(QtGui.QPen(QtCore.Qt.red, 1, QtCore.Qt.DashLine))
                ellipse = QtCore.QRect(self.start_point, self.hover_point)
                painter.drawEllipse(ellipse)
        





        if self.isDrawn:
            painter.setBrush(QtGui.QColor(255,0,0,50))
            ellipse = QtCore.QRect(self.start_point, self.release_point)
            #painter.drawRect(ellipse)
            self.commit_ellipse_to_image(ellipse)
            
        if len(selections) > 0:
            for selection in selections:
                painter.drawEllipse(selection)
            if not self.drawing:
                painter.drawEllipse(ellipse)
                self.is_first_click_of_selection = True

    def commit_ellipse_to_image(self,ellipse):
        painter = QtGui.QPainter(self.image)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setBrush(QtGui.QColor(255, 0, 0, 50))
        painter.setPen(QtGui.QPen(QtCore.Qt.red, 2))
        painter.drawEllipse(ellipse)
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
            png_path = export_texture_to_png(tex)
            app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
            win = CreateWindow(png_path)
            win.show()
            app.exec()