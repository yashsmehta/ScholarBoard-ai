#!/usr/bin/env python3
import pandas as pd
import os
import re
import glob
from collections import defaultdict
import argparse
import sys
import shutil

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

def extract_scholar_name_from_filename(filename):
    """
    Extract scholar name from perplexity info filename.
    
    Args:
        filename (str): Filename in format "Scholar Name_ID_raw.txt"
        
    Returns:
        str: Scholar name
    """
    # Extract the base filename without path
    base_name = os.path.basename(filename)
    # Split by underscore and take the first part (name)
    parts = base_name.split('_')
    if len(parts) >= 2:
        return parts[0]
    return None

def find_missing_scholars(vss_csv, perplexity_dir, output_csv=None):
    """
    Find scholars present in VSS data but missing from perplexity info folder.
    
    Args:
        vss_csv (str): Path to the VSS data CSV file
        perplexity_dir (str): Path to the perplexity info directory
        output_csv (str, optional): Path to save missing scholars to CSV
    
    Returns:
        tuple: (missing_scholars_df, count)
    """
    # Read the VSS CSV file
    print(f"Reading data from {vss_csv}...")
    vss_df = pd.read_csv(vss_csv)
    
    # Get unique scholars from VSS data using scholar_id
    vss_scholars = vss_df[['scholar_id', 'scholar_name', 'scholar_department', 'scholar_institution']].drop_duplicates('scholar_id')
    
    # Create normalized name column for comparison
    vss_scholars['normalized_name'] = vss_scholars['scholar_name'].apply(normalize_name)
    
    # Count total unique scholars in VSS data
    total_vss_scholars = len(vss_scholars)
    print(f"Total unique scholars in VSS data (by scholar_id): {total_vss_scholars}")
    
    # Get perplexity info files
    perplexity_files = glob.glob(os.path.join(perplexity_dir, "*_*_raw.txt"))
    print(f"Found {len(perplexity_files)} files in perplexity info directory")
    
    # Extract scholar names from perplexity files
    perplexity_scholars = []
    for file_path in perplexity_files:
        scholar_name = extract_scholar_name_from_filename(file_path)
        if scholar_name:
            perplexity_scholars.append({
                'name': scholar_name,
                'normalized_name': normalize_name(scholar_name),
                'file_path': file_path
            })
    
    # Convert to DataFrame
    perplexity_df = pd.DataFrame(perplexity_scholars) if perplexity_scholars else pd.DataFrame(columns=['name', 'normalized_name', 'file_path'])
    
    # Get normalized names from perplexity data
    perplexity_normalized_names = set(perplexity_df['normalized_name'])
    
    # Find scholars in VSS but not in perplexity
    missing_scholars = vss_scholars[~vss_scholars['normalized_name'].isin(perplexity_normalized_names)]
    
    # Count missing scholars
    missing_count = len(missing_scholars)
    
    print(f"\nFound {missing_count} scholars in VSS data that are missing from perplexity info")
    print(f"({missing_count / total_vss_scholars * 100:.2f}% of total scholars)")
    
    # Save to CSV if requested
    if output_csv:
        missing_scholars.to_csv(output_csv, index=False)
        print(f"Missing scholars list saved to {output_csv}")
    
    return missing_scholars, missing_count

