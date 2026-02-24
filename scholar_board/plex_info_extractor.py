import json
import os
import time
import csv
import argparse
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

from scholar_board.prompt_loader import render_prompt

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

    prompt = render_prompt(
        "fetch_researcher_info",
        scholar_name=scholar_name,
        institution=institution,
    )
    
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

def scholar_info_exists(scholar_id, output_dir):
    """
    Check if information for a scholar already exists in the output directory
    """
    for file_path in output_dir.glob(f"*_{scholar_id}_raw.txt"):
        return True
    return False

def extract_scholar_info(input_file="data/vss_data.csv", dry_run=False, limit=None):
    """
    Extract information about scholars from vss_data.csv and save individual responses
    Only processes each unique scholar_id once
    """
    # Create output directory if it doesn't exist
    output_dir = Path("data/perplexity_info")
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Read scholars from CSV
    scholars = {}  # Use dictionary to track unique scholar_ids
    print(f"Reading scholars from {input_file}")
    
    try:
        with open(input_file, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Skip header row or rows without scholar_id
                if 'scholar_id' not in row or not row['scholar_id']:
                    continue
                
                # Clean scholar_id - ensure it's a string
                scholar_id = row['scholar_id'].strip().strip('"\'')
                if not scholar_id:
                    continue
                
                # Try to pad scholar_id to 4 digits if it's numeric
                try:
                    if scholar_id.isdigit():
                        scholar_id = scholar_id.zfill(4)
                except:
                    pass
                
                # Only add scholar if we haven't seen this ID yet
                if scholar_id not in scholars:
                    # Extract required fields
                    scholar_name = row.get('scholar_name', '').strip().strip('"\'')
                    
                    # For institution, use scholar_institution if available, otherwise use scholar_department
                    institution = row.get('scholar_institution', '').strip().strip('"\'')
                    department = row.get('scholar_department', '').strip().strip('"\'')
                    
                    # If institution is N/A or empty, try to use department instead
                    if (not institution or institution == 'N/A') and department and department != 'N/A':
                        institution = department
                    
                    # Skip if missing required fields or both institution and department are N/A
                    if not scholar_name or not institution or institution == 'N/A':
                        print(f"Skipping scholar with ID {scholar_id} due to missing name or institution")
                        continue
                    
                    # Use abstract content to help identify the scholar's work
                    abstracts = []
                    if 'abstract' in row and row['abstract']:
                        abstracts.append(row['abstract'].strip().strip('"\''))
                    
                    scholars[scholar_id] = {
                        'scholar_id': scholar_id,
                        'scholar_name': scholar_name,
                        'institution': institution,
                        'abstracts': abstracts
                    }
                elif 'abstract' in row and row['abstract']:
                    # For existing scholars, add any additional abstracts
                    abstract = row['abstract'].strip().strip('"\'')
                    if abstract and abstract not in scholars[scholar_id].get('abstracts', []):
                        if 'abstracts' not in scholars[scholar_id]:
                            scholars[scholar_id]['abstracts'] = []
                        scholars[scholar_id]['abstracts'].append(abstract)
    except Exception as e:
        print(f"Error reading input file: {e}")
        return
    
    if not scholars:
        print("No scholars found in the input file.")
        return
    
    print(f"Found {len(scholars)} unique scholars to process.")

    # Apply limit
    scholar_items = list(scholars.items())
    if limit:
        scholar_items = scholar_items[:limit]
        print(f"Limiting to {limit} scholars")

    # Query Perplexity API for each unique scholar and save results
    processed_count = 0
    skipped_count = 0

    for i, (scholar_id, scholar) in enumerate(scholar_items):
        # Check if we already have information for this scholar
        if scholar_info_exists(scholar_id, output_dir):
            print(f"Skipping {i+1}/{len(scholar_items)}: {scholar['scholar_name']} (ID: {scholar_id}) - info already exists")
            skipped_count += 1
            continue

        if dry_run:
            print(f"[DRY RUN] Would fetch: {scholar['scholar_name']} from {scholar['institution']} (ID: {scholar_id})")
            processed_count += 1
            continue

        print(f"Processing {i+1}/{len(scholar_items)}: {scholar['scholar_name']} from {scholar['institution']} (ID: {scholar_id})")

        # Query Perplexity API
        research_info = query_perplexity(
            scholar['scholar_name'],
            scholar['institution'],
            scholar_id
        )

        processed_count += 1

        # Rate limiting to avoid API throttling
        if i < len(scholar_items) - 1:
            time.sleep(2)

    mode = " (dry run)" if dry_run else ""
    print(f"Completed{mode}! Processed {processed_count} scholars, skipped {skipped_count} existing scholars. Results saved to data/perplexity_info/")

def main():
    parser = argparse.ArgumentParser(
        description="Extract scholar info from Perplexity API"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be fetched without making API calls",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Max number of scholars to process",
    )
    args = parser.parse_args()

    # Ensure virtual environment is active
    if os.environ.get('VIRTUAL_ENV') is None:
        print("Warning: Virtual environment does not appear to be active. Please run 'source .venv/bin/activate' first.")

    extract_scholar_info(dry_run=args.dry_run, limit=args.limit)

if __name__ == "__main__":
    main() 