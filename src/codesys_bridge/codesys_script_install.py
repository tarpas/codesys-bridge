import os
import sys
import ctypes
import shutil
import json
import glob

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def get_installation_directories():
    """Returns a list of all Script Commands directories where we need to install"""
    directories = []
    
    # Get CODESYS directories
    codesys_base = os.path.join(os.environ.get('PROGRAMFILES', 'C:\\Program Files'), 'CODESYS 3.5')
    codesys_dirs = glob.glob(os.path.join(os.path.dirname(codesys_base), 'CODESYS 3.5.*'))
    for codesys_dir in codesys_dirs:
        directories.append(os.path.join(codesys_dir, 'CODESYS', 'Script Commands'))
    
    # Get SE Machine Expert directories
    se_base_dir = os.path.join(
        os.environ.get('PROGRAMFILES', 'C:\\Program Files'),
        'Schneider Electric',
        'EcoStruxure Machine Expert'
    )
    v2_dirs = glob.glob(os.path.join(se_base_dir, 'V2.*'))
    for v2_dir in v2_dirs:
        directories.append(os.path.join(v2_dir, 'LogicBuilder', 'Script Commands'))
    
    return directories

def install_to_directory(path, config_entry, is_codesys=False):
    """Install config and assets to a single directory"""
    print(f"\nInstalling to: {path}")
    
    # Create directory (recursive)
    os.makedirs(path, exist_ok=True)
    
    # Copy icon
    current_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(current_dir, 'assets', 'export_icon.ico')
    shutil.copy2(icon_path, os.path.join(path, 'export_icon.ico'))
    print(f"Copied export_icon.ico to {path}")
    
    # For CODESYS, copy the script file to the destination
    script_path = os.path.join(current_dir, 'cs_export.py')
    if is_codesys:
        shutil.copy2(script_path, os.path.join(path, 'cs_export.py'))
        print(f"Copied cs_export.py to {path}")
        config_entry["Path"] = 'cs_export.py'  # Just the filename for CODESYS
    else:
        # For Machine Expert, use the original script location
        config_entry["Path"] = script_path
    
    # Update or create config.json
    config_dest = os.path.join(path, 'config.json')
    if os.path.exists(config_dest):
        with open(config_dest, 'r') as f:
            config = json.load(f)
        
        # Update or add Git Support entry
        for i, entry in enumerate(config):
            if entry.get('Name') == "CodeSys Bridge Script":
                config[i] = config_entry
                print(f"Updated existing CodeSys Bridge Script entry in config.json")
                break
        else:
            config.append(config_entry)
            print(f"Added CodeSys Bridge Script entry to config.json")
    else:
        config = [config_entry]
        print(f"Created new config.json with CodeSys Bridge Script entry")
    
    with open(config_dest, 'w') as f:
        json.dump(config, f, indent=4)

def copy_to_script_commands():
    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Prepare our config entry
    git_support_entry = {
        "Name": "CodeSys Bridge Script",
        "Desc": "CodeSys Bridge Script",
        "Icon": "export_icon.ico",
        "Path": ""  # Will be set in install_to_directory
    }
    
    # Get all installation directories
    directories = get_installation_directories()
    
    if not directories:
        print("No installation directories found!")
        return
    
    # Install to each directory
    for directory in directories:
        # Check if this is a CODESYS directory
        is_codesys = 'CODESYS' in directory
        install_to_directory(directory, git_support_entry.copy(), is_codesys)

def main():
    if not is_admin():
        # ShellExecuteW returns an HINSTANCE (int) > 32 if successful
        result = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.argv[0], " ".join(sys.argv), None, 1)
        if result <= 32:  # Error codes are <= 32
            error_messages = {
                2: "File not found",
                5: "Access denied",
            }
            error_msg = error_messages.get(result, f"Ereror code ({result})")
            print(f"Failed to run {sys.argv[0]}: {error_msg}")
            sys.exit(1)
        sys.exit(0)
    
    try:
        copy_to_script_commands()
        print("Successfully installed script commands and assets")
    except Exception as e:
        import traceback
        print(f"Error during installation: {e}")
        traceback.print_exc()
        
        input("Press Enter to exit...")


if __name__ == "__main__":
    main() 