def compare_vss_and_perplexity_data(vss_csv, perplexity_dir, output_csv=None):
    """
    Compare scholars from VSS data and perplexity info folder, providing statistics.
    Uses scholar_id as the unique identifier for VSS scholars.
    
    Args:
        vss_csv (str): Path to the VSS data CSV file
        perplexity_dir (str): Path to the perplexity info directory
        output_csv (str, optional): Path to save missing scholars to CSV
    """
    # Read the VSS CSV file
    print(f"Reading data from {vss_csv}...")
    vss_df = pd.read_csv(vss_csv)
    
    # Get unique scholars from VSS data using scholar_id
    vss_scholars = vss_df[['scholar_id', 'scholar_name', 'scholar_department', 'scholar_institution']].drop_duplicates('scholar_id')
    
    # Create normalized name column for comparison
    vss_scholars['normalized_name'] = vss_scholars['scholar_name'].apply(normalize_name)
    
    # Count total unique scholars in VSS data
    total_vss_scholars = len(vss_scholars)
    print(f"Total unique scholars in VSS data (by scholar_id): {total_vss_scholars}")
    
    # Get perplexity info files
    perplexity_files = glob.glob(os.path.join(perplexity_dir, "*_*_raw.txt"))
    print(f"Found {len(perplexity_files)} files in perplexity info directory")
    
    # Extract scholar names from perplexity files
    perplexity_scholars = []
    for file_path in perplexity_files:
        scholar_name = extract_scholar_name_from_filename(file_path)
        if scholar_name:
            perplexity_scholars.append({
                'name': scholar_name,
                'normalized_name': normalize_name(scholar_name),
                'file_path': file_path
            })
    
    # Convert to DataFrame
    perplexity_df = pd.DataFrame(perplexity_scholars) if perplexity_scholars else pd.DataFrame(columns=['name', 'normalized_name', 'file_path'])
    
    # Count unique scholars in perplexity data
    total_perplexity_scholars = len(perplexity_df)
    unique_perplexity_names = perplexity_df['normalized_name'].nunique()
    print(f"Total scholars in perplexity info: {total_perplexity_scholars}")
    print(f"Unique scholars in perplexity info after normalization: {unique_perplexity_names}")
    
    # Find scholars present in both datasets
    vss_normalized_names = set(vss_scholars['normalized_name'])
    perplexity_normalized_names = set(perplexity_df['normalized_name'])
    
    # Calculate overlaps and unique scholars
    scholars_in_both = vss_normalized_names.intersection(perplexity_normalized_names)
    scholars_only_in_vss = vss_normalized_names - perplexity_normalized_names
    scholars_only_in_perplexity = perplexity_normalized_names - vss_normalized_names
    
    print("\n--- COMPARISON STATISTICS ---")
    print(f"Scholars present in both datasets: {len(scholars_in_both)}")
    print(f"Scholars only in VSS data: {len(scholars_only_in_vss)}")
    print(f"Scholars only in perplexity info: {len(scholars_only_in_perplexity)}")
    
    # Calculate percentage overlaps
    vss_overlap_percentage = (len(scholars_in_both) / len(vss_normalized_names)) * 100
    perplexity_overlap_percentage = (len(scholars_in_both) / len(perplexity_normalized_names)) * 100
    
    print(f"Percentage of VSS scholars also in perplexity info: {vss_overlap_percentage:.2f}%")
    print(f"Percentage of perplexity scholars also in VSS data: {perplexity_overlap_percentage:.2f}%")
    
    # Count scholars with affiliations
    has_affiliation = (
        vss_scholars['scholar_institution'].notna() & 
        (vss_scholars['scholar_institution'] != '') & 
        (vss_scholars['scholar_institution'] != 'N/A')
    )
    
    authors_with_affiliations = has_affiliation.sum()
    authors_without_affiliations = len(vss_scholars) - authors_with_affiliations
    
    print(f"\nScholars with affiliations: {authors_with_affiliations}")
    print(f"Scholars without affiliations: {authors_without_affiliations}")
    
    # Find missing scholars (in VSS but not in perplexity)
    missing_scholars = vss_scholars[~vss_scholars['normalized_name'].isin(perplexity_normalized_names)]
    
    # Save missing scholars to CSV if requested
    if output_csv:
        missing_scholars.to_csv(output_csv, index=False)
        print(f"\nMissing scholars list saved to {output_csv}")
    
    # Print scholars without affiliations
    if authors_without_affiliations > 0:
        print("\nScholars without institution information:")
        scholars_no_affiliation = vss_scholars[~has_affiliation]
        for _, scholar in scholars_no_affiliation.iterrows():
            print(f"- {scholar['scholar_name']} (ID: {scholar['scholar_id']})")
    
    # List missing scholars in VSS but not in perplexity
    if len(scholars_only_in_vss) > 0:
        print("\nList of scholars in VSS data but missing from perplexity info:")
        count = 1
        for _, scholar in missing_scholars.iterrows():
            print(f"{count}. {scholar['scholar_name']} (ID: {scholar['scholar_id']})")
            count += 1
    
    # List scholars only in perplexity info
    if len(scholars_only_in_perplexity) > 0:
        print("\nScholars only in perplexity info:")
        for name in perplexity_df[perplexity_df['normalized_name'].isin(scholars_only_in_perplexity)]['name']:
            print(f"- {name}")

