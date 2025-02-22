# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import unittest
from cs_export import (
    MockMETreeElement, 
    merge_var_sections, 
    parse_iec_element, 
    get_declaration_and_implementation,
    create_mock_me_tree,
    metree_dumps
)
import difflib


class HighLevelTest(unittest.TestCase):
    def atest_text_to_tree(self):
        text = (
"""\
FUNCTION_BLOCK NestedBlock
    VAR
        x : INT;
    END_VAR
    
    METHOD MyMethod
        VAR_INPUT
            param : INT;
        END_VAR
        x := param;
    END_METHOD
    
    x := 5;
END_FUNCTION_BLOCK
""")
        tree = merge_var_sections(parse_iec_element(text))
        self.assertEqual(tree.type, "FUNCTION_BLOCK")
        self.assertEqual(tree.name, "NestedBlock")
        self.assertEqual(len(tree.sub_elements), 1)
        self.assertEqual(tree.declaration, """
FUNCTION_BLOCK NestedBlock
    VAR
        x : INT;
    END_VAR
""")
        self.assertEqual(tree.textual_implementation.text, (
"""    
    x := 5;
END_FUNCTION_BLOCK
"""))
                         
                         
        method = tree.sub_elements[0]
        self.assertEqual(method.type, "METHOD")

        self.assertEqual(tree.sub_elements[0].type, "METHOD")
        self.assertEqual(tree.sub_elements[1].type, "VAR")
        




