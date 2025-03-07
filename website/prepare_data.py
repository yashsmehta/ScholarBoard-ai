import numpy as np
import json
import os
import shutil
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import random
import xarray as xr

# Add the scholar_board directory to the path so we can import from it
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scholar_board.search_embeddings import find_similar_scholars

def create_placeholder_image():
    """Create a placeholder image for scholars without profile pictures"""
    # Create a directory for images if it doesn't exist
    os.makedirs('website/images', exist_ok=True)
    
    # Create a 200x200 image with a blue background
    img = Image.new('RGB', (200, 200), color=(74, 111, 165))
    draw = ImageDraw.Draw(img)
    
    # Draw a circle in the center
    center = (100, 100)
    radius = 70
    draw.ellipse((center[0] - radius, center[1] - radius, 
                  center[0] + radius, center[1] + radius), 
                 fill=(255, 255, 255))
    
    # Draw a silhouette
    draw.ellipse((center[0] - 30, center[1] - 50, 
                  center[0] + 30, center[1] + 10), 
                 fill=(200, 200, 200))
    draw.rectangle((center[0] - 50, center[1] + 10, 
                   center[0] + 50, center[1] + 80), 
                  fill=(200, 200, 200))
    
    # Save the image
    img.save('website/images/placeholder.jpg')
    print("Created placeholder image at website/images/placeholder.jpg")

def prepare_website_data():
    """
    Extract scholar data from the projection data and prepare it for the website.
    This includes copying profile pictures and creating a JSON file with scholar data.
    """
    # Load scholar projection data
    projection_file = Path('data/scholar_projections.json')
    try:
        if not projection_file.exists():
            print(f"Projection file not found: {projection_file}")
            return
        
        with open(projection_file, 'r') as f:
            scholars = json.load(f)
        
        if len(scholars) == 0:
            print("No scholar data found")
            return
        
        print(f"Loaded projection data for {len(scholars)} scholars")
    except Exception as e:
        print(f"Error loading scholar projection data: {e}")
        return
    
    # Create website data directory if it doesn't exist
    os.makedirs('website/data', exist_ok=True)
    os.makedirs('website/images', exist_ok=True)
    
    # Create placeholder image
    create_placeholder_image()
    
    # Get list of available profile pictures
    profile_pics_dir = Path('data/profile_pics')
    if profile_pics_dir.exists():
        profile_pics = os.listdir(profile_pics_dir)
    else:
        profile_pics = []
        print(f"Warning: Profile pictures directory not found: {profile_pics_dir}")
    
    # Counters for image statistics
    new_images_copied = 0
    existing_images_used = 0
    
    # Extract scholar data
    website_data = []
    for scholar in scholars:
        # Format name for file matching - try different formats
        name = scholar['scholar_name']
        name_formats = [
            name.replace(' ', '_'),  # Michael_Bonner
            name.replace(' ', '_').replace('.', ''),  # Jack_L_Gallant
            name.replace(' ', '_').replace('.', '_')  # Jack_L_Gallant
        ]
        
        # Check for profile picture
        profile_pic = None
        for name_format in name_formats:
            for pic in profile_pics:
                pic_name = os.path.splitext(pic)[0]
                if pic_name.lower() == name_format.lower():
                    profile_pic = pic
                    # Check if the image already exists in the website images folder
                    target_path = Path(f"website/images/{pic}")
                    if not target_path.exists():
                        # Copy profile picture to website images folder only if it doesn't exist
                        shutil.copy(f"data/profile_pics/{pic}", str(target_path))
                        new_images_copied += 1
                    else:
                        existing_images_used += 1
                    break
            if profile_pic:
                break
        
        # Get coordinates from UMAP projection (default)
        coords = [scholar['umap_x'], scholar['umap_y']]
        
        # Add scholar data to website data
        scholar_data = {
            'id': scholar['scholar_id'],
            'name': scholar['scholar_name'],
            'coords': coords,
            'profile_pic': profile_pic if profile_pic else 'placeholder.jpg',
        }
        website_data.append(scholar_data)
    
    # Save website data as JSON
    website_data_file = Path('website/data/scholars.json')
    with open(website_data_file, 'w') as f:
        json.dump(website_data, f, indent=2)
    
    print(f"Prepared data for {len(website_data)} scholars")
    print(f"Saved scholar data to {website_data_file}")
    print(f"Profile pictures: {new_images_copied} new copied, {existing_images_used} existing used, {len(website_data) - (new_images_copied + existing_images_used)} using placeholder")
    
    # Copy scholar database files to website data directory
    source_files = [
        'data/scholar_database.npz',
        'data/scholar_embeddings.nc',
        'data/low_dim_embeddings.nc',
        'data/scholar_projections.json'
    ]
    
    files_copied = 0
    for source_file in source_files:
        source_path = Path(source_file)
        if source_path.exists():
            target_path = Path('website/data') / source_path.name
            shutil.copy(source_path, target_path)
            files_copied += 1
            print(f"Copied {source_path} to {target_path}")
        else:
            print(f"Warning: Source file not found: {source_path}")
    
    print(f"Copied {files_copied} database files to website data directory")

if __name__ == "__main__":
    prepare_website_data() 