import os
import sys
import ctypes
import shutil
import json
from pathlib import Path

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def copy_to_script_commands():
    # Define target directories
    program_files = os.environ.get('PROGRAMFILES', 'C:\\Program Files')
    base_path = os.environ.get('PROGRAMFILES', 'C:\\Program Files')
    v2_script_commands = os.path.join(base_path, 'Schneider Electric', 'EcoStruxure Machine Expert', 'V2.1', 'LogicBuilder', 'Script Commands')
    
    # Ensure directories exist
    for directory in [v2_script_commands]:
        os.makedirs(directory, exist_ok=True)
    
    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(current_dir, 'assets')
    
    # Copy icon only
    files_to_copy = {
        'git.ico': 'git.ico',
    }
    
    for source_file, dest_file in files_to_copy.items():
        source_path = os.path.join(assets_dir, source_file)
        if os.path.exists(source_path):
            shutil.copy2(source_path, os.path.join(v2_script_commands, dest_file))
            print(f"Copied {source_file} to Script Commands directory")
    
    # Update config.json with script paths
    config_template_path = os.path.join(assets_dir, 'config.json')
    if os.path.exists(config_template_path):
        with open(config_template_path, 'r') as f:
            config = json.load(f)
        
        # Update path in config for "Git Support" entry
        for entry in config:
            if entry.get('Name') == "Git Support":
                entry['Path'] = os.path.abspath(os.path.join(current_dir, 'git_support.py'))
                break
        
        # Write updated config
        config_dest = os.path.join(v2_script_commands, 'config.json')
        with open(config_dest, 'w') as f:
            json.dump(config, f, indent=4)
        print("Updated config.json with script paths")

def main():
    if not is_admin():
        # Re-run the program with admin rights
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