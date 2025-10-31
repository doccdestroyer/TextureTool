import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__)))
from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtWidgets import QWidget, QWidget
from PySide6.QtCore import Qt
import unreal
import math
from PySide6.QtGui import QPainterPath,  QPolygon, QPolygonF, QImage, QPixmap, QTransform
import PIL 
from PIL import ImageQt

###############################################################
#                     TEXTURE LAYER                           # 
###############################################################
# Convert Pixmap to Texture Layer
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
        # Establish Variables
        self.parent_window = parent_window
        self.texture_layers = parent_window.texture_layers
        self.panning = False
        self.last_pan_point = None
        self.dragging_layer = self.parent_window.selected_layer
        self.translucent_dragging_layer = self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index]
        self.drag_start_offset = QtCore.QPoint()
        # Set up window
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setFocus()

    # Get point in relation to scale and pan offset
    def get_scaled_point(self, pos):
        scale = self.parent_window.scale_factor
        pan = self.parent_window.pan_offset
        return QtCore.QPoint(int((pos.x() - pan.x()) / scale), int((pos.y() - pan.y()) / scale))

    # Get point in relation to scale and pan offset
    def set_scale_factor(self, scale):
        self.parent_window.scale_factor = scale
        base_size = self.parent_window.texture_layers[0].pixmap.size()
        new_size = base_size * scale
        self.resize(new_size)
        self.update()

    # Mouse Press Event to Pan or Start Moving
    def mousePressEvent(self, event):
        # If panning, update pan point
        if event.button() == QtCore.Qt.LeftButton:
            if self.panning:
                self.last_pan_point = event.position().toPoint()
                self.setCursor(QtCore.Qt.ClosedHandCursor)
            else: # Is Moving
                point = self.get_scaled_point(event.position())
                for layer in reversed(self.parent_window.texture_layers):
                    rectangle = QtCore.QRect(layer.position, layer.pixmap.size()) # Size of Layer
                    if rectangle.contains(point): # Check if point is within layer rectangle
                        if layer == self.parent_window.texture_layers[0]:
                            break # Do nothing if base layer selected
                        else:
                            # Set Selected Lauer
                            layer.selected = True
                            self.dragging_layer = layer
                            index = self.parent_window.texture_layers.index(self.dragging_layer)

                            self.parent_window.selected_layer = self.texture_layers[index]
                            self.parent_window.selected_layer_index = index
                            self.translucent_dragging_layer = self.parent_window.translucent_texture_layers[index]
                            # Change layer on UI
                            item = self.parent_window.layers.item(self.parent_window.selected_layer_index)
                            self.parent_window.layers.setCurrentItem(item)
                            # Set drag offset
                            self.drag_start_offset = point - layer.position
                            break
    
    # Mouse Move Event to pan or move image
    def mouseMoveEvent(self,event):
        if self.panning and self.last_pan_point:
            change = event.position().toPoint() - self.last_pan_point
            self.parent_window.pan_offset += change
            self.last_pan_point = event.position().toPoint()
            self.update()
        elif self.dragging_layer: #Set new position of selected layer
            new_position = self.get_scaled_point(event.position()) - self.drag_start_offset
            self.dragging_layer.position = new_position
            self.translucent_dragging_layer.position = new_position
            self.update()

    # Mouse Release Event to reset variables
    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            if self.panning:
                self.panning = False
                self.setCursor(QtCore.Qt.ArrowCursor)
            if self.dragging_layer:
                self.dragging_layer.selected = False
                self.dragging_layer = None
                self.translucent_dragging_layer = None

    # Detect space bar to start panning
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            self.panning = True
            self.setCursor(QtCore.Qt.OpenHandCursor)

    # Detect space bar to stop panning
    def keyReleaseEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            self.panning = False
            self.setCursor(QtCore.Qt.ArrowCursor)

    # Update Visuals
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.translate(self.parent_window.pan_offset) # Translate to pan offset
        painter.scale(self.parent_window.scale_factor, self.parent_window.scale_factor)  # Translate to zoom factor
        for layer in self.parent_window.translucent_texture_layers[0:]: # Paint all layers
            painter.drawPixmap(layer.position, layer.pixmap)
        painter.drawPixmap(QtCore.QPoint(0,0), self.parent_window.pen_overlay) # Draw Pen Overlay


