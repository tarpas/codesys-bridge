# encoding:utf-8
# We enable the new python 3 print syntax
from __future__ import print_function
from collections import defaultdict
import os
import shutil
import time
import subprocess

"""
prop_method		= Guid('792f2eb6-721e-4e64-ba20-bc98351056db')
tp				= Guid('2db5746d-d284-4425-9f7f-2663a34b0ebc') #dut
libm			= Guid('adb5cb65-8e1d-4a00-b70a-375ea27582f3')
method_no_ret	= Guid('f89f7675-27f1-46b3-8abb-b7da8e774ffd')
act				= Guid('8ac092e5-3128-4e26-9e7e-11016c6684f2')
fb				= Guid('6f9dac99-8de1-4efc-8465-68ac443b7d08')
itf				= Guid('6654496c-404d-479a-aad2-8551054e5f1e')
folder			= Guid('738bea1e-99bb-4f04-90bb-a7a567e74e3a')
gvl				= Guid('ffbfa93a-b94d-45fc-a329-229860183b1d')
prop			= Guid('5a3b8626-d3e9-4f37-98b5-66420063d91e')
textlist		= Guid('2bef0454-1bd3-412a-ac2c-af0f31dbc40f')
global_textlist	= Guid('63784cbb-9ba0-45e6-9d69-babf3f040511')
Device			= Guid('225bfe47-7336-4dbc-9419-4105a7c831fa')
task_config		= Guid('ae1de277-a207-4a28-9efb-456c06bd52f3')
method			= Guid('f8a58466-d7f6-439f-bbb8-d4600e41d099')
gvl_Persistent	= Guid('261bd6e6-249c-4232-bb6f-84c2fbeef430')
Project_Settings	=Guid('8753fe6f-4a22-4320-8103-e553c4fc8e04')
Plc_Logic			=Guid('40b404f9-e5dc-42c6-907f-c89f4a517386')
Application			=Guid('639b491f-5557-464c-af91-1471bac9f549')
Task				=Guid('98a2708a-9b18-4f31-82ed-a1465b24fa2d')
Task_pou			=Guid('413e2a7d-adb1-4d2c-be29-6ae6e4fab820')
Visualization		=Guid('f18bec89-9fef-401d-9953-2f11739a6808')
Visualization_Manager=Guid('4d3fdb8f-ab50-4c35-9d3a-d4bb9bb9a628')
TargetVisualization	=Guid('bc63f5fa-d286-4786-994e-7b27e4f97bd5')
WebVisualization	=Guid('0fdbf158-1ae0-47d9-9269-cd84be308e9d')
__VisualizationStyle=Guid('8e687a04-7ca7-42d3-be06-fcbda676c5ef')
ImagePool			=Guid('bb0b9044-714e-4614-ad3e-33cbdf34d16b')
Project_Information	=Guid('085afe48-c5d8-4ea5-ab0d-b35701fa6009')
SoftMotion_General_Axis_Pool=Guid('e9159722-55bc-49e5-8034-fbd278ef718f')

"""

print("Start export!")

# Get project path and set save folder to st_source subdirectory
project_path = projects.primary.path
parent_dir = os.path.dirname(os.path.dirname(project_path))  # Go up one more level
save_folder = os.path.join(
    parent_dir,
    os.path.splitext(os.path.basename(project_path))[0] + "_git",
    "st_source",
)

if not os.path.exists(save_folder):
    os.makedirs(save_folder)
else:
    directory_list = os.listdir(save_folder)
    for uknown_ot_file in directory_list:
        if not uknown_ot_file.startswith("."):
            sub_path = os.path.join(save_folder, uknown_ot_file)
            if os.path.isdir(sub_path):
                shutil.rmtree(sub_path)
            else:
                os.remove(sub_path)


unknown_object_types = defaultdict(lambda: [])

type_dist = {
    "792f2eb6-721e-4e64-ba20-bc98351056db": "pm",  # property method
    "2db5746d-d284-4425-9f7f-2663a34b0ebc": "dut",  # dut
    "adb5cb65-8e1d-4a00-b70a-375ea27582f3": "lib",  # lib manager
    "f89f7675-27f1-46b3-8abb-b7da8e774ffd": "m",  # method no ret
    "8ac092e5-3128-4e26-9e7e-11016c6684f2": "act",  # action
    "6f9dac99-8de1-4efc-8465-68ac443b7d08": "pou",  # pou
    "6654496c-404d-479a-aad2-8551054e5f1e": "itf",  # interface
    "738bea1e-99bb-4f04-90bb-a7a567e74e3a": "",  # folder
    "ffbfa93a-b94d-45fc-a329-229860183b1d": "gvl",  # global var
    "5a3b8626-d3e9-4f37-98b5-66420063d91e": "prop",  # property
    "2bef0454-1bd3-412a-ac2c-af0f31dbc40f": "tl",  # textlist
    "63784cbb-9ba0-45e6-9d69-babf3f040511": "gtl",  # global textlist
    "225bfe47-7336-4dbc-9419-4105a7c831fa": "dev",  # device
    "ae1de277-a207-4a28-9efb-456c06bd52f3": "tc",  # task configuration
    "f8a58466-d7f6-439f-bbb8-d4600e41d099": "m",  # method with ret
    "261bd6e6-249c-4232-bb6f-84c2fbeef430": "gvl",  # gvl_Persistent
    "98a2708a-9b18-4f31-82ed-a1465b24fa2d": "task",
    "c3fc9989-e24b-4002-a2c7-827a0a2595f4": "implicit",
}


def save(text, path, name):
    with open(os.path.join(path, name + ".st"), "w") as f:
        f.write(text.encode("utf-8"))


def walk_export_tree(treeobj, depth, path):
    global unknown_object_types
    curpath = path

    text_representation = ""
    object_type = ""

    name = treeobj.get_name(False)
    type_guid = treeobj.type.ToString()

    if type_guid in type_dist:
        object_type = type_dist[type_guid]
    else:
        unknown_object_types[type_guid].append(name)

    if treeobj.is_device:
        exports = [treeobj]
        projects.primary.export_native(exports, os.path.join(curpath, name + ".xml"))

    if treeobj.has_textual_declaration:
        a = treeobj.textual_declaration
        text_representation = text_representation + a.text

    if treeobj.has_textual_implementation:
        a = treeobj.textual_implementation
        text_representation = text_representation + a.text

    if treeobj.is_task:
        exports = [treeobj]
        projects.primary.export_native(exports, os.path.join(curpath, name + ".task"))

    if treeobj.is_libman:
        exports = [treeobj]
        projects.primary.export_native(exports, os.path.join(curpath, name + ".lib"))

    if treeobj.is_textlist:
        treeobj.export(os.path.join(curpath, name + ".tl"))

    children = treeobj.get_children(False)

    if children:
        if object_type:
            curpath = os.path.join(curpath, name + "." + object_type)
        else:
            curpath = os.path.join(curpath, name)

        if not os.path.exists(curpath):
            os.makedirs(curpath)

    if text_representation:
        save(text_representation, curpath, name)

    for child in treeobj.get_children(False):
        walk_export_tree(child, depth + 1, curpath)


for obj in projects.primary.get_children():
    walk_export_tree(obj, 0, save_folder)

with open(
    os.path.join(save_folder, "unknown_object_types.txt"), "w"
) as unknown_ot_file:
    unknown_ot_file.write(str(dict(unknown_object_types)))

print("--- Script finished. ---")
