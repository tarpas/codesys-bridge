# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import os
import re
import sys
from collections import defaultdict

# Import parsing functions from cs_export.py
from .cs_export import (
    parse_iec_element,
    get_element_type,
    MockScriptObject,
    MockScriptTextDocument,
    guid_type,
    get_declaration_and_implementation,
    merge_var_sections
)

# Mapping from file extension/type to creation function
OBJECT_TYPE_MAPPING = {
    "pou": "create_pou",
    "gvl": "create_gvl",
    "dut": "create_dut",
    "itf": "create_interface",
    "folder": "create_folder",
    "dev": "create_device",
    "lib": "add_library",
    "tl": "create_textlist",
    "gtl": "create_textlist",
    "tc": "create_task_configuration",
    "task": "create_task",
    "m": "create_method",
    "pm": "create_property_method",
    "act": "create_action",
    "prop": "create_property",
}

# Mapping from element type to PouType
POU_TYPE_MAPPING = {
    "FUNCTION_BLOCK": PouType.FunctionBlock,
    "FUNCTION": PouType.Function,
    "PROGRAM": PouType.Program,
}

# Mapping from element type to DutType
DUT_TYPE_MAPPING = {
    "STRUCT": "Structure",
    "UNION": "Union",
    "ENUM": "Enumeration",
}

if sys.version_info[0] < 3:
    # Python 2
    import codecs
    def open_file(path, mode='r'):
        return codecs.open(path, mode, encoding='utf-8')
else:
    # Python 3
    def open_file(path, mode='r'):
        return open(path, mode, encoding='utf-8')


def read_st_file(file_path):
    """Read an ST file and return its content."""
    try:
        with open_file(file_path) as f:
            return f.read()
    except UnicodeDecodeError:
        # Try with different encoding if utf-8 fails
        with codecs.open(file_path, 'r', encoding='latin-1') as f:
            return f.read()


def determine_object_type(file_path, content):
    """Determine the type of object based on file path and content."""
    # First check if the path contains a type indicator
    parts = file_path.split('.')
    if len(parts) > 1 and parts[-2] in OBJECT_TYPE_MAPPING:
        return parts[-2]
    
    # Otherwise try to determine from content
    element_type = get_element_type(content)
    if element_type in ["FUNCTION_BLOCK", "FUNCTION", "PROGRAM"]:
        return "pou"
    elif element_type == "INTERFACE":
        return "itf"
    elif element_type in ["STRUCT", "UNION", "ENUM"]:
        return "dut"
    elif element_type == "VAR_GLOBAL":
        return "gvl"
    
    # Default to folder if we can't determine
    return "folder"


def create_object(project, object_type, name, content=None):
    """Create an object in the CodeSys project based on its type."""
    if object_type == "pou":
        # Determine POU type from content
        pou_type = PouType.Program  # Default
        if content:
            element_type = get_element_type(content)
            if element_type in POU_TYPE_MAPPING:
                pou_type = POU_TYPE_MAPPING[element_type]
        
        if pou_type == PouType.Function:
            return project.create_pou(name, pou_type, return_type="INT") # The return type will be set by set_object_content from text.
        else:
            return project.create_pou(name, pou_type)

    elif object_type == "gvl":
        return project.create_gvl(name)
    
    elif object_type == "dut":
        # Determine DUT type from content
        dut_type = "Structure"  # Default
        if content:
            element_type = get_element_type(content)
            if element_type in DUT_TYPE_MAPPING:
                dut_type = DUT_TYPE_MAPPING[element_type]
        return project.create_dut(name, getattr(DutType, dut_type))
    
    elif object_type == "itf":
        return project.create_interface(name)
    
    elif object_type == "folder":
        return project.create_folder(name)
    
    elif object_type == "method":
        return project.create_method(name)
    
    elif object_type == "action":
        return project.create_action(name)
    
    elif object_type == "property":
        return project.create_property(name)
    
    elif object_type == "textlist":
        return project.create_textlist(name)
    
    elif object_type == "task":
        return project.create_task(name)
    
    elif object_type == "task_configuration":
        return project.create_task_configuration()
    
    # Add more object types as needed
    
    # Default case
    print("Unknown object type: {0} for {1}".format(object_type, name))
    return None


