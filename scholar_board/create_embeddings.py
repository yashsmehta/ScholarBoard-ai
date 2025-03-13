import os
import numpy as np
import xarray as xr
import re
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from tqdm import tqdm
from difflib import get_close_matches
import random

# Load environment variables
load_dotenv()

# Get API key from environment variable
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

def analyze_section_presence():
    """Analyze how many files have the target sections"""
    scholar_info_dir = Path("data/scholar_markdown")
    if not scholar_info_dir.exists():
        raise ValueError(f"Directory {scholar_info_dir} does not exist")
    
    # Get all markdown files
    md_files = list(scholar_info_dir.glob("*.md"))
    if not md_files:
        raise ValueError("No scholar markdown files found")
    
    print(f"Found {len(md_files)} markdown scholar files")
    
    # Define the sections we want to extract
    target_sections = [
        "Lab and Research Areas",
        "Core Research Questions"
    ]
    
    # Count section presence
    section_counts = {section: 0 for section in target_sections}
    both_sections = 0
    files_missing_sections = {section: [] for section in target_sections}
    
    for file_path in tqdm(md_files, desc="Analyzing section presence"):
        # Read the markdown file
        with open(file_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        # Extract all section headers
        headers = re.findall(r'## (.*?)(?=\n)', markdown_content)
        
        # Check for each target section using fuzzy matching
        found_sections = []
        for section in target_sections:
            # Try to find a close match among the headers
            matches = get_close_matches(section, headers, n=1, cutoff=0.7)
            if matches:
                section_counts[section] += 1
                found_sections.append(section)
            else:
                files_missing_sections[section].append(file_path.name)
        
        if len(found_sections) == len(target_sections):
            both_sections += 1
    
    print("\nSection presence analysis:")
    for section, count in section_counts.items():
        print(f"- '{section}': {count}/{len(md_files)} files ({count/len(md_files)*100:.1f}%)")
        if files_missing_sections[section]:
            print(f"  First file missing this section: {files_missing_sections[section][0]}")
    
    print(f"- Both sections: {both_sections}/{len(md_files)} files ({both_sections/len(md_files)*100:.1f}%)")
    
    return section_counts, both_sections, len(md_files), files_missing_sections

def load_scholar_data():
    """Load scholar data from markdown files, extracting only specific sections"""
    scholar_info_dir = Path("data/scholar_markdown")
    if not scholar_info_dir.exists():
        raise ValueError(f"Directory {scholar_info_dir} does not exist")
    
    # Get all markdown files
    md_files = list(scholar_info_dir.glob("*.md"))
    if not md_files:
        raise ValueError("No scholar markdown files found")
    
    print(f"Found {len(md_files)} markdown scholar files")
    
    # Define the sections we want to extract
    target_sections = [
        "Lab and Research Areas",
        "Core Research Questions"
    ]
    
    # Load scholar data
    scholars = []
    for file_path in tqdm(md_files, desc="Loading scholar data"):
        # Extract scholar_name and scholar_id from filename
        # Format: scholar_name_scholar_id.md
        filename = file_path.stem  # Get filename without extension
        parts = filename.split('_')
        
        # The ID should be the last part
        scholar_id = parts[-1] if len(parts) > 1 else "unknown"
        # The name could be multiple parts joined by underscores
        scholar_name = '_'.join(parts[:-1]) if len(parts) > 1 else filename
        
        # Read the markdown file
        with open(file_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        # Extract all section headers for fuzzy matching
        headers = re.findall(r'## (.*?)(?=\n)', markdown_content)
        
        # Extract only the target sections and clean the text
        extracted_text = ""
        
        # Use fuzzy matching to find sections
        for section in target_sections:
            # Try to find a close match among the headers
            matches = get_close_matches(section, headers, n=1, cutoff=0.8)
            
            if matches:
                matched_header = matches[0]
                # Use the matched header to extract content
                pattern = rf"## {re.escape(matched_header)}(.*?)(?=## |$)"
                content_matches = re.findall(pattern, markdown_content, re.DOTALL)
                
                if content_matches:
                    # Get the raw content without the section header
                    content = content_matches[0].strip()
                    
                    # Clean the markdown formatting
                    # Remove bullet points and asterisks
                    content = re.sub(r'^\s*\*\s+', '', content, flags=re.MULTILINE)
                    # Remove bold and italic formatting
                    content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)
                    content = re.sub(r'\*(.*?)\*', r'\1', content)
                    # Remove any subheadings (###, ####, etc.)
                    content = re.sub(r'^#{3,}.*$', '', content, flags=re.MULTILINE)
                    # Remove any remaining markdown formatting
                    content = re.sub(r'`(.*?)`', r'\1', content)
                    content = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', content)
                    # Remove extra whitespace and normalize spacing
                    content = re.sub(r'\n{3,}', '\n\n', content)
                    content = content.strip()
                    
                    # Add the cleaned content to the extracted text
                    extracted_text += f"{content}\n\n"
        
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
    # Create a tqdm progress bar with more details
    progress_bar = tqdm(texts, desc="Getting embeddings", unit="text")
    for text in progress_bar:
        try:
            response = client.embeddings.create(
                model=model,
                input=text
            )
            embeddings.append(response.data[0].embedding)
            # Update progress bar description instead of printing
            progress_bar.set_postfix(model=model)
        except Exception as e:
            # Print error without disrupting progress bar
            progress_bar.write(f"Error getting embedding: {e}")
            embeddings.append(None)
    
    print("Finished getting embeddings")
    return embeddings

def display_sample_texts(scholars, num_samples=10):
    """Display sample texts from the extracted sections"""
    if not scholars:
        print("No scholar data available to display samples")
        return
    
    # Select random samples (or all if fewer than num_samples)
    sample_size = min(num_samples, len(scholars))
    samples = random.sample(scholars, sample_size)
    
    print(f"\n===== SAMPLE TEXTS FROM EXTRACTED SECTIONS ({sample_size} samples) =====")
    for i, scholar in enumerate(samples, 1):
        print(f"\n----- Sample {i}: {scholar['scholar_name']} (ID: {scholar['scholar_id']}) -----")
        # Display the first 500 characters of the cleaned text
        text_sample = scholar['research_text']
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
    # First analyze section presence
    print("Analyzing section presence in scholar files...")
    _, _, _, files_missing_sections = analyze_section_presence()
    
    # Load scholar data from markdown files
    # Only extracts "Lab and Research Areas" and "Core Research Questions" sections
    scholars = load_scholar_data()
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
        if not get_user_confirmation("Proceed with creating embeddings? This will call the OpenAI API (y/n): "):
            print("Embedding creation cancelled by user")
            return
        
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