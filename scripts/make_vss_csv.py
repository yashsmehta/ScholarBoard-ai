#!/usr/bin/env python3
import json
import csv
import os
import re
import random
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict

def clean_scholar_name(name: str) -> str:
    """Clean up scholar names by fixing format issues like quotes and commas."""
    # Fix names with commas and quotes like "Bevil, R. Conway" -> "Bevil R. Conway"
    name = name.replace('"', '')  # Remove quotes
    if ',' in name:
        parts = name.split(',')
        if len(parts) == 2:
            # Assume format is "Last, First Middle" and convert to "First Middle Last"
            last_name = parts[0].strip()
            first_middle = parts[1].strip()
            name = f"{first_middle} {last_name}"
    return name

def normalize_name(name: str) -> str:
    """Normalize scholar names by removing dots after initials and middle initials."""
    # Remove dots after initials
    name = re.sub(r'(\b[A-Z])\.', r'\1', name)
    # Split the name into parts
    parts = name.split()
    if len(parts) <= 2:
        return name.lower()  # Just first and last name, return as is
    
    # For names with middle parts, keep only first and last
    return f"{parts[0]} {parts[-1]}".lower()

def are_likely_same_scholar(name1: str, name2: str, inst1: str, inst2: str) -> bool:
    """
    Determine if two scholar entries likely refer to the same person.
    Check if normalized names match or if one is a subset of the other and institutions match.
    """
    norm_name1 = normalize_name(name1)
    norm_name2 = normalize_name(name2)
    
    # Check if normalized names match
    if norm_name1 == norm_name2:
        return True
    
    # Check if one name is a subset of the other (e.g., "Anne Churchland" vs "Anne K Churchland")
    name1_parts = name1.lower().split()
    name2_parts = name2.lower().split()
    
    # Check if first and last names match
    if len(name1_parts) >= 2 and len(name2_parts) >= 2:
        if name1_parts[0] == name2_parts[0] and name1_parts[-1] == name2_parts[-1]:
            # Names are similar, now check institutions
            if inst1 == inst2 or inst1 == "N/A" or inst2 == "N/A":
                return True
    
    return False

def select_best_value(values):
    """
    Select a random value from a list, prioritizing non-N/A values.
    
    This function exactly matches the selection logic in unify_institutions.py.
    """
    # Remove any NaN or 'N/A' values
    valid_values = [val for val in values if val != 'N/A' and val != 'nan' and pd.notna(val)]
    
    # If there are no valid values, return 'N/A'
    if not valid_values:
        return 'N/A'
    
    # Return a random valid value
    return random.choice(valid_values)

def clean_text(text):
    """Clean text fields to remove any unusual characters."""
    if isinstance(text, str):
        return ' '.join(text.replace('\r', ' ').replace('\n', ' ').replace('\u2028', ' ').replace('\u2029', ' ').split())
    return text

