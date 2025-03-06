import json
import os
import time
import csv
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variable
API_KEY = os.getenv("PERPLEXITY_API_KEY")
if not API_KEY:
    raise ValueError("PERPLEXITY_API_KEY not found in environment variables")

def query_perplexity(researcher_name, institution):
    """
    Query the Perplexity API for comprehensive information about a researcher
    """
    client = OpenAI(
        api_key=API_KEY,
        base_url="https://api.perplexity.ai"
    )
    
    prompt = f"""
    Provide a comprehensive analysis of researcher {researcher_name} from {institution}. Include:
    
    1. Their main research areas and disciplines
    2. The specific research questions they are investigating
    3. What they are most known for in their field
    4. Their current research focus and ongoing projects
    5. Their major contributions to the field
    6. Their research methodology and approach
    7. Notable collaborations with other researchers
    8. The impact of their work on their field and beyond
    
    Please be technical and thorough and detailed in your response, covering the full scope of their research career and interests.
    """
    
    try:
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that provides comprehensive, detailed technical information about academic researchers. Your responses should be thorough and cover all aspects of a researcher's work, interests, and contributions."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        response = client.chat.completions.create(
            model="sonar-pro-online",
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error querying Perplexity API: {e}")
        return f"Error: {str(e)}"

def extract_researcher_info(input_file="researchers.csv", output_file="researcher_areas.json"):
    """
    Extract information about researchers from a CSV file and save to another JSON file
    """
    # Read researchers from CSV
    researchers = []
    print(f"Reading researchers from {input_file}")
    print(f"Writing to {output_file}")
    
    try:
        if input_file.endswith('.csv'):
            with open(input_file, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if 'researcher_name' not in row or 'institution' not in row:
                        raise ValueError("CSV must have 'researcher_name' and 'institution' columns")
                    researchers.append(row)
        else:
            with open(input_file, 'r') as jsonfile:
                researchers = json.load(jsonfile)
                if not isinstance(researchers, list):
                    raise ValueError("JSON file must contain a list of researcher objects")
                
                # Validate structure
                for researcher in researchers:
                    if not isinstance(researcher, dict) or 'researcher_name' not in researcher or 'institution' not in researcher:
                        raise ValueError("Each researcher must have 'researcher_name' and 'institution' fields")
    except Exception as e:
        print(f"Error reading input file: {e}")
        return
    
    if not researchers:
        print("No researchers found in the input file.")
        return
    
    print(f"Found {len(researchers)} researchers to process.")
    
    # Query Perplexity API for each researcher and save results
    results = []
    for i, researcher in enumerate(researchers):
        print(f"Processing {i+1}/{len(researchers)}: {researcher['researcher_name']} from {researcher['institution']}")
        
        # Query Perplexity API
        research_info = query_perplexity(researcher['researcher_name'], researcher['institution'])
        
        # Add to results
        results.append({
            'name': researcher['researcher_name'],
            'institution': researcher['institution'],
            'research_areas': research_info
        })
        
        # Save progress after each researcher
        with open(output_file, 'w', encoding='utf-8') as jsonfile:
            json.dump(results, jsonfile, indent=2, ensure_ascii=False)
        
        # Rate limiting to avoid API throttling
        if i < len(researchers) - 1:
            time.sleep(2)
    
    print(f"Completed! Results saved to {output_file}")

def main():
    extract_researcher_info()

if __name__ == "__main__":
    main() 