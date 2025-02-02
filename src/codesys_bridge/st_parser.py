# encoding: utf-8
from __future__ import print_function
import re

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

def find_element_boundaries(parsing_text, element_type):
    """Find the start and end of an IEC element in the text."""
    patterns = {
        'fb': (r'\bFUNCTION_BLOCK\s+(?P<name>\w+)', r'END_FUNCTION_BLOCK'),
        'function': (r'\bFUNCTION\s+(?P<name>\w+)', r'END_FUNCTION'),
        'interface': (r'\bINTERFACE\s+(?P<name>\w+)', r'END_INTERFACE'),
        'struct': (r'\bTYPE\s+(?P<name>\w+)\s*:\s*STRUCT\b', r'END_STRUCT'),
        'union': (r'\bTYPE\s+(?P<name>\w+)\s*:\s*UNION\b', r'END_UNION'),
        'enum': (r'\bTYPE\s+(?P<name>\w+)\s*:\s*\(\s*\w+\s*:=\s*\d+', r'END_TYPE'),
        'program': (r'\bPROGRAM\s+(?P<name>\w+)', r'END_PROGRAM'),
        'gvl': (r'\bVAR_GLOBAL\s+(?P<name>\w+)', r'END_VAR'),
    }
    
    start_pattern, end_keyword = patterns[element_type]
    element_match = re.search(start_pattern, parsing_text, re.DOTALL | re.IGNORECASE)
    if not element_match:
        return None, None, None
        
    name = element_match.group('name')
    start_pos = element_match.start()
    
    # Find the end
    end_match = re.search(end_keyword, parsing_text[start_pos:], re.IGNORECASE)
    if not end_match:
        return None, None, None
        
    end_pos = start_pos + end_match.end()
    return name, start_pos, end_pos

def parse_var_sections(text):
    """Parse all VAR sections and return the end position of the last one."""
    var_sections = re.finditer(r'VAR(?:_INPUT|_OUTPUT|_IN_OUT)?\b.*?END_VAR', text, re.DOTALL | re.IGNORECASE)
    last_end_var = None
    for var_match in var_sections:
        last_end_var = var_match.end()
    return last_end_var

def parse_methods(text, parsing_text):
    """Parse all methods in the text."""
    methods = []
    method_pattern = r'\bMETHOD\s+(?P<name>\w+).*?END_METHOD\b'
    
    for m in re.finditer(method_pattern, parsing_text, re.DOTALL | re.IGNORECASE):
        name = m.group('name')
        start_pos = m.start()
        end_pos = m.end()
        original_method_text = text[start_pos:end_pos]
        
        # Find the split between declaration and implementation
        var_end = parse_var_sections(original_method_text)
        if var_end:
            declaration = original_method_text[:var_end]
            implementation = original_method_text[var_end:].rstrip()
        else:
            # No VAR sections, split at first newline
            first_newline = original_method_text.find('\n')
            if first_newline >= 0:
                declaration = original_method_text[:first_newline]
                implementation = original_method_text[first_newline:].rstrip()
            else:
                declaration = original_method_text
                implementation = ""
        
        methods.append(Method(name, declaration, implementation))
    
    return methods

def parse_actions(text, parsing_text):
    """Parse all actions in the text."""
    actions = []
    action_pattern = r'ACTION\s+(?P<name>\w+)\s*(?P<implementation>.*?)END_ACTION'
    
    for a in re.finditer(action_pattern, parsing_text, re.DOTALL | re.IGNORECASE):
        name = a.group('name')
        start_pos = a.start()
        end_pos = a.end()
        original_action_text = text[start_pos:end_pos]
        implementation = original_action_text[original_action_text.find(name) + len(name):-10]
        actions.append(Action(name, implementation))
    
    return actions

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
    
    # Try to determine the type if not specified
    if not expected_type:
        for type_name in ['fb', 'function', 'interface', 'struct', 'union', 'enum', 'program', 'gvl']:
            name, start, end = find_element_boundaries(parsing_text, type_name)
            if name:
                expected_type = type_name
                break
        if not expected_type:
            raise ValueError("Could not determine element type")
    
    # Find the element boundaries
    name, start_pos, end_pos = find_element_boundaries(parsing_text, expected_type)
    if not name:
        raise ValueError("No {} found in text".format(expected_type.upper()))
    
    # Get the original text content
    element_text = text[:end_pos]
    element_parsing_text = parsing_text[start_pos:end_pos]
    
    # Initialize methods and actions
    methods = []
    actions = []
    
    # Split declaration and implementation
    if expected_type in ['fb', 'function', 'interface', 'program']:
        # These types can have VAR sections
        last_end_var = parse_var_sections(element_text[start_pos:])
        if last_end_var is not None:
            declaration = element_text[:start_pos + last_end_var]
            
            # For function blocks and interfaces, find all methods and actions first
            if expected_type in ['fb', 'interface']:
                methods = parse_methods(element_text[start_pos + last_end_var:], element_parsing_text[last_end_var:])
            if expected_type == 'fb':
                actions = parse_actions(element_text[start_pos + last_end_var:], element_parsing_text[last_end_var:])
            
            # Find the last METHOD or ACTION
            last_method_end = 0
            for method in methods:
                method_end = element_text[start_pos + last_end_var:].find('END_METHOD', method.declaration.find('METHOD')) + 10
                last_method_end = max(last_method_end, method_end)
            
            last_action_end = 0
            for action in actions:
                action_end = element_text[start_pos + last_end_var:].find('END_ACTION', element_text[start_pos + last_end_var:].find('ACTION ' + action.name)) + 10
                last_action_end = max(last_action_end, action_end)
            
            # Implementation starts after the last method or action
            impl_start = start_pos + last_end_var + max(last_method_end, last_action_end)
            
            # Find the next non-whitespace after the last method/action
            next_content = re.search(r'\S', element_text[impl_start:])
            if next_content:
                impl_start += next_content.start()
                implementation = element_text[impl_start:]
            else:
                implementation = ""
        else:
            declaration = element_text
            implementation = ""
    else:
        # For struct, union, enum, and gvl everything is declaration
        declaration = element_text
        implementation = ""
    
    return IECElement(name, expected_type, declaration, implementation, methods, actions) 