class TestTreeParser(unittest.TestCase):

    def test_simple_function_block(self):
        """Test parsing of a simple function block with no sub-elements"""
        text = """
FUNCTION_BLOCK SimpleBlock
    a := 1;
    b := 2;
END_FUNCTION_BLOCK
"""
        element = parse_iec_element(text)
        self.assertEqual(element.type, "FUNCTION_BLOCK")
        self.assertEqual(element.name, "SimpleBlock")
        self.assertEqual(len(element.sub_elements), 0)
        self.assertEqual(element.start_segment.start_line, 1)
        self.assertEqual(element.start_segment.end_line, 2)
        self.assertEqual(element.body_segment.start_line, 3)
        
    def test_function_block_with_var_sections(self):
        """Test parsing of a function block with VAR sections"""
        text = """
FUNCTION_BLOCK BlockWithVars
    VAR_INPUT
        in1 : INT;
        in2 : REAL;
    END_VAR
    VAR_OUTPUT
        out1 : BOOL;
    END_VAR
    a := in1;
    out1 := TRUE;
END_FUNCTION_BLOCK
"""
        element = parse_iec_element(text)
        self.assertEqual(element.type, "FUNCTION_BLOCK")
        self.assertEqual(len(element.sub_elements), 2)
        self.assertEqual(element.sub_elements[0].type, "VAR_INPUT")
        self.assertEqual(element.sub_elements[1].type, "VAR_OUTPUT")
        # Body should start after last VAR section
        self.assertTrue(element.body_segment.start_line > element.sub_elements[1].body_segment.end_line)
        
    def test_nested_elements(self):
        """Test parsing of nested elements (function block with method)"""
        text = """
FUNCTION_BLOCK NestedBlock
    VAR
        x : INT;
    END_VAR
    
    METHOD MyMethod
        VAR_INPUT
            param : INT;
        END_VAR
        x := param;
    END_METHOD
    
    x := 5;
END_FUNCTION_BLOCK
"""
        element = parse_iec_element(text)
        self.assertEqual(len(element.sub_elements), 2)  # VAR and METHOD
        method = next(e for e in element.sub_elements if e.type == "METHOD")
        self.assertEqual(method.name, "MyMethod")
        self.assertEqual(len(method.sub_elements), 1)  # VAR_INPUT
        
    def test_type_definition(self):
        """Test parsing of a TYPE definition"""
        text = """
TYPE MyStruct
    VAR
        field1 : INT;
        field2 : REAL;
    END_VAR
END_TYPE
"""
        element = parse_iec_element(text)
        self.assertEqual(element.type, "TYPE")
        self.assertEqual(element.name, "MyStruct")
        self.assertEqual(len(element.sub_elements), 1)
        
            
    def test_comments_before_elements(self):
        """Test that comments before elements are included in the element's segment"""
        text = """
(* Comment before function block *)
// Another comment
FUNCTION_BLOCK CommentedBlock
    a := 1;
END_FUNCTION_BLOCK
"""
        element = parse_iec_element(text)
        self.assertEqual(element.start_segment.start_line, 1)  # Should include the (* *) comment
        self.assertEqual(element.start_segment.end_line, 4)  # Should end after FUNCTION_BLOCK line
        
    def test_comments_before_var_sections(self):
        """Test that comments before VAR sections are included in their segment"""
        text = """
FUNCTION_BLOCK VarComments
    (* Comment before VAR section *)
    // Another comment
    VAR_INPUT
        x : INT;
    END_VAR
    
    (* Comment before second VAR *)
    VAR_OUTPUT
        y : INT;
    END_VAR
    
    x := 1;
END_FUNCTION_BLOCK
"""
        element = parse_iec_element(text)
        var_input = element.sub_elements[0]
        var_output = element.sub_elements[1]
        self.assertEqual(var_input.start_segment.start_line, 3)  # Should include first comment
        self.assertEqual(var_output.start_segment.start_line, 8)  # Should include second comment
        
    def test_comments_between_elements(self):
        """Test that comments between elements are handled correctly"""
        text = """
FUNCTION_BLOCK MethodComments
    VAR
        x : INT;
    END_VAR
    
    (* Comment before first method *)
    // Another comment
    METHOD Method1
        x := 1;
    END_METHOD
    
    (* Comment before second method *)
    METHOD Method2
        x := 2;
    END_METHOD
    
    (* This comment belongs to the body *)
    x := 3;
END_FUNCTION_BLOCK
"""
        element = parse_iec_element(text)
        methods = [e for e in element.sub_elements if e.type == "METHOD"]
        self.assertEqual(len(methods), 2)
        self.assertEqual(methods[0].start_segment.start_line, 6)  # Should include first method's comments
        self.assertEqual(methods[1].start_segment.start_line, 12)  # Should include second method's comments
        self.assertEqual(element.body_segment.start_line, 17)  # Body should start at its comment

    def test_inline_comments(self):
        """Test that inline comments are preserved in line counting"""
        text = """
FUNCTION_BLOCK InlineComments
    VAR_INPUT // Comment after VAR_INPUT
        x : INT; (* Comment after declaration *)
        y : REAL; // Another comment
    END_VAR (* Comment after END_VAR *)
    
    x := 1; // Comment after statement
END_FUNCTION_BLOCK
"""
        element = parse_iec_element(text)
        var_input = element.sub_elements[0]
        self.assertEqual(var_input.start_segment.start_line, 3)
        self.assertEqual(var_input.start_segment.end_line, 3)  # Should end on VAR_INPUT line
        self.assertEqual(var_input.body_segment.start_line, 4)  # Body starts at first declaration
        self.assertEqual(var_input.body_segment.end_line, 6)  # Body ends at END_VAR line

