import PySide6
from PySide6 import QtWidgets, QtGui, QtCore
import unreal


#from PIL import Image, ImageDraw
########################################################
#### GET SELECTED ASSETS (CONTENT BROWSER SELECTION) ###
########################################################

def getSelectedAssets():
    return unreal.EditorUtilityLibrary.get_selected_assets()
# Editor utility library = editor utility fuctionality - including content browser
assets = getSelectedAssets()
print ('Content browser selection: ' + str(assets))



class LassoTool(QtWidgets.QLabel):
    def __init__(self, image_path):
        super().__init__()
        self.image = QtGui.QPixmap(image_path)
        self.setPixmap(self.image)
        self.points = []
        self.setMouseTracking(True)

    def mousePressEvent(self, event):
        self.points = [event.pos()]

    def mouseMoveEvent(self, event):
        if event.buttons() == QtCore.Qt.LeftButton:
            self.points.append(event.pos())
            self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.drawPixmap(0, 0, self.image)
        if len(self.points) > 1:
            painter.setPen(QtGui.QPen(QtCore.Qt.red, 2))
            painter.drawPolyline(*self.points)

for actor in assets:
    path = unreal.EditorAssetLibrary.get_path_name_for_loaded_asset(actor)
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    win = LassoTool(path)
    win.show()





# def polygon_to_mask(image_size, polygon_points, output_path):
#     # Create a blank grayscale image
#     mask = Image.new("L", image_size, 0)
    
#     # Draw the polygon in white (255)
#     draw = ImageDraw.Draw(mask)
#     draw.polygon(polygon_points, outline=255, fill=255)
    
#     # Save the mask to disk as a PNG
#     mask.save(output_path)

# # Example use
# polygon_to_mask((1024, 1024),
#                 [(100,100), (300,150), (250,400), (120,380)],
#                 "C:/Temp/mask.png")