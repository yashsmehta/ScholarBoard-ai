import numpy as np
import json
import os
import shutil
import sys
import csv
from pathlib import Path
import xarray as xr

# Add the parent directory to the path so we can import from scholar_board
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from scholar_board.search_embeddings import find_similar_scholars

def prepare_data():
    """
    Extract scholar data from various sources and prepare a consolidated JSON file.
    This includes embeddings, profile pictures, and perplexity info.
    The output is saved to data/scholars.json.
    """
    # Get the parent directory (project root)
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = Path(parent_dir) / 'data'
    
    # Load scholars.csv for basic information
    scholars_csv = data_dir / 'scholars.csv'
    scholars_info = {}
    
    try:
        if not scholars_csv.exists():
            print(f"Scholars CSV file not found: {scholars_csv}")
            return
        
        with open(scholars_csv, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                scholar_id = row['scholar_id']
                scholars_info[scholar_id] = {
                    'id': scholar_id,
                    'name': row['scholar_name'],
                    'institution': row.get('institution', 'Unknown'),
                    'country': row.get('country', 'Unknown')
                }
        
        print(f"Loaded basic info for {len(scholars_info)} scholars from CSV")
    except Exception as e:
        print(f"Error loading scholars CSV: {e}")
        return
    
    # Load low dimensional embeddings for projection coordinates
    low_dim_file = data_dir / 'low_dim_embeddings.nc'
    
    if not low_dim_file.exists():
        print(f"Low dimensional embeddings file not found: {low_dim_file}")
        return
    
    try:
        # Load low dimensional embeddings
        ds = xr.open_dataset(low_dim_file)
        print(f"Loaded low dimensional embeddings for {ds.sizes['scholar']} scholars")
        
        # Extract scholar IDs
        scholar_ids = ds.scholar_id.values
        scholar_names = ds.scholar_name.values
        
        # Create a map of IDs to names for any missing scholars in CSV
        id_to_name = {str(id_val): name for id_val, name in zip(scholar_ids, scholar_names)}
        
        # Add any scholars from embeddings that weren't in the CSV
        for i, scholar_id in enumerate(scholar_ids):
            str_id = str(scholar_id)
            if str_id not in scholars_info:
                scholars_info[str_id] = {
                    'id': str_id,
                    'name': id_to_name[str_id],
                    'institution': 'Unknown',
                    'country': 'Unknown'
                }
        
        # Extract coordinates for each projection method
        for method in ['pca', 'tsne', 'umap']:
            if f'{method}_x' in ds and f'{method}_y' in ds:
                x_coords = ds[f'{method}_x'].values
                y_coords = ds[f'{method}_y'].values
                
                # Add coordinates to scholar info
                for i, scholar_id in enumerate(scholar_ids):
                    str_id = str(scholar_id)
                    if str_id in scholars_info:
                        scholars_info[str_id][method] = [
                            float(x_coords[i]), 
                            float(y_coords[i])
                        ]
        
        print(f"Added projection coordinates for scholars")
    except Exception as e:
        print(f"Error loading low dimensional embeddings: {e}")
        return
    
    # Get list of available profile pictures
    profile_pics_dir = data_dir / 'profile_pics'
    profile_pics_map = {}  # Map scholar names to their profile pic filenames
    
    if profile_pics_dir.exists():
        profile_pics = os.listdir(profile_pics_dir)
        # Create a map of lowercase name to filename for easier matching
        for pic in profile_pics:
            name = os.path.splitext(pic)[0].lower()
            profile_pics_map[name] = pic
        print(f"Found {len(profile_pics)} profile pictures")
    else:
        profile_pics = []
        print(f"Warning: Profile pictures directory not found: {profile_pics_dir}")
    
    # Map of scholar IDs to perplexity info files
    perplexity_dir = data_dir / 'perplexity_info'
    perplexity_files = {}
    
    if perplexity_dir.exists():
        # Map scholar IDs to perplexity info files
        for file_path in perplexity_dir.glob('*_raw.txt'):
            if file_path.is_file():
                # Extract scholar ID from filename (assuming format: Name_ID_raw.txt)
                filename_parts = file_path.stem.split('_')
                if len(filename_parts) >= 2:
                    scholar_id = filename_parts[-2]
                    perplexity_files[scholar_id] = file_path.name
        
        print(f"Found {len(perplexity_files)} perplexity info files")
    else:
        print(f"Warning: Perplexity info directory not found: {perplexity_dir}")
    
    # Create consolidated scholar data
    consolidated_scholars = []
    for scholar_id, scholar_info in scholars_info.items():
        name = scholar_info['name']
        
        # Format name for file matching - try different formats
        name_formats = [
            name.replace(' ', '_'),  # Michael_Bonner
            name.replace(' ', '_').replace('.', ''),  # Jack_L_Gallant
            name.replace(' ', '_').replace('.', '_')  # Jack_L_Gallant
        ]
        
        # Check for profile picture
        profile_pic = None
        for name_format in name_formats:
            if name_format.lower() in profile_pics_map:
                profile_pic = profile_pics_map[name_format.lower()]
                break
        
        # If not found, try a more flexible approach
        if not profile_pic:
            for name_format in name_formats:
                for pic_name in profile_pics_map:
                    if name_format.lower() in pic_name or pic_name in name_format.lower():
                        profile_pic = profile_pics_map[pic_name]
                        break
                if profile_pic:
                    break
        
        # Create scholar data with all available information
        scholar_data = {
            'id': scholar_id,
            'name': name,
            'institution': scholar_info.get('institution', 'Unknown'),
            'country': scholar_info.get('country', 'Unknown'),
            'profile_pic': profile_pic if profile_pic else 'placeholder.jpg',
            'pca': scholar_info.get('pca', [0, 0]),
            'tsne': scholar_info.get('tsne', [0, 0]),
            'umap': scholar_info.get('umap', [0, 0])
        }
        
        # Add perplexity info file reference if available
        if scholar_id in perplexity_files:
            file_name = perplexity_files[scholar_id]
            scholar_data['perplexity_file'] = f"perplexity_info/{file_name}"
        
        consolidated_scholars.append(scholar_data)
    
    # Save consolidated scholar data as JSON
    scholars_file = data_dir / 'scholars.json'
    with open(scholars_file, 'w') as f:
        json.dump(consolidated_scholars, f, indent=2)
    
    print(f"Created consolidated scholars.json with {len(consolidated_scholars)} scholars")
    print(f"Saved to {scholars_file}")

if __name__ == "__main__":
    prepare_data() 