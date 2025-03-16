import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import xarray as xr
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
from sklearn.manifold import TSNE
import os
import warnings
from pathlib import Path
import json
import joblib
warnings.filterwarnings('ignore')

def plot_projections(low_dim_ds, output_dir=None):
    """
    Create and save plots for low-dimensional projections with different configurations
    
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
    
    # Get all projection configurations from the dataset
    projection_configs = []
    for var in low_dim_ds.data_vars:
        if var.endswith('_x'):
            config = var[:-2]  # Remove the '_x' suffix
            projection_configs.append(config)
    
    print(f"Found {len(projection_configs)} projection configurations: {projection_configs}")
    
    # Create a figure for each projection configuration
    for config in projection_configs:
        if f'{config}_x' not in low_dim_ds or f'{config}_y' not in low_dim_ds:
            print(f"Skipping {config} plot - coordinates not found")
            continue
            
        fig, ax = plt.figure(figsize=(12, 10)), plt.gca()
        
        # Get coordinates
        x = low_dim_ds[f'{config}_x'].values
        y = low_dim_ds[f'{config}_y'].values
        
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
        
        # Extract method and parameters from config name
        config_parts = config.split('_')
        method = config_parts[0]
        
        if method == 'umap':
            if len(config_parts) >= 3:
                n_neighbors = config_parts[1].replace('n', '')
                min_dist = config_parts[2].replace('d', '')
                title = f'UMAP Projection (n_neighbors={n_neighbors}, min_dist={min_dist})'
            else:
                title = f'UMAP Projection ({config})'
        elif method == 'tsne':
            if len(config_parts) >= 3:
                perplexity = config_parts[1].replace('p', '')
                learning_rate = config_parts[2].replace('lr', '')
                title = f't-SNE Projection (perplexity={perplexity}, learning_rate={learning_rate})'
            else:
                title = f't-SNE Projection ({config})'
        else:
            title = f'Projection ({config})'
        
        # Add title and labels
        ax.set_title(title, fontsize=14)
        ax.set_xlabel(f'{method.upper()} Dimension 1', fontsize=12)
        ax.set_ylabel(f'{method.upper()} Dimension 2', fontsize=12)
        
        # Add grid
        ax.grid(alpha=0.3)
        
        # Tight layout
        plt.tight_layout()
        
        # Save or show the plot
        if output_dir is not None:
            plt.savefig(output_dir / f'{config}_projection.png', dpi=300, bbox_inches='tight')
            print(f"Saved {config} projection plot to {output_dir / f'{config}_projection.png'}")
        else:
            plt.show()
        
        plt.close()

def plot_projections_with_clusters(low_dim_ds, config_name, output_dir=None):
    """
    Create and save a plot for projection with DBSCAN clusters
    
    Parameters:
    -----------
    low_dim_ds : xarray.Dataset
        Dataset containing the low-dimensional projections and cluster assignments
    config_name : str
        Name of the projection configuration to plot
    output_dir : str or Path, optional
        Directory to save the plots. If None, plots are shown but not saved.
    """
    if output_dir is not None:
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True, parents=True)
    
    if f'{config_name}_x' not in low_dim_ds or f'{config_name}_y' not in low_dim_ds:
        print(f"Skipping {config_name} plot - coordinates not found")
        return
    
    if f'{config_name}_cluster' not in low_dim_ds:
        print(f"Skipping {config_name} plot - cluster assignments not found")
        return
        
    # Get coordinates and cluster assignments
    x = low_dim_ds[f'{config_name}_x'].values
    y = low_dim_ds[f'{config_name}_y'].values
    clusters = low_dim_ds[f'{config_name}_cluster'].values
    
    # Create figure
    fig, ax = plt.figure(figsize=(14, 12)), plt.gca()
    
    # Get unique clusters
    unique_clusters = np.unique(clusters)
    n_clusters = len(unique_clusters) - (1 if -1 in unique_clusters else 0)
    n_noise = list(clusters).count(-1)
    
    # Create a colormap
    colors = plt.cm.Spectral(np.linspace(0, 1, len(unique_clusters)))
    
    # Plot each cluster
    for i, cluster in enumerate(unique_clusters):
        # Get mask for points in this cluster
        mask = clusters == cluster
        
        # Set color (black for noise points)
        color = 'k' if cluster == -1 else colors[i]
        
        # Plot points
        ax.scatter(
            x[mask], y[mask],
            s=50 if cluster == -1 else 80,
            color=color,
            alpha=0.6 if cluster == -1 else 0.8,
            label=f'Cluster {cluster}' if cluster != -1 else 'Noise'
        )
    
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
    
    # Extract method and parameters from config name
    config_parts = config_name.split('_')
    method = config_parts[0]
    
    if method == 'umap':
        if len(config_parts) >= 3:
            n_neighbors = config_parts[1].replace('n', '')
            min_dist = config_parts[2].replace('d', '')
            title = f'UMAP Projection (n_neighbors={n_neighbors}, min_dist={min_dist})\n'
        else:
            title = f'UMAP Projection ({config_name})\n'
    elif method == 'tsne':
        if len(config_parts) >= 3:
            perplexity = config_parts[1].replace('p', '')
            learning_rate = config_parts[2].replace('lr', '')
            title = f't-SNE Projection (perplexity={perplexity}, learning_rate={learning_rate})\n'
        else:
            title = f't-SNE Projection ({config_name})\n'
    else:
        title = f'Projection ({config_name})\n'
    
    title += f'DBSCAN Clustering: {n_clusters} clusters, {n_noise} noise points'
    
    # Add title and labels
    ax.set_title(title, fontsize=14)
    ax.set_xlabel(f'{method.upper()} Dimension 1', fontsize=12)
    ax.set_ylabel(f'{method.upper()} Dimension 2', fontsize=12)
    
    # Add legend
    ax.legend(loc='best')
    
    # Add grid
    ax.grid(alpha=0.3)
    
    # Tight layout
    plt.tight_layout()
    
    # Save or show the plot
    if output_dir is not None:
        plt.savefig(output_dir / f'{config_name}_clusters.png', dpi=300, bbox_inches='tight')
        print(f"Saved {config_name} cluster plot to {output_dir / f'{config_name}_clusters.png'}")
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
        Dictionary with projection coordinates for each configuration
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
    
    # Find all model files (both UMAP and t-SNE)
    model_files = list(models_dir.glob('*_model.joblib'))
    
    if not model_files:
        print("No projection models found")
        return projections
    
    # Project using each model
    for model_path in model_files:
        config_name = model_path.stem.replace('_model', '')
        try:
            model = joblib.load(model_path)
            result = model.transform(embedding_normalized)
            projections[config_name] = {
                'x': float(result[0, 0]),
                'y': float(result[0, 1])
            }
            
            # Load DBSCAN model if available
            dbscan_path = models_dir / f'{config_name}_dbscan.joblib'
            if dbscan_path.exists():
                dbscan = joblib.load(dbscan_path)
                # Predict cluster for the new point
                cluster = dbscan.fit_predict(result)[0]
                projections[config_name]['cluster'] = int(cluster)
            
        except Exception as e:
            print(f"Error projecting with {config_name}: {e}")
    
    return projections

def create_scholar_projections(projection_method='umap', dbscan_params=None):
    """
    Create 2D visualizations of scholar similarity based on embeddings
    using UMAP or t-SNE and store the coordinates in a separate low-dimensional embeddings file
    
    Parameters:
    -----------
    projection_method : str
        Method to use for dimensionality reduction: 'umap' or 'tsne'
    dbscan_params : dict, optional
        Parameters for DBSCAN clustering. If None, default parameters will be used.
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
        
        # Print column names for debugging
        print(f"Columns in scholars.csv: {list(scholars_df.columns)}")
        
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
    
    # Create a new dataset for low-dimensional projections
    low_dim_ds = xr.Dataset(coords={
        'scholar': np.arange(len(scholar_ids)),
        'scholar_id': ('scholar', list(scholar_ids)),
        'scholar_name': ('scholar', list(scholar_names))
    })
    
    # Set up projection parameters based on method
    if projection_method.lower() == 'umap':
        try:
            import umap
        except ImportError:
            print("UMAP not installed. Please install it with 'pip install umap-learn'")
            return
            
        # UMAP parameters
        n_neighbors = 30
        min_dist = 0.2
        config_name = f'umap_n{n_neighbors}_d{min_dist}'
        print(f"Calculating {config_name} projection...")
        
        try:
            # Create and fit UMAP model
            model = umap.UMAP(
                n_neighbors=n_neighbors,
                min_dist=min_dist,
                n_components=2,
                metric='cosine',
                random_state=42
            )
            result = model.fit_transform(embeddings_normalized)
            
            # Save model
            joblib.dump(model, models_dir / f'{config_name}_model.joblib')
            print(f"Saved {config_name} model to {models_dir / f'{config_name}_model.joblib'}")
        except Exception as e:
            print(f"Error in {config_name} projection: {e}")
            import traceback
            traceback.print_exc()
            return
            
    elif projection_method.lower() == 'tsne':
        # t-SNE parameters
        perplexity = 30
        learning_rate = 200
        config_name = f'tsne_p{perplexity}_lr{learning_rate}'
        print(f"Calculating {config_name} projection...")
        
        try:
            # Create and fit t-SNE model
            model = TSNE(
                n_components=2,
                perplexity=perplexity,
                learning_rate=learning_rate,
                n_iter=1000,
                random_state=42
            )
            result = model.fit_transform(embeddings_normalized)
            
            # Save model
            joblib.dump(model, models_dir / f'{config_name}_model.joblib')
            print(f"Saved {config_name} model to {models_dir / f'{config_name}_model.joblib'}")
        except Exception as e:
            print(f"Error in {config_name} projection: {e}")
            import traceback
            traceback.print_exc()
            return
    else:
        print(f"Unknown projection method: {projection_method}")
        print("Supported methods: 'umap', 'tsne'")
        return
    
    # Add projection coordinates to dataset
    low_dim_ds[f'{config_name}_x'] = xr.DataArray(
        result[:, 0], 
        dims='scholar'
    )
    low_dim_ds[f'{config_name}_y'] = xr.DataArray(
        result[:, 1], 
        dims='scholar'
    )
    
    # Set default DBSCAN parameters if not provided
    if dbscan_params is None:
        if projection_method.lower() == 'umap':
            eps = 0.2
            min_samples = 8
        else:  # t-SNE typically needs different parameters
            eps = 10.0
            min_samples = 8
    else:
        eps = dbscan_params.get('eps', 0.2)
        min_samples = dbscan_params.get('min_samples', 8)
    
    # Apply DBSCAN clustering
    print(f"Applying DBSCAN clustering with eps={eps:.2f}, min_samples={min_samples}...")
    dbscan = DBSCAN(eps=eps, min_samples=min_samples)
    cluster_labels = dbscan.fit_predict(result)
    
    # Save DBSCAN model
    joblib.dump(dbscan, models_dir / f'{config_name}_dbscan.joblib')
    print(f"Saved DBSCAN model to {models_dir / f'{config_name}_dbscan.joblib'}")
    
    # Add cluster assignments to dataset
    low_dim_ds[f'{config_name}_cluster'] = xr.DataArray(
        cluster_labels,
        dims='scholar'
    )
    
    # Count clusters and analyze cluster sizes
    unique_clusters = set(cluster_labels)
    if -1 in unique_clusters:
        unique_clusters.remove(-1)
    n_clusters = len(unique_clusters)
    n_noise = list(cluster_labels).count(-1)
    
    # Calculate cluster sizes
    cluster_sizes = {}
    for label in unique_clusters:
        cluster_sizes[label] = list(cluster_labels).count(label)
    
    # Print cluster statistics
    print(f"DBSCAN found {n_clusters} clusters and {n_noise} noise points ({n_noise/len(cluster_labels)*100:.1f}%)")
    print(f"Cluster sizes: {cluster_sizes}")
    print(f"Largest cluster: {max(cluster_sizes.values()) if cluster_sizes else 0} points")
    
    # Create a DataFrame with scholar info and cluster assignments
    cluster_df = pd.DataFrame({
        'scholar_id': scholar_ids,
        'scholar_name': scholar_names,
        f'{projection_method.lower()}_x': result[:, 0],
        f'{projection_method.lower()}_y': result[:, 1],
        'cluster': cluster_labels
    })
    
    # Save cluster assignments to CSV
    cluster_csv = data_dir / f'{config_name}_clusters.csv'
    cluster_df.to_csv(cluster_csv, index=False)
    print(f"Saved cluster assignments to {cluster_csv}")
    
    # Create a more comprehensive JSON file with scholar information
    # First, create a mapping from scholar_id to cluster and projection coordinates
    scholar_to_cluster = {}
    for i, scholar_id in enumerate(scholar_ids):
        scholar_to_cluster[scholar_id] = {
            'cluster': int(cluster_labels[i]),
            f'{projection_method.lower()}_x': float(result[i, 0]),
            f'{projection_method.lower()}_y': float(result[i, 1])
        }
    
    # Create a dictionary to store scholar information
    scholars_dict = {}
    
    # Add each scholar to the dictionary
    for _, row in scholars_df.iterrows():
        scholar_id = row['scholar_id']
        
        # Skip scholars that don't have embeddings/clusters
        if scholar_id not in scholar_to_cluster:
            continue
            
        # Get institution if available, otherwise use empty string
        institution = row.get('institution', '')
        if pd.isna(institution):
            institution = ''
            
        # Get database ID if available, otherwise use empty string
        db_id = row.get('db_id', '')
        if pd.isna(db_id):
            db_id = ''
        
        # Add scholar to dictionary
        scholars_dict[scholar_id] = {
            'id': scholar_id,
            'name': row['scholar_name'],
            'institution': institution,
            'db_id': db_id,
            f'{projection_method.lower()}_projection': {
                'x': scholar_to_cluster[scholar_id][f'{projection_method.lower()}_x'],
                'y': scholar_to_cluster[scholar_id][f'{projection_method.lower()}_y']
            },
            'cluster': scholar_to_cluster[scholar_id]['cluster']
        }
    
    # Save to JSON file
    scholars_json_path = data_dir / f'{projection_method.lower()}_scholars.json'
    with open(scholars_json_path, 'w') as f:
        json.dump(scholars_dict, f, indent=2)
    
    print(f"Saved scholar information with clusters to {scholars_json_path}")
    
    # Also save a cluster-centric JSON file
    clusters_dict = {}
    
    # Group scholars by cluster
    for cluster_id in sorted(list(unique_clusters) + [-1]):  # Include noise cluster (-1)
        # Add cluster to dictionary
        clusters_dict[str(cluster_id)] = {
            'id': int(cluster_id),
            'size': 0,
            'scholars': []
        }
    
    # Add scholars to their respective clusters
    for scholar_id, info in scholars_dict.items():
        cluster_id = str(info['cluster'])
        if cluster_id in clusters_dict:
            clusters_dict[cluster_id]['scholars'].append({
                'id': scholar_id,
                'name': info['name'],
                'institution': info['institution'],
                f'{projection_method.lower()}_projection': info[f'{projection_method.lower()}_projection']
            })
            clusters_dict[cluster_id]['size'] += 1
    
    # Save to JSON file
    clusters_json_path = data_dir / f'{projection_method.lower()}_clusters.json'
    with open(clusters_json_path, 'w') as f:
        json.dump(clusters_dict, f, indent=2)
    
    print(f"Saved cluster-centric information to {clusters_json_path}")
    
    # Save as a separate netCDF file
    output_file = data_dir / 'low_dim_embeddings.nc'
    low_dim_ds.to_netcdf(output_file)
    print(f"Saved low-dimensional projections to {output_file}")
    
    # Create visualization plot with clusters
    plots_dir = data_dir / 'plots'
    plot_projections_with_clusters(low_dim_ds, config_name, plots_dir)
    print(f"Created cluster plot in {plots_dir}")
    
    return low_dim_ds


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Create low-dimensional projections of scholar embeddings')
    parser.add_argument('--method', type=str, default='umap', choices=['umap', 'tsne'], 
                        help='Projection method to use (umap or tsne)')
    parser.add_argument('--eps', type=float, default=None, 
                        help='DBSCAN eps parameter (optional)')
    parser.add_argument('--min_samples', type=int, default=None, 
                        help='DBSCAN min_samples parameter (optional)')
    
    args = parser.parse_args()
    
    # Set up DBSCAN parameters if provided
    dbscan_params = None
    if args.eps is not None or args.min_samples is not None:
        dbscan_params = {}
        if args.eps is not None:
            dbscan_params['eps'] = args.eps
        if args.min_samples is not None:
            dbscan_params['min_samples'] = args.min_samples
    
    create_scholar_projections(projection_method=args.method, dbscan_params=dbscan_params) 