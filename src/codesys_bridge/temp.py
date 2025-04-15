a = {
    "children": [
        {
            "children": [],
            "name": "Method1",
            "implementation": "        x := 1;\n    END_METHOD\n",
            "type": "METHOD",
            "declaration": "    \n",
        },
        {
            "children": [],
            "name": "Method2",
            "implementation": "        x := 2;\n    END_METHOD\n",
            "type": "METHOD",
            "declaration": "    \n",
        },
    ],
    "name": "MethodComments",
    "implementation": "    \n    (* This comment belongs to the body *)\n    x := 3;\nEND_FUNCTION_BLOCK\n",
    "type": "FUNCTION_BLOCK",
    "declaration": "FUNCTION_BLOCK MethodComments\n    VAR\n        x : INT;\n    END_VAR\n",
}
b = {
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
""",
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
""",
        },
    ],
    "name": "MethodComments",
    "implementation": """\

    (* This comment belongs to the body *)
    x := 3;
END_FUNCTION_BLOCK
""",
    "type": "FUNCTION_BLOCK",
    "declaration": """\
FUNCTION_BLOCK MethodComments
    VAR
        x : INT;
    END_VAR
""",
}
