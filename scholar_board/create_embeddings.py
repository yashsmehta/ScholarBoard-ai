import os
import numpy as np
import xarray as xr
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm
import random
from google import genai
import openai
from sentence_transformers import SentenceTransformer
import re

# Load environment variables
load_dotenv()

# Initialize API clients
gemini_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY")) if os.getenv("GOOGLE_API_KEY") else None
openai_client = openai.Client(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None

def clean_text(text, source_type):
    """Clean text based on source type"""
    # Only perform extensive cleaning for perplexity info
    if source_type == "perplexity_info":
        # Remove section headers (e.g., "1. Lab and Research Areas")
        text = re.sub(r'^\d+\.\s+[\w\s/]+$', '', text, flags=re.MULTILINE)
        
        # Convert bullet points to clean format
        text = re.sub(r'^\s*•\s*', '- ', text, flags=re.MULTILINE)
        
        # Convert asterisks used as bullet points
        text = re.sub(r'^\s*\*\s*', '- ', text, flags=re.MULTILINE)
        
        # Remove other asterisks and percent signs
        text = re.sub(r'[%]', '', text)
        
        # Clean up extra spaces
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Normalize newlines (no more than 2 consecutive)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove trailing % often found at the end of files
        text = re.sub(r'%+$', '', text)
        
        # Remove extra spaces at start and end
        text = text.strip()
    
    return text

def load_text_files(directory, desc):
    """Load scholar data from text files in a directory"""
    dir_path = Path(f"data/{directory}")
    if not dir_path.exists():
        raise ValueError(f"Directory {dir_path} does not exist")
    
    txt_files = list(dir_path.glob("*.txt"))
    if not txt_files:
        raise ValueError(f"No {desc} files found")
    
    print(f"Found {len(txt_files)} {desc} files")
    
    scholars = []
    for file_path in tqdm(txt_files, desc=f"Loading {desc}"):
        filename = file_path.stem
        parts = filename.split('_')
        
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read().strip()
        
        if not text:
            print(f"Warning: Empty file {file_path}")
            continue
        
        # Clean text based on source type
        text = clean_text(text, directory)
        
        # Extract ID and name from filename based on directory type
        if directory == "scholar_summaries":
            scholar_id = parts[-2] if len(parts) > 1 else str(len(scholars) + 1)
            scholar_name = ' '.join(parts[:-2]) if len(parts) > 1 else filename
        else:  # perplexity_info
            scholar_id = parts[-1] if len(parts) > 1 else str(len(scholars) + 1)
            scholar_name = ' '.join(parts[:-1]) if len(parts) > 1 else filename
            
        scholars.append({
            'scholar_id': scholar_id,
            'scholar_name': scholar_name,
            'summary_text': text
        })
    
    return scholars

def load_scholar_summaries():
    """Load scholar data from summary files"""
    return load_text_files("scholar_summaries", "scholar summary")

def load_perplexity_info():
    """Load scholar data from perplexity info files"""
    return load_text_files("perplexity_info", "perplexity info")

def load_abstracts_from_csv():
    """Load scholar abstracts from VSS data CSV file"""
    csv_path = Path("data/vss_data.csv")
    if not csv_path.exists():
        raise ValueError(f"CSV file {csv_path} does not exist")
    
    print(f"Loading scholar abstracts from {csv_path}")
    
    try:
        df = pd.read_csv(csv_path)
        print(f"Loaded CSV with {len(df)} rows")
    except Exception as e:
        raise ValueError(f"Error loading CSV file: {e}")
    
    # Check for required columns
    required_cols = ['scholar_id', 'scholar_name', 'abstract']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"CSV file must contain columns: {required_cols}")
    
    # Group abstracts by scholar ID
    scholar_abstracts = {}
    
    for _, row in tqdm(df.iterrows(), total=len(df), desc="Processing abstracts"):
        scholar_id = str(row['scholar_id']).strip()
        scholar_name = str(row['scholar_name']).strip()
        abstract = str(row['abstract']).strip()
        
        if not scholar_id or not abstract:
            continue
        
        # Initialize scholar entry or add to existing one
        if scholar_id not in scholar_abstracts:
            scholar_abstracts[scholar_id] = {
                'scholar_id': scholar_id,
                'scholar_name': scholar_name,
                'abstracts': []
            }
        
        scholar_abstracts[scholar_id]['abstracts'].append(abstract)
    
    # Combine abstracts into a single text for each scholar
    scholars = [
        {
            'scholar_id': data['scholar_id'],
            'scholar_name': data['scholar_name'],
            'summary_text': "\n\n".join(data['abstracts'])
        }
        for _, data in scholar_abstracts.items()
    ]
    
    print(f"Processed abstracts for {len(scholars)} unique scholars")
    return scholars

