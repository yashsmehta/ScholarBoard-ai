import os
import time
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variable
API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not API_KEY:
    raise ValueError("DEEPSEEK_API_KEY not found in environment variables")

def clean_scholar_data(raw_text_path):
    """
    Clean scholar data using DeepSeek API
    """
    client = OpenAI(
        api_key=API_KEY,
        base_url="https://api.deepseek.com/v1"  # DeepSeek API endpoint
    )
    
    # Read the raw text file
    with open(raw_text_path, "r", encoding="utf-8") as f:
        raw_text = f.read()
    
    prompt = f"""
    Please clean and structure the following scholar information text. 
    Organize it into clear sections based on:
    
    1. Main research areas and disciplines
    2. Specific research questions
    3. Notable achievements and contributions
    4. Current research focus
    5. Research methodology
    6. Collaborations
    7. Impact of work
    
    Remove any redundant information, fix grammatical errors, and ensure the text is 
    well-structured and easy to read. Maintain all technical details and accuracy.
    
    Here is the text to clean:
    
    {raw_text}
    """
    
    try:
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that cleans and structures academic information about scholars. Your task is to organize information clearly while maintaining technical accuracy."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        response = client.chat.completions.create(
            model="deepseek-chat",  # Use appropriate DeepSeek model
            messages=messages
        )
        
        cleaned_content = response.choices[0].message.content
        
        # Create output file path
        output_file = raw_text_path.replace("_raw.txt", "_cleaned.txt")
        
        # Save cleaned content
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(cleaned_content)
            
        print(f"Cleaned data saved to {output_file}")
        return cleaned_content
    
    except Exception as e:
        print(f"Error using DeepSeek API: {e}")
        return None

def process_all_raw_files():
    """
    Process all raw scholar data files and clean them using DeepSeek API
    """
    # Get all raw text files
    raw_dir = Path("data/scholar_info")
    if not raw_dir.exists():
        print(f"Directory {raw_dir} does not exist")
        return
    
    raw_files = list(raw_dir.glob("*_raw.txt"))
    if not raw_files:
        print("No raw files found to process")
        return
    
    print(f"Found {len(raw_files)} raw files to process")
    
    # Process each file
    for i, file_path in enumerate(raw_files):
        print(f"Processing {i+1}/{len(raw_files)}: {file_path.name}")
        
        # Check if cleaned file already exists
        cleaned_path = str(file_path).replace("_raw.txt", "_cleaned.txt")
        if Path(cleaned_path).exists():
            print(f"Cleaned file already exists for {file_path.name}, skipping")
            continue
        
        # Clean the data
        clean_scholar_data(str(file_path))
        
        # Rate limiting
        if i < len(raw_files) - 1:
            time.sleep(2)
    
    print("All files processed!")

def main():
    process_all_raw_files()

if __name__ == "__main__":
    main() 