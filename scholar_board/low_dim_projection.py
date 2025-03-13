import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import xarray as xr
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import os
import warnings
from pathlib import Path
import json
import joblib
warnings.filterwarnings('ignore')

def plot_projections(low_dim_ds, output_dir=None):
    """
    Create and save plots for UMAP projections with different configurations
    
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
    
    # Get all UMAP configurations from the dataset
    umap_configs = []
    for var in low_dim_ds.data_vars:
        if var.endswith('_x'):
            config = var[:-2]  # Remove the '_x' suffix
            umap_configs.append(config)
    
    print(f"Found {len(umap_configs)} UMAP configurations: {umap_configs}")
    
    # Create a figure for each UMAP configuration
    for config in umap_configs:
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
        
        # Extract n_neighbors and min_dist from config name
        config_parts = config.split('_')
        if len(config_parts) >= 3:
            n_neighbors = config_parts[1].replace('n', '')
            min_dist = config_parts[2].replace('d', '')
            title = f'UMAP Projection (n_neighbors={n_neighbors}, min_dist={min_dist})'
        else:
            title = f'UMAP Projection ({config})'
        
        # Add title and labels
        ax.set_title(title, fontsize=14)
        ax.set_xlabel('UMAP Dimension 1', fontsize=12)
        ax.set_ylabel('UMAP Dimension 2', fontsize=12)
        
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
    Create and save a plot for UMAP projection with DBSCAN clusters
    
    Parameters:
    -----------
    low_dim_ds : xarray.Dataset
        Dataset containing the low-dimensional projections and cluster assignments
    config_name : str
        Name of the UMAP configuration to plot
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
    
    # Extract n_neighbors and min_dist from config name
    config_parts = config_name.split('_')
    if len(config_parts) >= 3:
        n_neighbors = config_parts[1].replace('n', '')
        min_dist = config_parts[2].replace('d', '')
        title = f'UMAP Projection (n_neighbors={n_neighbors}, min_dist={min_dist})\n'
        title += f'DBSCAN Clustering: {n_clusters} clusters, {n_noise} noise points'
    else:
        title = f'UMAP Projection ({config_name})\n'
        title += f'DBSCAN Clustering: {n_clusters} clusters, {n_noise} noise points'
    
    # Add title and labels
    ax.set_title(title, fontsize=14)
    ax.set_xlabel('UMAP Dimension 1', fontsize=12)
    ax.set_ylabel('UMAP Dimension 2', fontsize=12)
    
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

def find_optimal_dbscan_params(data, eps_range=(0.1, 2.0), min_samples_range=(3, 20), target_clusters=(8, 20), max_noise_fraction=0.3, max_cluster_size=100):
    """
    Find optimal DBSCAN parameters to get a desired number of clusters
    
    Parameters:
    -----------
    data : numpy.ndarray
        Data to cluster
    eps_range : tuple
        Range of eps values to try (start, end)
    min_samples_range : tuple
        Range of min_samples values to try (start, end)
    target_clusters : tuple
        Desired range of clusters (min, max)
    max_noise_fraction : float
        Maximum acceptable fraction of points as noise (0.0 to 1.0)
    max_cluster_size : int
        Maximum desired size for the largest cluster
    
    Returns:
    --------
    tuple
        (best_eps, best_min_samples, n_clusters)
    """
    best_params = None
    best_n_clusters = 0
    best_score = float('-inf')
    
    # Try different combinations of eps and min_samples
    eps_values = np.linspace(eps_range[0], eps_range[1], 20)
    min_samples_values = range(min_samples_range[0], min_samples_range[1] + 1)
    
    print(f"Searching for optimal DBSCAN parameters to get {target_clusters[0]}-{target_clusters[1]} clusters with max {max_noise_fraction*100:.0f}% noise and largest cluster < {max_cluster_size} points...")
    
    # Track all valid solutions to allow manual selection if needed
    valid_solutions = []
    
    for eps in eps_values:
        for min_samples in min_samples_values:
            # Run DBSCAN
            dbscan = DBSCAN(eps=eps, min_samples=min_samples)
            labels = dbscan.fit_predict(data)
            
            # Count clusters (excluding noise)
            unique_labels = set(labels)
            if -1 in unique_labels:
                unique_labels.remove(-1)
            n_clusters = len(unique_labels)
            n_noise = list(labels).count(-1)
            noise_fraction = n_noise / len(labels)
            
            # Check if number of clusters is within target range
            if target_clusters[0] <= n_clusters <= target_clusters[1]:
                # Calculate cluster size distribution
                cluster_sizes = {}
                for label in unique_labels:
                    cluster_sizes[label] = list(labels).count(label)
                
                # Calculate coefficient of variation (CV) of cluster sizes
                # Lower CV means more uniform cluster sizes
                if n_clusters > 1:
                    cluster_sizes_values = list(cluster_sizes.values())
                    mean_size = np.mean(cluster_sizes_values)
                    std_size = np.std(cluster_sizes_values)
                    cv = std_size / mean_size if mean_size > 0 else float('inf')
                    
                    # Check for dominant clusters
                    non_noise_points = len(labels) - n_noise
                    max_cluster_size_actual = max(cluster_sizes_values)
                    max_cluster_fraction = max_cluster_size_actual / non_noise_points if non_noise_points > 0 else 1.0
                    
                    # Calculate size penalty - heavily penalize clusters larger than max_cluster_size
                    size_penalty = 0.0
                    if max_cluster_size_actual > max_cluster_size:
                        # Exponential penalty for exceeding max_cluster_size
                        size_penalty = ((max_cluster_size_actual - max_cluster_size) / max_cluster_size) ** 2 * 5.0
                    
                    # Calculate dominance penalty based on how large the biggest cluster is
                    # Heavily penalize clusters that contain more than 20% of points
                    dominance_penalty = max(0, (max_cluster_fraction - 0.20) * 6)
                    
                    # If the largest cluster has more than 30% of points, apply an even stronger penalty
                    if max_cluster_fraction > 0.30:
                        dominance_penalty += (max_cluster_fraction - 0.30) * 10
                else:
                    cv = float('inf')
                    dominance_penalty = 1.0  # Heavily penalize single-cluster solutions
                    size_penalty = 5.0  # Heavily penalize single-cluster solutions
                
                # Normalize CV to a score between 0 and 1 (lower CV gives higher score)
                cv_score = 1.0 / (1.0 + cv)
                
                # Calculate noise penalty - we want to minimize noise but not at the expense of cluster balance
                # Noise penalty increases exponentially as we approach max_noise_fraction
                noise_penalty = (noise_fraction / max_noise_fraction) ** 2 if noise_fraction <= max_noise_fraction else 10.0
                
                # Calculate score based on:
                # 1. How close we are to the middle of the target cluster range
                # 2. How low the noise fraction is (but with diminishing returns)
                # 3. How uniform the cluster sizes are
                # 4. How small the largest cluster is
                target_mid = (target_clusters[0] + target_clusters[1]) / 2
                cluster_count_score = 1.0 - abs(n_clusters - target_mid) / (target_mid - target_clusters[0])
                
                # Combined score (weighted to balance noise reduction and cluster balance)
                score = (
                    cluster_count_score * 0.2 + 
                    cv_score * 0.4
                ) - noise_penalty - dominance_penalty - size_penalty
                
                # Store this solution
                solution = {
                    'eps': eps,
                    'min_samples': min_samples,
                    'n_clusters': n_clusters,
                    'n_noise': n_noise,
                    'noise_fraction': noise_fraction,
                    'cluster_sizes': cluster_sizes,
                    'max_cluster_size': max_cluster_size_actual,
                    'score': score
                }
                valid_solutions.append(solution)
                
                # If this is better than our current best, update
                if score > best_score:
                    best_score = score
                    best_params = (eps, min_samples)
                    best_n_clusters = n_clusters
                    
                    # Get the size of the largest cluster
                    largest_cluster_size = max(cluster_sizes.values()) if cluster_sizes else 0
                    largest_cluster_pct = (largest_cluster_size / (len(labels) - n_noise)) * 100 if (len(labels) - n_noise) > 0 else 0
                    
                    print(f"  Found better params: eps={eps:.2f}, min_samples={min_samples}, clusters={n_clusters}, noise={n_noise} ({noise_fraction*100:.1f}%)")
                    print(f"    Cluster sizes: {cluster_sizes}")
                    print(f"    Largest cluster: {largest_cluster_size} points ({largest_cluster_pct:.1f}% of non-noise)")
    
    # If we have valid solutions but none are optimal, pick the one with the best balance
    if not best_params and valid_solutions:
        # Sort by score
        valid_solutions.sort(key=lambda x: x['score'], reverse=True)
        best_solution = valid_solutions[0]
        best_params = (best_solution['eps'], best_solution['min_samples'])
        best_n_clusters = best_solution['n_clusters']
        print(f"  Selected best balanced solution: eps={best_solution['eps']:.2f}, min_samples={best_solution['min_samples']}, clusters={best_solution['n_clusters']}, noise={best_solution['n_noise']} ({best_solution['noise_fraction']*100:.1f}%)")
        print(f"    Largest cluster: {best_solution['max_cluster_size']} points")
    
    # If we couldn't find parameters within the target range, try again with a more relaxed noise constraint
    if not best_params:
        print("Could not find parameters within target cluster range with noise constraint. Trying with higher noise tolerance...")
        return find_optimal_dbscan_params(data, eps_range, min_samples_range, target_clusters, max_noise_fraction * 1.5, max_cluster_size)
    
    return best_params[0], best_params[1], best_n_clusters

def project_new_embedding(embedding, models_dir=None):
    """
    Project a new embedding onto the existing low-dimensional space using UMAP
    
    Parameters:
    -----------
    embedding : numpy.ndarray
        The embedding vector to project (should have the same dimension as training embeddings)
    models_dir : str or Path, optional
        Directory where the models are saved. If None, uses default location.
        
    Returns:
    --------
    dict
        Dictionary with projection coordinates for each UMAP configuration
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
    
    # Find all UMAP model files
    umap_model_files = list(models_dir.glob('umap_*_model.joblib'))
    
    if not umap_model_files:
        print("No UMAP models found")
        return projections
    
    # Project using each UMAP model
    for model_path in umap_model_files:
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

