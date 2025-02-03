# encoding: utf-8
from __future__ import print_function
import re
from bisect import bisect_right
from collections import namedtuple

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
        
        # Check which group matched and get type/name
        if m.group(1):  # Named opening element
            element_type = m.group(1).upper()
            name = m.group('name')
        elif m.group(3):  # VAR section
            element_type = m.group(3).upper()
        else:  # Closing element
            element_type = m.group(4).upper()
        
        end_lineno = get_line_number(m.end(), newline_positions)
        element_delimiters.append(ElementDelimiter(
            type=element_type,
            name=name,
            start_line=prev_end_lineno,
            end_line=end_lineno
        ))
        prev_end_lineno = end_lineno + 1
    
    return element_delimiters

def build_element_tree(delimiters, start_idx=0):
    """
    Recursively build an IEC element tree from element delimiters.
    Returns (IECElement, next_idx) tuple.
    """
    if start_idx >= len(delimiters):
        return None, start_idx

    delimiter = delimiters[start_idx]
    
    # Skip if this is an END_* element
    if delimiter.type.startswith('END_'):
        return None, start_idx + 1
        
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

