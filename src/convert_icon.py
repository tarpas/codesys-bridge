from PIL import Image
import os

def convert_png_to_ico(input_path, output_path, size=(16, 16)):
    # Open the PNG image
    with Image.open(input_path) as img:
        # Convert to RGBA if not already
        img = img.convert('RGBA')
        # Resize the image
        img = img.resize(size, Image.Resampling.LANCZOS)
        # Save as ICO
        img.save(output_path, format='ICO')

if __name__ == '__main__':
    # Get the workspace directory (where the script is run from)
    workspace_dir = os.getcwd()
    
    # Define input and output paths
    input_path = os.path.join(workspace_dir, 'export_icon.png')
    output_path = os.path.join(workspace_dir, 'export_icon.ico')
    
    # Convert the image
    convert_png_to_ico(input_path, output_path)
    print(f"Converted {input_path} to {output_path}") 