def process_json_files(input_dir: str, output_file: str) -> None:
    """
    Process all JSON files in the input directory and create a CSV with scholar information.
    Incorporates institution unification logic to ensure consistent values per scholar.
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

            row = {
                "scholar_id": "",  # Will be filled later
                "scholar_name": clean_scholar_name(clean_text(data.get("last_author", ""))),
                "scholar_department": clean_text(last_author_dept),
                "scholar_institution": clean_text(last_author_inst),
                "abstract_id": str(data.get("abstract_id", "")),
                "title": clean_text(data.get("title", "")),
                "abstract": clean_text(data.get("abstract", ""))
            }
            rows.append(row)
    
    # Sort rows by scholar name alphabetically, case-insensitive
    rows.sort(key=lambda x: x["scholar_name"].lower())
    
    # Unify institution and department data for the same scholars
    print("Assigning IDs and unifying scholar data...")
    current_id = 0
    processed_scholars = []  # List of (name, institution, id) tuples
    scholar_data = defaultdict(lambda: {"rows": [], "institutions": set(), "departments": set()})
    
    # First pass - group rows by scholar ID and collect unique institutions and departments
    for row in rows:
        scholar_name = row["scholar_name"]
        scholar_inst = row["scholar_institution"]
        
        # Check if this scholar is similar to any we've seen before
        found_match = False
        for prev_name, prev_inst, prev_id in processed_scholars:
            if are_likely_same_scholar(scholar_name, prev_name, scholar_inst, prev_inst):
                row["scholar_id"] = prev_id
                found_match = True
                break
        
        # If no match found, assign a new ID
        if not found_match:
            current_id += 1
            row["scholar_id"] = f"{current_id:04d}"
            processed_scholars.append((scholar_name, scholar_inst, row["scholar_id"]))
        
        # Add to scholar data for unification
        scholar_id = row["scholar_id"]
        scholar_data[scholar_id]["rows"].append(row)
        scholar_data[scholar_id]["institutions"].add(row["scholar_institution"])
        scholar_data[scholar_id]["departments"].add(row["scholar_department"])
    
    # Create a unified dataset for the scholars
    print("Creating a unified dataset...")
    
    # First, save the initial data before unification to a temporary CSV
    temp_csv = output_file.replace(".csv", "_temp.csv")
    fieldnames = ["scholar_id", "scholar_name", "scholar_department", 
                 "scholar_institution", "abstract_id", "title", "abstract"]
    
    with open(temp_csv, 'w', newline='', encoding='utf-8') as f_out:
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    
    # Read the data back using pandas to match unify_institutions.py approach
    print(f"Reading data from {temp_csv}...")
    df = pd.read_csv(temp_csv)
    
    # Replace NaN values with 'N/A' for both fields
    df['scholar_institution'].fillna('N/A', inplace=True)
    df['scholar_department'].fillna('N/A', inplace=True)
    
    # Format scholar_id as 4-digit string with leading zeros
    df['scholar_id'] = df['scholar_id'].apply(lambda x: f"{int(x):04d}" if pd.notna(x) else "")
    
    # Group by scholar_id
    scholar_groups = df.groupby('scholar_id')
    
    # Track changes
    institution_changes = 0
    department_changes = 0
    scholars_modified = 0
    
    # Process each scholar - using the exact same logic as unify_institutions.py
    for scholar_id, group in scholar_groups:
        modified = False
        
        # Check for different institution values
        if len(group['scholar_institution'].unique()) > 1:
            institutions = list(group['scholar_institution'].unique())
            
            # Print before state for debugging (institutions)
            print(f"\nScholar {scholar_id} has multiple institutions:")
            for inst in institutions:
                count = len(group[group['scholar_institution'] == inst])
                print(f"  - '{inst}' ({count} entries)")
            
            # Select a random institution
            selected_institution = select_best_value(institutions)
            
            # Update all entries for this scholar to use the selected institution
            indices = df[df['scholar_id'] == scholar_id].index
            original_institutions = df.loc[indices, 'scholar_institution'].tolist()
            df.loc[indices, 'scholar_institution'] = selected_institution
            
            # Count how many entries were changed
            num_changed = sum(1 for inst in original_institutions if inst != selected_institution)
            institution_changes += num_changed
            modified = True
            
            print(f"  → Institution unified to '{selected_institution}' (changed {num_changed} entries)")
        
        # Check for different department values
        if len(group['scholar_department'].unique()) > 1:
            departments = list(group['scholar_department'].unique())
            
            # Print before state for debugging (departments)
            print(f"\nScholar {scholar_id} has multiple departments:")
            for dept in departments:
                count = len(group[group['scholar_department'] == dept])
                print(f"  - '{dept}' ({count} entries)")
            
            # Select a random department
            selected_department = select_best_value(departments)
            
            # Update all entries for this scholar to use the selected department
            indices = df[df['scholar_id'] == scholar_id].index
            original_departments = df.loc[indices, 'scholar_department'].tolist()
            df.loc[indices, 'scholar_department'] = selected_department
            
            # Count how many entries were changed
            num_changed = sum(1 for dept in original_departments if dept != selected_department)
            department_changes += num_changed
            modified = True
            
            print(f"  → Department unified to '{selected_department}' (changed {num_changed} entries)")
        
        if modified:
            scholars_modified += 1
    
    # Save the modified data to the final output file
    df.to_csv(output_file, index=False)
    
    # Clean up temporary file
    try:
        os.remove(temp_csv)
        print(f"Temporary file {temp_csv} removed.")
    except:
        print(f"Note: Could not remove temporary file {temp_csv}.")
    
    print(f"\nProcess completed:")
    print(f"- Processed {len(rows)} abstracts with {current_id} unique scholars")
    print(f"- Modified {scholars_modified} scholars")
    print(f"- Made {institution_changes} institution replacements")
    print(f"- Made {department_changes} department replacements")
    print(f"- Saved to {output_file}")

if __name__ == "__main__":
    # Define input and output file paths
    input_dir = "data/vss_scrape/processed_content"
    output_file = "data/vss_data.csv"
    
    # Set random seed for reproducibility - exactly the same as in unify_institutions.py
    random.seed(42)
    
    process_json_files(input_dir, output_file)
