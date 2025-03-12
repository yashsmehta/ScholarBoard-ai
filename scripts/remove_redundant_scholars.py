#!/usr/bin/env python3
import pandas as pd
import os
import re

def normalize_name(name):
    """
    Normalize author names to handle small redundancies like missing periods in initials.
    
    Args:
        name (str): Author name
        
    Returns:
        str: Normalized name
    """
    # Remove all periods and extra spaces
    normalized = re.sub(r'\.', '', name)
    # Replace multiple spaces with a single space
    normalized = re.sub(r'\s+', ' ', normalized)
    # Trim leading/trailing whitespace
    normalized = normalized.strip()
    return normalized.lower()  # Convert to lowercase for case-insensitive comparison

def extract_unique_last_authors(input_csv, output_csv):
    """
    Extract unique last authors from a CSV file and save them with their institutions
    to a new CSV file. If an author appears multiple times, prioritize entries with
    non-empty institution information. Authors without affiliations will be excluded.
    Results will be sorted alphabetically by name.
    
    Args:
        input_csv (str): Path to the input CSV file
        output_csv (str): Path to the output CSV file
    """
    # Read the CSV file
    print(f"Reading data from {input_csv}...")
    df = pd.read_csv(input_csv)
    
    # Filter only the last authors
    last_authors = df[df['position'] == 'last author'].copy()  # Create a copy to avoid SettingWithCopy warning
    
    # Print total number of last authors before normalization
    total_last_authors = len(last_authors)
    print(f"Total last authors before normalization: {total_last_authors}")
    
    # Print number of unique last authors before normalization
    unique_names_before = last_authors['name'].nunique()
    print(f"Unique last authors before normalization: {unique_names_before}")
    
    # Create a flag for rows with non-empty affiliations
    last_authors['has_affiliation'] = last_authors['affiliations'].notna() & (last_authors['affiliations'] != '')
    
    # Add normalized name column for grouping similar names
    last_authors['normalized_name'] = last_authors['name'].apply(normalize_name)
    
    # Group by normalized name and find the best entry for each author
    result = pd.DataFrame()
    
    # Get unique normalized names
    unique_normalized_names = last_authors['normalized_name'].unique()
    print(f"Unique last authors after normalization: {len(unique_normalized_names)}")
    print(f"Duplicates removed by normalization: {unique_names_before - len(unique_normalized_names)}")
    
    # For each normalized name, find the entry with affiliation if it exists
    authors_with_affiliations = 0
    for norm_name in unique_normalized_names:
        author_entries = last_authors[last_authors['normalized_name'] == norm_name]
        # Try to get an entry with affiliation
        entries_with_affiliation = author_entries[author_entries['has_affiliation']]
        
        if len(entries_with_affiliation) > 0:
            # Use the first entry with affiliation
            best_entry = entries_with_affiliation.iloc[0][['name', 'affiliations']]
            authors_with_affiliations += 1
            # Add to result - only add authors with affiliations
            result = pd.concat([result, pd.DataFrame([best_entry])], ignore_index=True)
        # Skip authors without affiliations - they won't be added to the result
    
    # Count how many authors had missing affiliations
    missing_affiliations = len(unique_normalized_names) - authors_with_affiliations
    
    # Sort the result alphabetically by name
    result = result.sort_values('name', key=lambda x: x.str.lower())
    result = result.reset_index(drop=True)  # Reset index after sorting
    
    # Save to a new CSV file
    print(f"Saving {len(result)} unique last authors with affiliations to {output_csv}...")
    print(f"Authors with affiliations: {authors_with_affiliations}")
    print(f"Authors excluded due to missing affiliations: {missing_affiliations}")
    result.to_csv(output_csv, index=False)
    print("Done!")

if __name__ == "__main__":
    # Define input and output file paths
    input_csv = "data/vss_all_authors.csv"
    output_csv = "data/unique_last_authors.csv"
    
    # Make sure the input file exists
    if not os.path.exists(input_csv):
        print(f"Error: Input file {input_csv} does not exist.")
        exit(1)
    
    # Extract unique last authors
    extract_unique_last_authors(input_csv, output_csv)
