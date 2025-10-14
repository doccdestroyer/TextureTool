
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
from PySide6.QtWidgets import QPushButton, QWidget
from PySide6.QtCore import Qt
import unreal
import math
###TODO ADJUST IMPORTS TO INCLUDE WHATS ONLY NECESARY
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget, QLineEdit, QLabel, QVBoxLayout, QSlider, QRadioButton, QButtonGroup, QComboBox, QDial
from PySide6.QtGui import QPainterPath,  QPolygon, QPolygonF,QGuiApplication

import PIL 
from PIL import Image




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
#                        MAIN WINDOW                          #
###############################################################
class CreateWindow(QtWidgets.QWidget):
    def __init__(self, image_path):
        super().__init__()
        self.setWindowTitle("Selection Tools")
        self.image_path = image_path
        self.active_tool_widget = None

        self.scale_factor = 1.0
        self.pan_offset = QtCore.QPoint(0,0)
        self.texture_layers = []

        self.pixmap = None

        # Load base image as first layer
        base_pixmap = QtGui.QPixmap(self.image_path)


        self.merged_selection_path = QPainterPath()
        self.selections_paths = []

        # self.image_label = QLabel()
        # self.image_label.setAlignment(Qt.AlignCenter)
        # self.image_label.setPixmap(base_pixmap)

        # base_pixmap = base_pixmap.scaled(base_pixmap)
        base_layer = TextureLayer(base_pixmap, QtCore.QPoint(0, 0))
        self.texture_layers.append(base_layer)

        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setFocus()

        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)

        self.active_tool_widget = MoveTool(parent_window=self)
        #self.layout.addWidget(self.active_tool_widget)
        self.layout.insertWidget(0,self.active_tool_widget)
        self.setFixedSize((self.active_tool_widget.size())*2)
        #self.setFixedSize(1200,850)

        self.add_texture_button = QPushButton("Add Texture")
        self.add_texture_button.clicked.connect(self.prompt_add_texture)
        #self.layout.addWidget(self.add_texture_button)
        self.layout.insertWidget(1,self.add_texture_button)


        self.tool_panel = ToolSectionMenu(parent=self)
        self.tool_panel.show()

        QtGui.QShortcut(QtGui.QKeySequence("Ctrl++"), self, activated=self.zoom_in)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+="), self, activated=self.zoom_in)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+-"), self, activated=self.zoom_out)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+0"), self, activated=self.reset_zoom)

        self.export_flat_button = QPushButton("Export Flattened Image")
        self.export_flat_button.clicked.connect(lambda: self.export_flattened_image("/Game/YourFolder"))
        self.layout.addWidget(self.export_flat_button)


    def prompt_add_texture(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select PNG Texture",
            "",
            "Images (*.png *.jpg *.jpeg)"
        )
        if file_path:
            self.add_new_texture_layer(file_path)

    def add_new_texture_layer(self, texture_path):
        self.pixmap = QtGui.QPixmap(texture_path)
        
        if self.pixmap.isNull():
            print(f"Failed to load texture: {texture_path}")
            return

        print(f"Loaded new texture: {texture_path}")
        new_layer = TextureLayer(self.pixmap, QtCore.QPoint(100, 100))
        self.texture_layers.append(new_layer)

        # Tell active tool to update/redraw
        if self.active_tool_widget:
            self.active_tool_widget.update()
        self.update()


    def zoom_changed(self, value):
        if self.active_tool_widget:
            self.active_tool_widget.set_scale_factor(value / 100.0)

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


    def export_flattened_image(self, unreal_folder="/Game/YourFolder"):
        temp_dir = os.path.join(unreal.Paths.project_intermediate_dir(), "TempExports")
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, "Composite.png")

        base_size = self.texture_layers[0].pixmap.size()
        final_image = QtGui.QImage(base_size, QtGui.QImage.Format_ARGB32)
        final_image.fill(QtCore.Qt.transparent)

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

        imported_asset_path = f"{unreal_folder}/Composite"
        if unreal.EditorAssetLibrary.does_asset_exist(imported_asset_path):
            unreal.log("Succesfully imported into Unreal")
        else:
            unreal.log_error("Failed to import into Unreal")


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
        self.pen_tool.setText('Pen Tool')
        self.lasso_tool = QRadioButton()
        self.lasso_tool.setText('Lasso Tool')
        self.rectangle_tool = QRadioButton()
        self.rectangle_tool.setText('Rectangle Tool')
        self.ellipse_tool = QRadioButton()
        self.ellipse_tool.setText('Ellipse Tool')
        self.polygonal_tool = QRadioButton()
        self.polygonal_tool.setText('Polygonal Tool')
        self.move_tool = QRadioButton()
        self.move_tool.setText('Move Tool')

        self.radioButtonGroup = QButtonGroup()
        self.radioButtonGroup.addButton(self.pen_tool)
        self.radioButtonGroup.addButton(self.lasso_tool)
        self.radioButtonGroup.addButton(self.rectangle_tool)
        self.radioButtonGroup.addButton(self.ellipse_tool)
        self.radioButtonGroup.addButton(self.polygonal_tool)
        self.radioButtonGroup.addButton(self.move_tool)

        layout.addWidget(self.pen_tool)
        layout.addWidget(self.lasso_tool)
        layout.addWidget(self.rectangle_tool)
        layout.addWidget(self.ellipse_tool)
        layout.addWidget(self.polygonal_tool)
        layout.addWidget(self.move_tool)

        for btn in [self.pen_tool, self.rectangle_tool, self.ellipse_tool, self.lasso_tool, self.polygonal_tool, self.move_tool]:
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
        parent_layout = self.parent_window.layout

        if hasattr(self.parent_window, "active_tool_widget") and self.parent_window.active_tool_widget:
            parent_layout.removeWidget(self.parent_window.active_tool_widget)
            self.parent_window.active_tool_widget.deleteLater()
        #else:
            #parent_layout.removeWidget(self.parent_window.image_label)
            #self.parent_window.image_label.deleteLater()

        self.parent_window.active_tool_widget = None

        if button == self.pen_tool:
            self.parent_window.active_tool_widget = PenTool(self.parent_window.image_path, parent_window=self.parent_window)
        elif button == self.rectangle_tool:
            self.parent_window.active_tool_widget = RectangularTool(self.parent_window.image_path, parent_window=self.parent_window)
        elif button == self.ellipse_tool:
            self.parent_window.active_tool_widget = EllipticalTool(self.parent_window.image_path, parent_window=self.parent_window)
        elif button == self.lasso_tool:
            self.parent_window.active_tool_widget = LassoTool(self.parent_window.image_path, parent_window=self.parent_window)
        elif button == self.polygonal_tool:
            self.parent_window.active_tool_widget = PolygonalTool(self.parent_window.image_path, parent_window=self.parent_window)
        elif button == self.move_tool:
            self.parent_window.active_tool_widget = MoveTool(parent_window=self.parent_window)


        if self.parent_window.active_tool_widget:
            parent_layout.insertWidget(0,self.parent_window.active_tool_widget)
            #parent_layout.insertWidget(1,self.parent_window.add_texture_button)
            self.parent_window.active_tool_widget.show()
            if self.parent_window.active_tool_widget == self.move_tool:
                self.parent_window.active_tool_widget.setCursor(QtCore.Qt.ArrowCursor)
            else: 
                self.parent_window.active_tool_widget.setCursor(QtCore.Qt.CrossCursor)

