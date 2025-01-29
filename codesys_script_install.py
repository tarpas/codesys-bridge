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

def copy_to_script_commands():
    # Define base directory
    base_dir = os.path.join(
        os.environ.get('PROGRAMFILES', 'C:\\Program Files'),
        'Schneider Electric',
        'EcoStruxure Machine Expert'
    )
    
    # Find all V2.x directories
    v2_dirs = glob.glob(os.path.join(base_dir, 'V2.*'))
    
    if not v2_dirs:
        print("No V2.x directories found in", base_dir)
        return
    
    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Prepare our config entry
    git_support_entry = {
        "Name": "CodeSys Bridge Script",
        "Desc": "CodeSys Bridge Script",
        "Icon": "git.ico",
        "Path": os.path.abspath(os.path.join(current_dir, 'codesys_bridge_script.py'))
    }
    
    # Install to each V2.x directory
    for v2_dir in v2_dirs:
        script_commands_dir = os.path.join(v2_dir, 'LogicBuilder', 'Script Commands')
        
        # Ensure directory exists
        os.makedirs(script_commands_dir, exist_ok=True)
        
        # Copy icon
        icon_path = os.path.join(current_dir, 'assets', 'git.ico')
        if os.path.exists(icon_path):
            shutil.copy2(icon_path, os.path.join(script_commands_dir, 'git.ico'))
            print(f"Copied git.ico to Script Commands directory in {v2_dir}")
        
        # Update or create config.json
        config_dest = os.path.join(script_commands_dir, 'config.json')
        if os.path.exists(config_dest):
            with open(config_dest, 'r') as f:
                config = json.load(f)
                
            # Update or add Git Support entry
            for i, entry in enumerate(config):
                if entry.get('Name') == "CodeSys Bridge Script":
                    config[i] = git_support_entry
                    print(f"Updated existing CodeSys Bridge Script entry in config.json in {v2_dir}")
                    break
            else:
                config.append(git_support_entry)
                print(f"Added CodeSys Bridge Script entry to config.json in {v2_dir}")
        else:
            config = [git_support_entry]  # config is a list
            print(f"Created new config.json with CodeSys Bridge Script entry in {v2_dir}")
        
        with open(config_dest, 'w') as f:
            json.dump(config, f, indent=4)

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