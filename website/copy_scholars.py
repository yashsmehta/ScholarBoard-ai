import os
import shutil
from pathlib import Path

def copy_scholars():
    """
    Copy scholars.json, markdown files, and profile pictures from the data directory to the website data directory.
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
    
    # Create website/data/scholar_markdown directory if it doesn't exist
    website_markdown_dir = website_data_dir / 'scholar_markdown'
    os.makedirs(website_markdown_dir, exist_ok=True)
    
    # Copy markdown files from data/scholar_markdown to website/data/scholar_markdown
    source_markdown_dir = data_dir / 'scholar_markdown'
    if source_markdown_dir.exists():
        print(f"Copying markdown files from {source_markdown_dir} to {website_markdown_dir}")
        for filename in os.listdir(source_markdown_dir):
            if filename.endswith('.md'):
                source_file = source_markdown_dir / filename
                dest_file = website_markdown_dir / filename
                
                # Only copy if the source file is newer or the destination doesn't exist
                if not dest_file.exists() or os.path.getmtime(source_file) > os.path.getmtime(dest_file):
                    shutil.copy2(source_file, dest_file)
        print(f"Copied {len(os.listdir(source_markdown_dir))} markdown files")
    else:
        print(f"Warning: scholar_markdown directory not found at {source_markdown_dir}")
    
    # Create website/data/profile_pics directory if it doesn't exist
    website_profile_pics_dir = website_data_dir / 'profile_pics'
    os.makedirs(website_profile_pics_dir, exist_ok=True)
    
    # Copy profile pictures from data/profile_pics to website/data/profile_pics
    source_profile_pics_dir = data_dir / 'profile_pics'
    if source_profile_pics_dir.exists():
        print(f"Copying profile pictures from {source_profile_pics_dir} to {website_profile_pics_dir}")
        copied_count = 0
        for filename in os.listdir(source_profile_pics_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                source_file = source_profile_pics_dir / filename
                dest_file = website_profile_pics_dir / filename
                
                # Only copy if the source file is newer or the destination doesn't exist
                if not dest_file.exists() or os.path.getmtime(source_file) > os.path.getmtime(dest_file):
                    shutil.copy2(source_file, dest_file)
                    copied_count += 1
        print(f"Copied {copied_count} profile pictures")
    else:
        print(f"Warning: profile_pics directory not found at {source_profile_pics_dir}")
    
    print("Copy complete!")

if __name__ == "__main__":
    copy_scholars() 