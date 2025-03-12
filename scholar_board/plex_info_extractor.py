import json
import os
import time
import csv
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variable
API_KEY = os.getenv("PERPLEXITY_API_KEY")
if not API_KEY:
    raise ValueError("PERPLEXITY_API_KEY not found in environment variables")

def query_perplexity(scholar_name, institution, scholar_id):
    """
    Query the Perplexity API for comprehensive information about a scholar
    """
    client = OpenAI(
        api_key=API_KEY,
        base_url="https://api.perplexity.ai"
    )
    
    prompt = f"""
    Comprehensive Research Profile: Scholar Analysis

    Provide a detailed and technical analysis of {scholar_name} from {institution}. Structure your response clearly, covering each section comprehensively:

    1. Lab and Research Areas
        • Name of their lab or research group
        • Main research areas
        • Specific subdisciplines they work within

    2. Core Research Questions
        • Identify and describe the primary research questions or problems they aim to solve.

    3. Major Contributions
        • What is the scholar most recognized for in their field? Describe their most impactful findings, or contributions.

    4. Current Research / Ongoing Projects
        • Clearly summarize their current research focus or list and briefly explain any active or recent projects.

    5. Methodology and Approach (Optional)
        • Provide an overview of their research methods, for example: Experimental techniques, analytical frameworks, computational methods, data sources or analysis strategies
        Note: If it is not clear and verified, do not make up information - just skip the section.

    6. Research Beliefs / Philosophy
        • Summarize the scholar's core beliefs or philosophy regarding research and its role in advancing their discipline.

    7. Academic / Research Trajectory
        • Present a concise chronological trajectory of their academic and professional development, including:
        • Undergraduate education (institution, major)
        • PhD (institution, advisor, lab/group name, dissertation topic)
        • Postdoctoral experience(s), if applicable (institution, mentor, research focus)
        • Notable career milestones or academic appointments

    Note: Please ensure the analysis is thorough, technical, and detailed, fully capturing the depth and scope of their research interests, methodologies, ideas, and intellectual contributions.
    Note: Be respectful (use Dr.)
    Note: Do not include any other text than the requested information (directly start with the requested information)
    """
    
    try:
        messages = [
            {
                "role": "system",
                "content": "You are a research analyst specializing in academic profiling. Provide comprehensive, technically precise information about scholars, emphasizing their research contributions, methodologies, and academic trajectory. Be technical, direct and to the point. Be respectful (use Dr.)"
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        response = client.chat.completions.create(
            model="sonar-pro",
            messages=messages
        )
        content = response.choices[0].message.content
        
        # Create directory if it doesn't exist
        output_dir = Path("data/perplexity_info")
        output_dir.mkdir(exist_ok=True, parents=True)
        
        # Save raw response to individual file
        output_file = output_dir / f"{scholar_name}_{scholar_id}_raw.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)
            
        print(f"Saved raw response for {scholar_name} to {output_file}")
        
        return content
    except Exception as e:
        print(f"Error querying Perplexity API: {e}")
        return f"Error: {str(e)}"

def extract_scholar_info(input_file="data/scholars.csv"):
    """
    Extract information about scholars from a CSV file and save individual responses
    """
    # Read scholars from CSV
    scholars = []
    print(f"Reading scholars from {input_file}")
    
    try:
        if input_file.endswith('.csv'):
            with open(input_file, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if 'scholar_name' not in row or 'institution' not in row or 'scholar_id' not in row:
                        raise ValueError("CSV must have 'scholar_name', 'scholar_id', and 'institution' columns")
                    
                    # Clean up any quotes in the fields that might have been added due to commas
                    cleaned_row = {
                        key: value.strip('"\'') if isinstance(value, str) else value 
                        for key, value in row.items()
                    }
                    scholars.append(cleaned_row)
        else:
            with open(input_file, 'r') as jsonfile:
                scholars = json.load(jsonfile)
                if not isinstance(scholars, list):
                    raise ValueError("JSON file must contain a list of scholar objects")
                
                # Validate structure
                for scholar in scholars:
                    if not isinstance(scholar, dict) or 'scholar_name' not in scholar or 'institution' not in scholar or 'scholar_id' not in scholar:
                        raise ValueError("Each scholar must have 'scholar_name', 'scholar_id', and 'institution' fields")
    except Exception as e:
        print(f"Error reading input file: {e}")
        return
    
    if not scholars:
        print("No scholars found in the input file.")
        return
    
    print(f"Found {len(scholars)} scholars to process.")
    
    # Query Perplexity API for each scholar and save results
    for i, scholar in enumerate(scholars):
        print(f"Processing {i+1}/{len(scholars)}: {scholar['scholar_name']} from {scholar['institution']}")
        
        # Query Perplexity API
        research_info = query_perplexity(
            scholar['scholar_name'], 
            scholar['institution'],
            scholar['scholar_id']
        )
        
        # Rate limiting to avoid API throttling
        if i < len(scholars) - 1:
            time.sleep(2)
    
    print(f"Completed! Results saved to data/scholar_info/")

def main():
    extract_scholar_info()

if __name__ == "__main__":
    main() 