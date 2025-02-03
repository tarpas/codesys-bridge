import unittest
from new_parser import parse_iec_element, IECElement
from collections import namedtuple

LineSegment = namedtuple('LineSegment', ['start_line', 'end_line'])

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
        self.assertEqual(element.start_segment.start_line, 1)  # Line numbers are 1-based
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
        
    def test_expected_type_validation(self):
        """Test that expected_type validation works"""
        text = "FUNCTION_BLOCK MyBlock\nEND_FUNCTION_BLOCK"
        with self.assertRaises(ValueError):
            parse_iec_element(text, expected_type="FUNCTION")
            
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

if __name__ == '__main__':
    unittest.main() 