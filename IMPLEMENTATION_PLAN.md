The overall goal si to be able to develop by switching between Machine Expert and Visual Studio Code/Cursor.

Machine Expert has proprietary binary project format. Visual Studio Code/Cursor cannot read it at all. Machine Expert has a Python scripting API which can read and write the project.

To make the goal, we'll make synchronization between ME and folder / text files repo using the Python scription of ME.

we 'll have 2 tree sctructures:

1. folders and files
1. the ME project

It's possible to walk the ME project but it has some quirks. Hopefully we could export each leaf using export_xml or export_native. Each non-leaf node will be a folder with {name}.{type} as the name.
If there is more information needed than name and type to re-create the node on import/load we'll include and {name}.xml in file in the folder. (export with recursive=False). For leaf nodes with have
textual_delaration and/or textual_implementation we'll include them as {name}.iecst files (delimited by (*#-#-#-#-#-#-#-#-#-#-#-#-#*))

We have a rudimentary script to export ME project in src/codesys_bridge/export.py and to load the resulting folders/files format into an empty ME project in src/codesys_bridge/load.py

Minimal goals set:
A. Non iecst text declarations and implementation would be maintained in the ME project and not changed by the scripts.
1\. export from ME to folder/file structure
2\. make changes in iecst files using Cursor/AI
3\. synchronize changes back to ME project
B. All of the above + making it quick
C. All of the above + ability to cooperate via git for all the aspects of the development (also non iecst)

I'm sceptical of the quality and completness and strategy of the export.py/load.py scripts.

Let's export in iecst format the leaf nodes with textual declaration/implementation and on import let's replace all nodes which have from folder/file structure. The leaf textual nodes from ME projects which don't have iecst files will be deleted.

# chunking, parsing, roundtripping
Our goal is to be able to parse and roundtrip structured text between 2 representations: 
    * file
    * A tree of Python objects (dicts, or special classes)

Each level of the Python tree has "declaration" and "implementation" and children (which are of the same type).

The most demanding and nested case is:
```
(* comment 1 *)
FUNCTION_BLOCK FB_A // comment 2
    VAR_INPUT
        i: INT;
    END_VAR
    METHOD M1 // comment 3
        VAR_INPUT
        END_VAR
        j:= 2;
    END_METHOD
    IF TRUE THEN
        1;
    END_IF
    (* comment 4 *)
END_FUNCTION_BLOCK
```

This should be parsed into:
```
{   "type": "FUNCTION_BLOCK",
    "name": "FB_A",
    "declaration": """\
(* comment 1 *)
FUNCTION_BLOCK FB_A // comment 2
""",
    "implementation": """\
    IF TRUE THEN
        1;
    END_IF
   (* comment 4 *)
""",
    "children": [
        {
            "type": "METHOD",
            "name": "M1",
            "declaration": "METHOD M1 // comment 3\n",
            "implementation": "j:= 2;\n",
            "children": []
        }
    ]
}
```

## Implementation details:
1. this needs to be pure python and I think to make it fast I would use regexes to find all the "delimiters" which will be used to split the file into chunks.
1. VAR_* TO END_VAR is optional. It is a part of declaration and concludes it. However, if it is not present, the declaration is concluded with the line `FUNCTION_BLOCK FB_A.`
1. We should probably have a simple debugging printout to see the chunks.
1. The "parser" (code which processes delimiter flas list to a tree) worries me the most. In previous attempts it becase quite complicated. Let's try to come up with minimal set of rules (ifs and rules about what line is the end of declaration/implementation) to cover all the cases. In the worst case we can create logical tree with VAR_*/END_VAR in the structure and then do another pass to merge FUNCTION_BLOCK <name> and VAR_*/END_VAR elements into one leaf. I think we should track line number and column number in the chunking as well as in the parsing phase. We don't need to track the actual content in the tree, just pointer (either position in the file or line,column or both.)
1. I think we should have one regular expression which will detect all interesting elements, opening as well as closing:

* FUNCTION_BLOCK <name>
* FUNCTION <name>
* INTERFACE <name>
* PROGRAM <name>
* TYPE <name>
* METHOD <name>
* ACTION <name>
* VAR_GLOBAL
* VAR_INPUT
* VAR_OUTPUT
* VAR_TEMP
* VAR_IN_OUT
* END_FUNCTION_BLOCK
* END_FUNCTION
* END_INTERFACE
* END_TYPE
* END_PROGRAM
* END_VAR
* END_METHOD
* END_ACTION