###############################################################
#                     PEN DEBUG TOOL                          #
###############################################################
class MoveTool(QtWidgets.QWidget):
    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window

        #base_layer = self.parent_window.texture_layers[0]
        #self.setFixedSize((base_layer.pixmap.size())*0.8)

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

        for layer in self.parent_window.texture_layers:
            painter.drawPixmap(layer.position, layer.pixmap)



###############################################################
#                     PEN DEBUG TOOL                          #
###############################################################
class PenTool(QtWidgets.QWidget):
    def __init__(self, image_path, parent_window=None):
        super().__init__()


        self.parent_window = parent_window

        self.image = self.parent_window.texture_layers[0].pixmap
        if self.image.isNull():
            raise ValueError("Failed to load image")

        self.original_image = self.image.copy()
        self.overlay = QtGui.QPixmap(self.image.size())
        self.overlay.fill(QtCore.Qt.transparent)

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
        painter = QtGui.QPainter(self)
        painter.translate(self.parent_window.pan_offset)     
        painter.scale(self.parent_window.scale_factor, self.parent_window.scale_factor)
        painter.drawPixmap(0, 0, self.image)
        #painter.drawPixmap(0, 0, self.overlay)

        for layer in self.parent_window.texture_layers[1:]:
            painter.drawPixmap(layer.position, layer.pixmap)

        painter.drawPixmap(0,0, self.overlay)
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
            self.points.append(point)
            self.update_overlay()

            if len(self.selections_paths) > 0:
                for i, path in enumerate(list(self.selections_paths)):
                    if path.contains(point):
                        self.in_selection = True
                    else:
                        self.in_selection = False
            self.update_overlay()


        if self.panning and self.last_pan_point:
            change = event.position().toPoint() - self.last_pan_point 
            self.parent_window.pan_offset += change                    
            self.last_pan_point = event.position().toPoint()
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

        painter.end()
        self.update()

    def clear_overlay(self):
        self.overlay.fill(QtCore.Qt.transparent)
        self.image = self.original_image.copy()
        self.points.clear()
        self.update()

    def commit_line_to_image(self, line):
        painter = QtGui.QPainter(self.image)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(QtGui.QPen(QtCore.Qt.black, 2))
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
                    #self.selections_paths.clear()
                    selections.clear()
                    self.merged_selection_path = QPainterPath()
                    self.image = self.original_image.copy()
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
                    return  # Not enough points to form a valid shape

                # Proceed only if valid polygon
                self.points.append(self.points[0])
                new_polygon_f = QPolygonF(QPolygon(self.points))
                new_path = QPainterPath()
                new_path.addPolygon(new_polygon_f)

                # Now safe to use new_path
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
        painter.drawPixmap(0, 0, self.image)
        painter.drawPixmap(0, 0, self.overlay)

        for layer in self.parent_window.texture_layers[1:]:
            painter.drawPixmap(layer.position, layer.pixmap)


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
    def __init__(self, image_path, parent_window=None):
        super().__init__()
        self.image = QtGui.QPixmap(image_path)

        self.parent_window = parent_window

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
                        selections.clear()
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
        painter.drawPixmap(0, 0, self.image)   
        painter.drawPixmap(0, 0, self.overlay)

        for layer in self.parent_window.texture_layers[1:]:
            painter.drawPixmap(layer.position, layer.pixmap)

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
#                     RECTANGLE TOOL                          #
###############################################################
class RectangularTool(QtWidgets.QLabel):
    def __init__(self, image_path, parent_window):
        super().__init__()
        self.image = QtGui.QPixmap(image_path)

        self.parent_window = parent_window


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

        self.panning = False
        self.last_pan_point = None

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
        painter.drawPixmap(0, 0, self.image)
        painter.drawPixmap(0, 0, self.overlay)

        for layer in self.parent_window.texture_layers[1:]:
            painter.drawPixmap(layer.position, layer.pixmap)

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
            



        if self.isDrawn:
            #painter.setBrush(QtGui.QColor(255,0,0,50))
            #self.commit_rectanlge_to_image(rectangle)
            selections.append(rectangle)

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
        painter.drawPixmap(0,0, self.image)
        painter.drawPixmap(0, 0, self.overlay)

        for layer in self.parent_window.texture_layers[1:]:
            painter.drawPixmap(layer.position, layer.pixmap)

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
                ellipse = QtCore.QRect(self.inital_point, self.temporary_release_point)
                painter.drawEllipse(ellipse)
                #self.isDrawn = True

                

            elif self.drawing and not self.isDrawn and not self.drawing_circle:
                painter.setPen(QtGui.QPen(QtCore.Qt.red, 1, QtCore.Qt.DashLine))
                ellipse = QtCore.QRect(self.start_point, self.hover_point)
                painter.drawEllipse(ellipse)



        if self.isDrawn:
            #painter.setBrush(QtGui.QColor(255,0,0,50))
            #self.commit_rectanlge_to_image(rectangle)
            selections.append(ellipse)

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
            app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
            win = CreateWindow(main_png_path)
            win.show()
            app.exec()