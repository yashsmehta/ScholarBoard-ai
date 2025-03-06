# Researcher Similarity Map

This is a static website that visualizes researchers based on their UMAP coordinates. The UMAP coordinates are generated from embeddings of the researchers' research areas, which captures the similarity between researchers.

## Features

- Interactive visualization of researchers based on their research similarity
- Profile pictures displayed in circles
- Hover over a researcher to see their name and institution
- Zoom and pan functionality to explore the map

## How to Run

1. Make sure you have Python installed
2. Run the prepare_data.py script to extract researcher data and copy profile pictures:
   ```
   python prepare_data.py
   ```
3. Run the serve.py script to start a local server and open the website:
   ```
   python serve.py
   ```
4. The website will open in your default browser at http://localhost:8000

## How It Works

1. The UMAP algorithm reduces the high-dimensional embeddings of researchers' research areas to 2D coordinates
2. The website positions each researcher on the map based on these coordinates
3. Researchers with similar research areas will be positioned closer together
4. The visualization helps to identify clusters and relationships between researchers

## Files

- `index.html`: The main HTML file for the website
- `css/styles.css`: CSS styles for the website
- `js/script.js`: JavaScript code for the interactive map
- `data/researchers.json`: JSON file containing researcher data
- `images/`: Directory containing researcher profile pictures
- `prepare_data.py`: Script to extract researcher data and copy profile pictures
- `serve.py`: Script to serve the website locally 