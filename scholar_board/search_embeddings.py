import os
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
from typing import Tuple
from pathlib import Path
import joblib

# Load environment variables
load_dotenv()

# Get API key from environment variable
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

def get_query_embedding(query_text):
    """Get embedding for a query text using OpenAI's API"""
    client = OpenAI(api_key=API_KEY)
    
    try:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=query_text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error getting embedding for query: {e}")
        return None

def project_query_to_umap(query_text: str) -> Tuple[float, float]:
    """
    Project a query text into the UMAP space
    
    Parameters:
    -----------
    query_text : str
        The query text to project
    
    Returns:
    --------
    Tuple of (x, y) coordinates in the UMAP space
    """
    # Get embedding for the query
    query_embedding = get_query_embedding(query_text)
    if query_embedding is None:
        raise ValueError("Failed to get embedding for query")
    
    # Load the UMAP model and scaler
    model_path = Path(__file__).parent.parent / 'data' / 'models' / 'umap_n30_d0.2_model.joblib'
    scaler_path = Path(__file__).parent.parent / 'data' / 'models' / 'scaler.joblib'
    
    if not model_path.exists() or not scaler_path.exists():
        raise FileNotFoundError(f"Model or scaler not found at {model_path} or {scaler_path}")
    
    try:
        umap_model = joblib.load(model_path)
        scaler = joblib.load(scaler_path)
        
        # Scale the embedding if a scaler was used during training
        scaled_embedding = scaler.transform(np.array(query_embedding).reshape(1, -1))
        
        # Project the embedding using the UMAP model
        projection = umap_model.transform(scaled_embedding)
        
        # Return the x, y coordinates
        return float(projection[0, 0]), float(projection[0, 1])
    
    except Exception as e:
        print(f"Error projecting query to UMAP space: {e}")
        raise

def get_query_umap_coords(query_text: str) -> dict:
    """
    Project a query text into UMAP space and return the coordinates as a dictionary
    
    This function is designed to be called from other parts of the application,
    such as a web interface.
    
    Parameters:
    -----------
    query_text : str
        The query text to project
    
    Returns:
    --------
    Dictionary containing:
    - coords: (x, y) coordinates of the query in UMAP space
    - error: Error message if an error occurred
    """
    try:
        # Project the query to UMAP space using the model at data/model/umap_n30_d0.2_model.joblib
        x, y = project_query_to_umap(query_text)
        
        # Return only the coordinates, no closest research features
        return {
            'coords': (x, y),
            'error': None
        }
    except Exception as e:
        print(f"Error projecting query to UMAP space: {e}")
        return {
            'coords': None,
            'error': str(e)
        }

def main():
    """Interactive demo for projecting queries to UMAP space"""
    print("Query Projection Demo")
    print("--------------------")
    
    while True:
        query = input("\nEnter a research query (or 'q' to quit): ")
        if query.lower() == 'q':
            break
        
        try:
            # Project the query to UMAP space
            x, y = project_query_to_umap(query)
            print(f"\nQuery projected to UMAP coordinates: ({x:.4f}, {y:.4f})")
        except Exception as e:
            print(f"Error projecting query: {e}")

if __name__ == "__main__":
    main() 