###############################################################
#                     PEN DEBUG TOOL                          #
###############################################################
class PenTool(QtWidgets.QWidget):
    def __init__(self, image_path, parent_window=None, color=QtGui.QColor.fromRgbF(0.000000, 0.000000, 0.000000, 1.000000)):
        super().__init__()
        # Establish parent and variables
        self.pen_color = color
        self.parent_window = parent_window
        self.texture_layers = parent_window.texture_layers
        self.image = self.parent_window.selected_layer.pixmap
        # Set overlay size to base image size and make transparent
        self.original_image = self.image.copy()
        self.overlay = QtGui.QPixmap(self.image.size())
        self.overlay.fill(QtCore.Qt.transparent)
        self.pen_overlay = parent_window.pen_overlay

        self.points = []
        self.drawing = False
        self.panning = False
        self.last_pan_point = None
        self.in_selection = False
        self.setFocus()
        self.resize(self.image.size()) 
        self.merged_selection_path = parent_window.merged_selection_path
        self.selections_paths = parent_window.selections_paths
        self.update_overlay()
        self.setMouseTracking(True)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.painter_point = QtCore.QPoint(0,0)

        #Establish shortcuts
        QtGui.QShortcut(QtGui.QKeySequence("["), self, activated=self.decrease_pen)
        QtGui.QShortcut(QtGui.QKeySequence("]"), self, activated=self.increase_pen)
        QtGui.QShortcut(QtGui.QKeySequence("Space"), self, activated=self.start_panning)

    # Start Panning
    def start_panning(self):
        self.panning = True

    # Get point relative to pan offset and zoom scale factor
    def get_scaled_point(self, pos):
        scale = self.parent_window.scale_factor
        pan = self.parent_window.pan_offset
        return QtCore.QPoint(int((pos.x() - pan.x()) / scale), int((pos.y() - pan.y()) / scale))
    
    # Get scaled point relative to pan offset, zoom scale factor and layer position
    def get_scaled_moved_point(self,pos):  
        scale = self.parent_window.scale_factor
        pan = self.parent_window.pan_offset
        base_position = self.parent_window.base_layer.position
        layer_position = self.parent_window.selected_layer.position
        layer_offset = base_position - layer_position
        return QtCore.QPoint(int((pos.x() - pan.x()) / scale) + layer_offset.x(), int((pos.y() - pan.y()) / scale) + layer_offset.y())
    
    # Sets scale factor of image based on zoom
    def set_scale_factor(self, scale):
        self.parent_window.scale_factor = scale
        base_size = self.parent_window.texture_layers[0].pixmap.size()
        new_size = base_size * scale
        self.resize(new_size)
        self.update()
    
    # Detects space for panning or Delete key to clear overlay
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            self.panning = True
            self.setCursor(QtCore.Qt.OpenHandCursor)
        if event.key() == QtCore.Qt.Key_Delete:
            self.clear_overlay()
            self.update_overlay()

    # Decreases Pen Size
    def decrease_pen(self):
        self.parent_window.pen_size -= 5
        if self.parent_window.pen_size < 2: # Min Size Cap
            self.parent_window.pen_size = 2

    # Increases Pen Size
    def increase_pen(self):
        self.parent_window.pen_size += 5
        if self.parent_window.pen_size > 750: # Max Size Cap
            self.parent_window.pen_size = 750

    # Stop Panning if was panning
    def keyReleaseEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            self.panning = False
            self.setCursor(QtCore.Qt.CrossCursor)
    
    # Update Visuals
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.translate(self.parent_window.pan_offset)   # Translate to pan offset  
        painter.scale(self.parent_window.scale_factor, self.parent_window.scale_factor) # Translate to pan offset  
        for layer in self.parent_window.translucent_texture_layers[0:]: # Paint all layers
            painter.drawPixmap(layer.position, layer.pixmap)
        painter.drawPixmap(0,0, self.overlay) # Draw Overlay
        # Set pens for circle hover of mouse
        white_pen = QtGui.QPen(QtCore.Qt.white)
        black_pen = QtGui.QPen(QtCore.Qt.black)
        # Draw circle hover over mouse reflecting pen size
        painter.setPen(black_pen)
        painter.drawEllipse(self.painter_point, (-self.parent_window.pen_size/1.95),(self.parent_window.pen_size/1.95))
        painter.drawEllipse(self.painter_point, (-self.parent_window.pen_size/2.05),(self.parent_window.pen_size/2.05))
        painter.setPen(white_pen)
        painter.drawEllipse(self.painter_point, (-self.parent_window.pen_size/2),(self.parent_window.pen_size/2))


    # Detect mouse click
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            point = self.get_scaled_moved_point(event.position())
            for i, path in enumerate(list(self.selections_paths)): 
                    # Check if pen is within any selection
                    if path.contains(point):
                        self.in_selection = True
                    else:
                        if self.in_selection == True:
                            pass
                        else:
                            self.in_selection = False
            # Enables drawing if there is a selection and if they are drawing within it OR if there is no selection
            if (len(self.selections_paths) > 0 and self.in_selection) or len(self.selections_paths)==0:
                # Begin panning
                if self.panning:
                    self.last_pan_point = event.position().toPoint()
                    self.setCursor(QtCore.Qt.ClosedHandCursor)
                # Begin drawing and append first point
                else:
                    point = self.get_scaled_moved_point(event.position())
                    self.drawing = True
                    self.points = [point]
                    self.update_overlay()
            else:
                return
    # Detects mouse move
    def mouseMoveEvent(self, event):
        if self.drawing and not self.panning:
            point = self.get_scaled_moved_point(event.position())
            if len(self.selections_paths) > 0: # Checks if there are multiple selections
                for i, path in enumerate(list(self.selections_paths)):
                    if path.contains(point): # Check if point overlaps
                        self.in_selection = True
                    else:
                        if self.in_selection == True:
                            pass
                        else:
                            self.in_selection = False

                if self.in_selection: # Append point if in selection
                    self.points.append(point)
                    self.update_overlay()
                else:
                    self.commit_line_to_image(QtGui.QPolygon(self.points)) # Draw line on layer
                    self.points.clear() # Reset
                    self.update_overlay()
                self.in_selection = False
            else: # If not mutliple selections, add to points
                self.points.append(point)
                self.update_overlay()
        # if panning, detect change in position
        elif self.panning and self.last_pan_point:
            change = event.position().toPoint() - self.last_pan_point 
            self.parent_window.pan_offset += change                    
            self.last_pan_point = event.position().toPoint()
            self.update()
        self.painter_point = self.get_scaled_point(event.position())
        self.update()
            

    # On mouse release update drawing/panning
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
        # Change layer to selected layer to force update
        item = self.parent_window.layers.item(self.parent_window.selected_layer_index)
        self.parent_window.change_layer(item)
    
    # Update visuals information
    def update_overlay(self):
        self.overlay.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap)
        drawing_pen = QtGui.QPen(self.pen_color, self.parent_window.pen_size) # Set pen
        drawing_pen.setCapStyle(Qt.RoundCap) # Make pen round
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        outline_pen = QtGui.QPen(QtCore.Qt.red, 2)
        fill_brush = QtGui.QBrush(QtGui.QColor(255, 0, 0, 50))
        # Draws if point is in selection of there are no selection paths
        if self.in_selection or len(self.selections_paths)<1:
            if len(self.points) > 1:
                painter.setPen(drawing_pen)
                painter.drawPolyline(QtGui.QPolygon(self.points))
                self.commit_line_to_image(QtGui.QPolygon(self.points))
                if not self.drawing:
                    self.points.clear()
        # Draws all selections
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
        # Updates pen color
        self.pen_color = self.parent_window.color
        painter.end()
        self.update()
    
    # Clears the overlay and resets the image
    def clear_overlay(self):
        self.pen_overlay.fill(QtCore.Qt.transparent)
        self.image = self.original_image.copy()
        self.points.clear()
        self.update()

    # Forces the line drawn onto the selected layer
    def commit_line_to_image(self, line):
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
        super().__init__()
        # Establish parent and variables
        self.parent_window = parent_window
        self.texture_layers = parent_window.texture_layers
        self.image = QtGui.QPixmap(image_path)
        self.points = []
        self.drawing = False
        self.making_additional_selection = False
        self.making_removal = False
        self.original_image = self.image.copy()
        self.overlay = QtGui.QPixmap(self.image.size())
        self.overlay.fill(QtCore.Qt.transparent)
        self.merged_selection_path = parent_window.merged_selection_path
        self.selections_paths = parent_window.selections_paths
        self.panning = False
        self.last_pan_point = None
        # Adjust Window
        self.setWindowTitle("Lasso Tool")
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setFocus()
        self.update_overlay()

    # Get point relative to pan offset and zoom scale factor
    def get_scaled_point(self, pos):         
        scale = self.parent_window.scale_factor
        pan = self.parent_window.pan_offset
        return QtCore.QPoint(int((pos.x() - pan.x()) / scale), int((pos.y() - pan.y()) / scale))
    
    # Sets scale factor of image based on zoom
    def set_scale_factor(self, scale):
        self.parent_window.scale_factor = scale
        new_size = self.original_image.size() * scale
        self.resize(new_size)
        self.update()

    # Detects space for panning or Escape/Delete key to clear overlay
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space: # Start panning
            self.panning = True
            self.setCursor(QtCore.Qt.OpenHandCursor)
        if event.key() == QtCore.Qt.Key_Delete: # Clear overlay, selections and points
            self.clear_overlay()
            self.drawing = False
            self.selections_paths.clear()
            self.points = []
        if event.key() == 16777216: # If delete is pressed, clear selections
            self.parent_window.clear_selections()
            self.drawing = False

    # Stop panning if space bar released
    def keyReleaseEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            self.panning = False
            self.setCursor(QtCore.Qt.CrossCursor)

    # Mouse press event to pan or make selection
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            if self.panning:
                self.last_pan_point = event.position().toPoint()
                self.setCursor(QtCore.Qt.ClosedHandCursor)
            else:
                self.points = []
                # Checks if shift is held to start making an addtional selection
                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    self.making_additional_selection = True
                    self.making_removal = False
                # Checks if alt is held to start making a selection removal
                elif event.modifiers() & Qt.KeyboardModifier.AltModifier:
                    self.making_removal = True
                    self.making_additional_selection = False
                else: # Makes a regular new selection
                    self.making_additional_selection = False
                    self.making_removal = False
                    self.selections_paths.clear()
                    self.merged_selection_path = QPainterPath()
                    self.clear_overlay()
                self.drawing = True
                self.points = [(self.get_scaled_point(event.position()))]
                self.update_overlay()

    # Detects mouse movement to pan/add points
    def mouseMoveEvent(self, event):
        # Adds location of new point to list if user isnt panning
        if self.drawing and not self.panning:
            self.points.append(self.get_scaled_point(event.position()))
            self.update_overlay()
        # Calculates change in pan
        if self.panning and self.last_pan_point:
            change = event.position().toPoint() - self.last_pan_point 
            self.parent_window.pan_offset += change                    
            self.last_pan_point = event.position().toPoint()
            self.update()

    # Detects mouse release event to finish selection/panning
    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            if self.panning: # Stop Panning
                self.panning = False
                self.setCursor(QtCore.Qt.CrossCursor)
            else: 
                self.drawing = False
                # Check if there are enough points to make a selection
                if len(self.points) <= 2:
                    self.points = []
                    self.update_overlay()
                    return 
                # Finish selection by appending the start point to the end
                self.points.append(self.points[0])
                # Make Polygon and path
                new_polygon_f = QPolygonF(QPolygon(self.points))
                new_path = QPainterPath()
                new_path.addPolygon(new_polygon_f)

                if not self.making_removal and not self.making_additional_selection:
                    self.selections_paths.clear()
                    self.selections_paths.append(new_path)
                else:
                    removed_from_merge = False
                    # Subtract new polygon from pre-existing selections if making removal
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
                                    # If paths intersect, get rid of subtraction path oversections and readd the path
                                    if self.selections_paths[i].intersects(other_path):
                                        self.selections_paths[i] = self.selections_paths[i].subtracted(other_path)
                                        self.selections_paths.pop(k)
                                        changed = True
                                        break
                        if not removed_from_merge:
                            self.selections_paths.append(new_path)
                # Clear prior selections and append new path is not making adjustments
                if not self.making_additional_selection and not self.making_removal:
                    self.selections_paths.clear()
                    self.selections_paths.append(new_path)
                elif not self.making_removal: 
                    merged_any_polygons = False
                    # Add a new polygon to selections, merging
                    for i, path in enumerate(list(self.selections_paths)):
                        # Check if paths intersect to merge
                        if path.intersects(new_path):
                            merge_path = path.united(new_path)
                            self.selections_paths[i] = merge_path
                            merged_any_polygons = True
                            changed = True
                            while changed: # Check for all prior selections
                                changed = False
                                for j, other_path in enumerate(list(self.selections_paths)):
                                    if j == i:
                                        continue
                                    # If paths intersect,add new path and merge and readd the path
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

    # Update Visuals
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.translate(self.parent_window.pan_offset) # Translate to pan offset  
        painter.scale(self.parent_window.scale_factor, self.parent_window.scale_factor) # Translate to scale factor   
        for layer in self.parent_window.translucent_texture_layers[0:]: # Paint all layers
            painter.drawPixmap(layer.position, layer.pixmap)
        painter.drawPixmap(QtCore.QPoint(0,0), self.parent_window.pen_overlay) # Draw pen overlay
        painter.drawPixmap(0, 0, self.overlay) # Draw Selections
        
    # Clears the overlay
    def clear_overlay(self):
        self.overlay.fill(QtCore.Qt.transparent)
        self.update()
    
    # Update visuals information 
    def update_overlay(self):
        self.overlay.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(self.overlay)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        # Establish brushes
        outline_pen = QtGui.QPen(QtCore.Qt.red, 2)
        fill_brush = QtGui.QBrush(QtGui.QColor(255, 0, 0, 50))
        # Draw prior all selections
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
        # Draw lasso selection
        if len(self.points) > 1:
            painter.setPen(outline_pen)
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.drawPolyline(QtGui.QPolygon(self.points))
        painter.end()
        self.update()

