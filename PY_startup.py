import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__)))

import PY_menu_setup as MenuSetUp
import PY_welcome_window as WelcomeWindow

# Set up button and open welcome window
def main():
    MenuSetUp.main()
    WelcomeWindow.launchWindow()

if __name__ == "__main__":
    main()