#!/usr/bin/env python3
import json
import csv
import os
from pathlib import Path
from typing import Dict, List

def process_json_files(input_dir: str, output_file: str) -> None:
    """
    Process all JSON files in the input directory and create a CSV with scholar information.
    """
    # Ensure the output directory exists
    output_dir = os.path.dirname(output_file)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Get all JSON files
    json_files = Path(input_dir).glob("processed_*.json")
    
    # Prepare data for CSV
    rows = []
    for json_path in json_files:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Clean and join department and institution lists
            last_author_dept = "; ".join(data.get("last_author_department", [])) or "N/A"
            last_author_inst = "; ".join(data.get("last_author_institution", [])) or "N/A"
            
            # Clean text fields to remove any unusual characters
            def clean_text(text):
                if isinstance(text, str):
                    return ' '.join(text.replace('\r', ' ').replace('\n', ' ').replace('\u2028', ' ').replace('\u2029', ' ').split())
                return text

            row = {
                "scholar_id": "",  # Will be filled later
                "scholar_name": clean_text(data.get("last_author", "")),
                "scholar_department": clean_text(last_author_dept),
                "scholar_institution": clean_text(last_author_inst),
                "abstract_id": str(data.get("abstract_id", "")),
                "title": clean_text(data.get("title", "")),
                "abstract": clean_text(data.get("abstract", ""))
            }
            rows.append(row)
    
    # Sort rows by abstract_id to ensure consistent ordering
    rows.sort(key=lambda x: x["abstract_id"])
    
    # Write to CSV
    if not rows:
        print("No JSON files found to process")
        return
        
    fieldnames = ["scholar_id", "scholar_name", "scholar_department", 
                 "scholar_institution", "abstract_id", "title", "abstract"]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f_out:
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()
        
        # Write each row with a 4-digit ID
        for i, row in enumerate(rows, start=0):
            row["scholar_id"] = f"{i:04d}"  # Format as 4 digits with leading zeros
            writer.writerow(row)
    
    print(f"Processed {len(rows)} scholars")
    print(f"Output saved to {output_file}")

if __name__ == "__main__":
    # Define input and output file paths
    input_dir = "data/vss_scrape/processed_content"
    output_file = "data/vss_data.csv"
    
    process_json_files(input_dir, output_file)
