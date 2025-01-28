import os
import sys
import ctypes
import shutil
import json

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def copy_to_script_commands():
    # Define target directory
    v2_script_commands = os.path.join(
        os.environ.get('PROGRAMFILES', 'C:\\Program Files'),
        'Schneider Electric',
        'EcoStruxure Machine Expert',
        'V2.1',
        'LogicBuilder',
        'Script Commands'
    )
    
    # Ensure directory exists
    os.makedirs(v2_script_commands, exist_ok=True)
    
    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Copy icon
    icon_path = os.path.join(current_dir, 'assets', 'git.ico')
    if os.path.exists(icon_path):
        shutil.copy2(icon_path, os.path.join(v2_script_commands, 'git.ico'))
        print("Copied git.ico to Script Commands directory")
    
    # Prepare our config entry
    git_support_entry = {
        "Name": "Git Support",
        "Desc": "Git integration tools",
        "Icon": "git.ico",
        "Path": os.path.abspath(os.path.join(current_dir, 'git_support.py'))
    }
    
    # Update or create config.json
    config_dest = os.path.join(v2_script_commands, 'config.json')
    if os.path.exists(config_dest):
        with open(config_dest, 'r') as f:
            config = json.load(f)
            
        # Update or add Git Support entry
        for i, entry in enumerate(config):
            if entry.get('Name') == "Git Support":
                config[i] = git_support_entry
                print("Updated existing Git Support entry in config.json")
                break
        else:
            config.append(git_support_entry)
            print("Added Git Support entry to config.json")
    else:
        config = [git_support_entry]  # config is a list
        print("Created new config.json with Git Support entry")
    
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