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
from matplotlib.colors import ListedColormap
import joblib
warnings.filterwarnings('ignore')

def plot_projections(low_dim_ds, output_dir=None):
    """
    Create and save plots for PCA, t-SNE, and UMAP projections
    
    Parameters:
    -----------
    low_dim_ds : xarray.Dataset
        Dataset containing the low-dimensional projections
    output_dir : str or Path, optional
        Directory to save the plots. If None, plots are shown but not saved.
    """
    if output_dir is not None:
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True, parents=True)
    
    projection_methods = ['pca', 'tsne', 'umap']
    titles = {
        'pca': 'PCA Projection of Scholar Embeddings',
        'tsne': 't-SNE Projection of Scholar Embeddings',
        'umap': 'UMAP Projection of Scholar Embeddings'
    }
    
    # Create a figure for each projection method
    for method in projection_methods:
        if f'{method}_x' not in low_dim_ds or f'{method}_y' not in low_dim_ds:
            print(f"Skipping {method} plot - coordinates not found")
            continue
            
        fig, ax = plt.figure(figsize=(12, 10)), plt.gca()
        
        # Get coordinates
        x = low_dim_ds[f'{method}_x'].values
        y = low_dim_ds[f'{method}_y'].values
        
        # Create scatter plot
        scatter = ax.scatter(x, y, alpha=0.7, s=50)
        
        # Add labels for a subset of points (to avoid overcrowding)
        n_scholars = len(low_dim_ds.scholar_id)
        label_indices = np.random.choice(n_scholars, min(20, n_scholars), replace=False)
        
        for idx in label_indices:
            name = low_dim_ds.scholar_name.values[idx]
            ax.annotate(
                name,
                (x[idx], y[idx]),
                fontsize=8,
                alpha=0.8,
                xytext=(5, 5),
                textcoords='offset points'
            )
        
        # Add title and labels
        ax.set_title(titles[method], fontsize=14)
        ax.set_xlabel(f'{method.upper()} Dimension 1', fontsize=12)
        ax.set_ylabel(f'{method.upper()} Dimension 2', fontsize=12)
        
        # Add grid
        ax.grid(alpha=0.3)
        
        # Tight layout
        plt.tight_layout()
        
        # Save or show the plot
        if output_dir is not None:
            plt.savefig(output_dir / f'{method}_projection.png', dpi=300, bbox_inches='tight')
            print(f"Saved {method} projection plot to {output_dir / f'{method}_projection.png'}")
        else:
            plt.show()
        
        plt.close()

def project_new_embedding(embedding, models_dir=None):
    """
    Project a new embedding onto the existing low-dimensional space
    
    Parameters:
    -----------
    embedding : numpy.ndarray
        The embedding vector to project (should have the same dimension as training embeddings)
    models_dir : str or Path, optional
        Directory where the models are saved. If None, uses default location.
        
    Returns:
    --------
    dict
        Dictionary with projection coordinates for each method
    """
    # Get the project root directory if models_dir not specified
    if models_dir is None:
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        models_dir = project_root / 'data' / 'models'
    else:
        models_dir = Path(models_dir)
    
    # Check if models directory exists
    if not models_dir.exists():
        raise FileNotFoundError(f"Models directory not found: {models_dir}")
    
    # Load the scaler
    scaler_path = models_dir / 'scaler.joblib'
    if not scaler_path.exists():
        raise FileNotFoundError(f"Scaler not found: {scaler_path}")
    
    scaler = joblib.load(scaler_path)
    
    # Normalize the embedding
    if embedding.ndim == 1:
        embedding = embedding.reshape(1, -1)
    embedding_normalized = scaler.transform(embedding)
    
    # Dictionary to store projections
    projections = {}
    
    # Project using each available method
    for method in ['pca', 'tsne', 'umap']:
        model_path = models_dir / f'{method}_model.joblib'
        if model_path.exists():
            try:
                model = joblib.load(model_path)
                result = model.transform(embedding_normalized)
                projections[method] = {
                    'x': float(result[0, 0]),
                    'y': float(result[0, 1])
                }
            except Exception as e:
                print(f"Error projecting with {method}: {e}")
    
    return projections

