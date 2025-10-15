import unreal

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
material_factory = unreal.MaterialFactoryNew()
package_path = "/Game/Developer/MessingAround"
material_name = "M_DecalTest"

texture_path = "/Game/Developer/MessingAround/tattoo"
texture = unreal.load_asset(texture_path)

material = asset_tools.create_asset(material_name, package_path, unreal.Material, material_factory)

mat_editor = unreal.MaterialEditingLibrary

material.set_editor_property("material_domain", unreal.MaterialDomain.MD_DEFERRED_DECAL)
material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)

texture_sample = mat_editor.create_material_expression(material, unreal.MaterialExpressionTextureSample, -400, 0)
texture_sample.set_editor_property("texture", texture)

mat_editor.connect_material_property(texture_sample, "rgb", unreal.MaterialProperty.MP_BASE_COLOR)
mat_editor.connect_material_property(texture_sample, "a", unreal.MaterialProperty.MP_OPACITY)

mat_editor.recompile_material(material)
unreal.EditorAssetLibrary.save_loaded_asset(material)

