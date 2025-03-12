import os
import numpy as np
import xarray as xr
import re
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from tqdm import tqdm

# Load environment variables
load_dotenv()

# Get API key from environment variable
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

def load_scholar_data():
    """Load scholar data from markdown files, extracting only specific sections"""
    scholar_info_dir = Path("data/formatted_scholar_info")
    if not scholar_info_dir.exists():
        raise ValueError(f"Directory {scholar_info_dir} does not exist")
    
    # Get all markdown files
    md_files = list(scholar_info_dir.glob("*.md"))
    if not md_files:
        raise ValueError("No scholar markdown files found")
    
    print(f"Found {len(md_files)} markdown scholar files")
    
    # Define the sections we want to extract
    target_sections = [
        "Core Research Questions",
        "Research Beliefs / Philosophy"
    ]
    
    # Load scholar data
    scholars = []
    for file_path in tqdm(md_files, desc="Loading scholar data"):
        # Extract scholar_name and scholar_id from filename
        # Format: scholar_name_scholar_id.md
        filename = file_path.stem  # Get filename without extension
        parts = filename.split('_')
        
        # The ID should be the last part
        scholar_id = parts[-1]
        # The name could be multiple parts joined by underscores
        scholar_name = '_'.join(parts[:-1])
        
        # Read the markdown file
        with open(file_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        # Extract only the target sections
        extracted_text = ""
        
        # Use regex to find sections
        for section in target_sections:
            pattern = rf"## .* {re.escape(section)}(.*?)(?=## |$)"
            matches = re.findall(pattern, markdown_content, re.DOTALL)
            
            if matches:
                extracted_text += f"## {section}\n{matches[0].strip()}\n\n"
        
        if extracted_text:
            scholars.append({
                'scholar_id': scholar_id,
                'scholar_name': scholar_name,
                'research_text': extracted_text.strip()
            })
        else:
            print(f"Warning: No target sections found in {file_path}")
    
    return scholars

def get_embeddings(texts, model="text-embedding-3-small"):
    """Get embeddings for a list of texts using OpenAI's API"""
    client = OpenAI(api_key=API_KEY)
    
    embeddings = []
    for i, text in enumerate(tqdm(texts, desc="Getting embeddings")):
        try:
            response = client.embeddings.create(
                model=model,
                input=text
            )
            embeddings.append(response.data[0].embedding)
            print(f"Processed {i+1}/{len(texts)} embeddings", end="\r")
        except Exception as e:
            print(f"\nError getting embedding for item {i+1}: {e}")
            embeddings.append(None)
    
    print("\nFinished getting embeddings")
    return embeddings

def main():
    # Check if scholar database already exists
    output_file = Path('data/scholar_database.npz')
    
    if output_file.exists():
        print(f"Loading existing scholar database from {output_file}")
        data = np.load(output_file, allow_pickle=True)
        scholar_data = data['scholars'].tolist()
        print(f"Loaded {len(scholar_data)} scholar records")
    else:
        # Load scholar data from markdown files
        # Only extracts "Core Research Questions" and "Research Beliefs / Philosophy" sections
        scholars = load_scholar_data()
        if not scholars:
            return
        
        print(f"Processing embeddings for {len(scholars)} scholars...")
        
        # Extract research texts (already filtered to include only target sections)
        research_texts = [s['research_text'] for s in scholars]
        
        # Get embeddings
        embedding_model = "text-embedding-3-small"
        embeddings = get_embeddings(research_texts, model=embedding_model)
        
        # Create scholar database with embeddings
        # Note: Some embeddings might be None if API calls failed
        scholar_data = []
        for scholar, embedding in zip(scholars, embeddings):
            scholar_data.append({
                'scholar_id': scholar['scholar_id'],
                'name': scholar['scholar_name'],
                'embedding': embedding
            })
        
        # Save as NPZ file
        np.savez(output_file, scholars=scholar_data)
        print(f"Saved {len(scholar_data)} scholar records to {output_file}")
    
    # Save as netCDF for queryable format
    # We filter out any records where embedding is None (API failures)
    # This creates valid_embeddings with only complete data for the netCDF file
    valid_embeddings = [(s['scholar_id'], s['name'], s['embedding']) 
                        for s in scholar_data if s['embedding'] is not None]
    
    if valid_embeddings:
        scholar_ids, scholar_names, embedding_array = zip(*valid_embeddings)
        embedding_array = np.array(embedding_array)
        embedding_dim = embedding_array.shape[1]
        
        ds = xr.Dataset(
            data_vars={
                'embedding': (['scholar', 'dim'], embedding_array)
            },
            coords={
                'scholar': np.arange(len(scholar_ids)),
                'dim': np.arange(embedding_dim),
                'scholar_id': ('scholar', list(scholar_ids)),
                'scholar_name': ('scholar', list(scholar_names))
            }
        )
        
        netcdf_file = Path('data/scholar_embeddings.nc')
        ds.to_netcdf(netcdf_file)
        print(f"Saved {len(valid_embeddings)} valid embeddings in netCDF format to {netcdf_file}")

if __name__ == "__main__":
    main() 