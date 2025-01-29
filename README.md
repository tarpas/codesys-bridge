# CodeSys Bridge Script Installer

This tool installs the CodeSys Bridge Script into SE Machine Expert installs and into CodeSys installs.

## Installation

1. Run `codesys_script_install.py` with administrator privileges
   - The script will automatically request elevation if needed
   - Windows UAC prompt will appear for confirmation

2. The installer will:
   - Install into the CodeSys Script Commands directory
   - Automatically detect all installed SE Machine Expert V2.x versions

   - Copy required assets (icons)
   - Create or update the configuration files

## What Gets Installed

The installer adds the following to each installation:
- `git.ico` - Icon file for the script command
- Updates to `config.json` - Adds or updates the CodeSys Bridge Script entry
- Reference to `codesys_bridge_script.py` - The main bridge script

## Requirements

- Windows operating system
- Administrator privileges (for SE Machine Expert installations)
- EcoStruxure Machine Expert V2.x and/or CodeSys 3.5.x installed


## Notes

- The script will automatically install to all detected V2.x versions
- Existing installations will be updated if already present
- The installation is non-destructive and will preserve other script commands
