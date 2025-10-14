#decal test

# create materials
# - create material 
# - create material instance using parent


import unreal


# Create the Material asset
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
material_factory = unreal.MaterialFactoryNew()


package_path = "/Game/Developer/MessingAround"
material_name = "M_TEST2"
material = asset_tools.create_asset(material_name, package_path, unreal.Material, material_factory)


# Get the material editor graph
ed_graph = unreal.MaterialEditingLibrary


# 1. Base Color (Vector Parameter)
base_color_param = ed_graph.create_material_expression(material, unreal.MaterialExpressionVectorParameter, -400, 0)
base_color_param.parameter_name = unreal.Name("Base Color")
base_color_param.default_value = unreal.LinearColor(0.18, 0.18, 0.18, 1.0)


# 2. Metallic (Scalar Parameter)
metallic_param = ed_graph.create_material_expression(material, unreal.MaterialExpressionScalarParameter, -400, 150)
metallic_param.parameter_name = "Metallic"
metallic_param.default_value = 0.0


# 3. Roughness (Scalar Parameter)
roughness_param = ed_graph.create_material_expression(material, unreal.MaterialExpressionScalarParameter, -400, 300)
roughness_param.parameter_name = "Roughness"
roughness_param.default_value = 1.0


# Connect parameters to the material output
ed_graph.connect_material_property(base_color_param, "", unreal.MaterialProperty.MP_BASE_COLOR)
ed_graph.connect_material_property(metallic_param, "", unreal.MaterialProperty.MP_METALLIC)
ed_graph.connect_material_property(roughness_param, "", unreal.MaterialProperty.MP_ROUGHNESS)


# Finalize (update & save)
ed_graph.recompile_material(material)
unreal.EditorAssetLibrary.save_loaded_asset(material)


print(f"Material '{material_name}' created at {package_path}")

































