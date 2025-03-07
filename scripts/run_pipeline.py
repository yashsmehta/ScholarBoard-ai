import os
import sys
import time
from pathlib import Path

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scholar_board.scholar_info.plex_info_extractor import extract_scholar_info
from scholar_board.scholar_info.deepseek_cleaner import process_all_raw_files
from scholar_board.get_embeddings import main as generate_embeddings
from scholar_board.low_dim_projection import create_scholar_projections

def ensure_directory_structure():
    """
    Ensure the required directory structure exists
    """
    directories = [
        "data/scholar_info",
        "data/profile_pics",
        "data/visualizations"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True, parents=True)
        print(f"Ensured directory exists: {directory}")

def run_pipeline():
    """
    Run the complete ScholarBoard.ai pipeline
    """
    print("Starting ScholarBoard.ai pipeline...")
    
    # Step 0: Ensure directory structure
    ensure_directory_structure()
    
    # Step 1: Extract scholar info using Plexity API
    print("\n=== Step 1: Extracting scholar info using Plexity API ===")
    extract_scholar_info()
    
    # Step 2: Clean scholar data using DeepSeek API
    print("\n=== Step 2: Cleaning scholar data using DeepSeek API ===")
    process_all_raw_files()
    
    # Step 3: Generate embeddings and store in xarray dataset
    print("\n=== Step 3: Generating embeddings ===")
    generate_embeddings()
    
    # Step 4: Generate low-dimensional projections (PCA, UMAP, t-SNE)
    print("\n=== Step 4: Generating low-dimensional projections ===")
    create_scholar_projections()
    
    print("\nPipeline completed successfully!")
    print("Data is now available in the following locations:")
    print("- Scholar CSV: data/scholars.csv")
    print("- Raw scholar info: data/scholar_info/<scholar_name>_<scholar_id>_raw.txt")
    print("- Cleaned scholar info: data/scholar_info/<scholar_name>_<scholar_id>_cleaned.txt")
    print("- Scholar embeddings: data/scholar_embeddings.nc")
    print("- Scholar projections: data/scholar_projections.json")
    print("- Visualizations: data/visualizations/")

if __name__ == "__main__":
    run_pipeline() 