# encoding: utf-8
from __future__ import print_function
import re
from bisect import bisect_right

class IECElement(object):
    def __init__(self, name, type, start_element, sub_elements, body_element):
        self.name = name
        self.type = type  # 'FUNCTION_BLOCK', 'FUNCTION', 'INTERFACE', 'PROGRAM', 'TYPE', 'VAR_GLOBAL' and inside FUNCTION_BLOCK: 'METHOD', 'ACTION', 'VAR_INPUT', 'VAR_OUTPUT', 'VAR_IN_OUT', 'VAR_TEMP'
        self.start_segment = start_element # (start_lineno, end_lineno)
        self.sub_elements = sub_elements # list of IECElements
        self.body_segment = body_element # (start_lineno, end_lineno)



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
    line = bisect_right(newline_positions, pos - 1)  # -1 because we want the line containing pos
    return line + 1

def find_all_element_delimiters(parsing_text, newline_positions):
    """Find all element boundaries in the text."""
    element_pattern = re.compile(r'''
        # Opening elements with names
        \b(FUNCTION_BLOCK|FUNCTION|INTERFACE|PROGRAM|TYPE|METHOD|ACTION)\s+(?P<name>\w+)\b
        |
        # Opening elements without names
        \b(VAR_GLOBAL|VAR_INPUT|VAR_OUTPUT|VAR_TEMP|VAR_IN_OUT|VAR)\b
        |
        # Closing elements
        \b(END_FUNCTION_BLOCK|END_FUNCTION|END_INTERFACE|END_TYPE|END_PROGRAM|END_VAR|END_METHOD|END_ACTION)\b
    ''', re.VERBOSE | re.IGNORECASE | re.MULTILINE)
    
    element_delimiters = []
    prev_end_lineno = 1  # Start from line 1
    
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
        
        # Start from the line after previous delimiter ended
        start_lineno = prev_end_lineno
        end_lineno = get_line_number(m.end(), newline_positions)
        element_delimiters.append((element_type, name, start_lineno, end_lineno))
        prev_end_lineno = end_lineno + 1  # Next element starts on next line
    
    return element_delimiters

def build_element_tree(delimiters, start_idx=0):
    """
    Recursively build an IEC element tree from element delimiters.
    Returns (IECElement, next_idx) tuple.
    """
    if start_idx >= len(delimiters):
        return None, start_idx

    curr_type, curr_name, start_lineno, end_lineno = delimiters[start_idx]
    
    # Skip if this is an END_* element
    if curr_type.startswith('END_'):
        return None, start_idx + 1
        
    # Find matching END element
    # VAR sections all use END_VAR
    end_type = 'END_VAR' if curr_type.startswith('VAR_') else 'END_' + curr_type
    end_idx = start_idx + 1
    sub_elements = []
    
    while end_idx < len(delimiters):
        next_type = delimiters[end_idx][0]
        if next_type == end_type:
            break
            
        # Recursively parse sub-elements
        sub_element, new_idx = build_element_tree(delimiters, end_idx)
        if sub_element:
            sub_elements.append(sub_element)
        end_idx = new_idx
        
    if end_idx >= len(delimiters):
        raise ValueError("No matching %s found for %s" % (end_type, curr_type))
        
    # Create element with found boundaries
    element = IECElement(
        name=curr_name,
        type=curr_type,
        start_element=(start_lineno, end_lineno),
        sub_elements=sub_elements,
        body_element=(
            # If there are sub_elements, start after the last one's end element
            # Otherwise start after the declaration
            sub_elements[-1].body_segment[1] + 1 if sub_elements 
            else end_lineno + 1,
            delimiters[end_idx][3]  # End at the end of END_* marker line
        )
    )
    
    return element, end_idx + 1

def parse_iec_element(text, expected_type=None):
    """
    Parse any IEC structured text element.
    
    Args:
        text (str): The complete text of the *.iecst file
        expected_type (str, optional): Expected type ('FUNCTION_BLOCK', 'FUNCTION', etc.')
        
    Returns:
        IECElement: The parsed element
    """
    # First remove comments and strings for parsing
    parsing_text = remove_comments_and_strings_for_parsing(text)
    
    # Find all newlines for line number lookups
    newline_positions = find_newline_positions(text)
    
    # Find all elements
    element_delimiters = find_all_element_delimiters(parsing_text, newline_positions)
    
    # Build element tree
    root_element, _ = build_element_tree(element_delimiters)
    
    if expected_type and root_element.type != expected_type:
        raise ValueError("Expected %s but found %s" % (expected_type, root_element.type))
            
    return root_element

