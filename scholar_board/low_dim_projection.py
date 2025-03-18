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

def plot_projection(x, y, scholar_names, clusters=None, title="Projection", output_path=None):
    """Simple function to plot 2D projections with optional cluster coloring"""
    plt.figure(figsize=(12, 10))
    
    if clusters is not None:
        # Plot with cluster colors
        scatter = plt.scatter(x, y, c=clusters, cmap='Spectral', alpha=0.8, s=50)
        n_clusters = len(set(clusters)) - (1 if -1 in clusters else 0)
        plt.title(f"{title}\nDBSCAN: {n_clusters} clusters, {list(clusters).count(-1)} noise points")
    else:
        # Plot without clusters
        scatter = plt.scatter(x, y, alpha=0.7, s=50)
        plt.title(title)
    
    # Add labels for a subset of points
    n_points = len(x)
    label_indices = np.random.choice(n_points, min(15, n_points), replace=False)
    
    for idx in label_indices:
        plt.annotate(
            scholar_names[idx],
            (x[idx], y[idx]),
            fontsize=8,
            alpha=0.8,
            xytext=(5, 5),
            textcoords='offset points'
        )
    
    plt.grid(alpha=0.3)
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved plot to {output_path}")
    else:
        plt.show()
    
    plt.close()

def project_new_embedding(embedding, method='umap', models_dir=None):
    """Project a new embedding using saved models"""
    if models_dir is None:
        models_dir = Path(__file__).parent.parent / 'data' / 'models'
    else:
        models_dir = Path(models_dir)
    
    # Load the scaler
    scaler = joblib.load(models_dir / 'scaler.joblib')
    
    # Normalize the embedding
    embedding = embedding.reshape(1, -1) if embedding.ndim == 1 else embedding
    embedding_normalized = scaler.transform(embedding)
    
    # Load and apply projection model
    model = joblib.load(models_dir / f'{method}_model.joblib')
    result = model.transform(embedding_normalized)
    
    # Get cluster if available
    try:
        dbscan = joblib.load(models_dir / f'{method}_dbscan.joblib')
        cluster = dbscan.fit_predict(result)[0]
    except:
        cluster = None
    
    return {
        'x': float(result[0, 0]),
        'y': float(result[0, 1]),
        'cluster': int(cluster) if cluster is not None else None
    }

