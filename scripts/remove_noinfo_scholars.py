#!/usr/bin/env python3
import os
import csv
import json
import sys
from pathlib import Path

# List of scholars to remove
NO_INFO_SCHOLARS = [
    "Greta Manini", "Kacie Lee", "Isabella M Durda", "Emily Oor", 
    "Megan Broderick", "Anton Janser", "Ilan Vol", "Mowei Zhen", 
    "Dasha Zdvizhkova", "Hyosun Kim", "AJ Jansen", "Margaret McCray", 
    "Amy Sultana", "Süheyla Aydemir", "Luiz Henrique Canto-Pereira", 
    "Rebecca Roy", "Jenny W. S. Chiu", "Mabel Shanahan", 
    "Ruggero Micheletto", "Enrico Guarnuto", "Jr."
]

def get_project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent

def find_scholar_files(scholar_name):
    """Find all files related to a scholar."""
    root_dir = get_project_root()
    files_to_delete = []
    
    # Check in scholars.csv
    scholars_csv = root_dir / "data" / "scholars.csv"
    scholar_id = None
    
    if scholars_csv.exists():
        with open(scholars_csv, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            for row in reader:
                if len(row) >= 2 and row[1] == scholar_name:
                    scholar_id = row[0]
                    break
    
    if scholar_id:
        print(f"Found scholar {scholar_name} with ID {scholar_id}")
    else:
        print(f"Scholar {scholar_name} not found in scholars.csv")
        return [], None
    
    # Check for markdown files
    markdown_dir = root_dir / "data" / "scholar_markdown"
    if markdown_dir.exists():
        for file in markdown_dir.glob(f"{scholar_name}_*.md"):
            files_to_delete.append(file)
    
    # Check for summary files
    summary_dir = root_dir / "data" / "scholar_summaries"
    if summary_dir.exists():
        for file in summary_dir.glob(f"{scholar_name}_*_summary.txt"):
            files_to_delete.append(file)
    
    # Check for perplexity info files
    perplexity_dir = root_dir / "data" / "perplexity_info"
    if perplexity_dir.exists():
        for file in perplexity_dir.glob(f"{scholar_name}_*.json"):
            files_to_delete.append(file)
        # Also check for raw.txt files
        for file in perplexity_dir.glob(f"{scholar_name}_*_raw.txt"):
            files_to_delete.append(file)
        
    # Check for perplexity reflection files
    reflection_dir = root_dir / "data" / "perplexity_reflection"
    if reflection_dir.exists():
        for file in reflection_dir.glob(f"{scholar_name}_*_reflection.txt"):
            files_to_delete.append(file)
    
    return files_to_delete, scholar_id

def remove_from_scholars_csv(scholar_name):
    """Remove a scholar from the scholars.csv file."""
    root_dir = get_project_root()
    scholars_csv = root_dir / "data" / "scholars.csv"
    
    if not scholars_csv.exists():
        print(f"scholars.csv not found at {scholars_csv}")
        return False, None
    
    # Read the CSV file
    rows = []
    scholar_id = None
    with open(scholars_csv, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        rows.append(header)
        for row in reader:
            if len(row) >= 2 and row[1] == scholar_name:
                scholar_id = row[0]
                continue
            rows.append(row)
    
    # Write the CSV file back
    with open(scholars_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    
    return True, scholar_id

def remove_from_json_files(scholar_name, scholar_id):
    """Remove a scholar from JSON files like scholars.json and clusters.json."""
    if not scholar_id:
        print(f"No scholar ID found for {scholar_name}, skipping JSON removal")
        return
    
    root_dir = get_project_root()
    
    # Handle scholars.json
    scholars_json = root_dir / "data" / "scholars.json"
    if scholars_json.exists():
        try:
            with open(scholars_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # scholars.json is a dictionary with scholar_id as keys
            if scholar_id in data:
                del data[scholar_id]
                print(f"Removed {scholar_name} (ID: {scholar_id}) from scholars.json")
            
            with open(scholars_json, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error processing scholars.json: {e}")
    
    # Handle clusters.json
    clusters_json = root_dir / "data" / "clusters.json"
    if clusters_json.exists():
        try:
            with open(clusters_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # clusters.json has a structure with scholars in each cluster
            for cluster_id, cluster_data in data.items():
                if 'scholars' in cluster_data:
                    # Filter out the scholar by ID
                    cluster_data['scholars'] = [
                        s for s in cluster_data['scholars'] 
                        if s.get('id') != scholar_id
                    ]
                    # Update the size
                    cluster_data['size'] = len(cluster_data['scholars'])
            
            with open(clusters_json, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            print(f"Removed {scholar_name} (ID: {scholar_id}) from clusters.json")
        except Exception as e:
            print(f"Error processing clusters.json: {e}")

def main():
    """Main function to remove scholars with no information."""
    print("Starting removal of scholars with no information...")
    
    for scholar_name in NO_INFO_SCHOLARS:
        print(f"\nProcessing scholar: {scholar_name}")
        
        # Find files to delete
        files_to_delete, scholar_id = find_scholar_files(scholar_name)
        
        if not files_to_delete:
            print(f"No files found for {scholar_name}")
            
            # Still try to remove from CSV and JSON
            success, found_id = remove_from_scholars_csv(scholar_name)
            if found_id:
                scholar_id = found_id
            
            if scholar_id:
                remove_from_json_files(scholar_name, scholar_id)
            
            print(f"Finished processing {scholar_name}, continuing to next scholar")
            continue
        
        # Ask for confirmation
        print(f"Found {len(files_to_delete)} files for {scholar_name}:")
        for file in files_to_delete:
            print(f"  - {file}")
        
        confirm = input(f"Delete these files and remove {scholar_name} from database? (y/n): ")
        
        if confirm.lower() == 'y':
            # Delete files
            for file in files_to_delete:
                try:
                    os.remove(file)
                    print(f"Deleted {file}")
                except Exception as e:
                    print(f"Error deleting {file}: {e}")
            
            # Remove from CSV
            success, found_id = remove_from_scholars_csv(scholar_name)
            if success:
                print(f"Removed {scholar_name} from scholars.csv")
                if found_id:
                    scholar_id = found_id
            
            # Remove from JSON files
            if scholar_id:
                remove_from_json_files(scholar_name, scholar_id)
            
            print(f"Successfully removed {scholar_name}")
        else:
            print(f"Skipping {scholar_name}")
        
        print(f"Finished processing {scholar_name}, continuing to next scholar")

if __name__ == "__main__":
    main()
