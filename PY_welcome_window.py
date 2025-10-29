import unreal
import sys

import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__)))
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QSlider, QRadioButton, QButtonGroup, QComboBox, QDial, QMessageBox


# Subclass QMainWindow to customize your application's main window
class UnrealWindow(QWidget):
    def __init__(self, parent = None):
        super(UnrealWindow, self).__init__(parent)

        self.mainWindow= QMainWindow()
        self.mainWindow.setParent(self)
        self.setFixedSize(500,100)
        self.label = QLabel()
        self.label.setText("\n\n     The Texture Editor Tool has been sucessfully installed.")

        layout = QVBoxLayout()

        layout.addWidget(self.label)

        container = QWidget()
        container.setLayout(layout)

        self.setStyleSheet("""
            background-color: #2c2c2c;
            color: #ffffff;
            font-family: Segoe UI;
            font-size: 12px;
            selection-background-color: #424242;                  
        """)   

        self.mainWindow.setCentralWidget(container)

def launchWindow():
    if QApplication.instance():
        # Id any current instances of tool and destroy
        for win in (QApplication.allWindows()):
            if 'welcomeWindow' in win.objectName(): # update this name to match name below
                win.destroy()
    else:
        QApplication(sys.argv)

    UnrealWindow.window = UnrealWindow()
    UnrealWindow.window.show()
    UnrealWindow.window.setWindowTitle("Welcome to the Texture Editor Tool")
    UnrealWindow.window.setObjectName("welcomeWindow")
    unreal.parent_external_window_to_slate(UnrealWindow.window.winId())


