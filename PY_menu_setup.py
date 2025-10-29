import unreal
import PY_main_script as MainScript

import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__)))

# def list_menu(num = 1000):
#     menu_list = set()

#     for i in range(num):
#         obj  = unreal.find_object(None, "/Engine/Transient.ToolMenus_0:RegisteredMenu_%s" %i)

#         if not obj:
#             obj = unreal.find_object(None, f"/Engine/Transient/ToolsMenu_0:ToolMenu_{i}")
#             if not obj:
#                 continue

#         menu_name = str(obj.menu_name)
#         if menu_name == "None":
#             continue

#         menu_list.add(menu_name)
#         print(menu_list)

# print ("test is working")

# list_menu()

###################IMPORTATN
tool_menus =  unreal.ToolMenus.get()

@unreal.uclass()
class myTextureActionScript(unreal.ToolMenuEntryScript):
    @unreal.ufunction(override=True)
    def execute(self,context):
        #return super().execute
        MainScript.main()


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
    print("MENU CREATED")

def main():
    create_new_texture_menu()