import os
import numpy as np
import xarray as xr
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm
import random
from google import genai

# Load environment variables
load_dotenv()

# Get API key from environment variable
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

# Initialize Google Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)

def load_scholar_summaries():
    """Load scholar data from summary files"""
    scholar_summaries_dir = Path("data/scholar_summaries")
    if not scholar_summaries_dir.exists():
        raise ValueError(f"Directory {scholar_summaries_dir} does not exist")
    
    # Get all text files
    txt_files = list(scholar_summaries_dir.glob("*.txt"))
    if not txt_files:
        raise ValueError("No scholar summary files found")
    
    print(f"Found {len(txt_files)} scholar summary files")
    
    # Load scholar data
    scholars = []
    for file_path in tqdm(txt_files, desc="Loading scholar summaries"):
        # Simply use the filename as the scholar ID and name
        filename = file_path.stem  # Get filename without extension
        
        # Read the summary file
        with open(file_path, 'r', encoding='utf-8') as f:
            summary_text = f.read().strip()
        
        if summary_text:
            scholars.append({
                'scholar_id': str(len(scholars) + 1),  # Just use a sequential ID
                'scholar_name': filename,  # Use filename as name
                'summary_text': summary_text  # Use the entire summary text
            })
        else:
            print(f"Warning: Empty summary in {file_path}")
    
    return scholars

def get_gemini_embeddings(texts, model="gemini-embedding-exp-03-07"):
    """Get embeddings for a list of texts using Google's Gemini API"""
    embeddings = []
    # Create a tqdm progress bar with more details
    progress_bar = tqdm(texts, desc="Getting embeddings", unit="text")
    for text in progress_bar:
        try:
            # Use the entire text for embedding
            result = client.models.embed_content(
                model=model,
                contents=text
            )
            embeddings.append(result.embeddings)
            # Update progress bar description instead of printing
            progress_bar.set_postfix(model=model)
        except Exception as e:
            # Print error without disrupting progress bar
            progress_bar.write(f"Error getting embedding: {e}")
            embeddings.append(None)
    
    print("Finished getting embeddings")
    return embeddings

def display_sample_texts(scholars, num_samples=10):
    """Display sample texts from the scholar summaries"""
    if not scholars:
        print("No scholar data available to display samples")
        return
    
    # Select random samples (or all if fewer than num_samples)
    sample_size = min(num_samples, len(scholars))
    samples = random.sample(scholars, sample_size)
    
    print(f"\n===== SAMPLE TEXTS FROM SCHOLAR SUMMARIES ({sample_size} samples) =====")
    for i, scholar in enumerate(samples, 1):
        print(f"\n----- Sample {i}: {scholar['scholar_name']} (ID: {scholar['scholar_id']}) -----")
        # Display the first 500 characters of the text
        text_sample = scholar['summary_text']
        print(text_sample[:500] + "..." if len(text_sample) > 500 else text_sample)
        print("-" * 80)

def get_user_confirmation(prompt="Continue with embedding creation? (y/n): "):
    """Get user confirmation before proceeding"""
    while True:
        response = input(prompt).strip().lower()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("Please enter 'y' or 'n'")

def main():
    # Load scholar data from summary files
    scholars = load_scholar_summaries()
    if not scholars:
        return
    
    # Display sample texts
    display_sample_texts(scholars, num_samples=10)
    
    # Check if scholar database already exists
    output_file = Path('data/scholar_database.npz')
    
    if output_file.exists():
        print(f"\nLoading existing scholar database from {output_file}")
        data = np.load(output_file, allow_pickle=True)
        scholar_data = data['scholars'].tolist()
        print(f"Loaded {len(scholar_data)} scholar records")
    else:
        print(f"\nProcessing embeddings for {len(scholars)} scholars...")
        
        # Ask for user confirmation before creating embeddings
        if not get_user_confirmation("Proceed with creating embeddings? This will call the Google Gemini API (y/n): "):
            print("Embedding creation cancelled by user")
            return
        
        # Extract summary texts
        summary_texts = [s['summary_text'] for s in scholars]
        
        # Get embeddings using Google Gemini
        embedding_model = "gemini-embedding-exp-03-07"
        embeddings = get_gemini_embeddings(summary_texts, model=embedding_model)
        
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
        # Ask for user confirmation before saving to netCDF
        if not get_user_confirmation("Save embeddings to netCDF format? (y/n): "):
            print("NetCDF creation cancelled by user")
            return
            
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