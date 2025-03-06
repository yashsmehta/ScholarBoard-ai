import json
import numpy as np
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment variable
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

def load_researcher_data(input_file="data/researcher_areas_small.json"):
    """Load researcher data from JSON file"""
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading researcher data: {e}")
        return None

def get_embeddings(texts):
    """Get embeddings for a list of texts using OpenAI's API"""
    client = OpenAI(api_key=API_KEY)
    
    embeddings = []
    for text in texts:
        try:
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            print("got embedding for ", text[0:10])
            embeddings.append(response.data[0].embedding)
        except Exception as e:
            print(f"Error getting embedding: {e}")
            embeddings.append(None)
    
    return embeddings

def main():
    # Load researcher data
    researchers = load_researcher_data()
    if not researchers:
        return
    
    # Extract research areas text
    research_texts = [r['research_areas'] for r in researchers]
    
    # Get embeddings
    embeddings = get_embeddings(research_texts)
    
    # Create comprehensive researcher database
    researcher_db = []
    for idx, (researcher, embedding) in enumerate(zip(researchers, embeddings)):
        if embedding is not None:  # Only include researchers with valid embeddings
            researcher_entry = {
                'researcher_id': idx,
                'name': researcher['name'],
                'institution': researcher['institution'],
                'research_areas': researcher['research_areas'],
                'embedding': embedding
            }
            researcher_db.append(researcher_entry)
    
    # Save as numpy compressed file to efficiently store both metadata and embeddings
    np.savez_compressed(
        'data/researcher_database.npz',
        researcher_data=np.array(researcher_db, dtype=object)
    )
    
    # Also save a JSON version without embeddings for easy reading
    researcher_metadata = [{
        'researcher_id': r['researcher_id'],
        'name': r['name'],
        'institution': r['institution'],
        'research_areas': r['research_areas']
    } for r in researcher_db]
    
    with open('data/researcher_metadata.json', 'w') as f:
        json.dump(researcher_metadata, f, indent=2)

    print(f"Saved {len(researcher_db)} researchers to researcher_database.npz")
    print("Saved readable metadata to researcher_metadata.json")

def load_researcher_database(file_path='data/researcher_database.npz'):
    """Helper function to load the researcher database"""
    data = np.load(file_path, allow_pickle=True)
    return data['researcher_data']

if __name__ == "__main__":
    main() 