import json
import numpy as np
import os
import xarray as xr
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment variable
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

def load_scholar_data():
    """Load scholar data from cleaned text files"""
    scholar_info_dir = Path("data/scholar_info")
    if not scholar_info_dir.exists():
        raise ValueError(f"Directory {scholar_info_dir} does not exist")
    
    # Get all cleaned text files
    cleaned_files = list(scholar_info_dir.glob("*_cleaned.txt"))
    if not cleaned_files:
        raise ValueError("No cleaned scholar files found")
    
    print(f"Found {len(cleaned_files)} cleaned scholar files")
    
    # Load scholar data
    scholars = []
    for file_path in cleaned_files:
        # Extract scholar_name and scholar_id from filename
        # Format: scholar_name_scholar_id_cleaned.txt
        filename = file_path.stem  # Get filename without extension
        parts = filename.split('_')
        
        # The ID should be the second-to-last part before "_cleaned"
        scholar_id = parts[-2]
        # The name could be multiple parts joined by underscores
        scholar_name = '_'.join(parts[:-2])
        
        # Read the cleaned text file
        with open(file_path, 'r', encoding='utf-8') as f:
            research_text = f.read()
        
        scholars.append({
            'scholar_id': scholar_id,
            'scholar_name': scholar_name,
            'research_text': research_text
        })
    
    return scholars

def get_embeddings(texts, model="text-embedding-3-small"):
    """Get embeddings for a list of texts using OpenAI's API"""
    client = OpenAI(api_key=API_KEY)
    
    embeddings = []
    for text in texts:
        try:
            response = client.embeddings.create(
                model=model,
                input=text
            )
            print(f"Got embedding for text (first 30 chars): {text[0:30]}...")
            embeddings.append(response.data[0].embedding)
        except Exception as e:
            print(f"Error getting embedding: {e}")
            embeddings.append(None)
    
    return embeddings

def main():
    # Load scholar data
    scholars = load_scholar_data()
    if not scholars:
        return
    
    # Extract research texts
    research_texts = [s['research_text'] for s in scholars]
    
    # Get embeddings
    embedding_model = "text-embedding-3-small"
    embeddings = get_embeddings(research_texts, model=embedding_model)
    
    # Create xarray dataset
    scholar_ids = [s['scholar_id'] for s in scholars]
    scholar_names = [s['scholar_name'] for s in scholars]
    
    # Convert embeddings to numpy array
    embedding_array = np.array(embeddings)
    embedding_dim = embedding_array.shape[1]
    
    # Create xarray dataset
    ds = xr.Dataset(
        data_vars={
            'embedding': (['scholar', 'dim'], embedding_array)
        },
        coords={
            'scholar': scholar_ids,
            'dim': np.arange(embedding_dim),
            'scholar_name': ('scholar', scholar_names),
            'embedding_type': embedding_model
        }
    )
    
    # Save as netCDF file
    output_file = Path('data/scholar_embeddings.nc')
    ds.to_netcdf(output_file)
    
    print(f"Saved {len(scholars)} scholar embeddings to {output_file}")
    
    # Also save a JSON metadata file without embeddings for easy reading
    scholar_metadata = [{
        'scholar_id': s['scholar_id'],
        'scholar_name': s['scholar_name']
    } for s in scholars]
    
    with open('data/scholar_metadata.json', 'w') as f:
        json.dump(scholar_metadata, f, indent=2)
    
    print("Saved readable metadata to scholar_metadata.json")

if __name__ == "__main__":
    main() 