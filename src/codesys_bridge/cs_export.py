# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from collections import defaultdict
import os
import shutil
import re
from bisect import bisect_right
from collections import namedtuple


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


# Named tuples for structured data
ElementDelimiter = namedtuple('ElementDelimiter', ['type', 'name', 'start_line', 'end_line'])
LineSegment = namedtuple('LineSegment', ['start_line', 'end_line'])

class IECElement(object):
    def __init__(self, name, type, start_segment, sub_elements, body_segment):
        self.name = name
        self.type = type  # 'FUNCTION_BLOCK', 'FUNCTION', 'INTERFACE', 'PROGRAM', 'TYPE', 'VAR_GLOBAL' and inside FUNCTION_BLOCK: 'METHOD', 'ACTION', 'VAR_INPUT', 'VAR_OUTPUT', 'VAR_IN_OUT', 'VAR_TEMP'
        self.start_segment = LineSegment(*start_segment) if isinstance(start_segment, tuple) else start_segment
        self.sub_elements = sub_elements # list of IECElements
        self.body_segment = LineSegment(*body_segment) if isinstance(body_segment, tuple) else body_segment



def find_newline_positions(text):
    """Find positions of all newlines in the text."""
    positions = []
    pos = -1
    while True:
        pos = text.find('\n', pos + 1)
        if pos == -1:
            break
        positions.append(pos)
    return positions

def get_line_number(pos, newline_positions):
    """Get 1-based line number for a character position using binary search."""
    if not newline_positions or pos <= newline_positions[0]:
        return 1
    line = bisect_right(newline_positions, pos - 1)  # -1 because we want the line containing pos
    return line + 1

def find_element_delimiters(text, newline_positions):
    """Find all element boundaries in the text."""
    element_pattern = re.compile(r'''
        # Comments and strings to ignore (non-capturing)
        (?:
            \(\*.*?\*\)  # Multiline comments
            |
            //[^\n]*     # Single line comments
            |
            "(?:[^"$]|\$")*(?<![$])"      # Double quoted strings with escaped quotes
            |
            '(?:[^'$]|\$')*(?<![$])'      # Single quoted strings with escaped quotes
        )
        |
        # Opening elements with names
        \b(?P<named_element>FUNCTION_BLOCK|FUNCTION|INTERFACE|PROGRAM|TYPE|METHOD|ACTION)\s+(?P<name>\w+)\b
        |
        # Opening elements without names
        \b(?P<var_section>VAR_GLOBAL|VAR_INPUT|VAR_OUTPUT|VAR_TEMP|VAR_IN_OUT|VAR)\b
        |
        # Closing elements
        \b(?P<end_element>END_FUNCTION_BLOCK|END_FUNCTION|END_INTERFACE|END_TYPE|END_PROGRAM|END_VAR|END_METHOD|END_ACTION)\b
    ''', re.VERBOSE | re.IGNORECASE | re.MULTILINE | re.DOTALL)
    
    element_delimiters = []
    start_line = 1  # Start from line 1
    
    for m in element_pattern.finditer(text):
        element_type = None
        name = None
        
        # Check which group matched and get type/name
        if m.group('named_element'):  # Named opening element
            element_type = m.group('named_element').upper()
            name = m.group('name')
        elif m.group('var_section'):  # VAR section
            element_type = m.group('var_section').upper()
        elif m.group('end_element'):  # Closing element
            element_type = m.group('end_element').upper()
        else:  # Must be a comment or string, skip it
            continue
        
        end_line = get_line_number(m.end(), newline_positions)
        element_delimiters.append(ElementDelimiter(
            type=element_type,
            name=name,
            start_line=start_line,
            end_line=end_line
        ))
        start_line = end_line + 1
    
    return element_delimiters

def build_element_tree(delimiters, start_idx=0):
    """
    Recursively build an IEC element tree from element delimiters.
    Returns (IECElement, next_idx) tuple.
    """
    if start_idx >= len(delimiters):
        return None, start_idx

    delimiter = delimiters[start_idx]
    
    # We should never start parsing from an END_* element
    assert not delimiter.type.startswith('END_'), "Unexpected END_* element at start"
        
    # Find matching END element
    # VAR sections all use END_VAR
    end_type = 'END_VAR' if delimiter.type.startswith('VAR_') else 'END_' + delimiter.type
    end_idx = start_idx + 1
    sub_elements = []
    
    while end_idx < len(delimiters):
        if delimiters[end_idx].type == end_type:
            break
            
        sub_element, new_idx = build_element_tree(delimiters, end_idx)
        if sub_element:
            sub_elements.append(sub_element)
        end_idx = new_idx
        
    if end_idx >= len(delimiters):
        raise ValueError("No matching %s found for %s" % (end_type, delimiter.type))
        
    # Create element with found boundaries
    return IECElement(
        name=delimiter.name,
        type=delimiter.type,
        start_segment=LineSegment(delimiter.start_line, delimiter.end_line),
        sub_elements=sub_elements,
        body_segment=LineSegment(
            sub_elements[-1].body_segment.end_line + 1 if sub_elements 
            else delimiter.end_line + 1,
            delimiters[end_idx].end_line  # End at the end of END_* marker line
        )
    ), end_idx + 1

