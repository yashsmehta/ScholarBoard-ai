import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from researcher_info.get_embeddings import load_researcher_database
from sklearn.decomposition import PCA
import os
import warnings
warnings.filterwarnings('ignore')

def create_researcher_map(use_pca=False):
    """
    Create a 2D visualization of researcher similarity based on embeddings
    and store the coordinates in the researcher database
    
    Args:
        use_pca: If True, use PCA (more reliable). If False, try UMAP (better clustering)
    """
    # Load researcher database
    try:
        # Use absolute path for database file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        db_path = os.path.join(project_root, 'data', 'researcher_database.npz')
        
        researcher_data = load_researcher_database(db_path)
        if len(researcher_data) == 0:
            print("No researcher data found")
            return
    except Exception as e:
        print(f"Error loading researcher data: {e}")
        return
    
    # Extract valid embeddings and names
    valid_data = []
    researcher_indices = []
    for i, r in enumerate(researcher_data):
        if r['embedding'] is not None:
            valid_data.append((r['embedding'], r['name']))
            researcher_indices.append(i)
    
    if not valid_data:
        print("No valid embeddings found")
        return
        
    # Convert to numpy arrays
    embeddings, names = zip(*valid_data)
    embeddings = np.array(embeddings, dtype=np.float32)
    
    print(f"Processing {len(embeddings)} researchers")
    
    # Normalize embeddings
    from sklearn.preprocessing import StandardScaler
    embeddings_normalized = StandardScaler().fit_transform(embeddings)
    
    # Reduce dimensions to 2D
    if use_pca:
        # Use PCA (more reliable)
        model = PCA(n_components=2)
        reduced_data = model.fit_transform(embeddings_normalized)
        method_name = "PCA"
    else:
        # Try UMAP if requested
        try:
            import umap
            model = umap.UMAP(
                n_neighbors=min(5, len(embeddings) - 1),
                min_dist=0.1,
                n_components=2,
                metric='cosine',
                random_state=42
            )
            reduced_data = model.fit_transform(embeddings_normalized)
            method_name = "UMAP"
        except Exception as e:
            print(f"UMAP failed: {e}, falling back to PCA")
            model = PCA(n_components=2)
            reduced_data = model.fit_transform(embeddings_normalized)
            method_name = "PCA"
    
    print(f"Reduced dimensionality using {method_name}")

    # Update researcher database with 2D coordinates
    for i, idx in enumerate(researcher_indices):
        researcher_data[idx]['umap_coords'] = reduced_data[i].tolist()
    
    # Save updated database
    np.savez_compressed(
        db_path,
        researcher_data=researcher_data
    )
    
    # Also update the JSON metadata
    researcher_metadata = []
    for r in researcher_data:
        metadata = {
            'researcher_id': r['researcher_id'],
            'name': r['name'],
            'institution': r['institution'],
            'research_areas': r['research_areas']
        }
        if 'umap_coords' in r:
            metadata['umap_coords'] = r['umap_coords']
        researcher_metadata.append(metadata)
    
    import json
    metadata_path = os.path.join(project_root, 'data', 'researcher_metadata.json')
    with open(metadata_path, 'w') as f:
        json.dump(researcher_metadata, f, indent=2)
    
    print(f"Updated researcher database with {method_name} coordinates")

    # Create visualization
    plt.figure(figsize=(10, 8))
    
    # Plot points
    scatter = plt.scatter(
        reduced_data[:, 0], 
        reduced_data[:, 1],
        c=np.arange(len(names)),
        cmap='viridis',
        s=100
    )
    
    # Add name labels
    for i, name in enumerate(names):
        plt.annotate(
            name,
            (reduced_data[i, 0], reduced_data[i, 1]),
            xytext=(5, 5),
            textcoords='offset points',
            fontsize=9
        )
    
    # Style the plot
    plt.colorbar(scatter, label='Researcher ID')
    plt.title(f'Researcher Similarity Map ({method_name})', fontsize=16)
    plt.xlabel('Dimension 1')
    plt.ylabel('Dimension 2')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    # Save the plot
    try:
        img_path = os.path.join(project_root, 'imgs', 'researcher_map.png')
        plt.savefig(img_path, dpi=300, bbox_inches='tight')
        print(f"Created visualization: {img_path}")
    except Exception as e:
        print(f"Error saving visualization: {e}")
    
    plt.close()

if __name__ == "__main__":
    create_researcher_map(use_pca=False) 