def rename_perplexity_files(vss_csv, perplexity_dir, dry_run=False, delete_nonmatching=False):
    """
    Rename perplexity files using scholar IDs from VSS data.
    
    Args:
        vss_csv (str): Path to the VSS data CSV file
        perplexity_dir (str): Path to the perplexity info directory
        dry_run (bool): If True, only show what would be renamed without actually renaming
        delete_nonmatching (bool): If True, delete files without matching VSS data
        
    Returns:
        tuple: (renamed_count, not_found_count, deleted_count)
    """
    # Read the VSS CSV file
    print(f"Reading data from {vss_csv}...")
    vss_df = pd.read_csv(vss_csv)
    
    # Get unique scholars from VSS data using scholar_id
    vss_scholars = vss_df[['scholar_id', 'scholar_name']].drop_duplicates('scholar_id')
    
    # Create normalized name column for comparison
    vss_scholars['normalized_name'] = vss_scholars['scholar_name'].apply(normalize_name)
    
    # Create a mapping from normalized name to scholar_id
    name_to_id_map = dict(zip(vss_scholars['normalized_name'], vss_scholars['scholar_id']))
    
    # Get perplexity info files
    perplexity_files = glob.glob(os.path.join(perplexity_dir, "*_*_raw.txt"))
    print(f"Found {len(perplexity_files)} files in perplexity info directory")
    
    renamed_count = 0
    not_found_count = 0
    deleted_count = 0
    
    for file_path in perplexity_files:
        # Extract scholar name from filename
        scholar_name = extract_scholar_name_from_filename(file_path)
        if not scholar_name:
            print(f"Warning: Could not extract scholar name from {file_path}")
            continue
            
        normalized_name = normalize_name(scholar_name)
        
        # Find the corresponding scholar_id
        if normalized_name in name_to_id_map:
            scholar_id = name_to_id_map[normalized_name]
            
            # Create new filename
            dir_name = os.path.dirname(file_path)
            base_name = os.path.basename(file_path)
            parts = base_name.split('_')
            
            # Format ID as 4-digit number with leading zeros
            formatted_id = f"{scholar_id:04d}"
            
            # Check if the file already has the correct ID
            if len(parts) >= 2 and parts[1] == formatted_id:
                continue
                
            # Create new filename with proper ID
            new_filename = f"{scholar_name}_{formatted_id}_raw.txt"
            new_path = os.path.join(dir_name, new_filename)
            
            if dry_run:
                print(f"Would rename: {base_name} → {new_filename}")
            else:
                try:
                    shutil.move(file_path, new_path)
                    print(f"Renamed: {base_name} → {new_filename}")
                    renamed_count += 1
                except Exception as e:
                    print(f"Error renaming {file_path}: {e}")
        else:
            not_found_count += 1
            if delete_nonmatching:
                if dry_run:
                    print(f"Would delete: {os.path.basename(file_path)} (no VSS scholar ID found for: {scholar_name})")
                else:
                    try:
                        os.remove(file_path)
                        print(f"Deleted: {os.path.basename(file_path)} (no VSS scholar ID found for: {scholar_name})")
                        deleted_count += 1
                    except Exception as e:
                        print(f"Error deleting {file_path}: {e}")
            else:
                print(f"No VSS scholar ID found for: {scholar_name}")
    
    print(f"\nRenamed {renamed_count} files")
    if deleted_count > 0:
        print(f"Deleted {deleted_count} files without matching VSS data")
    elif not_found_count > 0 and not delete_nonmatching:
        print(f"Could not find VSS scholar IDs for {not_found_count} files")
    
    return renamed_count, not_found_count, deleted_count

