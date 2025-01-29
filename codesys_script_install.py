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
        directories.append(os.path.join(codesys_dir, 'Script Commands'))
    
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

def install_to_directory(path, git_support_entry):
    """Install config and assets to a single directory"""
    print(f"\nInstalling to: {path}")
    
    # Create directory (recursive)
    os.makedirs(path, exist_ok=True)
    
    # Copy icon
    current_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(current_dir, 'assets', 'git.ico')
    if os.path.exists(icon_path):
        shutil.copy2(icon_path, os.path.join(path, 'git.ico'))
        print(f"Copied git.ico to {path}")
    
    # Update or create config.json
    config_dest = os.path.join(path, 'config.json')
    if os.path.exists(config_dest):
        with open(config_dest, 'r') as f:
            config = json.load(f)
        
        # Update or add Git Support entry
        for i, entry in enumerate(config):
            if entry.get('Name') == "CodeSys Bridge Script":
                config[i] = git_support_entry
                print(f"Updated existing CodeSys Bridge Script entry in config.json")
                break
        else:
            config.append(git_support_entry)
            print(f"Added CodeSys Bridge Script entry to config.json")
    else:
        config = [git_support_entry]
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
        "Icon": "git.ico",
        "Path": os.path.abspath(os.path.join(current_dir, 'codesys_bridge_script.py'))
    }
    
    # Get all installation directories
    directories = get_installation_directories()
    
    if not directories:
        print("No installation directories found!")
        return
    
    # Install to each directory
    for directory in directories:
        install_to_directory(directory, git_support_entry)

def main():
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        return
    
    try:
        copy_to_script_commands()
        print("Successfully installed script commands and assets")
    except Exception as e:
        print(f"Error during installation: {e}")
    
    input("Press Enter to exit...")

if __name__ == "__main__":
    main() 