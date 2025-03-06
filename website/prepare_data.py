import numpy as np
import json
import os
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import random

def create_placeholder_image():
    """Create a placeholder image for researchers without profile pictures"""
    # Create a directory for images if it doesn't exist
    os.makedirs('images', exist_ok=True)
    
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
    img.save('images/placeholder.jpg')
    print("Created placeholder image at images/placeholder.jpg")

def prepare_website_data():
    """
    Extract researcher data from the database and prepare it for the website.
    This includes copying profile pictures and creating a JSON file with researcher data.
    """
    # Load researcher database
    try:
        data = np.load('data/researcher_database.npz', allow_pickle=True)
        researchers = data['researcher_data']
        if len(researchers) == 0:
            print("No researcher data found")
            return
    except Exception as e:
        print(f"Error loading researcher data: {e}")
        return
    
    # Create website data directory if it doesn't exist
    os.makedirs('website/data', exist_ok=True)
    os.makedirs('website/images', exist_ok=True)
    
    # Create placeholder image
    create_placeholder_image()
    
    # Get list of available profile pictures
    profile_pics = os.listdir('data/profile_pics')
    
    # Extract researcher data
    website_data = []
    for r in researchers:
        if 'umap_coords' in r:
            # Format name for file matching - try different formats
            name_formats = [
                r['name'].replace(' ', '_'),  # Michael_Bonner
                r['name'].replace(' ', '_').replace('.', ''),  # Jack_L_Gallant
                r['name'].replace(' ', '_').replace('.', '_')  # Jack_L_Gallant
            ]
            
            # Check for profile picture
            profile_pic = None
            for name_format in name_formats:
                for pic in profile_pics:
                    pic_name = os.path.splitext(pic)[0]
                    if pic_name.lower() == name_format.lower():
                        profile_pic = pic
                        # Copy profile picture to website images folder
                        shutil.copy(f"data/profile_pics/{pic}", f"website/images/{pic}")
                        break
                if profile_pic:
                    break
            
            # Add researcher data to website data
            researcher_data = {
                'name': r['name'],
                'institution': r['institution'],
                'coords': r['umap_coords'],
                'profile_pic': profile_pic if profile_pic else 'placeholder.jpg',
                'research_areas': r.get('research_areas', '')
            }
            website_data.append(researcher_data)
    
    # Save website data as JSON
    with open('website/data/researchers.json', 'w') as f:
        json.dump(website_data, f, indent=2)
    
    # Also copy the full researcher metadata for additional details
    try:
        shutil.copy('data/researcher_metadata.json', 'website/data/researcher_metadata.json')
    except Exception as e:
        print(f"Warning: Could not copy researcher metadata: {e}")
    
    print(f"Prepared data for {len(website_data)} researchers")
    print(f"Copied {len([r for r in website_data if r['profile_pic'] != 'placeholder.jpg'])} profile pictures")

if __name__ == "__main__":
    prepare_website_data() 