def rename_markdown_files(vss_csv, perplexity_dir, markdown_dir, dry_run=False, delete_nonmatching=False):
    """
    Rename markdown files based on scholar IDs from VSS data and perplexity info.
    
    Args:
        vss_csv (str): Path to the VSS data CSV file
        perplexity_dir (str): Path to the perplexity info directory
        markdown_dir (str): Path to the Scholar Markdown directory
        dry_run (bool): If True, only show what would be renamed without actually renaming
        delete_nonmatching (bool): If True, delete files without matching scholar IDs
        
    Returns:
        tuple: (renamed_count, not_found_count, deleted_count)
    """
    # Read the VSS CSV file
    print(f"Reading data from {vss_csv}...")
    vss_df = pd.read_csv(vss_csv)
    
    # Get unique scholars from VSS data using scholar_id
    vss_scholars = vss_df[['scholar_id', 'scholar_name']].drop_duplicates('scholar_id')
    
    # Create normalized name column for comparison
    vss_scholars['normalized_name'] = vss_scholars['scholar_name'].apply(normalize_name)
    
    # Create a mapping from normalized name to scholar_id
    vss_name_to_id_map = dict(zip(vss_scholars['normalized_name'], vss_scholars['scholar_id']))
    
    # Get perplexity info files
    perplexity_files = glob.glob(os.path.join(perplexity_dir, "*_*_raw.txt"))
    print(f"Found {len(perplexity_files)} files in perplexity info directory")
    
    # Get markdown files
    markdown_files = glob.glob(os.path.join(markdown_dir, "*.md"))
    print(f"Found {len(markdown_files)} files in markdown directory")
    
    # Extract perplexity scholar names and IDs
    perplexity_scholars = []
    for file_path in perplexity_files:
        base_name = os.path.basename(file_path)
        parts = base_name.split('_')
        
        # Check if the file follows the expected format
        if len(parts) >= 3:
            scholar_name = parts[0]
            scholar_id = parts[1]
            
            # Clean up ID (remove leading zeros)
            try:
                id_num = int(scholar_id)
                perplexity_scholars.append({
                    'name': scholar_name,
                    'normalized_name': normalize_name(scholar_name),
                    'id': id_num,
                    'file_path': file_path
                })
            except ValueError:
                print(f"Warning: Invalid scholar ID in filename: {base_name}")
    
    # Create a mapping from normalized perplexity names to IDs
    perplexity_name_to_id_map = {}
    for scholar in perplexity_scholars:
        perplexity_name_to_id_map[scholar['normalized_name']] = scholar['id']
    
    # Get set of normalized names in perplexity data
    perplexity_normalized_names = set(perplexity_name_to_id_map.keys())
    
    # Process markdown files
    renamed_count = 0
    not_found_count = 0
    deleted_count = 0
    
    for md_file in markdown_files:
        base_name = os.path.basename(md_file)
        # Remove .md extension
        base_name_no_ext = os.path.splitext(base_name)[0]
        
        # Split by underscore to extract name and ID (if present)
        parts = base_name_no_ext.split('_')
        
        # Extract current name (everything before the last underscore)
        if len(parts) > 1:
            current_id = parts[-1]
            current_name = '_'.join(parts[:-1])
        else:
            current_id = None
            current_name = base_name_no_ext
        
        normalized_name = normalize_name(current_name)
        
        # Check if this scholar exists in perplexity data
        if normalized_name in perplexity_normalized_names:
            # Get the ID from perplexity data
            scholar_id = perplexity_name_to_id_map[normalized_name]
            
            # Format ID as 4-digit number with leading zeros
            formatted_id = f"{scholar_id:04d}"
            
            # Create new filename
            new_filename = f"{current_name}_{formatted_id}.md"
            new_path = os.path.join(markdown_dir, new_filename)
            
            # Check if we need to rename
            if base_name != new_filename:
                if dry_run:
                    print(f"Would rename: {base_name} → {new_filename}")
                else:
                    try:
                        shutil.move(md_file, new_path)
                        print(f"Renamed: {base_name} → {new_filename}")
                        renamed_count += 1
                    except Exception as e:
                        print(f"Error renaming {md_file}: {e}")
        else:
            # Try to find in VSS data if not in perplexity
            if normalized_name in vss_name_to_id_map:
                # Get the ID from VSS data
                scholar_id = vss_name_to_id_map[normalized_name]
                
                # Format ID as 4-digit number with leading zeros
                formatted_id = f"{scholar_id:04d}"
                
                # Create new filename
                new_filename = f"{current_name}_{formatted_id}.md"
                new_path = os.path.join(markdown_dir, new_filename)
                
                # Check if we need to rename
                if base_name != new_filename:
                    if dry_run:
                        print(f"Would rename (VSS match): {base_name} → {new_filename}")
                    else:
                        try:
                            shutil.move(md_file, new_path)
                            print(f"Renamed (VSS match): {base_name} → {new_filename}")
                            renamed_count += 1
                        except Exception as e:
                            print(f"Error renaming {md_file}: {e}")
            else:
                # Scholar not found in either perplexity or VSS data
                not_found_count += 1
                if delete_nonmatching:
                    if dry_run:
                        print(f"Would delete: {base_name} (no scholar ID found)")
                    else:
                        try:
                            os.remove(md_file)
                            print(f"Deleted: {base_name} (no scholar ID found)")
                            deleted_count += 1
                        except Exception as e:
                            print(f"Error deleting {md_file}: {e}")
                else:
                    print(f"Scholar not found in perplexity or VSS data: {current_name}")
    
    print(f"\nRenamed {renamed_count} files")
    if deleted_count > 0:
        print(f"Deleted {deleted_count} files without matching scholar IDs")
    elif not_found_count > 0 and not delete_nonmatching:
        print(f"Could not find corresponding IDs for {not_found_count} files")
    
    return renamed_count, not_found_count, deleted_count

