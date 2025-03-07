#!/usr/bin/env python3
import json
import os
from pathlib import Path

def test_scholars_json():
    """Test if the scholars.json file is valid and contains the expected data."""
    # Get the path to the scholars.json file
    file_path = Path('data/scholars.json')
    
    print(f"Testing {file_path}...")
    
    # Check if the file exists
    if not file_path.exists():
        print(f"ERROR: File not found: {file_path}")
        return False
    
    # Get the file size
    file_size = file_path.stat().st_size
    print(f"File size: {file_size} bytes")
    
    # Try to load the file
    try:
        with open(file_path, 'r') as f:
            scholars = json.load(f)
        
        # Check if it's a list
        if not isinstance(scholars, list):
            print(f"ERROR: Expected a list, got {type(scholars)}")
            return False
        
        # Check if it has items
        if len(scholars) == 0:
            print("ERROR: No scholars found in the file")
            return False
        
        print(f"Successfully loaded {len(scholars)} scholars")
        
        # Check the first scholar
        first_scholar = scholars[0]
        print(f"First scholar: {first_scholar.get('name', 'NO NAME')} (ID: {first_scholar.get('id', 'NO ID')})")
        
        # Check if scholars have the required fields
        valid_scholars = 0
        for i, scholar in enumerate(scholars):
            if i < 5 or i >= len(scholars) - 5:
                print(f"Scholar {i}: {scholar.get('name', 'NO NAME')} (ID: {scholar.get('id', 'NO ID')})")
            
            # Check required fields
            has_id = 'id' in scholar
            has_name = 'name' in scholar
            has_coords = 'coords' in scholar and isinstance(scholar['coords'], list) and len(scholar['coords']) == 2
            
            if has_id and has_name and has_coords:
                valid_scholars += 1
        
        print(f"Found {valid_scholars} valid scholars out of {len(scholars)}")
        
        return valid_scholars > 0
    
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON: {e}")
        return False
    
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    # Change to the script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Test the scholars.json file
    if test_scholars_json():
        print("SUCCESS: scholars.json is valid")
    else:
        print("FAILURE: scholars.json is invalid") 