import os
import numpy as np
import xarray as xr
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict, Any
from pathlib import Path

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

def cosine_similarity(a, b):
    """Calculate cosine similarity between two vectors"""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def load_scholar_embeddings(file_path=None):
    """Load scholar embeddings from netCDF file"""
    if file_path is None:
        file_path = Path('data/scholar_embeddings.nc')
    
    try:
        if not file_path.exists():
            print(f"Embeddings file not found: {file_path}")
            return None
        
        # Load the netCDF file
        ds = xr.open_dataset(file_path)
        print(f"Loaded embeddings for {ds.dims['scholar']} scholars")
        return ds
    except Exception as e:
        print(f"Error loading scholar embeddings: {e}")
        return None

def find_similar_scholars(query_text, top_n=5, use_low_dim=False, projection_method='pca'):
    """
    Find scholars most similar to the query text based on embedding similarity
    
    Parameters:
    -----------
    query_text : str
        The query text to find similar scholars for
    top_n : int
        Number of top scholars to return
    use_low_dim : bool
        Whether to use low-dimensional projections for similarity search
    projection_method : str
        Which projection method to use if use_low_dim is True ('pca', 'tsne', or 'umap')
    
    Returns:
    --------
    List of dictionaries containing scholar information and similarity scores
    """
    # Determine which file to use based on whether we're using low-dim projections
    if use_low_dim:
        file_path = Path('data/low_dim_embeddings.nc')
    else:
        file_path = Path('data/scholar_embeddings.nc')
    
    # Load scholar embeddings
    ds = load_scholar_embeddings(file_path)
    if ds is None:
        return []
    
    if use_low_dim:
        # For low-dim projections, we'll use Euclidean distance in 2D space
        # Get the projection coordinates
        if projection_method not in ['pca', 'tsne', 'umap']:
            print(f"Invalid projection method: {projection_method}. Using PCA.")
            projection_method = 'pca'
        
        # Get the query embedding and project it to 2D
        # This is a simplification - ideally we would apply the same transformation
        # For now, we'll just use the closest point in the projection space
        print(f"Using {projection_method} projection for similarity search")
        
        # Extract coordinates for the specified projection method
        x_coords = ds[f'{projection_method}_x'].values
        y_coords = ds[f'{projection_method}_y'].values
        
        # Combine into a single array of 2D points
        points = np.column_stack((x_coords, y_coords))
        
        # Calculate distances (using Euclidean distance in 2D space)
        # This is just a demonstration - in a real system, we would project the query
        # For now, we'll use the center of the projection as our query point
        query_point = np.mean(points, axis=0)
        
        # Calculate distances
        distances = np.sqrt(np.sum((points - query_point)**2, axis=1))
        
        # Convert distances to similarities (closer = more similar)
        max_dist = np.max(distances)
        similarities = 1 - (distances / max_dist)
        
        # Get indices of top N scholars
        top_indices = np.argsort(similarities)[-top_n:][::-1]
        
        # Get scholar information
        scholar_ids = ds.scholar_id.values
        scholar_names = ds.scholar_name.values
        
        # Create result list
        results = []
        for idx in top_indices:
            results.append({
                'scholar_id': scholar_ids[idx],
                'name': scholar_names[idx],
                'similarity': float(similarities[idx])
            })
        
        return results
    else:
        # For high-dimensional embeddings, we'll use cosine similarity
        # Get embedding for the query
        query_embedding = get_query_embedding(query_text)
        if query_embedding is None:
            return []
        
        # Extract embeddings and metadata
        embeddings = ds.embedding.values
        scholar_ids = ds.scholar_id.values
        scholar_names = ds.scholar_name.values
        
        # Calculate similarity scores
        similarities = []
        for i in range(len(embeddings)):
            similarity = cosine_similarity(query_embedding, embeddings[i])
            similarities.append((i, similarity))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Get top N scholars
        top_scholars = []
        for i, similarity in similarities[:top_n]:
            top_scholars.append({
                'scholar_id': scholar_ids[i],
                'name': scholar_names[i],
                'similarity': float(similarity)
            })
        
        return top_scholars

def main():
    """Interactive search demo"""
    print("Scholar Search Demo")
    print("------------------")
    
    while True:
        query = input("\nEnter a research query (or 'q' to quit): ")
        if query.lower() == 'q':
            break
        
        use_low_dim = input("Use low-dimensional projections? (y/n): ").lower() == 'y'
        
        if use_low_dim:
            projection_method = input("Projection method (pca, tsne, umap): ").lower()
            if projection_method not in ['pca', 'tsne', 'umap']:
                projection_method = 'pca'
                print("Using default projection method: PCA")
            
            results = find_similar_scholars(query, top_n=5, use_low_dim=True, 
                                           projection_method=projection_method)
        else:
            results = find_similar_scholars(query, top_n=5)
        
        if not results:
            print("No results found.")
            continue
        
        print(f"\nTop 5 scholars related to '{query}':")
        for i, scholar in enumerate(results):
            print(f"{i+1}. {scholar['name']} (ID: {scholar['scholar_id']}) - " 
                  f"Similarity: {scholar['similarity']:.4f}")

if __name__ == "__main__":
    main() 