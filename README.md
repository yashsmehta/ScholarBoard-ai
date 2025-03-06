# Scientist Board

A project to analyze and visualize researchers based on their research areas.

## Components

### 1. Researcher Information Extraction

- `researcher_info/info_extractor.py`: Extracts researcher information from various sources
- `researcher_info/get_embeddings.py`: Generates embeddings for researcher research areas using OpenAI's API
- `researcher_info/create_umap.py`: Creates a 2D visualization of researcher similarity using UMAP

### 2. Researcher Database

- `data/researcher_database.npz`: Contains researcher data including embeddings and UMAP coordinates
- `data/researcher_metadata.json`: Contains researcher metadata in a readable JSON format
- `data/profile_pics/`: Contains profile pictures of researchers

### 3. Researcher Visualization Website

- `website/`: Contains a static website that visualizes researchers based on their UMAP coordinates
- `website/index.html`: The main HTML file for the website
- `website/css/styles.css`: CSS styles for the website
- `website/js/script.js`: JavaScript code for the interactive map
- `website/prepare_data.py`: Script to extract researcher data and copy profile pictures
- `website/serve.py`: Script to serve the website locally

## How to Run

### Generate Embeddings and UMAP

1. Set up your OpenAI API key in a `.env` file:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

2. Run the embedding generation script:
   ```
   python -m researcher_info.get_embeddings
   ```

3. Run the UMAP generation script:
   ```
   python -m researcher_info.create_umap
   ```

### Run the Visualization Website

1. Prepare the website data:
   ```
   python website/prepare_data.py
   ```

2. Run the website server:
   ```
   cd website && python serve.py
   ```

3. The website will open in your default browser at http://localhost:8000

## Features

- Generate embeddings for researcher research areas
- Reduce dimensionality of embeddings to 2D using UMAP
- Visualize researchers on a 2D map based on their research similarity
- Interactive web interface with zoom and pan functionality
- Profile pictures and institution information for each researcher

# Researcher Information Extractor

Queries Perplexity API to gather comprehensive information about researchers from a CSV file.

## Installation

```bash
# Install uv if you don't have it
curl -sSf https://astral.sh/uv/install.sh | bash

# Install the package
uv pip install -e .
```

## Configuration

Create a `.env` file with your Perplexity API key:

```
PERPLEXITY_API_KEY=your_api_key_here
```

## Input Format

Create `researchers.csv` with columns:
- `researcher_name`: Name of the researcher
- `institution`: Researcher's institution

Example:
```csv
researcher_name, institution
Michael Bonner, Johns Hopkins University
Tyler Bonnen, UC Berkeley
Nancy Kanwisher, MIT
```

## Usage

```bash
# Default usage (JSON output)
researcher-info

# CSV output format
researcher-info --format csv

# Custom input/output files
researcher-info --input my_researchers.csv --output results.json
```

Alternative Python usage:

```python
# JSON output (recommended)
from researcher_info.json_extractor import extract_researcher_info_json
extract_researcher_info_json(input_file="researchers.csv", output_file="researcher_areas.json")

# CSV output
from researcher_info.csv_extractor import extract_researcher_info
extract_researcher_info(input_file="researchers.csv", output_file="researcher_areas.csv")
```

## Output

### JSON Output (Recommended)
Structured data for each researcher:
```json
[
  {
    "name": "Researcher Name",
    "institution": "Institution Name",
    "info": {
      "research_areas": ["Area 1", "Area 2"],
      "research_questions": "Description of questions",
      "known_for": "What they're known for",
      "current_work": "Current research focus",
      "key_papers": ["Paper 1", "Paper 2"],
      "methodology": "Research approach",
      "collaborations": "Notable collaborations",
      "impact": "Impact on the field",
      "comprehensive_summary": "Detailed summary"
    }
  }
]
```

### CSV Output
Single file with columns for name, institution, and research information.

## Troubleshooting

- **Missing dependencies**: Run `uv pip install -e .` again
- **API key issues**: Ensure `.env` file exists with correct API key

Notes: Rate limited (2s between requests), progress saved after each researcher, uses "llama-3.1-sonar-large-128k-online" model. 