def create_scholar_projections():
    """
    Create 2D visualizations of scholar similarity based on embeddings
    using multiple dimensionality reduction techniques (PCA, UMAP, t-SNE)
    and store the coordinates in a separate low-dimensional embeddings file
    """
    # Get the project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    data_dir = project_root / 'data'
    
    # Create models directory
    models_dir = data_dir / 'models'
    models_dir.mkdir(exist_ok=True, parents=True)
    
    # Load scholar embeddings from netCDF file
    try:
        embeddings_file = data_dir / 'scholar_embeddings.nc'
        if not embeddings_file.exists():
            print(f"Embeddings file not found: {embeddings_file}")
            return
        
        ds = xr.open_dataset(embeddings_file)
        print(f"Loaded embeddings for {ds.dims['scholar']} scholars")
        
    except Exception as e:
        print(f"Error loading scholar embeddings: {e}")
        return
    
    # Load scholar metadata
    try:
        scholars_csv = data_dir / 'scholars.csv'
        if not scholars_csv.exists():
            print(f"Scholars CSV file not found: {scholars_csv}")
            return
        
        # Read CSV with scholar_id as string to preserve leading zeros
        scholars_df = pd.read_csv(scholars_csv, dtype={'scholar_id': str})
        print(f"Loaded metadata for {len(scholars_df)} scholars")
        
    except Exception as e:
        print(f"Error loading scholar metadata: {e}")
        return
    
    # Extract embeddings, scholar IDs, and names
    embeddings = ds.embedding.values
    scholar_ids = ds.scholar_id.values
    scholar_names = ds.scholar_name.values
    
    # Debug: Print some sample IDs from both sources
    print(f"Sample scholar IDs from embeddings: {scholar_ids[:5]}")
    print(f"Sample scholar IDs from CSV: {scholars_df['scholar_id'].values[:5]}")
    
    if len(embeddings) == 0:
        print("No embeddings found")
        return
    
    print(f"Processing {len(embeddings)} scholars with embedding dimension {embeddings.shape[1]}")
    
    # Normalize embeddings
    scaler = StandardScaler()
    embeddings_normalized = scaler.fit_transform(embeddings)
    
    # Save the scaler
    joblib.dump(scaler, models_dir / 'scaler.joblib')
    print(f"Saved scaler to {models_dir / 'scaler.joblib'}")
    
    # Dictionary to store all projections
    projections = {}
    
    # 1. PCA projection
    print("Calculating PCA projection...")
    pca_model = PCA(n_components=2, random_state=42)
    pca_result = pca_model.fit_transform(embeddings_normalized)
    projections['pca'] = pca_result
    
    # Save PCA model
    joblib.dump(pca_model, models_dir / 'pca_model.joblib')
    print(f"Saved PCA model to {models_dir / 'pca_model.joblib'}")
    
    # 2. t-SNE projection
    print("Calculating t-SNE projection...")
    tsne_model = TSNE(n_components=2, perplexity=min(30, len(embeddings) - 1), 
                      random_state=42, n_iter=1000)
    tsne_result = tsne_model.fit_transform(embeddings_normalized)
    projections['tsne'] = tsne_result
    
    # Note: t-SNE doesn't support transform for new data directly
    # We'll use a workaround with a wrapper class
    class TSNEWrapper:
        def __init__(self, tsne_model, reference_data):
            self.tsne_model = tsne_model
            self.reference_data = reference_data
            self.reference_embedding = tsne_result
            
        def transform(self, new_data):
            # For t-SNE, we need to rerun fit_transform with the new point included
            # and then extract just the new point's coordinates
            # This is an approximation and not as accurate as the original embedding
            from sklearn.metrics.pairwise import cosine_similarity
            
            # Find the most similar point in the reference data
            similarities = cosine_similarity(new_data, self.reference_data)
            most_similar_idx = similarities.argmax()
            
            # Return the coordinates of the most similar point
            return self.reference_embedding[most_similar_idx].reshape(1, -1)
    
    tsne_wrapper = TSNEWrapper(tsne_model, embeddings_normalized)
    joblib.dump(tsne_wrapper, models_dir / 'tsne_model.joblib')
    print(f"Saved t-SNE wrapper model to {models_dir / 'tsne_model.joblib'}")
    
    # 3. UMAP projection
    print("Calculating UMAP projection...")
    try:
        import umap
        umap_model = umap.UMAP(
            n_neighbors=10,
            min_dist=0.1,
            n_components=2,
            metric='cosine',
            random_state=42
        )
        umap_result = umap_model.fit_transform(embeddings_normalized)
        projections['umap'] = umap_result
        
        # Save UMAP model
        joblib.dump(umap_model, models_dir / 'umap_model.joblib')
        print(f"Saved UMAP model to {models_dir / 'umap_model.joblib'}")
        
    except Exception as e:
        print(f"UMAP calculation failed: {e}")
    
    # Create a new dataset for low-dimensional projections
    low_dim_ds = xr.Dataset(coords={
        'scholar': np.arange(len(scholar_ids)),
        'scholar_id': ('scholar', list(scholar_ids)),
        'scholar_name': ('scholar', list(scholar_names))
    })
    
    # Add projections to the dataset
    for method, result in projections.items():
        # Create data variables for each projection method (x and y coordinates)
        low_dim_ds[f'{method}_x'] = xr.DataArray(
            result[:, 0], 
            dims='scholar'
        )
        low_dim_ds[f'{method}_y'] = xr.DataArray(
            result[:, 1], 
            dims='scholar'
        )
    
    # Save as a separate netCDF file
    output_file = data_dir / 'low_dim_embeddings.nc'
    low_dim_ds.to_netcdf(output_file)
    print(f"Saved low-dimensional projections to {output_file}")
    
    # Also save a JSON file with projection coordinates for easy access
    projection_data = []
    for i in range(len(scholar_ids)):
        entry = {
            'scholar_id': scholar_ids[i],
            'scholar_name': scholar_names[i]
        }
        
        # Add coordinates for each projection method
        for method in projections:
            entry[f'{method}_x'] = float(projections[method][i, 0])
            entry[f'{method}_y'] = float(projections[method][i, 1])
        
        projection_data.append(entry)
    
    # Create visualization plots
    plots_dir = data_dir / 'plots'
    plot_projections(low_dim_ds, plots_dir)
    print(f"Created projection plots in {plots_dir}")
    
    return low_dim_ds


if __name__ == "__main__":
    create_scholar_projections() 