# encoding: utf-8
from __future__ import print_function
import re
from bisect import bisect_right

class Method(object):
    def __init__(self, name, declaration, implementation):
        self.name = name
        self.declaration = declaration
        self.implementation = implementation

class Action(object):
    def __init__(self, name, implementation):
        self.name = name
        self.implementation = implementation

class IECElement(object):
    def __init__(self, name, type, declaration, implementation, methods=None, actions=None):
        self.name = name
        self.type = type  # 'fb', 'function', 'interface', 'struct', 'enum', 'program'
        self.declaration = declaration
        self.implementation = implementation
        self.methods = methods or []
        self.actions = actions or []

def remove_comments_and_strings_for_parsing(text):
    """
    Temporarily removes comments and string literals for parsing purposes while preserving whitespace.
    Uses regex substitution for efficiency.
    """
    # Create a copy of the text for parsing
    parsing_text = text
    
    # Replace string literals with spaces
    parsing_text = re.sub(r'"[^"]*"', lambda m: ' ' * len(m.group(0)), parsing_text)
    parsing_text = re.sub(r"'[^']*'", lambda m: ' ' * len(m.group(0)), parsing_text)
    
    # Replace (* *) style comments
    parsing_text = re.sub(r'\(\*.*?\*\)', lambda m: ' ' * len(m.group(0)), parsing_text, flags=re.DOTALL)
    
    # Replace // style comments
    parsing_text = re.sub(r'//.*$', lambda m: ' ' * len(m.group(0)), parsing_text, flags=re.MULTILINE)
    
    return parsing_text

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
    line = bisect_right(newline_positions, pos)
    return line + 1

def find_all_elements(parsing_text):
    """Find all element boundaries in the text."""
    element_pattern = re.compile(r'''
        # Opening elements with names
        \b(FUNCTION_BLOCK|FUNCTION|INTERFACE|PROGRAM|TYPE|METHOD|ACTION)\s+(?P<name>\w+)\b
        |
        # Opening elements without names
        \b(VAR_GLOBAL|VAR_INPUT|VAR_OUTPUT|VAR_TEMP|VAR_IN_OUT)\b
        |
        # Closing elements
        \b(END_FUNCTION_BLOCK|END_FUNCTION|END_INTERFACE|END_TYPE|END_PROGRAM|END_VAR|END_METHOD|END_ACTION)\b
    ''', re.VERBOSE | re.IGNORECASE | re.MULTILINE)
    
    elements = []
    for m in element_pattern.finditer(parsing_text):
        element_type = None
        name = None
        
        # Check which group matched
        if m.group(1):  # Named opening element
            element_type = m.group(1).upper()
            name = m.group('name')
        elif m.group(3):  # Unnamed opening element
            element_type = m.group(3).upper()
        else:  # Closing element
            element_type = m.group(4).upper()
        
        elements.append((element_type, name, m.start(), m.end()))
    
    return elements

def parse_iec_element(text, expected_type=None):
    """
    Parse any IEC structured text element.
    
    Args:
        text (str): The complete text of the *.iecst file
        expected_type (str, optional): Expected type ('fb', 'function', etc.')
        
    Returns:
        IECElement: The parsed element
    """
    # First remove comments and strings for parsing
    parsing_text = remove_comments_and_strings_for_parsing(text)
    
    # Find all newlines for line number lookups
    newline_positions = find_newline_positions(text)
    
    # Find all elements
    elements = find_all_elements(parsing_text)
    
    # Find the main element boundaries
    main_element = None
    for element_type, name, start, end in elements:
        if element_type in ['FUNCTION_BLOCK', 'FUNCTION', 'INTERFACE', 'PROGRAM', 'TYPE']:
            main_element = (element_type, name, start, end)
            break
    
    if not main_element:
        raise ValueError("Could not determine element type")
    
    element_type, name, start, end = main_element
    
    # Find all VAR sections
    var_sections = []
    for e_type, e_name, e_start, e_end in elements:
        if e_type.startswith('VAR_') and e_start > start:
            var_sections.append((e_start, e_end))
    
    # Find all methods and actions
    methods = []
    actions = []
    for e_type, e_name, e_start, e_end in elements:
        if e_type == 'METHOD' and e_start > start:
            method_text = text[e_start:e_end]
            methods.append(Method(e_name, method_text, ""))
        elif e_type == 'ACTION' and e_start > start:
            action_text = text[e_start:e_end]
            actions.append(Action(e_name, action_text))
    
    # Find the last VAR section
    last_var_end = 0
    for var_start, var_end in var_sections:
        last_var_end = max(last_var_end, var_end)
    
    # Split declaration and implementation
    if last_var_end > 0:
        declaration = text[:last_var_end]
        implementation = text[last_var_end:]
    else:
        declaration = text
        implementation = ""
    
    return IECElement(name, element_type.lower(), declaration, implementation, methods, actions) 