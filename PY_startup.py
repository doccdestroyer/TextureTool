import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__)))

import unreal
import PY_menu_setup as MenuSetUP
import PY_welcome_window as WelcomeWindow



def main():
    MenuSetUP.main()
    WelcomeWindow.launchWindow()

if __name__ == "__main__":
    main()
    