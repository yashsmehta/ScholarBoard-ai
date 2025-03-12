import os
import glob
import logging
from pathlib import Path
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

def format_scholar_info(raw_text, client):
    """Format raw scholar information into well-structured markdown."""
    prompt = f"""
    Format the following raw scholar information into a well-structured markdown document.
    Use proper markdown formatting with headers, bullet points, and sections.
    Make it visually appealing and easy to read (can use emojis). Dont use any other text than the requested information (directly start with the requested information).
    Remove any references, e.g. [1][2][3], etc.
    
    Here's the raw text:
    
    {raw_text}
    
    Format it into clean markdown with:
    - Main headers as H2 (##), + emojis: "Lab and Research Areas", "Core Research Questions", "Major Contributions", "Current Research / Ongoing Projects", "Methodology and Approach", "Research Beliefs / Philosophy", "Academic / Research Trajectory"
    - Proper bullet points and numbering
    - Emphasis on important information
    - Clean spacing between sections
    - dont use ```markdown at the beginning and end of the document
    - if it says - "not mentioned in the search results." - just skip it.
    """
    
    try:
        response = client.invoke(prompt)
        return response.content
    except Exception as e:
        logger.error(f"Error formatting scholar info: {e}")
        return None

def process_files():
    """Process all raw text files in the perplexity_info directory sequentially."""
    # Create Gemini client
    client = create_gemini_client()
    
    # Get all raw text files and sort them alphabetically
    raw_files_path = Path("data/perplexity_info")
    raw_files = sorted(list(raw_files_path.glob("*_raw.txt")))
    
    if not raw_files:
        logger.warning("No raw text files found in data/perplexity_info")
        return
    
    logger.info(f"Found {len(raw_files)} raw text files to process")
    logger.info("Files will be processed in alphabetical order")
    
    # Create output directory if it doesn't exist
    output_dir = Path("data/formatted_scholar_info")
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Process each file sequentially
    for i, raw_file in enumerate(raw_files, 1):
        logger.info(f"Processing file {i}/{len(raw_files)}: {raw_file.name}")
        
        # Skip if already processed
        filename_parts = raw_file.stem.split('_')
        scholar_name = filename_parts[0]
        scholar_id = filename_parts[1] if len(filename_parts) > 1 else "unknown"
        output_file = output_dir / f"{scholar_name}_{scholar_id}.md"
        
        if output_file.exists():
            logger.info(f"Skipping {raw_file.name} - already processed")
            continue
        
        # Read raw text
        try:
            with open(raw_file, 'r', encoding='utf-8') as f:
                raw_text = f.read()
        except Exception as e:
            logger.error(f"Error reading file {raw_file}: {e}")
            continue
        
        # Format text
        formatted_text = format_scholar_info(raw_text, client)
        if not formatted_text:
            logger.error(f"Failed to format {raw_file.name}")
            continue
        
        # Save formatted text
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(formatted_text)
            logger.info(f"Saved formatted file!")
        except Exception as e:
            logger.error(f"Error saving formatted file {output_file}: {e}")
            continue

def main():
    """Main function to run the formatter."""
    logger.info("Starting scholar info formatter")
    process_files()
    logger.info("Completed formatting scholar info")

if __name__ == "__main__":
    main()
