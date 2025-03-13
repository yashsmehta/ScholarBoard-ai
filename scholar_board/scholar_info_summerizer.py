import os
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

def generate_scholar_summary(markdown_content, client):
    """Generate a three-sentence technical summary of scholar based on their markdown info."""
    prompt = f"""
    Generate a precisely three-sentence technical summary for this vision scientist, based solely on the provided information.
    Sentence 1: Articulate their specific research focus within vision science (avoid generic terms like "vision scientist").
    Sentence 2: Describe their research questions / problems they are trying to solve.
    Sentence 3: Highlight their most significant contributions or findings to the field of vision science.

Use technical academic language appropriate for publication. Do not fabricate information not present in the source material.

Scholar Information:
{markdown_content}
"""
    
    try:
        response = client.invoke(prompt)
        return response.content
    except Exception as e:
        logger.error(f"Error generating scholar summary: {e}")
        return None

def process_scholar_files():
    """Process all markdown files in the scholar_markdown directory and generate summaries."""
    # Create Gemini client
    client = create_gemini_client()
    
    # Get all markdown files
    markdown_files_path = Path("data/scholar_markdown")
    markdown_files = sorted(list(markdown_files_path.glob("*.md")))
    
    if not markdown_files:
        logger.warning("No markdown files found in data/scholar_markdown")
        return
    
    logger.info(f"Found {len(markdown_files)} scholar markdown files to process")
    
    # Create output directory for summaries if it doesn't exist
    output_dir = Path("data/scholar_summaries")
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Process each file sequentially
    for i, markdown_file in enumerate(markdown_files, 1):
        logger.info(f"Processing file {i}/{len(markdown_files)}: {markdown_file.name}")
        
        # Extract scholar identifier from filename
        scholar_id = markdown_file.stem
        output_file = output_dir / f"{scholar_id}_summary.txt"
        
        if output_file.exists():
            logger.info(f"Skipping {markdown_file.name} - summary already exists")
            continue
        
        # Read markdown content
        try:
            with open(markdown_file, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
        except Exception as e:
            logger.error(f"Error reading file {markdown_file}: {e}")
            continue
        
        # Generate summary
        summary = generate_scholar_summary(markdown_content, client)
        if not summary:
            logger.error(f"Failed to generate summary for {markdown_file.name}")
            continue
        
        # Save summary
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(summary)
            logger.info(f"Saved summary for {scholar_id}")
        except Exception as e:
            logger.error(f"Error saving summary file {output_file}: {e}")
            continue

def main():
    """Main function to run the scholar summarizer."""
    logger.info("Starting scholar summary generator")
    process_scholar_files()
    logger.info("Completed generating scholar summaries")

if __name__ == "__main__":
    main()