###############################################################
#                    POLYGONAL LASSO                          #
###############################################################
class PolygonalTool(QtWidgets.QLabel):
    def __init__(self, image_path, parent_window=None):
        super().__init__()
        # Establish parent and variables
        self.image = QtGui.QPixmap(image_path)
        self.parent_window = parent_window
        self.texture_layers = parent_window.texture_layers
        self.original_image = self.image.copy()
        self.overlay = QtGui.QPixmap(self.image.size())
        self.overlay.fill(QtCore.Qt.transparent)
        self.points = []
        self.hover_point = None
        self.drawing = False
        self.is_first_click = True
        self.making_additional_selection = False
        self.making_removal = False
        self.panning = False
        self.last_pan_point = None
        self.merged_selection_path = parent_window.merged_selection_path
        self.selections_paths = parent_window.selections_paths
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setFocus()
        self.setMouseTracking(True)
        self.setWindowTitle("Polygonal Tool")
        self.update_overlay()

    # Get point relative to pan offset and zoom scale factor
    def get_scaled_point(self, pos):         
        scale = self.parent_window.scale_factor
        pan = self.parent_window.pan_offset
        return QtCore.QPoint(int((pos.x() - pan.x()) / scale), int((pos.y() - pan.y()) / scale))
    
    # Sets scale factor of image based on zoom
    def set_scale_factor(self, scale):
        self.parent_window.scale_factor = scale
        new_size = self.original_image.size() * scale
        self.resize(new_size)
        self.update()

    # Detects space for panning or Delete to remove most recent point and Esc to clear overlay
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            self.panning = True
            self.setCursor(QtCore.Qt.OpenHandCursor)
        # Detects if delete is pressed
        if event.key() == QtCore.Qt.Key_Delete:
            # If user is drawing and there are multiple selection points, delete selection point
            if self.drawing:
                if len(self.points)>0:
                    self.points.remove(self.points[-1])
                    self.update_overlay()
                # If user is drawing but there arent multiple seleciton points, clear overlay
                else:
                    self.clear_overlay()
                    self.drawing = False
                    self.selections_paths.clear()
                    self.points = []
                    self.is_first_click = True
            # If not drawing, clear selections
            else:   
                self.clear_overlay()
                self.drawing = False
                self.selections_paths.clear()
                self.points = []
                self.is_first_click = True
        # If Esc is pressed, clear overlay
        if event.key() == 16777216:
            self.parent_window.clear_selections()
            self.drawing = False
    
    # Stop Panning if was panning
    def keyReleaseEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            self.panning = False
            self.setCursor(QtCore.Qt.CrossCursor)

    # Detect mouse click
    def mousePressEvent(self, event):
        # TODO DELETE ME
        global selections
        # Establish local variables
        isComplete = False
        new_path = QPainterPath()
        # Check if left button is clicked
        if event.button() == QtCore.Qt.LeftButton:
            if self.panning: # If panning, update paninning point
                self.last_pan_point = event.position().toPoint()
                self.setCursor(QtCore.Qt.ClosedHandCursor)
            else: # Is drawing
                point = self.get_scaled_point(event.position()) 
                if self.is_first_click:
                    # Update variables
                    isComplete = False
                    self.points = [point]
                    self.drawing = True
                    self.is_first_click = False
                    # Checks if shift is held to start making an addtional selection
                    if event.modifiers() & QtCore.Qt.ShiftModifier:
                        self.making_additional_selection = True
                        self.making_removal = False
                    # Checks if alt is held to start making a selection removal
                    elif event.modifiers() & Qt.KeyboardModifier.AltModifier:
                        self.making_removal = True
                        self.making_additional_selection = False
                    else: # Makes a regular new selection
                        self.making_additional_selection = False
                        self.making_removal = False
                        self.selections_paths.clear()
                        self.merged_selection_path = QPainterPath()
                        self.image = self.original_image.copy()
                        self.clear_overlay()
                        self.update()
                else: 
                    # Check if polygonal has been completed by seeing if recent point is close enough to original point
                    if (point - self.points[0]).manhattanLength() < (20):
                        isComplete = True
                        # Add starting point to list of points to ensure polygon is closed
                        self.points.append(self.points[0])
                        self.drawing = False 
                        self.is_first_click = True
                        # TODO DELETE ME
                        if self.making_additional_selection:
                            selections.append(QtGui.QPolygon(self.points))
                        else:
                            selections = [QtGui.QPolygon(self.points)]

                        # Draw new polygon
                        new_polygon = QPolygonF(QPolygon(self.points))
                        polygon_path = QtGui.QPainterPath()
                        polygon_path.addPolygon(new_polygon)
                        new_polygon = polygon_path.toFillPolygon()
                        # Get points along the polygon of circumference/100
                        new_polygon_f = QtGui.QPolygonF(self.map_points_of_polygon(new_polygon, 100))
                        new_path = QPainterPath()
                        new_path.addPolygon(new_polygon_f)
                        # If complete and not making and addtions/subtractions, clear the selections and append the new selection
                        if not self.making_removal and not self.making_additional_selection and isComplete:
                            self.selections_paths.clear()
                            self.selections_paths.append(new_path)
                        # If making a removal, remove from prior selections
                        elif self.making_removal and isComplete:
                            removed_from_merge = False
                            # Checks if polygon intersects any pre-existing polygons in the selection
                            for i, path in enumerate(list(self.selections_paths)):
                                if path.intersects(new_path):
                                    # Remove new selection from prior paths
                                    subtraction_path = path.subtracted(new_path)
                                    self.selections_paths[i] = subtraction_path
                                    removed_from_merge = True
                                    # Check if intersects with any other polygons in the prior selections
                                    changed = True
                                    while changed:
                                        changed = False
                                        for k, other_path in enumerate(list(self.selections_paths)):
                                            if k == i:
                                                continue
                                            # If paths intersect, get rid of subtraction path oversections and readd the path
                                            if self.selections_paths[i].intersects(other_path):
                                                self.selections_paths[i] = self.selections_paths[i].subtracted(other_path)
                                                self.selections_paths.pop(j)
                                                changed = True
                                                break
                                if not removed_from_merge:
                                    self.selections_paths.append(new_path)
                        # Clear prior selections and append new path is not making adjustments
                        if not self.making_additional_selection and not self.making_removal:
                            self.selections_paths.clear()
                            self.selections_paths.append(new_path)
                        elif not self.making_removal: # Is merging polygons
                            merged_any_polygons = False
                            # Add a new polygon to selections
                            for i, path in enumerate(list(self.selections_paths)):
                                # Check if paths intersect to merge
                                if path.intersects(new_path):
                                    merge_path = path.united(new_path)
                                    self.selections_paths[i] = merge_path
                                    merged_any_polygons = True
                                    changed = True
                                    while changed: # Check for all prior selections
                                        changed = False
                                        for j, other_path in enumerate(list(self.selections_paths)):
                                            if j == i:
                                                continue
                                            # If paths intersect,add new path and merge and readd the path
                                            if self.selections_paths[i].intersects(other_path):
                                                self.selections_paths[i] = self.selections_paths[i].united(other_path)
                                                self.selections_paths.pop(j)
                                                changed = True
                                                break
                                    break
                                if not merged_any_polygons: # If no polygons to merge, add new path
                                    self.selections_paths.append(new_path)
                            self.clear_overlay()
                    else: # Add new point if not in range to finish selection
                        self.points.append(point)
                self.update_overlay()

    # Detects mouse movement to pan/add points
    def mouseMoveEvent(self, event):
        # Adds location of new point to list if user isnt panning
        if self.panning and self.last_pan_point:
            change = event.position().toPoint() - self.last_pan_point 
            self.parent_window.pan_offset += change
            self.last_pan_point = event.position().toPoint()
            self.update()
        # Calculates change in pan
        else:
            self.hover_point = self.get_scaled_point(event.position())
            if self.drawing:
                self.update_overlay()
            self.update()

    # Detects mouse release event to finish panning
    def mouseReleaseEvent(self,event):
        if event.button() == QtCore.Qt.LeftButton:
            if self.panning:
                self.panning = False
                self.last_pan_point = None
                self.setCursor(QtCore.Qt.CrossCursor)

    # Update Visuals
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.translate(self.parent_window.pan_offset) # Translate to pan offset 
        painter.scale(self.parent_window.scale_factor, self.parent_window.scale_factor) # Translate to scale factor   
        for layer in self.parent_window.translucent_texture_layers[0:]: # Paint all layers
            painter.drawPixmap(layer.position, layer.pixmap)
        painter.drawPixmap(QtCore.QPoint(0,0), self.parent_window.pen_overlay) # Draw pen overlay
        painter.drawPixmap(0, 0, self.overlay) # Draw Selections
        
    # Clears the overlay
    def clear_overlay(self):
        self.overlay.fill(QtCore.Qt.transparent)
        self.update()

    # Update visuals  information  
    def update_overlay(self):
        self.overlay.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(self.overlay)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        # Estabish Pens/Brushes
        outline_pen = QtGui.QPen(QtCore.Qt.red, 2)
        fill_brush = QtGui.QBrush(QtGui.QColor(255, 0, 0, 50))
        # Draw prior all selections
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
        # Draw polygonal selection
        if len(self.points) > 1 and self.drawing:
            painter.setPen(outline_pen)
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.drawPolyline(QtGui.QPolygon(self.points))
        # Draw dotted line to current hover point
        if self.drawing and self.hover_point and self.points:
            painter.setPen(QtGui.QPen(QtCore.Qt.red, 1, QtCore.Qt.DashLine))
            painter.drawLine(self.points[-1], self.hover_point)
        painter.end()
        self.update()

    # Map points of polygon spread evenly through the inputted number of points
    def map_points_of_polygon(self, polygon, number_of_points):
        path = QPainterPath()
        path.addPolygon(polygon)
        return [path.pointAtPercent(i/(number_of_points-1)) for i in range (number_of_points)]

