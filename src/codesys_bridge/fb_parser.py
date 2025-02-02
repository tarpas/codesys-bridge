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

class FunctionBlock(object):
    def __init__(self, name, declaration, implementation, methods=None, actions=None):
        self.name = name
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
    # Handle both single and double quoted strings, but don't match quotes inside comments
    text = re.sub(r'"[^"]*"', lambda m: ' ' * len(m.group(0)), text)
    text = re.sub(r"'[^']*'", lambda m: ' ' * len(m.group(0)), text)
    
    # Then replace (* *) style comments
    # Replace everything between (* and *) with spaces, preserving newlines
    text = re.sub(r'\(\*.*?\*\)', lambda m: ' ' * len(m.group(0)), text, flags=re.DOTALL)
    
    # Finally replace // style comments
    # Replace everything from // to end of line with spaces
    text = re.sub(r'//.*$', lambda m: ' ' * len(m.group(0)), text, flags=re.MULTILINE)
    
    return text

def parse_function_block(text):
    """
    Parses a function block file including its methods and actions.
    Preserves all comments and whitespace.
    
    Args:
        text (str): The complete text of the *.iecst file
        
    Returns:
        FunctionBlock: Object containing the parsed function block
    """
    # First remove comments and strings for parsing (but keep original text for content)
    parsing_text = remove_comments_and_strings_for_parsing(text)
    
    # Find the main parts: FB declaration and content
    fb_pattern = r'(?P<fb>(?P<pre>.*?)\bFUNCTION_BLOCK\s+(?P<name>\w+).*?)(?:(?=\n\s*METHOD\s+)|(?=\n\s*ACTION\s+)|END_FUNCTION_BLOCK)'
    fb_match = re.search(fb_pattern, parsing_text, re.DOTALL | re.IGNORECASE)
    
    if not fb_match:
        raise ValueError("No FUNCTION_BLOCK found in text")
        
    fb_name = fb_match.group('name')
    fb_text = text[0:fb_match.end('fb')]  # Use original text for content
    
    # Split declaration and implementation at the last END_VAR
    var_sections = re.finditer(r'VAR(?:_INPUT|_OUTPUT|_IN_OUT)?\b.*?END_VAR', fb_text, re.DOTALL | re.IGNORECASE)
    last_end_var = None
    for var_match in var_sections:
        last_end_var = var_match.end()
    
    if last_end_var is not None:
        # Find the next line start after END_VAR for implementation
        next_line_match = re.search(r'\n\s*', fb_text[last_end_var:])
        if next_line_match:
            impl_start = last_end_var + next_line_match.start()
            fb_declaration = fb_text[:last_end_var]
            fb_implementation = fb_text[impl_start:]  # Removed rstrip()
        else:
            fb_declaration = fb_text
            fb_implementation = ""
    else:
        # No VAR sections found
        fb_declaration = fb_text
        fb_implementation = ""
    
    # Find all methods
    methods = []
    method_pattern = r'METHOD\s+(?P<name>\w+)(?P<declaration>\s*:\s*\w+(?:\s*\([^)]*\))?.*?END_VAR)(?P<implementation>.*?)END_METHOD'
    for m in re.finditer(method_pattern, parsing_text, re.DOTALL | re.IGNORECASE):  # Use parsing_text instead of text
        name = m.group('name')
        # Get the original text for the content using the positions
        start_pos = m.start()
        end_pos = m.end()
        original_method_text = text[start_pos:end_pos]
        
        # Find the END_VAR position in the original text
        end_var_match = re.search(r'END_VAR', original_method_text, re.IGNORECASE)
        if end_var_match:
            declaration = original_method_text[:end_var_match.end()]
            implementation = original_method_text[end_var_match.end():-10]  # -10 to remove END_METHOD
        else:
            declaration = 'METHOD ' + name + m.group('declaration')
            implementation = original_method_text[:-10]  # -10 to remove END_METHOD
        
        methods.append(Method(name, declaration, implementation))
    
    # Find all actions
    actions = []
    action_pattern = r'ACTION\s+(?P<name>\w+)\s*(?P<implementation>.*?)END_ACTION'
    for a in re.finditer(action_pattern, parsing_text, re.DOTALL | re.IGNORECASE):  # Use parsing_text instead of text
        name = a.group('name')
        # Get the original text for the content using the positions
        start_pos = a.start()
        end_pos = a.end()
        original_action_text = text[start_pos:end_pos]
        
        # Remove ACTION and END_ACTION
        implementation = original_action_text[original_action_text.find(name) + len(name):-10]  # -10 to remove END_ACTION
        actions.append(Action(name, implementation))
    
    return FunctionBlock(fb_name, fb_declaration, fb_implementation, methods, actions)

# Example usage
if __name__ == '__main__':
    sample = """
(* Header comment for the function block
FUNCTION_BLOCK Somethings *)
FUNCTION_BLOCK FB_Motor
    VAR_INPUT
        Speed : REAL; // Speed setpoint
        Enable : BOOL; (* Enable motor *)
        Message : STRING := 'FUNCTION_BLOCK FB_Fake'; // This string should not fool the parser
        Text : STRING := "METHOD BadMethod END_METHOD"; // This string should not fool the parser
    END_VAR
    
    VAR
        CurrentSpeed : REAL;
    END_VAR
    
    // Implementation starts here
    IF Enable THEN
        CurrentSpeed := Speed;
        Message := 'ACTION BadAction END_ACTION';  // This string should not fool the parser
    END_IF
    
    METHOD Start : BOOL
        VAR_INPUT
            InitialSpeed : REAL;
        END_VAR
        
        Speed := InitialSpeed;
        Start := TRUE;
    END_METHOD
    
    ACTION Stop
        Speed := 0;
        Enable := FALSE;
    END_ACTION
END_FUNCTION_BLOCK
    """
    
    try:
        fb = parse_function_block(sample)
        print("Function Block:", fb.name)
        print("\nDeclaration:")
        print(fb.declaration)
        print("\nImplementation:")
        print(fb.implementation)
        
        print("\nMethods:")
        for method in fb.methods:
            print("  Method:", method.name)
            print("  Declaration:", method.declaration)
            print("  Implementation:", method.implementation)
            print()
            
        print("\nActions:")
        for action in fb.actions:
            print("  Action:", action.name)
            print("  Implementation:", action.implementation)
            print()
            
    except Exception as e:
        print("Error:", str(e)) 