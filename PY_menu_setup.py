import unreal
import PY_main_script as MainScript

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__)))


tool_menus =  unreal.ToolMenus.get()

# Runs the main script when button pressed
@unreal.uclass()
class myTextureActionScript(unreal.ToolMenuEntryScript):
    @unreal.ufunction(override=True)
    def execute(self,context):
        MainScript.main()
        
# Creates button for textures when right clicked
def create_new_texture_menu():
    texture2dmenu = tool_menus.find_menu("ContentBrowser.AssetContextMenu.Texture")
    textScriptObj = myTextureActionScript()
    textScriptObj.init_entry(
        owner_name = texture2dmenu.menu_name,
        menu = texture2dmenu.menu_name,
        section= "GetAssetActions",
        name =  "MyTextureName",
        label = "Open Texture Editor",
        tool_tip = "Click to Open Texture Editor"
    )
    textScriptObj.register_menu_entry()
    tool_menus.refresh_all_widgets()

def main():
    create_new_texture_menu()