import unreal
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__)))
import unreal
from PY_main_window import MainWindow as MainWindow

# Gets selected texture as path to PNG
def export_texture_to_png(texture_asset):
    # Check selection is texture
    if not isinstance(texture_asset, unreal.Texture):
        return None

    # Create temp path
    temp_dir = os.path.join(unreal.Paths.project_intermediate_dir(), "TempExports")
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, f"{texture_asset.get_name()}.png")

    # Export to PNG
    task = unreal.AssetExportTask()
    task.object = texture_asset
    task.filename = temp_path
    task.automated = True
    task.replace_identical = True
    task.prompt = False
    task.exporter = unreal.TextureExporterPNG()
    unreal.Exporter.run_asset_export_task(task)

    # Check if path exists and return it
    if os.path.exists(temp_path):
        return temp_path
    else:
        return None

# Shows the main window 
def main():
    assets = unreal.EditorUtilityLibrary.get_selected_assets()
    for tex in assets:
        if isinstance(tex, unreal.Texture):
            # if __name__ == "__main__":
            main_png_path = export_texture_to_png(tex)
            win = MainWindow(main_png_path)
            win.show()