class TestTreeToText(unittest.TestCase):

    original_file_input = """\
FUNCTION_BLOCK MethodComments
    VAR
        x : INT;
    END_VAR
    
    (* Comment before first method *)
    // Another comment
    METHOD Method1
        x := 1;
    END_METHOD
    
    (* Comment before second method *)
    METHOD Method2
        x := 2;
    END_METHOD
    
    (* This comment belongs to the body *)
    x := 3;
END_FUNCTION_BLOCK
"""

    expected_tree = {
                        "children": [
                {
                    "type": "METHOD",
                    "name": "Method1",
                    "declaration": """\
    
    (* Comment before first method *)
    // Another comment
    METHOD Method1
""",
                    "children": [],
                    "implementation": """\
        x := 1;
    END_METHOD
"""
                },
                {
                    "type": "METHOD",
                    "name": "Method2",
                    "declaration": """\
    
    (* Comment before second method *)
    METHOD Method2
""",
                    "children": [],
                    "implementation": """\
        x := 2;
    END_METHOD
"""
                }
            ],
"type": "FUNCTION_BLOCK",
            "name": "MethodComments",
            "declaration": """\
FUNCTION_BLOCK MethodComments
    VAR
        x : INT;
    END_VAR
""",
            "implementation": """\
    
    (* This comment belongs to the body *)
    x := 3;
END_FUNCTION_BLOCK
"""
        }


    def assertMyDictEqual(self, d1, d2, msg=None, path=""):
        """Assert that two dictionaries are equal regardless of key order."""
        # Convert any non-dict values to dicts for nested comparison
        if isinstance(d1, dict) and isinstance(d2, dict):
            # Check keys match
            keys1, keys2 = set(d1.keys()), set(d2.keys())
            if keys1 != keys2:
                extra1 = keys1 - keys2
                extra2 = keys2 - keys1
                raise AssertionError(
                    "Keys don't match at path '%s'\n"
                    "Only in first dict: %s\n"
                    "Only in second dict: %s" % (path, extra1, extra2)
                )
            
            # Recursively compare values
            for k in d1:
                new_path = "%s.%s" % (path, k) if path else k
                self.assertMyDictEqual(d1[k], d2[k], path=new_path)
        elif isinstance(d1, str) and isinstance(d2, str):
            if d1 != d2:
                # Convert whitespace characters to visible symbols
                def visualize_whitespace(s):
                    return s.replace(' ', '·').replace('\t', '→').replace('\n', '↵\n')
                
                diff = list(difflib.ndiff(d1.splitlines(keepends=True), d2.splitlines(keepends=True)))
                visible_diff = [visualize_whitespace(line) for line in diff]
                raise AssertionError(
                    "String difference at path '%s':\n%s" % (path, ''.join(visible_diff))
                )
        else:
            # For non-dict, non-string values, do regular equality comparison
            if d1 != d2:
                raise AssertionError(
                    "Values don't match at path '%s'\n"
                    "First value: %s\n"
                    "Second value: %s" % (path, d1, d2)
                )

    def dump_iec_element(self, element, indent=0):
        """Print a readable representation of an IECElement."""
        indent_str = "  " * indent
        print("%sType: %s" % (indent_str, element.type))
        print("%sName: %s" % (indent_str, element.name))
        print("%sStart segment: %s" % (indent_str, element.start_segment))
        print("%sBody segment: %s" % (indent_str, element.body_segment))
        if element.sub_elements:
            print("%sSub elements:" % indent_str)
            for sub in element.sub_elements:
                self.dump_iec_element(sub, indent + 1)
        print()

    def test_text_to_tree(self):
        element = parse_iec_element(self.original_file_input)

        transformed_element = merge_var_sections(element)


        text_lines = self.original_file_input.splitlines(True)
        actual_tree = text_to_tree(transformed_element, text_lines)

        self.assertMyDictEqual(actual_tree, self.expected_tree)


    def test_element_tree_to_mock_me_tree_element(self):
        element = parse_iec_element(self.original_file_input)
        transformed_element = merge_var_sections(element)
        text_lines = self.original_file_input.splitlines(True)
        mocked_tree = create_mock_me_tree(transformed_element, text_lines)


    def test_tree_to_text(self):
        element = parse_iec_element(self.original_file_input)
        transformed_element = merge_var_sections(element)
        text_lines = self.original_file_input.splitlines(True)
        mocked_tree = create_mock_me_tree(transformed_element, text_lines)
        self.assertEqual(metree_dumps(mocked_tree), self.original_file_input)


def text_to_tree(element, text_lines):
    """Convert IECElement to dictionary representation."""
    declaration, implementation = get_declaration_and_implementation(element, text_lines)
    tree = {
        "type": element.type,
        "name": element.name,
        "declaration": ''.join(declaration),
        "children": [text_to_tree(sub, text_lines) for sub in element.sub_elements],
        "implementation": ''.join(implementation)
    }
    return tree

if __name__ == '__main__':
    unittest.main()