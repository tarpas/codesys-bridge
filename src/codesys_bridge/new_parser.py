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
    assert not delimiter.type.startswith('END_'), "Unexpected END_* element at start: "
        
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

def parse_iec_element(text,):
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

    def get_children(self):  # -> list of METreeElement
        return self.children

    def get_name(self):  # str
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

    