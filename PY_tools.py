

import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__)))
import PySide6
from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtWidgets import QPushButton, QWidget, QApplication, QMainWindow, QPushButton, QWidget, QLineEdit, QLabel, QVBoxLayout, QHBoxLayout, QSlider, QRadioButton, QButtonGroup, QComboBox, QDial, QMenu, QMenuBar, QColorDialog, QDockWidget, QListWidget, QMessageBox
from PySide6.QtCore import Qt, Signal
import unreal
import math
###TODO ADJUST IMPORTS TO INCLUDE WHATS ONLY NECESARY
#from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget, QLineEdit, QLabel, QVBoxLayout, QHBoxLayout, QSlider, QRadioButton, QButtonGroup, QComboBox, QDial, QMenu, QMenuBar, QColorDialog
from PySide6.QtGui import QPainterPath,  QPolygon, QPolygonF, QAction, QImage, QColor, QPixmap, QAction, QTransform, QIcon

import PIL 
from PIL import Image, ImageEnhance, ImageOps, ImageQt, ImageFilter

###############################################################
#                     TEXTURE LAYER                           # 
###############################################################
class TextureLayer:
    def __init__(self, pixmap: QtGui.QPixmap, position: QtCore.QPoint = QtCore.QPoint(0, 0)):
        self.pixmap = pixmap
        self.position = position
        self.selected = False
###############################################################
#                        MOVETOOL                             # 
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

        self.dragging_layer = self.parent_window.selected_layer
        self.translucent_dragging_layer = self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index]
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
                self.setCursor(QtCore.Qt.ClosedHandCursor)
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
                            index = self.parent_window.texture_layers.index(self.dragging_layer)

                            self.parent_window.selected_layer = self.texture_layers[index]
                            self.parent_window.selected_layer_index = index
                            self.translucent_dragging_layer = self.parent_window.translucent_texture_layers[index]


                            item = self.parent_window.layers.item(self.parent_window.selected_layer_index)
                            self.parent_window.layers.setCurrentItem(item)

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
            self.translucent_dragging_layer.position = new_position
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            if self.panning:
                self.panning = False
                self.setCursor(QtCore.Qt.ArrowCursor)
            if self.dragging_layer:
                self.dragging_layer.selected = False
                self.dragging_layer = None
                self.translucent_dragging_layer = None



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

        for layer in self.parent_window.translucent_texture_layers[0:]:
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

        self.image = self.parent_window.selected_layer.pixmap
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

        QtGui.QShortcut(QtGui.QKeySequence("["), self, activated=self.decrease_pen)
        QtGui.QShortcut(QtGui.QKeySequence("]"), self, activated=self.increase_pen)
        QtGui.QShortcut(QtGui.QKeySequence("Space"), self, activated=self.start_panning)

        self.setFocus()
        self.resize(self.image.size()) 

        self.merged_selection_path = parent_window.merged_selection_path
        self.selections_paths = parent_window.selections_paths
        self.update_overlay()
        self.setMouseTracking(True)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.painter_point = QtCore.QPoint(0,0)