def create_scholar_projections():
    """
    Create 2D visualizations of scholar similarity based on embeddings
    using UMAP with different configurations and store the coordinates
    in a separate low-dimensional embeddings file
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
    
    # Import UMAP
    try:
        import umap
    except ImportError:
        print("UMAP not installed. Please install it with 'pip install umap-learn'")
        return
    
    # Create a new dataset for low-dimensional projections
    low_dim_ds = xr.Dataset(coords={
        'scholar': np.arange(len(scholar_ids)),
        'scholar_id': ('scholar', list(scholar_ids)),
        'scholar_name': ('scholar', list(scholar_names))
    })
    
    # Use only the specified UMAP configuration
    n_neighbors = 30
    min_dist = 0.2
    config_name = f'umap_n{n_neighbors}_d{min_dist}'
    print(f"Calculating {config_name} projection...")
    
    try:
        # Create and fit UMAP model
        umap_model = umap.UMAP(
            n_neighbors=n_neighbors,
            min_dist=min_dist,
            n_components=2,
            metric='cosine',
            random_state=42
        )
        umap_result = umap_model.fit_transform(embeddings_normalized)
        
        # Save UMAP model
        joblib.dump(umap_model, models_dir / f'{config_name}_model.joblib')
        print(f"Saved {config_name} model to {models_dir / f'{config_name}_model.joblib'}")
        
        # Add UMAP coordinates to dataset
        low_dim_ds[f'{config_name}_x'] = xr.DataArray(
            umap_result[:, 0], 
            dims='scholar'
        )
        low_dim_ds[f'{config_name}_y'] = xr.DataArray(
            umap_result[:, 1], 
            dims='scholar'
        )
        
        # Find optimal DBSCAN parameters
        best_eps, best_min_samples, best_n_clusters = find_optimal_dbscan_params(
            umap_result, 
            eps_range=(0.1, 0.3),  # Use smaller eps values to break up large clusters
            min_samples_range=(5, 12),  # Adjust min_samples range
            target_clusters=(25, 40),  # Target more clusters to break up large ones
            max_noise_fraction=0.35,  # Allow more noise to get better cluster balance
            max_cluster_size=100  # Enforce maximum cluster size of 100 points
        )
        
        # Apply DBSCAN clustering to the UMAP projection with optimal parameters
        print(f"Applying DBSCAN clustering with eps={best_eps:.2f}, min_samples={best_min_samples}...")
        dbscan = DBSCAN(eps=best_eps, min_samples=best_min_samples)
        cluster_labels = dbscan.fit_predict(umap_result)
        
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
            'umap_x': umap_result[:, 0],
            'umap_y': umap_result[:, 1],
            'cluster': cluster_labels
        })
        
        # Save cluster assignments to CSV
        cluster_csv = data_dir / f'{config_name}_clusters.csv'
        cluster_df.to_csv(cluster_csv, index=False)
        print(f"Saved cluster assignments to {cluster_csv}")
        
        # Create a more comprehensive JSON file with scholar information
        # First, create a mapping from scholar_id to cluster and UMAP coordinates
        scholar_to_cluster = {}
        for i, scholar_id in enumerate(scholar_ids):
            scholar_to_cluster[scholar_id] = {
                'cluster': int(cluster_labels[i]),
                'umap_x': float(umap_result[i, 0]),
                'umap_y': float(umap_result[i, 1])
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
                'umap_projection': {
                    'x': scholar_to_cluster[scholar_id]['umap_x'],
                    'y': scholar_to_cluster[scholar_id]['umap_y']
                },
                'cluster': scholar_to_cluster[scholar_id]['cluster']
            }
        
        # Save to JSON file
        scholars_json_path = data_dir / 'scholars.json'
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
                    'umap_projection': info['umap_projection']
                })
                clusters_dict[cluster_id]['size'] += 1
        
        # Save to JSON file
        clusters_json_path = data_dir / 'clusters.json'
        with open(clusters_json_path, 'w') as f:
            json.dump(clusters_dict, f, indent=2)
        
        print(f"Saved cluster-centric information to {clusters_json_path}")
        
    except Exception as e:
        print(f"Error in {config_name} projection: {e}")
        import traceback
        traceback.print_exc()
    
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
    create_scholar_projections() 