def parse_iec_element(text):
    newline_positions = find_newline_positions(text)
    element_delimiters = find_element_delimiters(text, newline_positions)
    root_element, _ = build_element_tree(element_delimiters)                
    return root_element


def is_var_section(element_type):
    return element_type.startswith('VAR_') or element_type == 'VAR'


def get_declaration_and_implementation(element, text_lines):
    """
    Get declaration and implementation text from an IECElement.
    
    Args:
        element: IECElement
        text_lines: List of text lines
        
    Returns:
        tuple: (declaration_lines, implementation_lines)
    """
    declaration = text_lines[element.start_segment.start_line - 1:element.start_segment.end_line]
    implementation = text_lines[element.body_segment.start_line - 1:element.body_segment.end_line]
    return declaration, implementation

def metree_dumps(element):
    """
    Convert a MockMETreeElement tree to its text representation.
    
    Args:
        element (MockMETreeElement): The root element to convert
        
    Returns:
        str: The complete text representation of the tree
    """
    result = []
    result.append(element.textual_declaration.text)
    for child in element.get_children():
        result.append(metree_dumps(child))
    result.append(element.textual_implementation.text)
    return ''.join(result)

class MockScriptTextDocument(object):
    def __init__(self, text):
        self.text = text

    def replace(self, new_text):
        self.text = new_text

class MockMETreeElement(object):
    def __init__(self, element_type, element_name, declaration, implementation, text_lines):
        """
        Create a new MockMETreeElement.
        
        Args:
            element_type (str): The type of the element
            element_name (str): The name of the element
            declaration (list[str]): The declaration text lines
            implementation (list[str]): The implementation text lines
            text_lines (list[str]): The original text lines
        """
        self.lines_list = text_lines
        self.type = element_type
        self.name = element_name
        self.children = []
        self.textual_declaration = MockScriptTextDocument(''.join(declaration))
        self.textual_implementation = MockScriptTextDocument(''.join(implementation))

    def get_children(self):
        return self.children

    def get_name(self):
        return self.name

    @property
    def has_textual_declaration(self):
        return self.textual_declaration.text != ''

    @property
    def has_textual_implementation(self):
        return self.textual_implementation.text != ''

def merge_var_sections(element):
    """
    Transform an IECElement by merging VAR sections into the parent's start segment.
    Returns a new IECElement with VAR sections merged and removed from sub_elements.
    """
    # Find the last VAR section's end line (if any)
    var_sections = [sub for sub in element.sub_elements if is_var_section(sub.type)]
    non_var_elements = [sub for sub in element.sub_elements if not is_var_section(sub.type)]

    if var_sections:
        # Update the start segment to include all VAR sections
        last_var_end = max(var.body_segment.end_line for var in var_sections)
        new_start_segment = LineSegment(
            element.start_segment.start_line,
            last_var_end
        )
    else:
        new_start_segment = element.start_segment

    # Recursively process non-VAR sub-elements
    new_sub_elements = [merge_var_sections(sub) for sub in non_var_elements]

    return IECElement(
        name=element.name,
        type=element.type,
        start_segment=new_start_segment,
        sub_elements=new_sub_elements,
        body_segment=element.body_segment
    )

def create_mock_me_tree(element_tree, text_lines):
    """
    Create a MockMETreeElement from an IECElement and text lines.
    
    Args:
        element_tree (IECElement): The IEC element tree to convert
        text_lines (list[str]): The original text lines
        
    Returns:
        MockMETreeElement: The converted tree element
    """
    declaration, implementation = get_declaration_and_implementation(element_tree, text_lines)
    mock_element = MockMETreeElement(
        element_type=element_tree.type,
        element_name=element_tree.name,
        declaration=declaration,
        implementation=implementation,
        text_lines=text_lines
    )
    
    for child in element_tree.sub_elements:
        mock_element.children.append(create_mock_me_tree(child, text_lines))
    
    return mock_element


if __name__ == "__main__":
    print("Export started.")

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


    for obj in projects.primary.get_children():
        walk_export_tree(obj, 0, save_folder)

    with open(
        os.path.join(save_folder, "unknown_object_types.txt"), "w"
    ) as unknown_ot_file:
        unknown_ot_file.write(str(dict(unknown_object_types)))

    print("Export finished.")
