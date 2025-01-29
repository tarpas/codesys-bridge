# CodeSys Bridge Script Installer

This tool installs the CodeSys Bridge Script into SE Machine Expert installs and into CodeSys installs.

## Installation

1. Run `codesys_script_install.py` with administrator privileges
   - The script will automatically request elevation if needed
   - Windows UAC prompt will appear for confirmation

2. The installer will:
   - Automatically detect all installed EcoStruxure Machine Expert V2.x versions
   - Install the bridge script into each version's Script Commands directory
   - Copy required assets (icons)
   - Create or update the configuration files

## What Gets Installed

The installer adds the following to each detected V2.x installation:
- `git.ico` - Icon file for the script command
- Updates to `config.json` - Adds or updates the CodeSys Bridge Script entry
- Reference to `codesys_bridge_script.py` - The main bridge script

## Installation Locations

The script installs to all detected versions at:

## Requirements

- Windows operating system
- Administrator privileges
- EcoStruxure Machine Expert V2.x installed

## Troubleshooting

If you encounter any errors during installation:
1. Ensure you have administrator privileges
2. Verify that EcoStruxure Machine Expert is installed
3. Check the error message displayed by the installer
4. Press Enter to exit if an error occurs

## Notes

- The script will automatically install to all detected V2.x versions
- Existing installations will be updated if already present
- The installation is non-destructive and will preserve other script commands
