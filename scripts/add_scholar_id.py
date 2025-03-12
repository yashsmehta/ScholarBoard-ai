#!/usr/bin/env python3
import csv
import os
from pathlib import Path

def add_scholar_ids(input_file, output_file):
    """
    Read scholars.csv, add 3-digit IDs (001, 002, etc.), and save to a new file.
    """
    # Ensure the data directory exists
    output_dir = os.path.dirname(output_file)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Read the input CSV file
    with open(input_file, 'r', encoding='utf-8') as f_in:
        reader = csv.reader(f_in)
        header = next(reader)  # Get the header row
        rows = list(reader)    # Get all data rows
    
    # Add the ID column to the header
    new_header = ['scholar_id'] + header
    
    # Write to the output CSV file with IDs
    with open(output_file, 'w', newline='', encoding='utf-8') as f_out:
        writer = csv.writer(f_out)
        writer.writerow(new_header)  # Write the new header
        
        # Write each row with a 3-digit ID
        for i, row in enumerate(rows, start=1):
            scholar_id = f"{i:03d}"  # Format as 3 digits with leading zeros
            writer.writerow([scholar_id] + row)
    
    print(f"Added IDs to {len(rows)} scholars")
    print(f"Output saved to {output_file}")

if __name__ == "__main__":
    # Define input and output file paths
    input_file = "data/scholars.csv"
    output_file = "data/scholars_with_ids.csv"
    
    add_scholar_ids(input_file, output_file)
