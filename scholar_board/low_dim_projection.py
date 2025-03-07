import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import xarray as xr
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.preprocessing import StandardScaler
import os
import warnings
from pathlib import Path
import json
warnings.filterwarnings('ignore')

def create_scholar_projections():
    """
    Create 2D visualizations of scholar similarity based on embeddings
    using multiple dimensionality reduction techniques (PCA, UMAP, t-SNE)
    and store the coordinates in the scholar embeddings file
    """
    # Load scholar embeddings from netCDF file
    try:
        embeddings_file = Path('data/scholar_embeddings.nc')
        if not embeddings_file.exists():
            print(f"Embeddings file not found: {embeddings_file}")
            return
        
        ds = xr.open_dataset(embeddings_file)
        print(f"Loaded embeddings for {ds.dims['scholar']} scholars")
        
    except Exception as e:
        print(f"Error loading scholar embeddings: {e}")
        return
    
    # Extract embeddings, scholar IDs, and names
    embeddings = ds.embedding.values
    scholar_ids = ds.scholar.values
    scholar_names = ds.scholar_name.values
    
    if len(embeddings) == 0:
        print("No embeddings found")
        return
    
    print(f"Processing {len(embeddings)} scholars")
    
    # Normalize embeddings
    embeddings_normalized = StandardScaler().fit_transform(embeddings)
    
    # Dictionary to store all projections
    projections = {}
    
    # 1. PCA projection
    print("Calculating PCA projection...")
    pca_model = PCA(n_components=2, random_state=42)
    pca_result = pca_model.fit_transform(embeddings_normalized)
    projections['pca'] = pca_result
    
    # 2. t-SNE projection
    print("Calculating t-SNE projection...")
    tsne_model = TSNE(n_components=2, perplexity=min(30, len(embeddings) - 1), 
                      random_state=42, n_iter=1000)
    tsne_result = tsne_model.fit_transform(embeddings_normalized)
    projections['tsne'] = tsne_result
    
    # 3. UMAP projection
    print("Calculating UMAP projection...")
    try:
        import umap
        umap_model = umap.UMAP(
            n_neighbors=min(15, len(embeddings) - 1),
            min_dist=0.1,
            n_components=2,
            metric='cosine',
            random_state=42
        )
        umap_result = umap_model.fit_transform(embeddings_normalized)
        projections['umap'] = umap_result
    except Exception as e:
        print(f"UMAP calculation failed: {e}")
    
    # Add projections to the dataset
    for method, result in projections.items():
        # Create new data variables for each projection method
        ds[f'{method}_x'] = xr.DataArray(
            result[:, 0], 
            dims='scholar',
            coords={'scholar': scholar_ids}
        )
        ds[f'{method}_y'] = xr.DataArray(
            result[:, 1], 
            dims='scholar',
            coords={'scholar': scholar_ids}
        )
    
    # Save updated dataset
    ds.to_netcdf(embeddings_file)
    print(f"Updated scholar embeddings with projections: {', '.join(projections.keys())}")
    
    # Also save a JSON file with projection coordinates for easy access
    projection_data = []
    for i, scholar_id in enumerate(scholar_ids):
        entry = {
            'scholar_id': scholar_id,
            'scholar_name': scholar_names[i],
        }
        
        # Add coordinates for each projection method
        for method in projections:
            entry[f'{method}_x'] = float(projections[method][i, 0])
            entry[f'{method}_y'] = float(projections[method][i, 1])
        
        projection_data.append(entry)
    
    # Save projection data to JSON
    projection_file = Path('data/scholar_projections.json')
    with open(projection_file, 'w') as f:
        json.dump(projection_data, f, indent=2)
    
    print(f"Saved projection data to {projection_file}")
    
    # Create visualizations
    create_projection_visualizations(projections, scholar_names)

def create_projection_visualizations(projections, scholar_names):
    """
    Create visualizations for each projection method
    """
    # Create directory for visualizations
    vis_dir = Path('data/visualizations')
    vis_dir.mkdir(exist_ok=True, parents=True)
    
    # Create a visualization for each projection method
    for method, result in projections.items():
        plt.figure(figsize=(12, 10))
        
        # Plot points
        scatter = plt.scatter(
            result[:, 0], 
            result[:, 1],
            c=np.arange(len(scholar_names)),
            cmap='viridis',
            s=100,
            alpha=0.7
        )
        
        # Add name labels
        for i, name in enumerate(scholar_names):
            plt.annotate(
                name,
                (result[i, 0], result[i, 1]),
                xytext=(5, 5),
                textcoords='offset points',
                fontsize=9
            )
        
        # Style the plot
        plt.colorbar(scatter, label='Scholar Index')
        plt.title(f'Scholar Similarity Map ({method.upper()})', fontsize=16)
        plt.xlabel('Dimension 1')
        plt.ylabel('Dimension 2')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()
        
        # Save the plot
        img_path = vis_dir / f'scholar_map_{method}.png'
        plt.savefig(img_path, dpi=300, bbox_inches='tight')
        print(f"Created visualization: {img_path}")
        
        plt.close()

if __name__ == "__main__":
    create_scholar_projections() 