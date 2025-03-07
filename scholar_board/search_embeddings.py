import numpy as np
import os
from openai import OpenAI
from dotenv import load_dotenv
from researcher_info.get_embeddings import load_researcher_database

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

def find_similar_researchers(query_text, top_n=5):
    """
    Find researchers most similar to the query text based on embedding similarity
    
    Args:
        query_text: The research question or idea to search for
        top_n: Number of top researchers to return
        
    Returns:
        List of top researchers with similarity scores
    """
    # Get embedding for the query
    query_embedding = get_query_embedding(query_text)
    if query_embedding is None:
        return []
    
    # Load researcher database
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        db_path = os.path.join(project_root, 'data', 'researcher_database.npz')
        
        researcher_data = load_researcher_database(db_path)
        if len(researcher_data) == 0:
            print("No researcher data found")
            return []
    except Exception as e:
        print(f"Error loading researcher data: {e}")
        return []
    
    # Calculate similarity scores
    similarities = []
    for i, researcher in enumerate(researcher_data):
        if researcher['embedding'] is not None:
            similarity = cosine_similarity(query_embedding, researcher['embedding'])
            similarities.append((i, similarity))
    
    # Sort by similarity (descending)
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    # Get top N researchers
    top_researchers = []
    for i, similarity in similarities[:top_n]:
        researcher = researcher_data[i]
        top_researchers.append({
            'researcher_id': researcher['researcher_id'],
            'name': researcher['name'],
            'institution': researcher['institution'],
            'research_areas': researcher['research_areas'],
            'similarity': float(similarity)  # Convert to float for JSON serialization
        })
    
    return top_researchers 