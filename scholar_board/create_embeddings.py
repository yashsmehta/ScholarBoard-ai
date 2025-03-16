import os
import numpy as np
import xarray as xr
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm
import random
from google import genai
import openai
from sentence_transformers import SentenceTransformer

# Load environment variables
load_dotenv()

# Get API keys from environment variables
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize Google Gemini client if API key is available
gemini_client = None
if GOOGLE_API_KEY:
    gemini_client = genai.Client(api_key=GOOGLE_API_KEY)

# Initialize OpenAI client if API key is available
openai_client = None
if OPENAI_API_KEY:
    openai_client = openai.Client(api_key=OPENAI_API_KEY)

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
    if not gemini_client:
        raise ValueError("Gemini API key not found or client not initialized")
    
    embeddings = []
    progress_bar = tqdm(texts, desc="Getting Gemini embeddings", unit="text")
    for text in progress_bar:
        try:
            result = gemini_client.models.embed_content(
                model=model,
                contents=text
            )
            embeddings.append(result.embeddings)
            progress_bar.set_postfix(model=model)
        except Exception as e:
            progress_bar.write(f"Error getting Gemini embedding: {e}")
            embeddings.append(None)
    
    print("Finished getting Gemini embeddings")
    return embeddings

def get_openai_embeddings(texts, model="text-embedding-3-small"):
    """Get embeddings for a list of texts using OpenAI API"""
    if not openai_client:
        raise ValueError("OpenAI API key not found or client not initialized")
    
    embeddings = []
    progress_bar = tqdm(texts, desc="Getting OpenAI embeddings", unit="text")
    for text in progress_bar:
        try:
            result = openai_client.embeddings.create(
                model=model,
                input=text
            )
            embeddings.append(result.data[0].embedding)
            progress_bar.set_postfix(model=model)
        except Exception as e:
            progress_bar.write(f"Error getting OpenAI embedding: {e}")
            embeddings.append(None)
    
    print("Finished getting OpenAI embeddings")
    return embeddings

def get_sentence_bert_embeddings(texts, model_name="all-mpnet-base-v2"):
    """Get embeddings for a list of texts using Sentence-BERT"""
    try:
        model = SentenceTransformer(model_name)
    except Exception as e:
        raise ValueError(f"Failed to load Sentence-BERT model: {e}")
    
    embeddings = []
    progress_bar = tqdm(texts, desc="Getting Sentence-BERT embeddings", unit="text")
    
    # Process in batches to improve performance
    batch_size = 32
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        try:
            batch_embeddings = model.encode(batch, show_progress_bar=False)
            embeddings.extend(batch_embeddings.tolist())
            for _ in range(len(batch)):
                progress_bar.update(1)
                progress_bar.set_postfix(model=model_name)
        except Exception as e:
            progress_bar.write(f"Error getting Sentence-BERT embeddings for batch: {e}")
            embeddings.extend([None] * len(batch))
            progress_bar.update(len(batch))
    
    print("Finished getting Sentence-BERT embeddings")
    return embeddings

def get_embeddings(texts, provider="gemini", model=None):
    """Get embeddings using the specified provider and model"""
    if provider == "gemini":
        model = model or "gemini-embedding-exp-03-07"
        return get_gemini_embeddings(texts, model=model)
    elif provider == "openai":
        model = model or "text-embedding-3-small"
        return get_openai_embeddings(texts, model=model)
    elif provider == "sentence-bert":
        model = model or "all-mpnet-base-v2"
        return get_sentence_bert_embeddings(texts, model_name=model)
    else:
        raise ValueError(f"Unsupported embedding provider: {provider}")

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
        print(f"\nExisting scholar database found at {output_file}")
        
        # Prompt user to decide whether to use existing database or re-extract embeddings
        if not get_user_confirmation("Do you want to re-extract embeddings? (y/n) [n]: "):
            print("Using existing embeddings database.")
            data = np.load(output_file, allow_pickle=True)
            scholar_data = data['scholars'].tolist()
            print(f"Loaded {len(scholar_data)} scholar records")
        else:
            print("Re-extracting embeddings...")
            scholar_data = process_embeddings(scholars, output_file)
    else:
        print(f"\nNo existing database found. Creating new embeddings...")
        scholar_data = process_embeddings(scholars, output_file)
    
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

def process_embeddings(scholars, output_file):
    """Process and create embeddings for scholars"""
    print(f"\nProcessing embeddings for {len(scholars)} scholars...")
    
    # Ask for embedding provider
    provider_options = {
        "1": "gemini",
        "2": "openai",
        "3": "sentence-bert"
    }
    
    print("\nSelect embedding provider:")
    for key, value in provider_options.items():
        print(f"{key}. {value}")
    
    provider_choice = ""
    while provider_choice not in provider_options:
        provider_choice = input("Enter your choice (1-3): ").strip()
        if provider_choice not in provider_options:
            print("Invalid choice. Please try again.")
    
    provider = provider_options[provider_choice]
    
    # Set model based on provider (no user selection)
    if provider == "gemini":
        model = "gemini-embedding-exp-03-07"
    elif provider == "openai":
        model = "text-embedding-3-small"
    else:  # sentence-bert
        model = "all-mpnet-base-v2"
    
    print(f"\nUsing {provider} with model: {model}")
    
    # Ask for user confirmation before creating embeddings
    if not get_user_confirmation(f"Proceed with creating embeddings using {provider} ({model})? This will call the API (y/n): "):
        print("Embedding creation cancelled by user")
        return []
    
    # Extract summary texts
    summary_texts = [s['summary_text'] for s in scholars]
    
    # Get embeddings using selected provider and model
    embeddings = get_embeddings(summary_texts, provider=provider, model=model)
    
    # Create scholar database with embeddings
    # Note: Some embeddings might be None if API calls failed
    scholar_data = []
    for scholar, embedding in zip(scholars, embeddings):
        scholar_data.append({
            'scholar_id': scholar['scholar_id'],
            'name': scholar['scholar_name'],
            'embedding': embedding,
            'provider': provider,
            'model': model
        })
    
    # Save as NPZ file
    np.savez(output_file, scholars=scholar_data)
    print(f"Saved {len(scholar_data)} scholar records to {output_file}")
    
    return scholar_data

if __name__ == "__main__":
    main() 