def set_object_content(obj, content):
    """Set the textual content of an object."""
    if not content:
        return
    
    # Parse the content to determine declaration and implementation
    try:
        element_tree = parse_iec_element(content)
        if element_tree:
            # Transform the element tree to merge VAR sections
            transformed_element = merge_var_sections(element_tree)
            
            # Get text lines for processing
            text_lines = content.splitlines(True)
            
            # Get declaration and implementation
            declaration, implementation = get_declaration_and_implementation(
                transformed_element, text_lines
            )
            
            if obj.has_textual_declaration:
                obj.textual_declaration.replace("".join(declaration))
            
            if obj.has_textual_implementation:
                obj.textual_implementation.replace("".join(implementation))
            
            # Process child elements (methods, actions, etc.)
            for sub_element in transformed_element.sub_elements:
                # Skip VAR sections as they're part of the declaration
                if sub_element.type.startswith("VAR_") or sub_element.type == "VAR":
                    continue
                
                # Create child object based on type
                child_obj = None
                if sub_element.type == "METHOD":
                    child_obj = obj.create_method(sub_element.name)
                elif sub_element.type == "ACTION":
                    child_obj = obj.create_action(sub_element.name)
                elif sub_element.type == "PROPERTY":
                    child_obj = obj.create_property(sub_element.name)
                
                if child_obj:
                    # Get declaration and implementation for the child
                    child_decl, child_impl = get_declaration_and_implementation(
                        sub_element, text_lines, deindent_level=1
                    )
                    
                    if child_obj.has_textual_declaration:
                        child_obj.textual_declaration.replace("".join(child_decl))
                    
                    if child_obj.has_textual_implementation:
                        child_obj.textual_implementation.replace("".join(child_impl))
                    
                    # Recursively process child's children
                    process_child_elements(child_obj, sub_element, text_lines)
        else:
            # If parsing fails, try a simpler approach
            if obj.has_textual_declaration:
                obj.textual_declaration.replace(content)
    except Exception as e:
        print("Error setting content: {0}".format(e))
        # Fallback: just set the whole content as declaration
        if obj.has_textual_declaration:
            obj.textual_declaration.replace(content)


def find_or_create_object(project, path, name, content=None):
    """Find an object by name or create it if it doesn't exist."""
    # First try to find the object
    found = project.find(name, False)
    if found and len(found) > 0:
        return found[0]
    
    # If not found, determine the type and create it
    object_type = determine_object_type(path, content)
    return create_object(project, object_type, name, content)


def process_st_file(project, file_path):
    """Process a single ST file and create/update the corresponding object."""
    name = os.path.splitext(os.path.basename(file_path))[0]
    content = read_st_file(file_path)
    
    # Create or find the object
    obj = find_or_create_object(project, file_path, name, content)
    if obj:
        # Set the content
        set_object_content(obj, content)
        return obj
    return None


def process_directory(project, directory_path):
    """Process a directory of ST files recursively."""
    for item in os.listdir(directory_path):
        item_path = os.path.join(directory_path, item)
        
        if os.path.isdir(item_path) and not item.startswith('.'):
            # Process subdirectory
            folder_name = item
            # Check if the folder name has a type suffix
            if '.' in folder_name:
                name_parts = folder_name.split('.')
                folder_name = name_parts[0]
                # object_type = name_parts[1]
            
            # Create or find the folder
            folder_obj = find_or_create_object(project, item_path, folder_name)
            if folder_obj:
                # Process the contents of the folder
                process_directory(folder_obj, item_path)
        
        elif item.endswith('.st'):
            # Process ST file
            process_st_file(project, item_path)


def import_st_files(project_path, source_directory):
    """
    Import ST files from a directory into a CodeSys project.
    
    Args:
        project_path (str): Path to the CodeSys project file
        source_directory (str): Path to the directory containing ST files
    """
    # Close any open project
    if projects.primary:
        projects.primary.close()
    
    # Create or open the project
    proj = projects.create(project_path)
    
    # Process the source directory
    process_directory(proj, source_directory)

    proj.save()
    proj.close()
    
    print("Import completed successfully.")


def process_child_elements(parent_obj, element_tree, text_lines):
    """Process child elements of a parent object based on the parsed element tree."""
    if not element_tree or not element_tree.sub_elements:
        return
    
    for sub_element in element_tree.sub_elements:
        # Skip VAR sections as they're part of the declaration
        if sub_element.type.startswith("VAR_") or sub_element.type == "VAR":
            continue
        
        # Create child object based on type
        child_obj = None
        if sub_element.type == "METHOD":
            child_obj = parent_obj.create_method(sub_element.name)
        elif sub_element.type == "ACTION":
            child_obj = parent_obj.create_action(sub_element.name)
        elif sub_element.type == "PROPERTY":
            child_obj = parent_obj.create_property(sub_element.name)
        
        if child_obj:
            # Get declaration and implementation for the child
            declaration, implementation = get_declaration_and_implementation(
                sub_element, text_lines, deindent_level=1
            )
            
            if child_obj.has_textual_declaration:
                child_obj.textual_declaration.replace("".join(declaration))
            
            if child_obj.has_textual_implementation:
                child_obj.textual_implementation.replace("".join(implementation))
            
            # Recursively process child's children
            process_child_elements(child_obj, sub_element, text_lines)


        # Default paths for testing - use raw strings with double backslashes
project_path = "C:\\Users\\tibor\\Documents\\sample2.project"
source_directory = "C:\\Users\\tibor\\sample_txt\\st_source"

import_st_files(project_path, source_directory) 