# ScholarBoard.ai

A project to analyze and visualize scholars based on their research areas.

## Components

### 1. Scholar Information Extraction

- `scholar_board/scholar_info/plex_info_extractor.py`: Extracts scholar information using Plexity API
- `scholar_board/scholar_info/deepseek_cleaner.py`: Cleans scholar data using DeepSeek API
- `scholar_board/get_embeddings.py`: Generates embeddings for scholar research areas using OpenAI's API
- `scholar_board/low_dim_projection.py`: Creates 2D projections using PCA, UMAP, and t-SNE

### 2. Scholar Database

- `data/scholar_embeddings.nc`: Contains scholar embeddings and projections in xarray netCDF format
- `data/scholar_metadata.json`: Contains scholar metadata in a readable JSON format
- `data/scholar_projections.json`: Contains 2D coordinates for each projection method
- `data/scholar_info/`: Contains raw and cleaned text files for each scholar
- `data/profile_pics/`: Contains profile pictures of scholars
- `data/visualizations/`: Contains visualization plots of the projections

### 3. Scholar Visualization Website

- `website/`: Contains a static website that visualizes scholars based on their research similarity
- `website/index.html`: The main HTML file for the website
- `website/css/styles.css`: CSS styles for the website
- `website/js/script.js`: JavaScript code for the interactive map
- `website/prepare_data.py`: Script to extract scholar data and copy profile pictures
- `website/serve.py`: Script to serve the website locally

## How to Run

### Complete Pipeline

1. Set up your API keys in a `.env` file:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   PERPLEXITY_API_KEY=your_perplexity_api_key_here
   DEEPSEEK_API_KEY=your_deepseek_api_key_here
   ```

2. Run the complete pipeline:
   ```
   python scripts/run_pipeline.py
   ```

### Individual Steps

1. Update CSV columns from researcher_* to scholar_*:
   ```
   python scripts/update_csv_columns.py
   ```

2. Extract scholar info using Plexity API:
   ```
   python -m scholar_board.scholar_info.plex_info_extractor
   ```

3. Clean scholar data using DeepSeek API:
   ```
   python -m scholar_board.scholar_info.deepseek_cleaner
   ```

4. Generate embeddings:
   ```
   python -m scholar_board.get_embeddings
   ```

5. Generate low-dimensional projections:
   ```
   python -m scholar_board.low_dim_projection
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

- Generate embeddings for scholar research areas
- Store embeddings efficiently using xarray
- Create multiple 2D projections using PCA, UMAP, and t-SNE
- Visualize scholars on a 2D map based on their research similarity
- Interactive web interface with zoom and pan functionality
- Profile pictures and institution information for each scholar

# Scholar Information Extractor

Queries Plexity API to gather comprehensive information about scholars from a CSV file, cleans the data using DeepSeek API, and generates embeddings.

## Installation

```bash
# Install uv if you don't have it
curl -sSf https://astral.sh/uv/install.sh | bash

# Install the package
uv pip install -e .
```

## Configuration

Create a `.env` file with your API keys:

```
PERPLEXITY_API_KEY=your_perplexity_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

## Input Format

Create `scholars.csv` with columns:
- `scholar_id`: Unique identifier for the scholar
- `scholar_name`: Name of the scholar
- `institution`: Scholar's institution
- `country`: Scholar's country

Example:
```csv
scholar_id,scholar_name,institution,country
001,Michael Bonner,Johns Hopkins University,USA
002,Leyla Isik,Johns Hopkins University,USA
003,Nancy Kanwisher,MIT,USA
```

## Data Processing Pipeline

1. **Data Collection**: Extract scholar information using Plexity API
   - Raw data saved to `data/scholar_info/<scholar_name>_<scholar_id>_raw.txt`

2. **Data Cleaning**: Clean and structure the raw data using DeepSeek API
   - Cleaned data saved to `data/scholar_info/<scholar_name>_<scholar_id>_cleaned.txt`

3. **Embedding Generation**: Generate embeddings from cleaned data using OpenAI API
   - Embeddings saved to `data/scholar_embeddings.nc` in xarray format

4. **Dimensionality Reduction**: Generate 2D projections using multiple methods
   - PCA: Linear dimensionality reduction
   - t-SNE: Non-linear dimensionality reduction that preserves local structure
   - UMAP: Non-linear dimensionality reduction that preserves both local and global structure
   - Projections saved to the same xarray dataset and to `data/scholar_projections.json`
   - Visualizations saved to `data/visualizations/`

## Troubleshooting

- **Missing dependencies**: Run `uv pip install -e .` again
- **API key issues**: Ensure `.env` file exists with correct API keys
- **Directory structure**: Ensure required directories exist

Notes: Rate limited (2s between requests), progress saved after each scholar, uses "sonar-pro-online" model for Plexity API and "text-embedding-3-small" for embeddings. 