Having the position of all of these elements then we'll work on getting Machine Expert "declaration" and "implementation".

All lines which are in between and end of previous element and start of next element belong to the next element.
Declaration ends with last END_VAR.

Implementation ends with last END_{IECELEMENT}.

Methods and Actions are children of their FUNCTION_BLOCK or INTERFACE.

We should create 


## Reading the leaves with either textual declaration or textual implementation
Machine Expert has a hierarchy of classes (ScriptObject -> ScriptTreeObject, ScriptTextDocument, ScriptTextualObjectMarker etc... see the dir scriptengine) which have:
get_children
get_name
@property has_textual_declaration
@property has_textual_implementation
@property type

## writing the leaves with either textual declaration or textual implementation
In the folder/file structure the first level below are leaves (files).
In the ME project, the hiararchy continues to be distinguished and has to be created object by object:

create_dut - I think by calling textual_declaration.replace(new_text), the type will change to correct (STRUCT, ENUM, UNION)
create_pou(name, PouType.FUNCTION_BLOCK)
        create_method(name)
        create_action(name)
create_pou(name, PouType.INTERFACE)
        create_method(name)
        create_action(name)
create_pou(name, PouType.FUNCTION)
create_pou(name, PouType.PROGRAM)
create_gvl(name)

### syncing
Means, if the ME project has a object with a given name, it should be replaced. If it doesn't have it, it should be created. If there are objects which have textual_declaration or textual_implementation, they should be deleted and don't exist in the file/folder structure.
    

# TODOvelone

I now have a python tree structure. the creation of that I'll transfrom to create text_lines and MockMETreeElement....
Along with changing the methods which can dump file content.





ME project_tree to folder/file structure
folder/file structure to ME project_tree

good intermediate formats to avoid having all the machinery of ME in tests:
class TextualRepresentation(object):
    def __init__(self, text):
        self.text = text

class METreeElement(object):
    def __init__(self, textual_declaration, textual_implementation, children, type, name):
        self.textual_declaration = TextualRepresentation(textual_declaration)
        self.textual_implementation = TextualRepresentation(textual_implementation) 
        self.children = children
        self.type = type
        self.name = name


    def get_children(self): # -> list of METreeElement
        return self.children


    def get_name(self): # str
        return self.name

    def get_declaration(self): # -> TextualRepresentation
        return self.textual_declaration


    def get_implementation(self): # -> TextualRepresentation
        return self.textual_implementation


from folder/file structure I'll need create_dut, create_fb and deleting correct notes, whhile leaving navigating the rest. for dump, we can mimic the necessary functions using the classes above (as intermdiate). To test roundtirp, 
we have to decide:



## old
From each *.iecst file we'll need these info:
* type, one of:
        'fb': (r'\bFUNCTION_BLOCK\s+(?P<name>\w+)', r'END_VAR', r'END_FUNCTION_BLOCK'),
        'function': (r'\bFUNCTION\s+(?P<name>\w+)', r'END_VAR', r'END_FUNCTION'),
        'interface': (r'\bINTERFACE\s+(?P<name>\w+)', r'END_VAR', None),
        'struct': (r'\bTYPE\s+(?P<name>\w+)\s*:\s*STRUCT\b', r'END_TYPE', None),
        'union': (r'\bTYPE\s+(?P<name>\w+)\s*:\s*UNION\b', r'END_TYPE', None),
        'enum': (r'\bTYPE\s+(?P<name>\w+)\s*:\s*\(\s*\w+\s*:=\s*\d+', r'END_TYPE', None),
        'program': (r'\bPROGRAM\s+(?P<name>\w+)', r'END_VAR', r'END_PROGRAM'),
        'gvl': (r'\bVAR_GLOBAL\s+(?P<name>\w+)', r'END_VAR', None),
        'method': (r'\bMETHOD\s+(?P<name>\w+)', r'END_VAR', r'END_METHOD'),
        'action': (r'\bACTION\s+(?P<name>\w+)', r'', r'END_ACTION'), # TODO
* line where declaration ends. (implementation starts at the next line). implementation ends at the end of file or on line before END_{IECELEMENT} 




