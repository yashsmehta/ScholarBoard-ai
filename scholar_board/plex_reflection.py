import os
import time
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variable
API_KEY = os.getenv("PERPLEXITY_API_KEY")
if not API_KEY:
    raise ValueError("PERPLEXITY_API_KEY not found in environment variables")

def create_reflection(scholar_id, scholar_name, scholar_info):
    """
    Query Perplexity API with existing scholar info to create a more detailed reflection
    
    Args:
        scholar_id: ID of the scholar
        scholar_name: Name of the scholar
        scholar_info: Existing information about the scholar
    """
    client = OpenAI(
        api_key=API_KEY,
        base_url="https://api.perplexity.ai"
    )
    
    prompt = f"""
    Conduct comprehensive research on vision neuroscience researcher Dr. {scholar_name} (ID: {scholar_id}). 
    Use multiple authoritative sources including: Google Scholar, university profiles, lab websites, conference proceedings, research databases (PubMed, Web of Science), ORCID, ResearchGate, and academic CVs.
    
    Verify all information across multiple sources when possible. Do not fabricate or assume information that cannot be verified.
    
    Present findings in a highly technical, information-dense format organized into these exact sections:

    ## About
    - Technical Summary: [2-3 sentences capturing core research focus and impact]
    - Lab: [Full laboratory name]
    - Department: [Specific department affiliation]
    - Institution: [Current university/research center]
    - Location: [State (if in the US), Country]

    Use the following information as a starting point, but significantly expand and verify each section through additional research.
    Dont add new sections, only expand and verify the ones that are already there.

    {scholar_info}

    Important guidelines:
    1. Prioritize ACCURACY over comprehensiveness - if information cannot be verified, indicate this clearly
    2. Use precise technical terminology appropriate for vision neuroscience
    3. Include specific research methods, paradigms, and technical approaches
    4. Cite specific papers or findings where possible
    5. Maintain objectivity and avoid evaluative language
    6. Focus on factual, verifiable information from reputable sources
    7. Dont add new sections, only expand and verify the ones that are already there.
    """
    
    try:
        messages = [
            {
                "role": "system",
                "content": "You are a specialized academic research analyst with expertise in vision neuroscience. Your task is to create comprehensive, technically precise profiles of researchers by synthesizing information from multiple authoritative sources. Prioritize accuracy, technical precision, and information density. Avoid speculation and clearly indicate when information cannot be verified."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        response = client.chat.completions.create(
            model="sonar-reasoning-pro",
            messages=messages
        )
        content = response.choices[0].message.content
        
        # Create directory if it doesn't exist
        output_dir = Path("data/perplexity_reflection")
        output_dir.mkdir(exist_ok=True, parents=True)
        
        # Save reflection to individual file
        output_file = output_dir / f"{scholar_name}_{scholar_id}_reflection.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)
            
        print(f"Saved reflection for {scholar_name} to {output_file}")
        
        return content
    except Exception as e:
        print(f"Error querying Perplexity API for reflection: {e}")
        return f"Error: {str(e)}"

def process_scholar(scholar_id=None):
    """
    Process a single scholar by ID or all scholars if no ID is provided
    
    Args:
        scholar_id: ID of the scholar to process, or None to process all
    """
    info_dir = Path("data/perplexity_info")
    
    if not info_dir.exists():
        print(f"Directory {info_dir} does not exist.")
        return
    
    # Get raw info files
    if scholar_id:
        info_files = list(info_dir.glob(f"*_{scholar_id}_raw.txt"))
        if not info_files:
            print(f"No scholar info file found for ID: {scholar_id}")
            return
    else:
        info_files = list(info_dir.glob("*_raw.txt"))
        if not info_files:
            print(f"No scholar info files found in {info_dir}.")
            return
    
    print(f"Found {len(info_files)} scholar info file(s) to process.")
    
    # Process each file
    for i, file_path in enumerate(info_files):
        # Extract scholar name and ID from filename
        filename = file_path.name
        parts = filename.replace("_raw.txt", "").split("_")
        file_scholar_id = parts[-1]
        scholar_name = "_".join(parts[:-1])
        
        print(f"Processing {i+1}/{len(info_files)}: {scholar_name} (ID: {file_scholar_id})")
        
        # Read scholar info
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                scholar_info = f.read()
            
            # Create reflection
            create_reflection(file_scholar_id, scholar_name, scholar_info)
            
            # Rate limiting to avoid API throttling
            if i < len(info_files) - 1:
                time.sleep(2)
                
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    print(f"Completed! Reflections saved to data/perplexity_reflection/")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Create detailed reflections from existing scholar info")
    parser.add_argument("--scholar", help="Process a specific scholar by ID")
    parser.add_argument("--all", action="store_true", help="Process all scholars")
    
    args = parser.parse_args()
    
    if args.scholar:
        process_scholar(args.scholar)
    elif args.all:
        process_scholar()
    else:
        print("Please specify an action: --scholar ID or --all")

if __name__ == "__main__":
    main() 