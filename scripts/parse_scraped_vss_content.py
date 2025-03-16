#!/usr/bin/env python3
"""
Script to extract authors and their affiliations from Vision Sciences Society (VSS) 
conference abstract pages using Google Gemini Flash 2.
"""

import os
import json
import asyncio
import glob
from typing import Dict, List, Any
from tqdm import tqdm
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_gemini_client(temperature=0.2):
    """Create a Google Gemini Flash client."""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables")
    
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        api_key=api_key,
        temperature=temperature,
    )

async def extract_author_info_with_gemini(abstract_data: Dict[str, Any], client) -> Dict[str, Any]:
    """
    Extract author information from abstract data using Google Gemini Flash 2.
    
    Args:
        abstract_data: Dictionary containing abstract data
        client: Gemini client
        
    Returns:
        Dictionary containing title, authors, and affiliations
    """
    # Extract relevant information from the abstract data
    title = abstract_data.get('title', 'Unknown Title')
    # Escape any curly braces in the author_info to prevent format string errors
    author_info = abstract_data.get('author_info', '').replace('{', '{{').replace('}', '}}')
    abstract_text = abstract_data.get('abstract', '')
    url = abstract_data.get('url', '')
    
    # Create a prompt for Gemini
    prompt = f"""
    #Author and Affiliation Extraction Task

    ##Instructions:
    Extract author and affiliation information from the academic paper citation provided at the end of this prompt. Format the information into JSON following these rules:

    1. Identify the first and last authors in the list
    2. Extract their full names (without superscript numbers or email references)
    3. Extract their complete affiliations by matching superscript numbers with institutions
    4. Split affiliations into department and institution components when possible
    5. Format output as a JSON object with the exact keys shown in examples
    6. Format departments and institutions as lists of strings, even when there's only one item
    7. Properly handle special characters (like accented letters and Unicode)
    8. Remove any email addresses or placeholders like "(*protected email*)"
    9. Clean institution names by removing parenthetical abbreviations when the full name is provided

    ## Examples:

    QUERY:
    Akshita Reddy Mavurapu1(*protected email*), Manish Singh2, Ömer Dağlar Tanrikulu1;1University of New Hampshire,2Rutgers University, New Brunswick

    ANSWER:
    {{
    "first_author": "Akshita Reddy Mavurapu",
    "first_author_department": [],
    "first_author_institution": ["University of New Hampshire"],
    "last_author": "Ömer Dağlar Tanrikulu",
    "last_author_department": [],
    "last_author_institution": ["University of New Hampshire"]
    }}

    QUERY:
    Ching-Yi Wang1(*protected email*);1University of California, Los Angeles (UCLA)

    ANSWER:
    {{
    "first_author": "Ching-Yi Wang",
    "first_author_department": [],
    "first_author_institution": ["University of California, Los Angeles"],
    "last_author": "Ching-Yi Wang",
    "last_author_department": [],
    "last_author_institution": ["University of California, Los Angeles"]
    }}

    QUERY:
    Brandon R. Nanfito1,2,3(*protected email*), Kristina J. Nielsen1,2,3;1Johns Hopkins School of Medicine,2Zanvyl Krieger Mind/Brain Institute,3Kavli Neuroscience Discovery Institute

    ANSWER:
    {{
    "first_author": "Brandon R. Nanfito",
    "first_author_department": ["Zanvyl Krieger Mind/Brain Institute", "Kavli Neuroscience Discovery Institute"],
    "first_author_institution": ["Johns Hopkins School of Medicine"],
    "last_author": "Kristina J. Nielsen",
    "last_author_department": ["Zanvyl Krieger Mind/Brain Institute", "Kavli Neuroscience Discovery Institute"],
    "last_author_institution": ["Johns Hopkins School of Medicine"]
    }}

    Now process this citation:
    {author_info}

    Return ONLY the JSON output following the same format as the examples above. Do not include any other text in your response.
    """
    
    try:
        # Generate the response using the LangChain client
        response = client.invoke(prompt)
        result_text = response.content
        
        # Find JSON content in the response
        json_start = result_text.find('{')
        json_end = result_text.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = result_text[json_start:json_end]
            try:
                result = json.loads(json_str)
                # Add the original data to the result
                result.update({
                    'url': url,
                    'title': title,
                    'abstract': abstract_text,
                    'author_info': author_info
                })
                # Print the processed result nicely
                print(f"\nAbstract {result.get('abstract_id', 'unknown')}:")
                print(json.dumps({
                    'first_author': result['first_author'],
                    'first_author_department': result['first_author_department'],
                    'first_author_institution': result['first_author_institution'],
                    'last_author': result['last_author'],
                    'last_author_department': result['last_author_department'],
                    'last_author_institution': result['last_author_institution']
                }, indent=2))
                return result
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON from Gemini response for {url}: {e}")
                return {
                    'title': title,
                    'first_author': '',
                    'first_author_department': [],
                    'first_author_institution': [],
                    'last_author': '',
                    'last_author_department': [],
                    'last_author_institution': [],
                    'url': url,
                    'abstract': abstract_text,
                    'author_info': author_info,
                    'error': 'Failed to parse JSON from Gemini response'
                }
        else:
            print(f"No JSON found in Gemini response for {url}")
            return {
                'title': title,
                'first_author': '',
                'first_author_department': [],
                'first_author_institution': [],
                'last_author': '',
                'last_author_department': [],
                'last_author_institution': [],
                'url': url,
                'abstract': abstract_text,
                'author_info': author_info,
                'error': 'No JSON found in Gemini response'
            }
            
    except Exception as e:
        print(f"Error calling Gemini API for {url}: {str(e)}")
        return {
            'title': title,
            'first_author': '',
            'first_author_department': [],
            'first_author_institution': [],
            'last_author': '',
            'last_author_department': [],
            'last_author_institution': [],
            'url': url,
            'abstract': abstract_text,
            'author_info': author_info,
            'error': str(e)
        }