###############################################################
#                     RECTANGLE TOOL                          #
###############################################################
class RectangularTool(QtWidgets.QLabel):
    def __init__(self, image_path, parent_window):
        super().__init__()
        # Establish parent and variables
        self.image = QtGui.QPixmap(image_path)
        self.parent_window = parent_window
        self.texture_layers = parent_window.texture_layers
        self.points = []
        self.original_image = self.image.copy()
        self.overlay = QtGui.QPixmap(self.image.size())
        self.overlay.fill(QtCore.Qt.transparent)
        self.release_point = QtCore.QPoint(0, 0)
        self.start_point = QtCore.QPoint(0, 0)
        self.hover_point = QtCore.QPoint(0, 0)
        self.drawing = False
        self.drawing_square = False
        self.drawing_in_place = False
        self.making_additional_selection = False
        self.making_removal = False
        self.panning = False
        self.last_pan_point = None
        self.merged_selection_path = parent_window.merged_selection_path
        self.selections_paths = parent_window.selections_paths
        self.setWindowTitle("Rectangle Tool")
        self.setMouseTracking(True)
        self.setPixmap(self.image)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setFocus()
        self.resize(self.image.size())
        self.update_overlay()

    # Get point relative to pan offset and zoom scale factor
    def get_scaled_point(self, pos):         
        scale = self.parent_window.scale_factor
        pan = self.parent_window.pan_offset
        return QtCore.QPoint(int((pos.x() - pan.x()) / scale), int((pos.y() - pan.y()) / scale))

    # Sets scale factor of image based on zoom
    def set_scale_factor(self, scale):
        self.parent_window.scale_factor = scale
        new_size = self.original_image.size() * scale
        self.resize(new_size)
        self.update()

    # Detects space for panning or Escape/Delete key to clear overlay
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space: # Start panning
            self.panning = True
            self.setCursor(QtCore.Qt.OpenHandCursor)
        if event.key() == QtCore.Qt.Key_Delete: # Clear overlay, selections and points
            self.clear_overlay()
            self.drawing = False
            self.selections_paths.clear()
            self.points = []
        if event.key() == 16777216: # If Esc is pressed, clear selections
            self.parent_window.clear_selections()
            self.drawing = False
            self.isDrawn = False

    # Stop panning if space bar released
    def keyReleaseEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            self.panning = False
            self.setCursor(QtCore.Qt.CrossCursor)

    # Mouse press event to pan or make selection
    def mousePressEvent(self,event):
        if event.button() == QtCore.Qt.LeftButton:
            if self.panning:
                self.last_pan_point = event.position().toPoint()
                self.setCursor(QtCore.Qt.ClosedHandCursor)
            else:
                # Checks if shift is held to start making an addtional selection
                if event.modifiers() & QtCore.Qt.ShiftModifier:
                    self.making_additional_selection = True
                    self.making_removal = False
                # Checks if alt is held to start making a selection removal
                elif event.modifiers() & Qt.KeyboardModifier.AltModifier:
                    self.making_removal = True
                    self.making_additional_selection = False
                else: # Makes a regular new selection
                    self.making_additional_selection = False
                    self.making_removal = False
                    self.selections_paths.clear()
                    self.merged_selection_path = QPainterPath()
                    self.image = self.original_image.copy()
                    self.clear_overlay()
                # Reset variables
                self.release_point = QtCore.QPoint(0, 0)
                self.start_point = QtCore.QPoint(0, 0)
                self.drawing = True
                self.start_point = self.get_scaled_point(event.position())
                self.update_overlay()

    # Detects mouse movement to pan/add points and update hover point
    def mouseMoveEvent(self, event):
        if self.drawing and not self.panning:
            # If shift is being held, user is drawing a square
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.drawing_square = True
            else:
                self.drawing_square = False
            # If alt is being held, user is drawing around a point
            if event.modifiers() & Qt.KeyboardModifier.AltModifier:
                self.drawing_in_place = True
            else:
                self.drawing_in_place = False
            # Get hover point of current relative mouse position
            self.hover_point = self.get_scaled_point(event.position())
            self.update_overlay()
            self.update()
        # Calculates change in pan
        if self.panning and self.last_pan_point:
            change = event.position().toPoint() - self.last_pan_point 
            self.parent_window.pan_offset += change                    
            self.last_pan_point = event.position().toPoint()
            self.update()

    # Detects mouse release event to finish selection/panning
    def mouseReleaseEvent(self,event):
        if event.button() == QtCore.Qt.LeftButton:
            if self.panning: # Stop Panning
                self.panning = False
                self.last_pan_point = None
                self.setCursor(QtCore.Qt.CrossCursor)
            else:            
                if self.drawing: # Get release point
                    self.release_point = self.get_scaled_point(event.position())
                if self.drawing_square:
                    self.drawing_square = False # Reset variable
                    # Calculate different between release point and start point
                    self.x_difference = (self.release_point.x()-self.start_point.x())
                    self.y_difference = (self.release_point.y()-self.start_point.y())
                    # Find the smaller value between the differences
                    variance = min(abs(self.x_difference), abs(self.y_difference))
                    # If the x difference is negative, establish direction multiplier as -1
                    if self.x_difference <0:
                        directionX = -1
                    else:
                        directionX = 1
                    # If the y difference is negative, establish direction multiplier as -1
                    if self.y_difference <0:
                        directionY = -1
                    else:
                        directionY = 1
                    # Set release point location to match square dimensions and direction multipliers
                    self.release_point.setY(self.start_point.y() + variance * directionY)
                    self.release_point.setX(self.start_point.x() + variance * directionX)
                    self.update_overlay()
                else: # If not drawing a square, set release point to current relative position
                    self.release_point = self.get_scaled_point(event.position())
                    self.drawing = False
                    self.update()
                if self.drawing_in_place:
                    self.drawing_in_place = False # Reset variable
                    self.central_point = self.start_point # Set central point to start point
                    self.start_point = self.hover_point # Set start point to hover point
                    # Calculate differences in hover points and central points
                    self.x_difference = (self.hover_point.x()-self.central_point.x())
                    self.y_difference = (self.hover_point.y()-self.central_point.y())
                    # Set the release point based on the differences
                    self.release_point.setY(self.central_point.y()-self.y_difference)
                    self.release_point.setX(self.central_point.x()-self.x_difference)
                    self.update()
                elif not self.drawing_square:
                    self.update()
            # Create and get path of new polygon from rectangle
            new_polygon_f = QPolygonF(QPolygon(QtCore.QRect(self.start_point, self.release_point)))
            new_path = QPainterPath()
            new_path.addPolygon(new_polygon_f)
            # Add new path to selection paths if making addtional selections
            if self.making_additional_selection and self.drawing:
                self.selections_paths.append(new_path)
            self.drawing = False
            self.update_overlay()
            # If making regular selection, clear prior selections and add new one
            if not self.making_removal and not self.making_additional_selection:
                self.selections_paths.clear()
                self.selections_paths.append(new_path)
            elif self.making_removal:
                removed_from_merge = False
                # Subtract new polygon from pre-existing selections if making removal
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
                                # If paths intersect, get rid of subtraction path oversections and readd the path
                                if self.selections_paths[i].intersects(other_path):
                                    self.selections_paths[i] = self.selections_paths[i].subtracted(other_path)
                                    print ("section removed")
                                    self.selections_paths.pop(k)
                                    changed = True
                                    break
                    if not removed_from_merge:
                        self.selections_paths.append(new_path)
            # Clear prior selections and append new path is not making adjustments
            elif not self.making_additional_selection:
                self.selections_paths.clear()
                self.selections_paths.append(new_path)
            else:
                merged_any_polygons = False
                # Add a new polygon to selections, merging
                for i, path in enumerate(list(self.selections_paths)):
                    # Check if paths intersect to merge
                    if path.intersects(new_path):
                        merge_path = path.united(new_path)
                        self.selections_paths[i] = merge_path
                        merged_any_polygons = True
                        changed = True
                        while changed: # Check for all prior selections
                            changed = False
                            for l, other_path in enumerate(list(self.selections_paths)):
                                if l == i:
                                    continue
                                # If paths intersect,add new path and merge and readd the path
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

    # Update Visuals
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.translate(self.parent_window.pan_offset)  # Translate to pan offset  
        painter.scale(self.parent_window.scale_factor, self.parent_window.scale_factor) # Translate to scale factor 
        for layer in self.parent_window.translucent_texture_layers[0:]:  # Paint all layers
            painter.drawPixmap(layer.position, layer.pixmap)
        painter.drawPixmap(QtCore.QPoint(0,0), self.parent_window.pen_overlay) # Draw pen overlay
        painter.drawPixmap(0, 0, self.overlay)  # Draw Selections

    # Clears the overlay
    def clear_overlay(self):
        self.overlay.fill(QtCore.Qt.transparent)
        self.update()

    # Update visuals information 
    def update_overlay(self):
        self.overlay.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(self.overlay)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        self.isDrawn = False
        # If not in original postions and user is drawing, calculate the hover rectangle
        if self.start_point != QtCore.QPoint(0, 0) and self.hover_point != QtCore.QPoint(0, 0) and self.drawing:
            if self.drawing_square and self.drawing:
                # Calculate the difference between hover and start points
                self.x_difference = (self.hover_point.x()-self.start_point.x())
                self.y_difference = (self.hover_point.y()-self.start_point.y())
                # Find the smallest absolute value
                variance = min(abs(self.x_difference), abs(self.y_difference))
                # If the x difference is negative, establish direction multiplier as -1
                if self.x_difference <0:
                    directionX = -1
                else:
                    directionX = 1
                # If the y difference is negative, establish direction multiplier as -1
                if self.y_difference <0:
                    directionY = -1
                else:
                    directionY = 1
                # Set hover point location to match square dimensions and direction multipliers
                self.hover_point.setY(self.start_point.y() + variance * directionY)
                self.hover_point.setX(self.start_point.x() + variance * directionX)
                # Establish rectanlge into square with new hover point
                rectangle = QtCore.QRect(self.start_point, self.hover_point)
                if not self.drawing_in_place:
                    # Draw outline of square with dashed line
                    painter.setPen(QtGui.QPen(QtCore.Qt.red, 1, QtCore.Qt.DashLine))
                    painter.drawRect(rectangle)
                self.update()
            # If drawing in place, lock the dashed line preview around center point
            if self.drawing_in_place and self.drawing:
                # Set center point and intial point
                self.central_point = self.start_point
                self.inital_point = self.hover_point
                # Caluculate difference between intial point and central point
                self.x_difference = (self.inital_point.x()-self.central_point.x())
                self.y_difference = (self.inital_point.y()-self.central_point.y())     
                # Set up temporary release point based on difference
                self.temporary_release_point =  QtCore.QPoint(0, 0)
                self.temporary_release_point.setY(self.central_point.y()-self.y_difference)
                self.temporary_release_point.setX(self.central_point.x()-self.x_difference)
                # Draw dotted line to show preview
                painter.setPen(QtGui.QPen(QtCore.Qt.red, 1, QtCore.Qt.DashLine))
                rectangle = QtCore.QRect(self.inital_point, self.temporary_release_point)
                painter.drawRect(rectangle)
            # Draw dotted line to show rectanlge preview
            elif self.drawing and not self.isDrawn and not self.drawing_square:
                painter.setPen(QtGui.QPen(QtCore.Qt.red, 1, QtCore.Qt.DashLine))
                rectangle = QtCore.QRect(self.start_point, self.hover_point)
                painter.drawRect(rectangle)
        if not self.drawing:
            self.clear_overlay()
        # Setup selection pens and brush
        outline_pen = QtGui.QPen(QtCore.Qt.red, 2)
        fill_brush = QtGui.QBrush(QtGui.QColor(255, 0, 0, 50))
        # Draw selections
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
#                       ELLIPSE TOOL                          #
###############################################################
class EllipticalTool(QtWidgets.QLabel):
    def __init__(self, image_path, parent_window):
        # Establish parent and variables
        self.parent_window = parent_window
        self.texture_layers = parent_window.texture_layers
        super().__init__()
        self.image = QtGui.QPixmap(image_path)
        self.points = []
        self.overlay = QtGui.QPixmap(self.image.size())
        self.overlay.fill(QtCore.Qt.transparent)
        self.original_image = self.image.copy()
        self.release_point = QtCore.QPoint(0, 0)
        self.start_point = QtCore.QPoint(0, 0)
        self.hover_point = QtCore.QPoint(0, 0)
        self.drawing = False
        self.drawing_circle = False
        self.drawing_in_place = False
        self.making_additional_selection = False
        self.making_removal = False
        self.merged_selection_path = parent_window.merged_selection_path
        self.selections_paths = parent_window.selections_paths
        self.panning = False
        self.last_pan_point = None
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setFocus()
        self.setMouseTracking(True)
        self.setPixmap(self.image)
        self.setWindowTitle("Ellipse Tool")
        self.update_overlay()

    # Get point relative to pan offset and zoom scale factor
    def set_scale_factor(self, scale):
        self.parent_window.scale_factor = scale
        new_size = self.original_image.size() * scale
        self.resize(new_size)
        self.update()

    # Sets scale factor of image based on zoom
    def get_scaled_point(self, pos):         
        scale = self.parent_window.scale_factor
        pan = self.parent_window.pan_offset
        return QtCore.QPoint(int((pos.x() - pan.x()) / scale), int((pos.y() - pan.y()) / scale))

    # Detects space for panning or Escape/Delete key to clear overlay
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space: # Start panning
            self.panning = True
            self.setCursor(QtCore.Qt.OpenHandCursor)
        if event.key() == QtCore.Qt.Key_Delete: # Clear overlay, selections and points
            self.clear_overlay()
            self.drawing = False
            self.selections_paths.clear()
            self.points = []
        if event.key() == 16777216:
            self.parent_window.clear_selections() # If Esc is pressed, clear selections
            self.drawing = False
            self.isDrawn = False

    # Stop panning if space bar released
    def keyReleaseEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            self.panning = False
            self.setCursor(QtCore.Qt.CrossCursor)

    # Mouse press event to pan or make selection
    def mousePressEvent(self,event):
        if event.button() == QtCore.Qt.LeftButton:
            if self.panning:
                self.last_pan_point = event.position().toPoint()
                self.setCursor(QtCore.Qt.ClosedHandCursor)
            else:
                # Checks if shift is held to start making an addtional selection
                if event.modifiers() & QtCore.Qt.ShiftModifier:
                    self.making_additional_selection = True
                    self.making_removal = False
                # Checks if alt is held to start making a selection removal
                elif event.modifiers() & Qt.KeyboardModifier.AltModifier:
                    self.making_removal = True
                    self.making_additional_selection = False
                else:  # Makes a regular new selection
                    self.making_additional_selection = False
                    self.making_removal = False
                    self.selections_paths.clear()
                    self.merged_selection_path = QPainterPath()
                    self.image = self.original_image.copy()
                    self.clear_overlay()
                # Reset variables
                self.release_point = QtCore.QPoint(0, 0)
                self.start_point = QtCore.QPoint(0, 0)
                self.drawing = True
                self.start_point = self.get_scaled_point(event.position())
                self.update_overlay()

    # Detects mouse movement to pan/add points and update hover point
    def mouseMoveEvent(self, event):
        if self.drawing and not self.panning:
            # If shift is being held, user is drawing a circle
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.drawing_circle = True
            else:
                self.drawing_circle = False
            # If alt is being held, user is drawing around a point
            if event.modifiers() & Qt.KeyboardModifier.AltModifier:
                self.drawing_in_place = True
            else:
                self.drawing_in_place = False
            # Get hover point of current relative mouse position
            self.hover_point = self.get_scaled_point(event.position())
            self.update_overlay()
            self.update()
        # Calculates change in pan
        if self.panning and self.last_pan_point:
            change = event.position().toPoint() - self.last_pan_point 
            self.parent_window.pan_offset += change                    
            self.last_pan_point = event.position().toPoint()
            self.update()

    # Detects mouse release event to finish selection/panning
    def mouseReleaseEvent(self,event):
        if event.button() == QtCore.Qt.LeftButton:
            if self.panning:  # Stop Panning
                self.panning = False
                self.last_pan_point = None
                self.setCursor(QtCore.Qt.CrossCursor)
            else:               
                if self.drawing:  # Get release point
                    self.release_point = self.get_scaled_point(event.position())
                if self.drawing_circle:
                    self.drawing_circle = False # Reset variable
                    # Calculate different between release point and start point
                    self.x_difference = (self.release_point.x()-self.start_point.x())
                    self.y_difference = (self.release_point.y()-self.start_point.y())
                    # Find the smaller value between the differences
                    variance = min(abs(self.x_difference), abs(self.y_difference))
                    # If the x difference is negative, establish direction multiplier as -1
                    if self.x_difference <0:
                        directionX = -1
                    else:
                        directionX = 1
                    # If the y difference is negative, establish direction multiplier as -1
                    if self.y_difference <0:
                        directionY = -1
                    else:
                        directionY = 1
                    # Set release point location to match circle dimensions and direction multipliers
                    self.release_point.setY(self.start_point.y() + variance * directionY)
                    self.release_point.setX(self.start_point.x() + variance * directionX)
                    self.update_overlay()
                else: # If not drawing a circle, set release point to current relative position
                    self.release_point = self.get_scaled_point(event.position())
                    self.drawing = False
                    self.update()
                if self.drawing_in_place:
                    self.drawing_in_place = False  # Reset variable
                    self.central_point = self.start_point # Set central point to start point
                    self.start_point = self.hover_point # Set start point to hover point
                    # Calculate differences in hover points and central points
                    self.x_difference = (self.hover_point.x()-self.central_point.x())
                    self.y_difference = (self.hover_point.y()-self.central_point.y())
                    # Set the release point based on the differences
                    self.release_point.setY(self.central_point.y()-self.y_difference)
                    self.release_point.setX(self.central_point.x()-self.x_difference)
                    # Establish ellipse
                    ellipse = QtCore.QRect(self.start_point, self.release_point)
                    self.update()
                elif not self.drawing_circle:
                    self.update()
                    # Establist ellipse
                    ellipse = QtCore.QRect(self.start_point, self.hover_point)
            # Create and get path of new polygon from ellipse
            ellipse_path = QtGui.QPainterPath()
            ellipse_path.addEllipse(ellipse)
            ellipse_polygon = ellipse_path.toFillPolygon()
            new_polygon_f = QtGui.QPolygonF(self.map_points_of_polygon(ellipse_polygon, 100))
            new_path = QPainterPath()
            new_path.addPolygon(new_polygon_f)
            # Add new path to selection paths if making addtional selections
            if self.making_additional_selection:
                self.selections_paths.append(new_path)
            self.drawing = False
            self.update_overlay()
            # If making regular selection, clear prior selections and add new one
            if not self.making_removal and not self.making_additional_selection:
                self.selections_paths.clear()
                self.selections_paths.append(new_path)
            elif self.making_removal:
                removed_from_merge = False
                # Subtract new polygon from pre-existing selections if making removal
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
                                # If paths intersect, get rid of subtraction path oversections and readd the path
                                if self.selections_paths[i].intersects(other_path):
                                    self.selections_paths[i] = self.selections_paths[i].subtracted(other_path)
                                    print ("section removed")
                                    self.selections_paths.pop(k)
                                    changed = True
                                    break
                    if not removed_from_merge:
                        self.selections_paths.append(new_path)
            # Clear prior selections and append new path is not making adjustments
            elif not self.making_additional_selection:
                self.selections_paths.clear()
                self.selections_paths.append(new_path)
            else:
                merged_any_polygons = False
                # Add a new polygon to selections, merging
                for i, path in enumerate(list(self.selections_paths)):
                    # Check if paths intersect to merge
                    if path.intersects(new_path):
                        merge_path = path.united(new_path)
                        self.selections_paths[i] = merge_path
                        merged_any_polygons = True
                        changed = True
                        while changed: # Check for all prior selections
                            changed = False
                            for l, other_path in enumerate(list(self.selections_paths)):
                                if l == i:
                                    continue
                                # If paths intersect,add new path and merge and readd the path
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

    # Update Visuals
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.translate(self.parent_window.pan_offset) # Translate to pan offset  
        painter.scale(self.parent_window.scale_factor, self.parent_window.scale_factor) # Translate to scale factor 
        for layer in self.parent_window.translucent_texture_layers[0:]:  # Paint all layers
            painter.drawPixmap(layer.position, layer.pixmap)
        painter.drawPixmap(QtCore.QPoint(0,0), self.parent_window.pen_overlay) # Draw pen overlay
        painter.drawPixmap(0, 0, self.overlay)  # Draw Selections

    # Clears the overlay 
    def clear_overlay(self):
        self.overlay.fill(QtCore.Qt.transparent)
        self.update()

    # Update visuals information 
    def update_overlay(self):
        self.overlay.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(self.overlay)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        self.isDrawn = False
        # # If not in original postions and user is drawing, calculate the hover "rectanlge and turn into ellipse
        if self.start_point != QtCore.QPoint(0, 0) and self.hover_point != QtCore.QPoint(0, 0) and self.drawing:
            if self.drawing_circle and self.drawing:
                # Calculate the difference between hover and start points
                self.x_difference = (self.hover_point.x()-self.start_point.x())
                self.y_difference = (self.hover_point.y()-self.start_point.y())
                # Find the smallest absolute value
                variance = min(abs(self.x_difference), abs(self.y_difference))
                # If the x difference is negative, establish direction multiplier as -1
                if self.x_difference <0:
                    directionX = -1
                else:
                    directionX = 1
                # If the y difference is negative, establish direction multiplier as -1
                if self.y_difference <0:
                    directionY = -1
                else:
                    directionY = 1
                # Set hover point location to match square dimensions and direction multipliers
                self.hover_point.setY(self.start_point.y() + variance * directionY)
                self.hover_point.setX(self.start_point.x() + variance * directionX)
                # Establish ellipse/rectanlge into circle with new hover point
                ellipse = QtCore.QRect(self.start_point, self.hover_point)
                if not self.drawing_in_place:
                    # Draw outline of square with dashed line
                    painter.setPen(QtGui.QPen(QtCore.Qt.red, 1, QtCore.Qt.DashLine))
                    painter.drawEllipse(ellipse)
                self.update()
            # If drawing in place, lock the dashed line preview around center point
            if self.drawing_in_place and self.drawing:
                # Set center point and inital point
                self.central_point = self.start_point
                self.inital_point = self.hover_point
                # Caluculate difference between intial point and central point
                self.x_difference = (self.inital_point.x()-self.central_point.x())
                self.y_difference = (self.inital_point.y()-self.central_point.y())     
                # Set up temporary release point based on difference
                self.temporary_release_point =  QtCore.QPoint(0, 0)
                self.temporary_release_point.setY(self.central_point.y()-self.y_difference)
                self.temporary_release_point.setX(self.central_point.x()-self.x_difference)
                # Draw dotted line to show preview
                painter.setPen(QtGui.QPen(QtCore.Qt.red, 1, QtCore.Qt.DashLine))
                ellipse = QtCore.QRect(self.inital_point, self.temporary_release_point)
                painter.drawEllipse(ellipse)
            # Draw dotted line to show rectanlge preview
            elif self.drawing and not self.isDrawn and not self.drawing_circle:
                painter.setPen(QtGui.QPen(QtCore.Qt.red, 1, QtCore.Qt.DashLine))
                ellipse = QtCore.QRect(self.start_point, self.hover_point)
                painter.drawEllipse(ellipse)
        if not self.drawing:
            self.clear_overlay()
        # Setup selection pens and brush
        outline_pen = QtGui.QPen(QtCore.Qt.red, 2)
        fill_brush = QtGui.QBrush(QtGui.QColor(255, 0, 0, 50))
        # Draw selections
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

    # Map points of polygon spread evenly through the inputted number of points
    def map_points_of_polygon(self, polygon, n):
        path = QPainterPath()
        path.addPolygon(polygon)
        return [path.pointAtPercent(i/(n-1)) for i in range (n)]
    
