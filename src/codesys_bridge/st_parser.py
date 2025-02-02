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
    # First replace string literals with spaces
    text = re.sub(r'"[^"]*"', lambda m: ' ' * len(m.group(0)), text)
    text = re.sub(r"'[^']*'", lambda m: ' ' * len(m.group(0)), text)
    
    # Then replace (* *) style comments
    text = re.sub(r'\(\*.*?\*\)', lambda m: ' ' * len(m.group(0)), text, flags=re.DOTALL)
    
    # Finally replace // style comments
    text = re.sub(r'//.*$', lambda m: ' ' * len(m.group(0)), text, flags=re.MULTILINE)
    
    return text

def find_element_boundaries(parsing_text, element_type):
    """Find the start and end of an IEC element in the text."""
    patterns = {
        'fb': (r'\bFUNCTION_BLOCK\s+(?P<name>\w+)', r'END_FUNCTION_BLOCK'),
        'function': (r'\bFUNCTION\s+(?P<name>\w+)', r'END_FUNCTION'),
        'interface': (r'\bINTERFACE\s+(?P<name>\w+)', r'END_INTERFACE'),
        'struct': (r'\bTYPE\s+(?P<name>\w+)\s*:\s*STRUCT\b', r'END_STRUCT'),
        'enum': (r'\bTYPE\s+(?P<name>\w+)\s*:\s*\(\s*\w+\s*:=\s*\d+', r'END_TYPE'),
        'program': (r'\bPROGRAM\s+(?P<name>\w+)', r'END_PROGRAM'),
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
    method_pattern = r'METHOD\s+(?P<name>\w+)(?P<declaration>\s*:\s*\w+(?:\s*\([^)]*\))?.*?END_VAR)(?P<implementation>.*?)END_METHOD'
    
    for m in re.finditer(method_pattern, parsing_text, re.DOTALL | re.IGNORECASE):
        name = m.group('name')
        start_pos = m.start()
        end_pos = m.end()
        original_method_text = text[start_pos:end_pos]
        
        end_var_match = re.search(r'END_VAR', original_method_text, re.IGNORECASE)
        if end_var_match:
            declaration = original_method_text[:end_var_match.end()]
            implementation = original_method_text[end_var_match.end():-10]
        else:
            declaration = 'METHOD ' + name + m.group('declaration')
            implementation = original_method_text[:-10]
        
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
        expected_type (str, optional): Expected type ('fb', 'function', etc.)
        
    Returns:
        IECElement: The parsed element
    """
    # First remove comments and strings for parsing
    parsing_text = remove_comments_and_strings_for_parsing(text)
    
    # Try to determine the type if not specified
    if not expected_type:
        for type_name in ['fb', 'function', 'interface', 'struct', 'enum', 'program']:
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
    element_text = text[0:end_pos]
    
    # Split declaration and implementation
    if expected_type in ['fb', 'function', 'interface', 'program']:
        # These types can have VAR sections
        last_end_var = parse_var_sections(element_text)
        if last_end_var is not None:
            next_line_match = re.search(r'\n\s*', element_text[last_end_var:])
            if next_line_match:
                impl_start = last_end_var + next_line_match.start()
                declaration = element_text[:last_end_var]
                implementation = element_text[impl_start:]
            else:
                declaration = element_text
                implementation = ""
        else:
            declaration = element_text
            implementation = ""
    else:
        # For struct and enum, everything is declaration
        declaration = element_text
        implementation = ""
    
    # Parse methods and actions if applicable
    methods = []
    actions = []
    if expected_type in ['fb', 'interface']:
        methods = parse_methods(text, parsing_text)
    if expected_type == 'fb':
        actions = parse_actions(text, parsing_text)
    
    return IECElement(name, expected_type, declaration, implementation, methods, actions)

# Example usage
if __name__ == '__main__':
    samples = {
        'fb': """
    (* Function Block Example *)
    FUNCTION_BLOCK FB_Motor
        VAR_INPUT
            Speed : REAL; // Speed setpoint
            Enable : BOOL; (* Enable motor *)
        END_VAR
        
        IF Enable THEN
            Speed := 10.0;
        END_IF
        
        METHOD Start : BOOL
            VAR_INPUT
                InitialSpeed : REAL;
            END_VAR
            Speed := InitialSpeed;
        END_METHOD
        
        ACTION Stop
            Speed := 0;
        END_ACTION
    END_FUNCTION_BLOCK
    """,
        'interface': """
    INTERFACE IController
        METHOD Start : BOOL
            VAR_INPUT
                Speed : REAL;
            END_VAR
        
        METHOD Stop : BOOL
    END_INTERFACE
    """,
        'function': """
    FUNCTION Add : INT
        VAR_INPUT
            a : INT;
            b : INT;
        END_VAR
        
        Add := a + b;
    END_FUNCTION
    """,
        'struct': """
    TYPE ST_Point :
    STRUCT
        x : REAL;
        y : REAL;
        z : REAL;
    END_STRUCT
    END_TYPE
    """,
        'enum': """
    TYPE E_Colors :
    (
        Red := 0,
        Green := 1,
        Blue := 2
    );
    END_TYPE
    """
    }
    
    for type_name, sample in samples.items():
        print("\nParsing {}:".format(type_name.upper()))
        print("-" * 40)
        try:
            element = parse_iec_element(sample)
            print("Type: {}".format(element.type))
            print("Name: {}".format(element.name))
            print("\nDeclaration:")
            print(element.declaration)
            if element.implementation:
                print("\nImplementation:")
                print(element.implementation)
            
            if element.methods:
                print("\nMethods:")
                for method in element.methods:
                    print("  Method: {}".format(method.name))
                    print("  Declaration:", method.declaration)
                    print("  Implementation:", method.implementation)
                    print()
            
            if element.actions:
                print("\nActions:")
                for action in element.actions:
                    print("  Action: {}".format(action.name))
                    print("  Implementation:", action.implementation)
                    print()
            
        except Exception as e:
            print("Error: {}".format(str(e)))
        print("=" * 40) 