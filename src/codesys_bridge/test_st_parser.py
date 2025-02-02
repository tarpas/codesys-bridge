# encoding: utf-8
from __future__ import print_function
import unittest
from st_parser import parse_iec_element, remove_comments_and_strings_for_parsing

class TestSTParser(unittest.TestCase):
    def setUp(self):
        # Test samples that will be used across multiple tests
        self.samples = {
            'fb': """
    (* Function Block Example *)
    FUNCTION_BLOCK FB_Motor
        VAR_INPUT
            Speed : REAL; // Speed setpoint
            Enable : BOOL; (* Enable motor *)
        END_VAR
        
        METHOD Start : BOOL
            VAR_INPUT
                InitialSpeed : REAL;
            END_VAR
            Speed := InitialSpeed;
        END_METHOD
        
        ACTION Stop
            Speed := 0;
        END_ACTION
        
        IF Enable THEN
            Speed := 10.0;
        END_IF
    END_FUNCTION_BLOCK
    """,
            'interface': """
    INTERFACE IController
        METHOD Start : BOOL
            VAR_INPUT
                Speed : REAL;
            END_VAR
        END_METHOD
        
        METHOD Stop : BOOL
        END_METHOD
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
    """,
            'gvl': """
    VAR_GLOBAL MyGlobalVars
        Speed : REAL;
        Enable : BOOL;
    END_VAR
    """,
            'union': """
    TYPE U_Data :
    UNION
        intVal : INT;
        realVal : REAL;
        timeVal : TIME;
    END_UNION
    END_TYPE
    """
        }
    
    def test_function_block_parsing(self):
        """Test parsing of function blocks with methods and actions"""
        element = parse_iec_element(self.samples['fb'])
        self.assertEqual(element.type, 'fb')
        self.assertEqual(element.name, 'FB_Motor')
        self.assertTrue('Speed : REAL' in element.declaration)
        self.assertTrue('Enable : BOOL' in element.declaration)
        self.assertTrue('Speed := 10.0' in element.implementation)
        
        # Test methods
        self.assertEqual(len(element.methods), 1)
        method = element.methods[0]
        self.assertEqual(method.name, 'Start')
        self.assertTrue('InitialSpeed : REAL' in method.declaration)
        self.assertTrue('Speed := InitialSpeed' in method.implementation)
        
        # Test actions
        self.assertEqual(len(element.actions), 1)
        action = element.actions[0]
        self.assertEqual(action.name, 'Stop')
        self.assertTrue('Speed := 0' in action.implementation)
    
    def test_interface_parsing(self):
        """Test parsing of interfaces with methods"""
        element = parse_iec_element(self.samples['interface'])
        self.assertEqual(element.type, 'interface')
        self.assertEqual(element.name, 'IController')
        self.assertEqual(len(element.methods), 2)
        self.assertEqual(element.methods[0].name, 'Start')
        self.assertEqual(element.methods[1].name, 'Stop')
    
    def test_function_parsing(self):
        """Test parsing of functions"""
        element = parse_iec_element(self.samples['function'])
        self.assertEqual(element.type, 'function')
        self.assertEqual(element.name, 'Add')
        self.assertTrue('VAR_INPUT' in element.declaration)
        self.assertTrue('Add := a + b' in element.implementation)
    
    def test_struct_parsing(self):
        """Test parsing of struct types"""
        element = parse_iec_element(self.samples['struct'])
        self.assertEqual(element.type, 'struct')
        self.assertEqual(element.name, 'ST_Point')
        self.assertTrue('x : REAL' in element.declaration)
        self.assertTrue('y : REAL' in element.declaration)
        self.assertTrue('z : REAL' in element.declaration)
        self.assertEqual(element.implementation, '')
    
    def test_enum_parsing(self):
        """Test parsing of enum types"""
        element = parse_iec_element(self.samples['enum'])
        self.assertEqual(element.type, 'enum')
        self.assertEqual(element.name, 'E_Colors')
        self.assertTrue('Red := 0' in element.declaration)
        self.assertTrue('Green := 1' in element.declaration)
        self.assertTrue('Blue := 2' in element.declaration)
        self.assertEqual(element.implementation, '')
    
    def test_union_parsing(self):
        """Test parsing of union types"""
        element = parse_iec_element(self.samples['union'])
        self.assertEqual(element.type, 'union')
        self.assertEqual(element.name, 'U_Data')
        self.assertTrue('intVal : INT' in element.declaration)
        self.assertTrue('realVal : REAL' in element.declaration)
        self.assertTrue('timeVal : TIME' in element.declaration)
        self.assertEqual(element.implementation, '')
    
    def test_gvl_parsing(self):
        """Test parsing of global variable lists"""
        element = parse_iec_element(self.samples['gvl'])
        self.assertEqual(element.type, 'gvl')
        self.assertEqual(element.name, 'MyGlobalVars')
        self.assertTrue('Speed : REAL' in element.declaration)
        self.assertTrue('Enable : BOOL' in element.declaration)
        self.assertEqual(element.implementation, '')
    
    def test_comment_handling(self):
        """Test that comments are preserved but don't interfere with parsing"""
        text = """
        (* This is a block comment *)
        // This is a line comment
        FUNCTION_BLOCK FB_Test // Comment after declaration
            VAR_INPUT
                x : INT; (* Comment in var section *)
            END_VAR
        END_FUNCTION_BLOCK
        """
        element = parse_iec_element(text)
        self.assertEqual(element.type, 'fb')
        self.assertEqual(element.name, 'FB_Test')
        self.assertTrue('(* This is a block comment *)' in element.declaration)
        self.assertTrue('// This is a line comment' in element.declaration)
        self.assertTrue('(* Comment in var section *)' in element.declaration)
    
    def test_string_handling(self):
        """Test that strings don't interfere with parsing"""
        text = """
        FUNCTION_BLOCK FB_Test
            VAR
                msg1 : STRING := 'FUNCTION_BLOCK should not be parsed';
                msg2 : STRING := "METHOD should not be parsed";
            END_VAR
        END_FUNCTION_BLOCK
        """
        element = parse_iec_element(text)
        self.assertEqual(element.type, 'fb')
        self.assertEqual(element.name, 'FB_Test')
        self.assertTrue("'FUNCTION_BLOCK should not be parsed'" in element.declaration)
        self.assertTrue('"METHOD should not be parsed"' in element.declaration)
    
    def test_auto_type_detection(self):
        """Test that element type is correctly auto-detected"""
        for type_name, sample in self.samples.items():
            element = parse_iec_element(sample)
            self.assertEqual(element.type, type_name)

if __name__ == '__main__':
    unittest.main() 