"""\
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

expected = { "type":"FUNCTION_BLOCK", "name": "MethodComments", "declaration": """\
FUNCTION_BLOCK MethodComments
    VAR
        x : INT;
    END_VAR
""", "children": [ {"type": "METHOD", "name": "Method1", "declaration": """\
    
    (* Comment before first method *)
    // Another comment
    METHOD Method1
""", "children": [], "implementation": """\
        x := 1;
    END_METHOD
"""}, {"type": "METHOD", "name": "Method2", "declaration": """\
    
    (* Comment before second method *)
    METHOD Method2
""", "children" : [], "implementation": """\
        x := 2;
    END_METHOD
""",}], "implementation": """\

    (* This comment belongs to the body *)
    x := 3;
END_FUNCTION_BLOCK
"""}