def get_embeddings(texts, provider="gemini", model=None):
    """Get embeddings using the specified provider and model"""
    if not texts:
        return []
    
    models = {
        "gemini": "gemini-embedding-exp-03-07",
        "openai": "text-embedding-3-small",
        "sentence-bert": "all-mpnet-base-v2"
    }
    
    model = model or models.get(provider)
    desc = f"Getting {provider} embeddings"
    
    if provider == "gemini":
        if not gemini_client:
            raise ValueError("Gemini API key not found or client not initialized")
        
        embeddings = []
        for text in tqdm(texts, desc=desc, unit="text"):
            try:
                result = gemini_client.models.embed_content(model=model, contents=text)
                embeddings.append(result.embeddings)
            except Exception as e:
                tqdm.write(f"Error getting Gemini embedding: {e}")
                embeddings.append(None)
    
    elif provider == "openai":
        if not openai_client:
            raise ValueError("OpenAI API key not found or client not initialized")
            
        embeddings = []
        for text in tqdm(texts, desc=desc, unit="text"):
            try:
                result = openai_client.embeddings.create(model=model, input=text)
                embeddings.append(result.data[0].embedding)
            except Exception as e:
                tqdm.write(f"Error getting OpenAI embedding: {e}")
                embeddings.append(None)
    
    elif provider == "sentence-bert":
        try:
            model = SentenceTransformer(model)
        except Exception as e:
            raise ValueError(f"Failed to load Sentence-BERT model: {e}")
        
        embeddings = []
        batch_size = 32
        progress_bar = tqdm(total=len(texts), desc=desc, unit="text")
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            try:
                batch_embeddings = model.encode(batch, show_progress_bar=False)
                embeddings.extend(batch_embeddings.tolist())
            except Exception as e:
                tqdm.write(f"Error encoding batch: {e}")
                embeddings.extend([None] * len(batch))
            progress_bar.update(len(batch))
        progress_bar.close()
    
    else:
        raise ValueError(f"Unsupported embedding provider: {provider}")
    
    print(f"Finished getting {provider} embeddings")
    return embeddings

def display_sample_texts(scholars, num_samples=5):
    """Display sample texts from the scholar data"""
    if not scholars:
        print("No scholar data available")
        return
    
    sample_size = min(num_samples, len(scholars))
    samples = random.sample(scholars, sample_size)
    
    print(f"\n===== SAMPLE TEXTS ({sample_size} samples) =====")
    for i, scholar in enumerate(samples, 1):
        print(f"\n----- Sample {i}: {scholar['scholar_name']} (ID: {scholar['scholar_id']}) -----")
        text = scholar['summary_text']
        print(text[:500] + "..." if len(text) > 500 else text)
        print("-" * 80)

def get_user_confirmation(prompt="Continue? (y/n): "):
    """Get user confirmation before proceeding"""
    response = input(prompt).strip().lower()
    return response in ['y', 'yes']

def load_data_by_source(data_source):
    """Load scholar data based on the selected data source"""
    sources = {
        "abstracts": load_abstracts_from_csv,
        "scholar_summaries": load_scholar_summaries,
        "perplexity_info": load_perplexity_info
    }
    
    if data_source not in sources:
        raise ValueError(f"Unsupported data source: {data_source}")
        
    return sources[data_source]()