async def process_abstract_file(file_path: str, client) -> Dict[str, Any]:
    """Process a single abstract JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            abstract_data = json.load(f)
        
        # Extract the abstract ID from the filename
        abstract_id = os.path.basename(file_path).replace('abstract_', '').replace('.json', '')
        
        # Check if the raw content has empty values
        if not abstract_data.get('author_info', '').strip():
            print(f"Skipping {file_path} due to empty author_info in raw content")
            return {
                'title': abstract_data.get('title', 'Error'),
                'abstract_id': abstract_id,
                'url': abstract_data.get('url', ''),
                'abstract': abstract_data.get('abstract', ''),
                'author_info': '',
                'error': 'Empty author_info in raw content'
            }
        
        # Extract author information using Gemini
        result = await extract_author_info_with_gemini(abstract_data, client)
        
        # Add the abstract ID to the result
        result['abstract_id'] = abstract_id
        
        return result
    
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
        try:
            return {
                'title': abstract_data.get('title', 'Error'),
                'abstract_id': abstract_id if 'abstract_id' in locals() else 'unknown',
                'url': abstract_data.get('url', ''),
                'abstract': abstract_data.get('abstract', ''),
                'author_info': abstract_data.get('author_info', ''),
                'error': str(e)
            }
        except:
            return {
                'title': 'Error',
                'abstract_id': abstract_id if 'abstract_id' in locals() else 'unknown',
                'url': '',
                'abstract': '',
                'author_info': '',
                'error': str(e)
            }

async def process_all_abstracts(abstracts_dir: str, output_dir: str):
    """Process all abstract files in the directory and save results individually."""
    # Create Gemini client
    client = create_gemini_client()
    
    # Get all abstract JSON files and sort them by abstract ID
    abstract_files = glob.glob(os.path.join(abstracts_dir, 'abstract_*.json'))
    abstract_files.sort(key=lambda x: int(os.path.basename(x).replace('abstract_', '').replace('.json', '')))
    total_abstracts = len(abstract_files)
    print(f"Found {total_abstracts} abstract files to process")
    
    # Process each file
    results = []
    empty_files = []
    processed_files = []
    
    for i, file_path in enumerate(abstract_files, 1):
        print(f"\nProcessing abstract {i} of {total_abstracts}")
        result = await process_abstract_file(file_path, client)
        
        # Add abstract_id to result before any processing
        abstract_id = os.path.basename(file_path).replace('abstract_', '').replace('.json', '')
        result['abstract_id'] = abstract_id
        
        # Check if this was an empty file
        if 'error' in result and 'Empty author_info' in result.get('error', ''):
            empty_files.append(os.path.basename(file_path))
            continue
            
        # Save individual result
        output_file = os.path.join(output_dir, f'processed_{abstract_id}.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
            
        results.append(result)
        processed_files.append(os.path.basename(file_path))
    
    # Save summary files
    summary_file = os.path.join(output_dir, 'summary.json')
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            'total_files': len(abstract_files),
            'processed_files': len(processed_files),
            'empty_files': len(empty_files),
            'processed_file_list': processed_files,
            'empty_file_list': empty_files,
            'results': results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nProcessing Summary:")
    print(f"Total files found: {len(abstract_files)}")
    print(f"Successfully processed: {len(processed_files)}")
    print(f"Files with empty author info: {len(empty_files)}")
    print(f"Empty files: {', '.join(empty_files)}")
    print(f"\nResults saved to {output_dir}")
    
    # Generate a CSV file with author information
    generate_authors_csv(results, os.path.join(output_dir, 'authors_summary.csv'))

def generate_authors_csv(results: List[Dict[str, Any]], output_csv: str):
    """Generate a CSV file with author information."""
    import csv
    
    with open(output_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['abstract_id', 'title', 'first_author', 'first_author_department', 
                        'first_author_institution', 'last_author', 'last_author_department',
                        'last_author_institution', 'url', 'abstract'])
        
        for result in results:
            abstract_id = result.get('abstract_id', '')
            title = result.get('title', '')
            url = result.get('url', '')
            first_author = result.get('first_author', '')
            first_author_department = ','.join(result.get('first_author_department', []))
            first_author_institution = ','.join(result.get('first_author_institution', []))
            last_author = result.get('last_author', '')
            last_author_department = ','.join(result.get('last_author_department', []))
            last_author_institution = ','.join(result.get('last_author_institution', []))
            abstract = result.get('abstract', '')
            
            writer.writerow([abstract_id, title, first_author, first_author_department,
                           first_author_institution, last_author, last_author_department,
                           last_author_institution, url, abstract])

async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract author information from VSS abstracts using Google Gemini.')
    parser.add_argument('--abstracts-dir', type=str, default='data/vss_scrape/content_raw',
                        help='Directory containing abstract JSON files')
    parser.add_argument('--output-dir', type=str, default='data/vss_scrape/processed_content',
                        help='Output directory for processed author information')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Process all abstracts
    await process_all_abstracts(args.abstracts_dir, args.output_dir)

if __name__ == "__main__":
    print("Starting VSS author extraction with Google Gemini...")
    asyncio.run(main())
    print("Extraction completed!") 