def main():
    parser = argparse.ArgumentParser(description='Compare scholars between VSS data and perplexity info')
    parser.add_argument('--vss', type=str, default="data/vss_data.csv", help='Path to VSS data CSV file')
    parser.add_argument('--perplexity', type=str, default="data/perplexity_info", help='Path to perplexity info directory')
    parser.add_argument('--output', type=str, help='Path to save missing scholars list to CSV')
    parser.add_argument('--list-only', action='store_true', help='Only list missing scholars without comparison stats')
    parser.add_argument('--rename', action='store_true', help='Rename perplexity files using scholar IDs from VSS data')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be renamed without actually making changes')
    parser.add_argument('--delete-nonmatching', action='store_true', help='Delete files without matching VSS data')
    parser.add_argument('--markdown', type=str, default="data/scholar_markdown", help='Path to Scholar Markdown directory')
    parser.add_argument('--rename-markdown', action='store_true', help='Rename markdown files using scholar IDs from perplexity/VSS data')
    args = parser.parse_args()
    
    # Make sure the input file and directory exist
    if not os.path.exists(args.vss):
        print(f"Error: Input file {args.vss} does not exist.")
        sys.exit(1)
    
    if not os.path.exists(args.perplexity):
        print(f"Error: Perplexity info directory {args.perplexity} does not exist.")
        sys.exit(1)
    
    if args.rename_markdown:
        # Check if markdown directory exists
        if not os.path.exists(args.markdown):
            print(f"Error: Markdown directory {args.markdown} does not exist.")
            sys.exit(1)
        
        # Rename markdown files using scholar IDs from perplexity/VSS data
        rename_markdown_files(args.vss, args.perplexity, args.markdown, args.dry_run, args.delete_nonmatching)
    elif args.rename:
        # Rename perplexity files using VSS scholar IDs
        rename_perplexity_files(args.vss, args.perplexity, args.dry_run, args.delete_nonmatching)
    elif args.list_only:
        # Only list missing scholars
        missing_scholars, count = find_missing_scholars(args.vss, args.perplexity, args.output)
        
        # Print the list of missing scholars
        print("\nList of scholars in VSS data but missing from perplexity info:")
        for i, (_, scholar) in enumerate(missing_scholars.iterrows(), 1):
            print(f"{i}. {scholar['scholar_name']} (ID: {scholar['scholar_id']:04d})")
    else:
        # Compare VSS and perplexity data with full statistics
        compare_vss_and_perplexity_data(args.vss, args.perplexity, args.output)

if __name__ == "__main__":
    main()
