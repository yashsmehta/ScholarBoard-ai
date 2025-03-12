import os
import shutil
from pathlib import Path

def copy_scholars():
    """
    Copy scholars.json from the data directory to the website data directory.
    """
    # Get the parent directory (project root)
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = Path(parent_dir) / 'data'
    website_data_dir = Path(os.path.abspath(__file__)).parent / 'data'
    
    # Create website data directory if it doesn't exist
    os.makedirs(website_data_dir, exist_ok=True)
    
    # Copy scholars.json
    scholars_file = data_dir / 'scholars.json'
    if scholars_file.exists():
        shutil.copy(scholars_file, website_data_dir / 'scholars.json')
        print(f"Copied scholars.json to {website_data_dir}")
    else:
        print(f"Warning: scholars.json not found at {scholars_file}")
    
    print("Copy complete!")

if __name__ == "__main__":
    copy_scholars() 