#HERE HERE HERE HERE LAYERS


    #     if hasattr(self.parent_window, "Layers"):
    #         self.parent_window.layout.removeWidget(parent_window.layers)
    #         # self.parent_window.layers.deleteLater()

    #     dock = QDockWidget("Layers", self)
    #     parent_window.layers = QListWidget(dock)

    # ####needs to be initalised with a tool and needs to update when the widget is cchanged w radio button
    #     i = 0
    #     for layer in parent_window.texture_layers:
    #         if i == 0:
    #             parent_window.layers.addItem("Base Layer")
    #         else:
    #             parent_window.layers.addItem("Layer "+ str(i))
    #         i+=1

    #     # self.layers.addItems((
    #     #     "Layer 2",
    #     #     "Layer 1",
    #     #     "Base Layer"))
    #     parent_window.layers.itemClicked.connect(parent_window.change_layer)

    #     dock.setWidget(parent_window.layers)
    #     parent_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
    def start_panning(self):
        self.panning = True

    # def get_scaled_point(self, pos):         
    #     scale = self.parent_window.scale_factor
    #     pan = self.parent_window.pan_offset
    #     return QtCore.QPoint(int((pos.x() - pan.x()) / scale), int((pos.y() - pan.y()) / scale))

    def get_scaled_point(self, pos):
        scale = self.parent_window.scale_factor
        pan = self.parent_window.pan_offset
        return QtCore.QPoint(int((pos.x() - pan.x()) / scale), int((pos.y() - pan.y()) / scale))
    
    def get_scaled_moved_point(self,pos):  

        scale = self.parent_window.scale_factor
        pan = self.parent_window.pan_offset

        intial_point = QtCore.QPoint(int((pos.x() - pan.x()) / scale), int((pos.y() - pan.y()) / scale))
        base_position = self.parent_window.base_layer.position
        layer_position = self.parent_window.selected_layer.position

        layer_offset = base_position - layer_position
        new_point = intial_point + layer_offset

        return QtCore.QPoint(int((pos.x() - pan.x()) / scale) + layer_offset.x(), int((pos.y() - pan.y()) / scale) + layer_offset.y())
    
    def set_scale_factor(self, scale):
        self.parent_window.scale_factor = scale
        base_size = self.parent_window.texture_layers[0].pixmap.size()
        new_size = base_size * scale
        self.resize(new_size)
        self.update()
    
    def keyPressEvent(self, event):
        unreal.log(event.key())

        if event.key() == QtCore.Qt.Key_Space:
            self.panning = True
            self.setCursor(QtCore.Qt.OpenHandCursor)
        if event.key() == QtCore.Qt.Key_Delete:
            self.clear_overlay()
            self.update_overlay()

    def decrease_pen(self):
        self.parent_window.pen_size -= 5
        if self.parent_window.pen_size < 2:
            self.parent_window.pen_size = 2

    def increase_pen(self):
        self.parent_window.pen_size += 5
        if self.parent_window.pen_size > 750:
            self.parent_window.pen_size = 750

    def keyReleaseEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            self.panning = False
            self.setCursor(QtCore.Qt.CrossCursor)
        
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.translate(self.parent_window.pan_offset)     
        painter.scale(self.parent_window.scale_factor, self.parent_window.scale_factor)
        #painter.drawPixmap(0, 0, self.image)
        #painter.drawPixmap(0, 0, self.overlay)

        for layer in self.parent_window.translucent_texture_layers[0:]:
            painter.drawPixmap(layer.position, layer.pixmap)

        painter.drawPixmap(0,0, self.overlay)

        white_pen = QtGui.QPen(QtCore.Qt.white)
        black_pen = QtGui.QPen(QtCore.Qt.black)


        painter.setPen(black_pen)
        painter.drawEllipse(self.painter_point, (-self.parent_window.pen_size/1.95),(self.parent_window.pen_size/1.95))
        painter.drawEllipse(self.painter_point, (-self.parent_window.pen_size/2.05),(self.parent_window.pen_size/2.05))
        painter.setPen(white_pen)
        painter.drawEllipse(self.painter_point, (-self.parent_window.pen_size/2),(self.parent_window.pen_size/2))



    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            point = self.get_scaled_moved_point(event.position())
            # point = self.get_scaled_point(event.position())
            for i, path in enumerate(list(self.selections_paths)):
                    if path.contains(point):
                        self.in_selection = True
                    else:
                        if self.in_selection == True:
                            pass
                        else:
                            self.in_selection = False

            if (len(self.selections_paths) > 0 and self.in_selection) or len(self.selections_paths)==0:
                if self.panning:
                    self.last_pan_point = event.position().toPoint()
                    self.setCursor(QtCore.Qt.ClosedHandCursor)
                else:
                    point = self.get_scaled_moved_point(event.position())
                    self.drawing = True
                    self.points = [point]
                    self.update_overlay()
            else:
                return

    def mouseMoveEvent(self, event):
        if self.drawing and not self.panning:
            point = self.get_scaled_moved_point(event.position())
            # self.points.append(point)
            # self.update_overlay()

            if len(self.selections_paths) > 0:
                for i, path in enumerate(list(self.selections_paths)):
                    if path.contains(point):
                        self.in_selection = True
                    else:
                        if self.in_selection == True:
                            pass
                        else:
                            self.in_selection = False

                if self.in_selection:
                    self.points.append(point)

                    self.update_overlay()
                else:
                    self.commit_line_to_image(QtGui.QPolygon(self.points))
                    self.points.clear()
                    self.update_overlay()
                self.in_selection = False
            else:
                self.points.append(point)
                self.update_overlay()

        elif self.panning and self.last_pan_point:
            change = event.position().toPoint() - self.last_pan_point 
            self.parent_window.pan_offset += change                    
            self.last_pan_point = event.position().toPoint()
            self.update()


        self.painter_point = self.get_scaled_point(event.position())

        self.update()
            


    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            if self.drawing:
                self.drawing = False
                self.update_overlay()

            if self.panning:
                self.panning = False
                self.setCursor(QtCore.Qt.CrossCursor)
        self.in_selection = False
        self.update_overlay()

        item = self.parent_window.layers.item(self.parent_window.selected_layer_index)
        self.parent_window.change_layer(item)
        
    def update_overlay(self):
        self.overlay.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap)
        drawing_pen = QtGui.QPen(self.pen_color, self.parent_window.pen_size)
        drawing_pen.setCapStyle(Qt.RoundCap)

        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        outline_pen = QtGui.QPen(QtCore.Qt.red, 2)
        fill_brush = QtGui.QBrush(QtGui.QColor(255, 0, 0, 50))

        if self.in_selection or len(self.selections_paths)<1:
            if len(self.points) > 1:
                #pen = QtGui.QPen(QtCore.Qt.black, 3)
                painter.setPen(drawing_pen)
                painter.drawPolyline(QtGui.QPolygon(self.points))
                self.commit_line_to_image(QtGui.QPolygon(self.points))
                if not self.drawing:
                    self.points.clear()
        #elif not self.in_selection and len(self.selections_paths)>0:
            #self.drawing = False
        painter = QtGui.QPainter(self.overlay)
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
        #painter = QtGui.QPainter(self.pen_overlay)
        painter = QtGui.QPainter(self.parent_window.selected_layer.pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        drawing_pen = QtGui.QPen(self.pen_color, self.parent_window.pen_size)
        drawing_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(drawing_pen)
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
        if event.key() == 16777216:
            self.parent_window.clear_selections()
            self.drawing = False

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
                                        self.selections_paths.pop(k)
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

        for layer in self.parent_window.translucent_texture_layers[0:]:
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
                    self.update_overlay()
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
        if event.key() == 16777216:
            self.parent_window.clear_selections()
            self.drawing = False
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
                    if (point - self.points[0]).manhattanLength() < (20):
                        isComplete = True
                        self.points.append(self.points[0])
                        self.drawing = False 
                        self.is_first_click = True
                        if self.making_additional_selection:
                            selections.append(QtGui.QPolygon(self.points))
                        else:
                            selections = [QtGui.QPolygon(self.points)]


                        
                        new_polygon = QPolygonF(QPolygon(self.points))

                        polygon_path = QtGui.QPainterPath()
                        polygon_path.addPolygon(new_polygon)
                        new_polygon = polygon_path.toFillPolygon()

                        new_polygon_f = QtGui.QPolygonF(self.map_points_of_polygon(new_polygon, 100))
                        new_path = QPainterPath()
                        new_path.addPolygon(new_polygon_f)

                        unreal.log(print(new_path))

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

        for layer in self.parent_window.translucent_texture_layers[0:]:
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
            
    def map_points_of_polygon(self, polygon, n):
        path = QPainterPath()
        path.addPolygon(polygon)
        return [path.pointAtPercent(i/(n-1)) for i in range (n)]

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
        if event.key() == 16777216:
            self.parent_window.clear_selections()
            self.drawing = False
            self.isDrawn = False

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

        for layer in self.parent_window.translucent_texture_layers[0:]:
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
        if event.key() == 16777216:
            self.parent_window.clear_selections()
            self.drawing = False
            self.isDrawn = False

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

            new_polygon_f = QtGui.QPolygonF(self.map_points_of_polygon(ellipse_polygon, 100))
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

        for layer in self.parent_window.translucent_texture_layers[0:]:
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

    def map_points_of_polygon(self, polygon, n):
        path = QPainterPath()
        path.addPolygon(polygon)
        return [path.pointAtPercent(i/(n-1)) for i in range (n)]
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


        self.drag_start_offset = QtCore.QPoint()

        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setFocus()

        self.texture_layers = parent_window.texture_layers

        self.inSelection = True

        #self.merged_selection_path = parent_window.merged_selection_path

        self.image = self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap

        self.overlay = QtGui.QPixmap(self.image.size())
        self.overlay.fill(QtCore.Qt.transparent)

        self.selected_pixmap = QtGui.QPixmap(self.image.size())
        #self.overlay = QtGui.QPixmap()
        #self.overlay.fill(QtCore.Qt.transparent)
        self.scaling = False
        self.rotating = False

        self.update_overlay()

        self.rectangle = None

        self.point = None
        self.rotation_angle = 0

        self.OGHEIGHT = None
        self.OGWIDTH = None

        self.topLeft = None


        self.rectangle = QtCore.QRect(self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].position, self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap.size())
        self.center_point = self.rectangle.center()
        self.paint_center_point = self.center_point

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
        if self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index] == self.parent_window.texture_layers[0]:
            pass
        else:
            if event.button() == QtCore.Qt.LeftButton and self.inSelection:
                if self.panning:
                    self.last_pan_point = event.position().toPoint()
                    self.setCursor(QtCore.Qt.ClosedHandCursor)
                else:
                    self.point = self.get_scaled_point(event.position())
                    self.rectangle = QtCore.QRect(self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].position, self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap.size())
                    
                    self.topLeft = self.rectangle.topLeft()

                    expanded_rectangle = self.expand_rectangle(self.rectangle, 1.2)

                    self.center_point = self.rectangle.center()


                    half_pix_height = self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap.height() * 0.5
                    half_pix_width = self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap.width() * 0.5
                    
                    #self.center_point = QtCore.QPoint(self.topLeft.x() + half_pix_width, self.topLeft.y() + half_pix_height)

                    #self.center_point = (self.rectangle.height()/2 , self.rectangle.width()/2)
                    unreal.log(print(self.center_point))
                    print(self.center_point)

                    self.selected_pixmap = self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap
                    self.og_pixmap = self.parent_window.selected_layer.pixmap

                    if self.rectangle.contains(self.point):

                       

        
                            # self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index] = self.texture_layers[index]
                            # self.parent_window.selected_layer_index = index


                            # item = self.parent_window.layers.item(self.parent_window.selected_layer_index)
                            # self.parent_window.layers.setCurrentItem(item)
                            self.drag_start_offset = self.point - self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].position

                            #############

                            #self.overlay = QtGui.QPixmap(self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap.size())
                            self.scaling = False
                            self.rotating = False



                            self.update_overlay()
                    elif expanded_rectangle.contains(self.point):
                        unreal.log ("YOU DID IT YOU DID IT")
                        self.scaling = True
                        self.rotating = False

                        base_image = self.selected_pixmap.toImage()
                        convert = base_image.convertToFormat(QImage.Format_ARGB32)
                        self.pillow_image = ImageQt.fromqimage(convert)  




                        base_image = self.og_pixmap.toImage()
                        convert = base_image.convertToFormat(QImage.Format_ARGB32)
                        self.opaque_pillow_image = ImageQt.fromqimage(convert)   




                        self.rectangle = QtCore.QRect(self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].position, self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap.size())
                        self.center_point_of_scaling = QtCore.QPoint(self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].position.x(),self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].position.y())
                        self.original_dragging_layer_data = self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index]

                    else: #currently set to scaling settings which will need ot be changed once ui and indication is clearer
                        unreal.log ("ROTATION")


                        self.scaling = False
                        self.rotating = True
                        #self.center_point_of_rotating = QtCore.QPoint(self.dragging_layer.position.x(),self.dragging_layer.position.y())




                        rectangle = QtCore.QRect(self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].position, self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap.size())
                        self.topLeft = rectangle.topLeft()
                        self.center_point = QtCore.QPoint(self.topLeft.x() + half_pix_width, self.topLeft.y() + half_pix_height)
                        #self.paint_center_point = self.center_point

                        base_image = self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap.toImage()
                        convert = base_image.convertToFormat(QImage.Format_ARGB32)
                        self.pillow_image = ImageQt.fromqimage(convert) 


                        #################################
                        base_image = self.og_pixmap.toImage()
                        convert = base_image.convertToFormat(QImage.Format_ARGB32)
                        self.opaque_pillow_image = ImageQt.fromqimage(convert)  
                        #################################   


                        self.OGHEIGHT = self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap.height()
                        self.OGWIDTH = self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap.width()


                        if self.parent_window.never_rotated == True:
                            self.pillow_image = self.pillow_image.rotate(45, expand = True)
                            self.pillow_image = self.pillow_image.rotate(0, expand = True)

                            #################################   
                            self.opaque_pillow_image = self.opaque_pillow_image.rotate(45, expand = True)
                            self.opaque_pillow_image = self.opaque_pillow_image.rotate(0, expand = True)
                            #################################   


                            self.parent_window.never_rotated = False
                            print("NEVER ROTATED SET TO FALSE BECAUSE IT WAS TRUE, IMAGE EXPANDED TWICE")
                        # base_image = self.dragging_pixmap.toImage()
                        # convert = base_image.convertToFormat(QImage.Format_ARGB32)
                        # self.pillow_image = ImageQt.fromqimage(convert) 
                    #self.overlay = QtGui.QPixmap(self.dragging_pixmap.size())
                    self.update()
                            
    def mouseMoveEvent(self,event): 
        if self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index] == self.parent_window.texture_layers[0]:
            pass
        else:
            if self.panning and self.last_pan_point:
                change = event.position().toPoint() - self.last_pan_point
                self.parent_window.pan_offset += change
                self.last_pan_point = event.position().toPoint()
                self.update()
            if self.scaling:
                hover_point = self.get_scaled_point(event.position())

                self.x_hover_difference = (self.center_point_of_scaling.x()-hover_point.x())
                self.y_hover_difference = (self.center_point_of_scaling.y()-hover_point.y())
                hover_variance = max(abs(self.x_hover_difference), abs(self.y_hover_difference))

                self.x_main_difference = (self.center_point_of_scaling.x()-self.point.x())
                self.y_main_difference = (self.center_point_of_scaling.y()-self.point.y())
                main_variance = max(abs(self.x_main_difference), abs(self.y_main_difference))

                self.image_scale_factor = hover_variance/main_variance
                
                if self.image_scale_factor < 0.1:
                    self.image_scale_factor = 0.1

                if self.image_scale_factor > 20:
                    self.image_scale_factor = 20

                height_difference = self.original_dragging_layer_data.pixmap.height()*self.image_scale_factor - self.original_dragging_layer_data.pixmap.height()
                width_difference =  self.original_dragging_layer_data.pixmap.width()*self.image_scale_factor -  self.original_dragging_layer_data.pixmap.width()
                
                unreal.log(print("self image scale factor:", self.image_scale_factor))
                



                resized_image = self.pillow_image.resize((int(self.pillow_image.size[0]*self.image_scale_factor), int(self.pillow_image.size[1]*self.image_scale_factor)))

                new_qimage = ImageQt.ImageQt(resized_image).convertToFormat(QImage.Format_ARGB32)
                new_image = QPixmap.fromImage(new_qimage)

                self.selected_pixmap = new_image

                new_position = QtCore.QPoint(self.original_dragging_layer_data.position.x() - width_difference/2, self.original_dragging_layer_data.position.y() - height_difference/2)


                new_layer = TextureLayer(self.selected_pixmap, new_position)

                self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index] = new_layer
                #self.parent_window.selected_layer = self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index]


                #################################   
                resized_image = self.opaque_pillow_image.resize((int(self.opaque_pillow_image.size[0]*self.image_scale_factor), int(self.opaque_pillow_image.size[1]*self.image_scale_factor)))

                new_qimage = ImageQt.ImageQt(resized_image).convertToFormat(QImage.Format_ARGB32)
                new_image = QPixmap.fromImage(new_qimage)
                
                self.og_pixmap = new_image

                new_position = QtCore.QPoint(self.original_dragging_layer_data.position.x() - width_difference/2, self.original_dragging_layer_data.position.y() - height_difference/2)


                new_layer = TextureLayer(self.og_pixmap, new_position)

                self.parent_window.texture_layers[self.parent_window.selected_layer_index] = new_layer
                self.parent_window.selected_layer = self.parent_window.texture_layers[self.parent_window.selected_layer_index]
                #################################   
                self.update_overlay()
                




            elif self.rotating:
                hover_point = self.get_scaled_point(event.position())
                self.parent_window.never_rotated = False
                rectangle = QtCore.QRect(self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].position, self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap.size())
                topLeft = rectangle.topLeft()
                
                print("TOP LEFT BASE: ", self.topLeft)

    


                half_pix_height_difference = (self.OGHEIGHT - self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap.height())/2
                half_pix_width_differenece = (self.OGWIDTH - self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap.width())/2


                # self.center_point = QtCore.QPoint(topLeft.x() - half_pix_width, topLeft.y() - half_pix_height)

                newTopLeft = QtCore.QPoint(self.topLeft.x() + half_pix_width_differenece, self.topLeft.y() + half_pix_height_difference)

                a = self.point.x(), self.point.y()
                b = self.center_point.x(), self.center_point.y()
                c = hover_point.x(), hover_point.y()
                rotation_angle = math.degrees(math.atan2(c[1]-b[1], c[0]-b[0]) - math.atan2(a[1]-b[1], a[0]-b[0]))
                if rotation_angle <0:
                    rotation_angle += 360
                self.rotation_angle = rotation_angle
                
            
            
                rotated_image = self.pillow_image.rotate(360 - rotation_angle)


                # larger_scalar = max(self.OGHEIGHT, self.OGWIDTH)

                # difference_y = rotated_image.height - larger_scalar*4/3
                # difference_x = rotated_image.width - larger_scalar*4/3

                # left_x = difference_x/2
                # top_y = difference_y/2
                # right_x = rotated_image.width - difference_x/2
                # bottom_y = rotated_image.height - difference_y/2

                # print("LEFT X, ", left_x)
                # print("top_y, ", top_y)
                # print("right_x ", left_x)
                # print("LEFT X, ", left_x)
                

                # cropped_image = rotated_image.crop((left_x, top_y, right_x, bottom_y))
                unreal.log(print("image rotated"))
                unreal.log(print(rotation_angle))

                new_qimage = ImageQt.ImageQt(rotated_image).convertToFormat(QImage.Format_ARGB32)
                new_image = QPixmap.fromImage(new_qimage)

                
                new_layer = TextureLayer(new_image, newTopLeft)

                #self.parent_window.texture_layers[self.parent_window.selected_layer_index] = new_layer
                self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index] = new_layer
                
                
                #############################################################
                rotated_image = self.opaque_pillow_image.rotate(360 - rotation_angle)
                new_qimage = ImageQt.ImageQt(rotated_image).convertToFormat(QImage.Format_ARGB32)
                new_image = QPixmap.fromImage(new_qimage)

                
                new_layer = TextureLayer(new_image, newTopLeft)

                self.parent_window.texture_layers[self.parent_window.selected_layer_index] = new_layer
                self.parent_window.selected_layer = self.parent_window.texture_layers[self.parent_window.selected_layer_index]
                #############################################################
                
                self.update_overlay()

                        
            else:
                new_position = self.get_scaled_point(event.position()) - self.drag_start_offset
                self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].position = new_position
                
                half_pix_height = self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap.height() * 0.5
                half_pix_width = self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap.width() * 0.5
                rectangle = QtCore.QRect(self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].position, self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap.size())
                topLeft = rectangle.topLeft()
                self.paint_center_point = QtCore.QPoint(topLeft.x() + half_pix_width, topLeft.y() + half_pix_height)
                #half_pix_height = self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap.height() * 0.5
                #half_pix_width = self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap.width() * 0.5
                #self.paint_center_point = QtCore.QPoint(self.topLeft.x() + half_pix_width, self.topLeft.y() + half_pix_height)



            self.update()

    def mouseReleaseEvent(self, event):
        if self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index] == self.parent_window.texture_layers[0]:
            pass
        else:
            if event.button() == QtCore.Qt.LeftButton:
                if self.panning:
                    self.panning = False
                    self.setCursor(QtCore.Qt.ArrowCursor)
                # else:
                #     base_image = self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap.toImage()
                #     convert = base_image.convertToFormat(QImage.Format_ARGB32)
                #     self.pillow_image = ImageQt.fromqimage(convert) 
                    
                if self.scaling:
                    self.update_overlay()
                    # self.selected_pixmap = self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap
                    self.scaling = False
                    # self.rectangle = None
                    self.point = None
                    # self.center_point = None
                    self.update_overlay()

                    #self.parent_window.never_rotated = True


                    item = self.parent_window.layers.item(self.parent_window.selected_layer_index)
                    self.parent_window.change_layer(item)

                    self.parent_window.tool_panel.refresh_tool()
                elif self.rotating:
                    self.update_overlay()   

                    self.selected_pixmap = self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap
                    self.rotating = False






                    self.update_overlay()   
                # if self.panning != True:
                #     new_layer = TextureLayer(self.dragging_pixmap, self.dragging_layer.position)
                #     self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index] = self.parent_window.texture_layers[(self.parent_window.texture_layers.index(new_layer))]

                    self.rectangle = QtCore.QRect(self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].position, self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap.size())
                    self.topLeft = self.rectangle.topLeft()

                    ##################################
                    item = self.parent_window.layers.item(self.parent_window.selected_layer_index)
                    self.parent_window.change_layer(item)
                    self.parent_window.tool_panel.refresh_tool()
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

        for layer in self.parent_window.translucent_texture_layers[0:]:
            painter.drawPixmap(layer.position, layer.pixmap)
        painter.drawPixmap(QtCore.QPoint(0,0), self.parent_window.pen_overlay)

        # painter = QtGui.QPainter(self.overlay)
        if self.parent_window.selected_layer_index != 0:
            painter.drawRect(QtCore.QRect(self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].position, self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap.size()))
            pen = QtGui.QPen(QtCore.Qt.white, 10)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.drawPoint(self.paint_center_point)


        #painter.drawPixmap((self.center_point.x(),self.center_point.y()), self.overlay)


        # rect = self.rect()
        # xc = self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap.width() * 0.5
        # yc = self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap.height() * 0.5

        # painter.setPen(QtGui.QPen(QtCore.Qt.black, 1))


        # painter.drawLine(xc, rect.top(), xc, rect.bottom())
        # painter.drawLine(rect.left(), yc, rect.right(), yc)
                         
        # painter.setBrush(QtGui.QBrush(QtCore.Qt.white))
        # painter.setPen(QtGui.QPen(QtCore.Qt.blue, 1))

        # painter.translate(xc, yc)

        # painter.rotate(self.rotation_angle)

        # rx = -(13 * 0.5)
        # ry = -(17 * 0.5)
        # painter.drawRect(QtCore.QRect(rx, ry, 13, 17))
        # center_of_new_rect = (QtCore.QRect(rx, ry, 13, 17)).center()

        # painter.setPen(QtGui.QPen(QtCore.Qt.green, 80))
        # painter.drawPoint(center_of_new_rect)



        
    def clear_overlay(self):
        # self.overlay.fill(QtCore.Qt.transparent)
        # self.update()
        pass

    def clear_dragging_layer(self):
        # self.dragging_pixmap.fill(QtCore.Qt.transparent)
        # self.update()
        pass
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
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)

        outline_pen =QtGui.QPen(QtGui.QColor(0, 0, 255, 255), 5)

        if self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index]:
            
            painter.setRenderHint(QtGui.QPainter.Antialiasing)

            painter = QtGui.QPainter(self.overlay)
            painter.setPen(QtGui.QPen(outline_pen))
            rect = QtCore.QRect(self.selected_pixmap.rect())
            unreal.log(rect)

        painter.end()
        self.update()



