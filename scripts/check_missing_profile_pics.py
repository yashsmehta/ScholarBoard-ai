#!/usr/bin/env python3
import os
import csv
from pathlib import Path
import pandas as pd

def check_missing_profile_pics():
    """
    Check which scholar IDs don't have profile pictures and generate statistics.
    """
    # Define paths
    data_dir = Path("data")
    profile_pics_dir = data_dir / "profile_pics"
    scholars_csv = data_dir / "scholars.csv"
    
    # Ensure directories and files exist
    if not profile_pics_dir.exists():
        raise FileNotFoundError(f"Profile pictures directory not found: {profile_pics_dir}")
    
    if not scholars_csv.exists():
        raise FileNotFoundError(f"Scholars CSV file not found: {scholars_csv}")
    
    # Get all profile picture filenames (without extension)
    profile_pic_ids = set()
    for file_path in profile_pics_dir.glob("*.*"):
        # Extract ID from filename (remove extension)
        profile_pic_ids.add(file_path.stem)
    
    print(f"Found {len(profile_pic_ids)} profile pictures")
    
    # Load scholar IDs from CSV
    scholars_df = pd.read_csv(scholars_csv)
    
    # Ensure scholar_id is properly formatted as a 3-digit string
    scholars_df["scholar_id"] = scholars_df["scholar_id"].astype(str).str.zfill(3)
    scholar_ids = set(scholars_df["scholar_id"])
    
    print(f"Found {len(scholar_ids)} scholars in the CSV")
    
    # Find missing profile pictures
    missing_ids = scholar_ids - profile_pic_ids
    
    # Print results
    print(f"\nMissing profile pictures: {len(missing_ids)} scholars")
    print(f"Coverage: {(len(scholar_ids) - len(missing_ids)) / len(scholar_ids) * 100:.2f}%")
    
    # Print the missing IDs
    if missing_ids:
        print("\nScholars without profile pictures:")
        for scholar_id in sorted(missing_ids):
            # Get the scholar name if available
            scholar_name = scholars_df.loc[scholars_df["scholar_id"] == scholar_id, "scholar_name"].values
            if len(scholar_name) > 0:
                print(f"  - ID: {scholar_id}, Name: {scholar_name[0]}")
            else:
                print(f"  - ID: {scholar_id}")

if __name__ == "__main__":
    check_missing_profile_pics() 