def process_embeddings(scholars, output_file):
    """Process and create embeddings for scholars"""
    print(f"\nProcessing embeddings for {len(scholars)} scholars...")
    
    provider_options = {
        "1": "gemini",
        "2": "openai",
        "3": "sentence-bert"
    }
    
    print("\nSelect embedding provider:")
    for key, value in provider_options.items():
        print(f"{key}. {value}")
    
    provider_choice = input("Enter your choice (1-3): ").strip()
    while provider_choice not in provider_options:
        print("Invalid choice. Please try again.")
        provider_choice = input("Enter your choice (1-3): ").strip()
    
    provider = provider_options[provider_choice]
    
    # Set model based on provider
    models = {
        "gemini": "gemini-embedding-exp-03-07",
        "openai": "text-embedding-3-small",
        "sentence-bert": "all-mpnet-base-v2"
    }
    model = models[provider]
    
    print(f"\nUsing {provider} with model: {model}")
    
    if not get_user_confirmation(f"Proceed with creating embeddings using {provider} ({model})? This will call the API (y/n): "):
        print("Embedding creation cancelled")
        return []
    
    # Get embeddings using selected provider and model
    embeddings = get_embeddings([s['summary_text'] for s in scholars], provider=provider, model=model)
    
    # Create scholar database with embeddings
    scholar_data = [
        {
            'scholar_id': scholar['scholar_id'],
            'name': scholar['scholar_name'],
            'embedding': embedding,
            'provider': provider,
            'model': model
        }
        for scholar, embedding in zip(scholars, embeddings)
    ]
    
    # Save as NPZ file
    np.savez(output_file, scholars=scholar_data)
    print(f"Saved {len(scholar_data)} scholar records to {output_file}")
    
    return scholar_data

def save_to_netcdf(scholar_data):
    """Save valid embeddings to netCDF format"""
    valid_embeddings = [(s['scholar_id'], s['name'], s['embedding']) 
                        for s in scholar_data if s['embedding'] is not None]
    
    if not valid_embeddings:
        print("No valid embeddings to save")
        return
        
    if not get_user_confirmation("Save embeddings to netCDF format? (y/n): "):
        print("NetCDF creation cancelled")
        return
            
    scholar_ids, scholar_names, embedding_array = zip(*valid_embeddings)
    embedding_array = np.array(embedding_array)
    
    ds = xr.Dataset(
        data_vars={
            'embedding': (['scholar', 'dim'], embedding_array)
        },
        coords={
            'scholar': np.arange(len(scholar_ids)),
            'dim': np.arange(embedding_array.shape[1]),
            'scholar_id': ('scholar', list(scholar_ids)),
            'scholar_name': ('scholar', list(scholar_names))
        }
    )
    
    netcdf_file = Path('data/scholar_embeddings.nc')
    ds.to_netcdf(netcdf_file)
    print(f"Saved {len(valid_embeddings)} valid embeddings to {netcdf_file}")

def main():
    # Data source selection
    data_sources = {
        "1": ("abstracts", "Author abstracts from vss_data.csv (recommended)"),
        "2": ("scholar_summaries", "Scholar summaries from scholar_summaries folder"),
        "3": ("perplexity_info", "Perplexity info from perplexity_info folder")
    }
    
    print("\nSelect data source for embeddings:")
    for key, (_, desc) in data_sources.items():
        print(f"{key}. {desc}")
    
    choice = input("Enter your choice (1-3) [1]: ").strip() or "1"
    while choice not in data_sources:
        print("Invalid choice. Please try again.")
        choice = input("Enter your choice (1-3) [1]: ").strip() or "1"
    
    data_source = data_sources[choice][0]
    print(f"\nUsing data source: {data_source}")
    
    # Load scholar data from the selected source
    try:
        scholars = load_data_by_source(data_source)
    except ValueError as e:
        print(f"Error: {e}")
        return
    
    if not scholars:
        print(f"No scholar data found for source: {data_source}")
        return
    
    # Display sample texts
    display_sample_texts(scholars)
    
    # Check if scholar database already exists
    output_file = Path('data/scholar_database.npz')
    
    if output_file.exists():
        print(f"\nExisting scholar database found at {output_file}")
        
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
    save_to_netcdf(scholar_data)

if __name__ == "__main__":
    main() 