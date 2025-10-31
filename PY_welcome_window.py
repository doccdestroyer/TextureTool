import unreal
import sys

import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__)))

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout

# Welcome Window to show install has worked
class WelcomeWindow(QWidget):
    # Set Up Window
    def __init__(self, parent = None):
        super(WelcomeWindow, self).__init__(parent)
        self.mainWindow= QMainWindow()
        self.mainWindow.setParent(self)
        self.setFixedSize(500,100)
        self.label = QLabel()
        self.label.setText("\n\n     The Texture Editor Tool has been sucessfully installed.")
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        container = QWidget()
        container.setLayout(layout)
        # Set Dark Mode
        self.setStyleSheet("""
            background-color: #2c2c2c;
            color: #ffffff;
            font-family: Segoe UI;
            font-size: 12px;
            selection-background-color: #424242;                  
        """)   
        self.mainWindow.setCentralWidget(container)

# Destroys window if it exists, otherwise launches window
def launchWindow():
    if QApplication.instance():
        # Id any current instances of tool and destroy
        for win in (QApplication.allWindows()):
            if 'welcomeWindow' in win.objectName():
                win.destroy()
    else: # Opens Welcome Window
        QApplication(sys.argv)
    WelcomeWindow.window = WelcomeWindow()
    WelcomeWindow.window.show()
    WelcomeWindow.window.setWindowTitle("Welcome to the Texture Editor Tool")
    WelcomeWindow.window.setObjectName("welcomeWindow")
    unreal.parent_external_window_to_slate(WelcomeWindow.window.winId())