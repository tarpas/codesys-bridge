# CodeSys Text Export

This tool exports Structured Text (ST) source code from a CodeSys/Machine Expert project with these key features:

1. Creates a directory structure matching the project structure
2. Each ST element (Programs, Function Blocks, Functions, etc.) gets exported to `.st` files
3. For Function Blocks and Interfaces, all their sub-elements (methods, actions, properties) are kept together in the same file

For example, a Function Block called `FB_Motor` with methods and actions would be exported to a single `FB_Motor.st` file like this:

```
FUNCTION_BLOCK FB_Motor
VAR_INPUT
    Enable : BOOL;
    Speed : REAL;
END_VAR

VAR
    isRunning : BOOL;
    currentSpeed : REAL;
END_VAR

    METHOD Start
    VAR_INPUT
        acceleration : REAL;
    END_VAR
        isRunning := TRUE;
        currentSpeed := Speed * acceleration;
    END_METHOD

    METHOD Stop
        isRunning := FALSE;
        currentSpeed := 0;
    END_METHOD

    ACTION Update
        IF isRunning THEN
            // Update motor logic
            currentSpeed := Speed;
        END_IF
    END_ACTION

END_FUNCTION_BLOCK
```

## Installation

1. If your Windows doesn't have python3.9 or higher installed, install it from Microsoft Store/[python.org](https://python.org) or any other source.

2. Open Command Prompt or PowerShell as administrator
   - Right-click on Command Prompt/PowerShell and select "Run as administrator"
   - Windows UAC prompt will appear for confirmation

3. Install the CodeSys Bridge package:
   ```
   pip install codesys-bridge
   ```

4. Run the bridge installation:
   ```
   codesys-bridge
   ```

The installer will:
- Install into the CodeSys Script Commands directory
- Automatically detect all installed SE Machine Expert V2.x versions
- Create or update the configuration files

You have to restart CodeSys/ME after installation for the script icon to appear. 
"Text Export" should become visible in Tools -> Scripting menu.

## What Gets Installed

The installer adds the following to each installation:
- Updates to `config.json` - Adds or updates the CodeSys Bridge Script entry
- Reference to `cs_export.py` - The main bridge script


## Surfacing icon for Text Export
After that you should look for the new icon and add it to your toolbar.

Go to Tools -> Customize -> Add Command -> ScriptEngine Commands -> Text Export

![image](https://raw.githubusercontent.com/tarpas/codesys-bridge/refs/heads/main/pngs/step1.png)

![image](https://raw.githubusercontent.com/tarpas/codesys-bridge/refs/heads/main/pngs/step2.png)

![image](https://raw.githubusercontent.com/tarpas/codesys-bridge/refs/heads/main/pngs/step3.png)




## Requirements

- Windows operating system
- Python 3.9 or higher
- Administrator privileges (for SE Machine Expert installations)
- EcoStruxure Machine Expert V2.x and/or CodeSys 3.5.x installed

## Notes

- The script will automatically install to all detected V2.x versions
- Existing installations will be updated if already present
- The installation is non-destructive and will preserve other script commands