def create_projections(method='umap'):
    """
    Create 2D projections of scholar embeddings using UMAP or t-SNE with DBSCAN clustering
    
    Parameters:
    -----------
    method : str
        Projection method to use: 'umap' or 'tsne'
    """
    # Setup paths
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / 'data'
    models_dir = data_dir / 'models'
    plots_dir = data_dir / 'plots'
    
    for dir_path in [models_dir, plots_dir]:
        dir_path.mkdir(exist_ok=True, parents=True)
    
    # Load embeddings
    embeddings_file = data_dir / 'scholar_embeddings.nc'
    try:
        ds = xr.open_dataset(embeddings_file)
        print(f"Loaded embeddings for {ds.dims['scholar']} scholars")
    except Exception as e:
        print(f"Error loading embeddings: {e}")
        return
    
    # Extract data
    embeddings = ds.embedding.values
    scholar_ids = ds.scholar_id.values
    scholar_names = ds.scholar_name.values
    
    # Load scholar information from vss_data.csv
    vss_data_path = data_dir / 'vss_data.csv'
    try:
        vss_df = pd.read_csv(vss_data_path)
        print(f"Loaded VSS data for {len(vss_df)} scholars")
        
        # Create a dictionary for quick lookup
        scholar_info = {}
        
        # Check for the expected column names in the CSV
        id_col = None
        for possible_id_col in ['scholar_id', 'id', 'ID']:
            if possible_id_col in vss_df.columns:
                id_col = possible_id_col
                break
        
        inst_col = None
        for possible_inst_col in ['institution', 'scholar_institution', 'Institution']:
            if possible_inst_col in vss_df.columns:
                inst_col = possible_inst_col
                break
                
        dept_col = None
        for possible_dept_col in ['department', 'scholar_department', 'Department']:
            if possible_dept_col in vss_df.columns:
                dept_col = possible_dept_col
                break
        
        # If we found both columns, map scholar_id to their info
        if id_col and (inst_col or dept_col):
            for _, row in vss_df.iterrows():
                scholar_id = str(row[id_col])
                # Make sure scholar_id is a 4-digit string
                if scholar_id.isdigit():
                    scholar_id = f"{int(scholar_id):04d}"
                
                institution = str(row.get(inst_col, '')) if inst_col else ''
                if pd.isna(institution):
                    institution = ''
                    
                department = str(row.get(dept_col, '')) if dept_col else ''
                if pd.isna(department):
                    department = ''
                
                scholar_info[scholar_id] = {
                    'institution': institution,
                    'department': department
                }
            
            print(f"Created scholar info map with {len(scholar_info)} entries")
        else:
            print(f"Couldn't find required columns in VSS data CSV. Found columns: {list(vss_df.columns)}")
    except Exception as e:
        print(f"Error loading VSS data: {e}")
        scholar_info = {}
    
    # Normalize embeddings
    scaler = StandardScaler()
    embeddings_normalized = scaler.fit_transform(embeddings)
    joblib.dump(scaler, models_dir / 'scaler.joblib')
    
    # Create projection
    if method.lower() == 'umap':
        try:
            import umap
            # Configure UMAP to focus more on local information
            # Lower n_neighbors (5-15) focuses more on local structure
            # Lower min_dist (0.0-0.1) allows closer packing of points
            model = umap.UMAP(
                n_components=2,
                n_neighbors=10,    # Lower value (default is 15) - focuses more on local structure
                min_dist=0.1,     # Lower value (default is 0.1) - allows for tighter clusters
                metric='cosine',
                random_state=42
            )
            print("Using UMAP with local focus: n_neighbors=10, min_dist=0.05")
        except ImportError:
            print("UMAP not installed. Install with 'pip install umap-learn'")
            return
    elif method.lower() == 'tsne':
        model = TSNE(n_components=2, perplexity=30, random_state=42)
    else:
        print(f"Unknown method: {method}. Use 'umap' or 'tsne'")
        return
    
    # Fit and transform
    result = model.fit_transform(embeddings_normalized)
    
    # Save the model
    joblib.dump(model, models_dir / f'{method}_model.joblib')
    print(f"Saved {method} model")
    
    # Apply DBSCAN clustering with parameters tuned to find between 12-45 clusters
    # For UMAP: smaller eps because points are more tightly packed
    # For t-SNE: larger eps because points are more spread out
    max_attempts = 5  # Maximum number of attempts to find good clustering
    min_clusters = 12  # Minimum number of clusters we want
    max_clusters = 45  # Maximum number of clusters we want
    
    # Start with moderately aggressive parameters
    if method.lower() == 'umap':
        eps = 0.2           # Starting epsilon
        min_samples = 3     # Smaller min_samples allows smaller clusters
    else:  # t-SNE
        eps = 3.0           # Starting eps for t-SNE
        min_samples = 3
    
    # Try different parameters until we get enough clusters
    attempt = 1
    best_clusters = None
    best_n_clusters = 0
    best_eps = eps
    
    while attempt <= max_attempts:
        print(f"DBSCAN attempt {attempt}/{max_attempts} with eps={eps:.4f}, min_samples={min_samples}")
        
        dbscan = DBSCAN(eps=eps, min_samples=min_samples)
        clusters = dbscan.fit_predict(result)
        
        # Count clusters
        unique_clusters = set(clusters)
        if -1 in unique_clusters:
            unique_clusters.remove(-1)
        n_clusters = len(unique_clusters)
        n_noise = list(clusters).count(-1)
        
        print(f"Found {n_clusters} clusters and {n_noise} noise points ({n_noise/len(clusters)*100:.1f}%)")
        
        # If this is our first clustering in range or better than previous best, save it
        if min_clusters <= n_clusters <= max_clusters:
            # If this is our first valid clustering or closer to target than previous best
            if best_clusters is None or abs(n_clusters - min_clusters) < abs(best_n_clusters - min_clusters):
                best_clusters = clusters
                best_n_clusters = n_clusters
                best_eps = eps
                print(f"New best clustering: {n_clusters} clusters with eps={eps:.4f}")
            
            # If we're already in a good range and this is not our last attempt, we can stop
            if attempt < max_attempts and n_clusters >= min_clusters:
                break
                
        # If too few clusters, reduce epsilon to create more clusters
        if n_clusters < min_clusters:
            eps *= 0.75
        # If too many clusters, increase epsilon to create fewer clusters
        elif n_clusters > max_clusters:
            eps *= 1.3
        # Otherwise we're in range, but try one more slight adjustment to get closer to min_clusters
        else:
            # If we're closer to max than min, try to increase clusters slightly
            if n_clusters > (min_clusters + max_clusters) / 2:
                eps *= 0.9
            else:
                eps *= 1.1
        
        attempt += 1
    
    # Use the best clustering we found, or the last one if none were good
    if best_clusters is not None:
        clusters = best_clusters
        eps = best_eps
        n_clusters = best_n_clusters
        print(f"Using best clustering found: {n_clusters} clusters with eps={eps:.4f}")
    else:
        # If no good clustering was found, use the last one
        print(f"No optimal clustering found. Using last attempt.")
        
    # Get final cluster count and noise count
    unique_clusters = set(clusters)
    if -1 in unique_clusters:
        unique_clusters.remove(-1)
    n_clusters = len(unique_clusters)
    n_noise = list(clusters).count(-1)
    
    # Create final DBSCAN model for saving
    dbscan = DBSCAN(eps=eps, min_samples=min_samples)
    dbscan.fit(result)
    
    # Save the final DBSCAN model
    joblib.dump(dbscan, models_dir / f'{method}_dbscan.joblib')
    print(f"Final DBSCAN: {n_clusters} clusters and {n_noise} noise points ({n_noise/len(clusters)*100:.1f}%)")
    
    # Create plot visualization
    plot_projection(
        result[:, 0], result[:, 1], scholar_names, 
        clusters=clusters,
        title=f"{method.upper()} Projection with DBSCAN Clustering",
        output_path=plots_dir / f"{method}_clusters.png"
    )
    
    # Create a JSON file with results
    output_dict = {}
    for i, scholar_id in enumerate(scholar_ids):
        # Ensure scholar_id is a 4-digit string
        formatted_id = f"{int(scholar_id):04d}" if scholar_id.isdigit() else scholar_id
        
        # Get institution and department from VSS data if available
        scholar_data = scholar_info.get(formatted_id, {})
        institution = scholar_data.get('institution', '')
        department = scholar_data.get('department', '')
        
        output_dict[formatted_id] = {
            'id': formatted_id,
            'name': scholar_names[i],
            'institution': institution,
            'department': department,
            'db_id': '',  # Keep db_id for compatibility
            f'{method}_projection': {
                'x': float(result[i, 0]),
                'y': float(result[i, 1])
            },
            'cluster': int(clusters[i])
        }
    
    # Save to JSON file
    with open(data_dir / f'scholars.json', 'w') as f:
        json.dump(output_dict, f, indent=2)
    print(f"Saved scholar data to {data_dir / 'scholars.json'}")
    
    return output_dict

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Create projections of scholar embeddings')
    parser.add_argument('--method', type=str, default='umap', choices=['umap', 'tsne'], 
                       help='Projection method to use')
    
    args = parser.parse_args()
    create_projections(method=args.method) 