###############################################################
#                     TRANSFORM TOOL                          #
###############################################################
class TransformTool(QWidget):
    def __init__(self,parent_window):
        super().__init__()
        # Establish parent and vaibesl
        self.parent_window = parent_window
        self.panning = False
        self.last_pan_point = None
        self.drag_start_offset = QtCore.QPoint()
        self.texture_layers = parent_window.texture_layers
        self.inSelection = True
        self.image = self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap
        self.overlay = QtGui.QPixmap(self.image.size())
        self.overlay.fill(QtCore.Qt.transparent)
        self.selected_pixmap = QtGui.QPixmap(self.image.size())
        self.scaling = False
        self.rotating = False
        self.rectangle = None
        self.point = None
        self.rotation_angle = 0
        self.OGHEIGHT = None
        self.OGWIDTH = None
        self.topLeft = None
        self.rectangle = QtCore.QRect(self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].position, self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap.size())
        self.center_point = self.rectangle.center()
        self.paint_center_point = self.center_point
        # Set up Window
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setFocus()
        self.update_overlay()

    # Get point in relation to scale and pan offset
    def get_scaled_point(self, pos):
        scale = self.parent_window.scale_factor
        pan = self.parent_window.pan_offset
        return QtCore.QPoint(int((pos.x() - pan.x()) / scale), int((pos.y() - pan.y()) / scale))

    # Get point in relation to scale and pan offset
    def set_scale_factor(self, scale):
        self.parent_window.scale_factor = scale
        base_size = self.parent_window.texture_layers[0].pixmap.size()
        new_size = base_size * scale
        self.resize(new_size)
        self.update()

    # Mouse Press Event to Pan or Start Transformation
    def mousePressEvent(self, event):
        # If selected layer is base layer, do nothing
        if self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index] == self.parent_window.texture_layers[0]:
            pass
        else:
            # Check if click is in selection
            if event.button() == QtCore.Qt.LeftButton and self.inSelection:
                # If panning, update pan point
                if self.panning:
                    self.last_pan_point = event.position().toPoint()
                    self.setCursor(QtCore.Qt.ClosedHandCursor)
                else:
                    self.point = self.get_scaled_point(event.position()) # Set point of click
                    # Establish rectanlge over selected layer
                    self.rectangle = QtCore.QRect(self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].position, self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap.size())
                    self.topLeft = self.rectangle.topLeft()
                    # Establish expanded rectanlge for scale detection
                    expanded_rectangle = self.expand_rectangle(self.rectangle, 1.2)
                    # Estbalish center of rectanlge
                    self.center_point = self.rectangle.center()
                    # Get half the pixmap height and width of original layer
                    half_pix_height = self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap.height() * 0.5
                    half_pix_width = self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap.width() * 0.5
                    # Establih pixmaps
                    self.selected_pixmap = self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap
                    self.og_pixmap = self.parent_window.selected_layer.pixmap
                    # Check if click point is within the rectangle to start moving a layer
                    if self.rectangle.contains(self.point):
                            self.drag_start_offset = self.point - self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].position
                            self.scaling = False
                            self.rotating = False
                            self.update_overlay()
                    # Check if click point is within the expanded rectangle to start scaling a layer
                    elif expanded_rectangle.contains(self.point):
                        self.scaling = True
                        self.rotating = False
                        # Establish pillow image of translucent (displayed) layer
                        base_image = self.selected_pixmap.toImage()
                        convert = base_image.convertToFormat(QImage.Format_ARGB32)
                        self.pillow_image = ImageQt.fromqimage(convert)  
                        # Establish pillow image of opaque (calculatory) layer
                        base_image = self.og_pixmap.toImage()
                        convert = base_image.convertToFormat(QImage.Format_ARGB32)
                        self.opaque_pillow_image = ImageQt.fromqimage(convert)   
                        # Establish bounds rectangle and layer data of original
                        self.rectangle = QtCore.QRect(self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].position, self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap.size())
                        self.center_point_of_scaling = QtCore.QPoint(self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].position.x(),self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].position.y())
                        self.original_dragging_layer_data = self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index]

                    else: # Is rotating
                        self.scaling = False
                        self.rotating = True
                        # Establish base layer rectanle and set center point based on top left
                        rectangle = QtCore.QRect(self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].position, self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap.size())
                        self.topLeft = rectangle.topLeft()
                        self.center_point = QtCore.QPoint(self.topLeft.x() + half_pix_width, self.topLeft.y() + half_pix_height)
                        # Establish pillow image of translucent (displayed) layer
                        base_image = self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap.toImage()
                        convert = base_image.convertToFormat(QImage.Format_ARGB32)
                        self.pillow_image = ImageQt.fromqimage(convert) 
                        # Establish pillow image of opaque (calculatory) layer
                        base_image = self.og_pixmap.toImage()
                        convert = base_image.convertToFormat(QImage.Format_ARGB32)
                        self.opaque_pillow_image = ImageQt.fromqimage(convert)  
                        # Establish original height and width
                        self.OGHEIGHT = self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap.height()
                        self.OGWIDTH = self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap.width()
                        # If layer has not been rotated, set up bounding box size
                        if self.parent_window.never_rotated == True:
                            # Rotate pillow images to get expanded bounding box
                            self.pillow_image = self.pillow_image.rotate(45, expand = True)
                            self.pillow_image = self.pillow_image.rotate(0, expand = True)
                            self.opaque_pillow_image = self.opaque_pillow_image.rotate(45, expand = True)
                            self.opaque_pillow_image = self.opaque_pillow_image.rotate(0, expand = True)
                            self.parent_window.never_rotated = False
                    self.update()

    # Mouse Move Event to Pan or undergo transformation    
    def mouseMoveEvent(self,event): 
        # If selected layer is base layer, do nothing
        if self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index] == self.parent_window.texture_layers[0]:
            pass
        else:
            # If panning, update pan point
            if self.panning and self.last_pan_point:
                change = event.position().toPoint() - self.last_pan_point
                self.parent_window.pan_offset += change
                self.last_pan_point = event.position().toPoint()
                self.update()
            # Scale the layer
            if self.scaling:
                # Get hovered point based on scaled location of mouse
                hover_point = self.get_scaled_point(event.position())
                # Get differences of centre point of scaling and hover point
                self.x_hover_difference = (self.center_point_of_scaling.x()-hover_point.x())
                self.y_hover_difference = (self.center_point_of_scaling.y()-hover_point.y())
                # Find largest absolute difference
                hover_variance = max(abs(self.x_hover_difference), abs(self.y_hover_difference))
                # Find difference between the center point and the original point
                self.x_main_difference = (self.center_point_of_scaling.x()-self.point.x())
                self.y_main_difference = (self.center_point_of_scaling.y()-self.point.y())
                # Find largest absolute difference
                main_variance = max(abs(self.x_main_difference), abs(self.y_main_difference))
                # Set scale factor based on ratio between hover variance and main variance
                self.image_scale_factor = hover_variance/main_variance
                # Lock scale factor above 0.1
                if self.image_scale_factor < 0.1:
                    self.image_scale_factor = 0.1
                # Lock scale factor below 20
                if self.image_scale_factor > 20:
                    self.image_scale_factor = 20
                # Figure out difference in size based on original data and scale factor
                height_difference = self.original_dragging_layer_data.pixmap.height()*self.image_scale_factor - self.original_dragging_layer_data.pixmap.height()
                width_difference =  self.original_dragging_layer_data.pixmap.width()*self.image_scale_factor -  self.original_dragging_layer_data.pixmap.width()
                # Resize the image
                resized_image = self.pillow_image.resize((int(self.pillow_image.size[0]*self.image_scale_factor), int(self.pillow_image.size[1]*self.image_scale_factor)))
                #Adjusts the scaling of the viewed translucent layer
                new_qimage = ImageQt.ImageQt(resized_image).convertToFormat(QImage.Format_ARGB32)
                new_image = QPixmap.fromImage(new_qimage)
                self.selected_pixmap = new_image
                new_position = QtCore.QPoint(self.original_dragging_layer_data.position.x() - width_difference/2, self.original_dragging_layer_data.position.y() - height_difference/2)
                new_layer = TextureLayer(self.selected_pixmap, new_position)
                # Writes new image to texture layers
                self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index] = new_layer
                # Adjusts the scaling of the opaque layer
                resized_image = self.opaque_pillow_image.resize((int(self.opaque_pillow_image.size[0]*self.image_scale_factor), int(self.opaque_pillow_image.size[1]*self.image_scale_factor)))
                new_qimage = ImageQt.ImageQt(resized_image).convertToFormat(QImage.Format_ARGB32)
                new_image = QPixmap.fromImage(new_qimage)
                self.og_pixmap = new_image
                new_position = QtCore.QPoint(self.original_dragging_layer_data.position.x() - width_difference/2, self.original_dragging_layer_data.position.y() - height_difference/2)
                new_layer = TextureLayer(self.og_pixmap, new_position)
                # Writes new images to texture layers
                self.parent_window.texture_layers[self.parent_window.selected_layer_index] = new_layer
                self.parent_window.selected_layer = self.parent_window.texture_layers[self.parent_window.selected_layer_index]
                self.update_overlay()
            
            elif self.rotating:
                # Get hovered point based on scaled location of mouse
                hover_point = self.get_scaled_point(event.position())
                self.parent_window.never_rotated = False
                rectangle = QtCore.QRect(self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].position, self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap.size())
                topLeft = rectangle.topLeft()
                # Get the size difference based on the original dimensions  vs the new dimensiosn
                half_pix_height_difference = (self.OGHEIGHT - self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap.height())/2
                half_pix_width_differenece = (self.OGWIDTH - self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap.width())/2
                newTopLeft = QtCore.QPoint(self.topLeft.x() + half_pix_width_differenece, self.topLeft.y() + half_pix_height_difference)
                # Get 3 points to calculate the angle of rotation (start point, center point, hover point)
                a = self.point.x(), self.point.y()
                b = self.center_point.x(), self.center_point.y()
                c = hover_point.x(), hover_point.y()
                rotation_angle = math.degrees(math.atan2(c[1]-b[1], c[0]-b[0]) - math.atan2(a[1]-b[1], a[0]-b[0]))
                # If the rotation angle is below 0, add 360 
                if rotation_angle <0:
                    rotation_angle += 360
                self.rotation_angle = rotation_angle
                #Adjusts the rotation of the translucent layer
                rotated_image = self.pillow_image.rotate(360 - rotation_angle)
                new_qimage = ImageQt.ImageQt(rotated_image).convertToFormat(QImage.Format_ARGB32)
                new_image = QPixmap.fromImage(new_qimage)
                new_layer = TextureLayer(new_image, newTopLeft)
                self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index] = new_layer
                # Adjusts the rotation of the opaque layer
                rotated_image = self.opaque_pillow_image.rotate(360 - rotation_angle)
                new_qimage = ImageQt.ImageQt(rotated_image).convertToFormat(QImage.Format_ARGB32)
                new_image = QPixmap.fromImage(new_qimage)
                new_layer = TextureLayer(new_image, newTopLeft)
                self.parent_window.texture_layers[self.parent_window.selected_layer_index] = new_layer
                self.parent_window.selected_layer = self.parent_window.texture_layers[self.parent_window.selected_layer_index]
                self.update_overlay()      
            else:
                # Is moving and updates new position of layer
                new_position = self.get_scaled_point(event.position()) - self.drag_start_offset
                self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].position = new_position
                # Gets half sizes of pixmap of current layer
                half_pix_height = self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap.height() * 0.5
                half_pix_width = self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap.width() * 0.5
                # Establishes rectanlge based on pixmap size
                rectangle = QtCore.QRect(self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].position, self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap.size())
                topLeft = rectangle.topLeft()
                # Sets paint point for centre of rectangle
                self.paint_center_point = QtCore.QPoint(topLeft.x() + half_pix_width, topLeft.y() + half_pix_height)
            self.update()

    # Mouse Release Event to reset variables and call updates
    def mouseReleaseEvent(self, event):
        if self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index] == self.parent_window.texture_layers[0]:
            pass
        else:
            # Stop panning
            if event.button() == QtCore.Qt.LeftButton:
                if self.panning:
                    self.panning = False
                    self.setCursor(QtCore.Qt.ArrowCursor)
                if self.scaling:
                    self.update_overlay()
                    self.scaling = False
                    self.point = None
                    self.update_overlay()
                    # Change layer to refresh
                    item = self.parent_window.layers.item(self.parent_window.selected_layer_index)
                    self.parent_window.change_layer(item)
                    # Refresh tool
                    self.parent_window.tool_panel.refresh_tool()
                elif self.rotating:
                    self.update_overlay()   
                    # Update pixmap selection
                    self.selected_pixmap = self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap
                    self.rotating = False
                    self.update_overlay()  
                    # Reset Rectanlge 
                    self.rectangle = QtCore.QRect(self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].position, self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap.size())
                    self.topLeft = self.rectangle.topLeft()
                    # Change layers and tool to refresh
                    item = self.parent_window.layers.item(self.parent_window.selected_layer_index)
                    self.parent_window.change_layer(item)
                    self.parent_window.tool_panel.refresh_tool()

    # Start panning if spacebar is pressed
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            self.panning = True
            self.setCursor(QtCore.Qt.OpenHandCursor)

    # Stop panning if spacebar released
    def keyReleaseEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            self.panning = False
            self.setCursor(QtCore.Qt.ArrowCursor)

    # Update Visuals
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.translate(self.parent_window.pan_offset) # Translate to pan offset
        painter.scale(self.parent_window.scale_factor, self.parent_window.scale_factor) # Translate to zoom factor
        for layer in self.parent_window.translucent_texture_layers[0:]: # Paint all layers
            painter.drawPixmap(layer.position, layer.pixmap)
        painter.drawPixmap(QtCore.QPoint(0,0), self.parent_window.pen_overlay) # Draw Pen Overlay
        # Draw rectanlge around selected layer if it is not the base layer
        if self.parent_window.selected_layer_index != 0:
            painter.drawRect(QtCore.QRect(self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].position, self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index].pixmap.size()))
            pen = QtGui.QPen(QtCore.Qt.white, 10)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            # Draw center point of boudning rectanlge
            painter.drawPoint(self.paint_center_point)

    # Expands the rectanlge by desired scale factor
    def expand_rectangle(self,rectangle,scale_factor):
        transform = QTransform()
        center = rectangle.center()
        transform.translate(center.x(), center.y())
        transform.scale(scale_factor, scale_factor)
        transform.translate(-center.x(), -center.y())
        new_rectangle = QPolygon.boundingRect(transform.map(rectangle))
        return new_rectangle
    
    # Update visuals information
    def update_overlay(self):
        self.overlay.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(self.overlay)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)
        outline_pen =QtGui.QPen(QtGui.QColor(0, 0, 255, 255), 5)
        # Draw rectanlge on selected layer
        if self.parent_window.translucent_texture_layers[self.parent_window.selected_layer_index]:
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            painter = QtGui.QPainter(self.overlay)
            painter.setPen(QtGui.QPen(outline_pen))
            rect = QtCore.QRect(self.selected_pixmap.rect())
        painter.end()
        self.update()