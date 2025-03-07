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
warnings.filterwarnings('ignore')

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
    
    # Load scholar metadata including country information
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
    
    # Create multiple mappings from scholar_id to country to handle different ID formats
    id_to_country = {}
    
    # Add mappings for original IDs
    for _, row in scholars_df.iterrows():
        scholar_id = row['scholar_id']
        country = row['country']
        id_to_country[scholar_id] = country
        
        # Also add mappings for IDs with/without leading zeros
        # This handles cases where IDs might be stored differently
        id_to_country[scholar_id.lstrip('0')] = country  # Without leading zeros
        id_to_country[scholar_id.zfill(3)] = country     # With leading zeros (3 digits)
    
    # Get country for each scholar in our embeddings
    scholar_countries = []
    for scholar_id in scholar_ids:
        country = id_to_country.get(scholar_id, 'Unknown')
        scholar_countries.append(country)
    
    # Debug: Print country distribution
    country_counts = pd.Series(scholar_countries).value_counts()
    print(f"Country distribution: {country_counts.head(5)}")
    print(f"Unknown countries: {scholar_countries.count('Unknown')} out of {len(scholar_countries)}")
    
    if len(embeddings) == 0:
        print("No embeddings found")
        return
    
    print(f"Processing {len(embeddings)} scholars with embedding dimension {embeddings.shape[1]}")
    
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
    
    # Create a new dataset for low-dimensional projections
    low_dim_ds = xr.Dataset(coords={
        'scholar': np.arange(len(scholar_ids)),
        'scholar_id': ('scholar', list(scholar_ids)),
        'scholar_name': ('scholar', list(scholar_names)),
        'scholar_country': ('scholar', scholar_countries)
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
            'scholar_name': scholar_names[i],
            'country': scholar_countries[i]
        }
        
        # Add coordinates for each projection method
        for method in projections:
            entry[f'{method}_x'] = float(projections[method][i, 0])
            entry[f'{method}_y'] = float(projections[method][i, 1])
        
        projection_data.append(entry)
    
    # Save projection data to JSON
    projection_file = data_dir / 'scholar_projections.json'
    with open(projection_file, 'w') as f:
        json.dump(projection_data, f, indent=2)
    
    print(f"Saved projection data to {projection_file}")
    
    # Create visualizations
    create_projection_visualizations(projections, scholar_names, scholar_countries, data_dir)
    
    return low_dim_ds

def create_projection_visualizations(projections, scholar_names, scholar_countries, data_dir):
    """
    Create visualizations for each projection method with dots colored by country
    """
    # Create directory for visualizations
    vis_dir = data_dir / 'visualizations'
    vis_dir.mkdir(exist_ok=True, parents=True)
    
    # Set a modern style for plots
    plt.style.use('seaborn-v0_8-whitegrid')
    
    # Get unique countries and create a mapping to numeric values
    unique_countries = sorted(set(scholar_countries))
    country_to_num = {country: i for i, country in enumerate(unique_countries)}
    
    # Count occurrences of each country
    country_counts = pd.Series(scholar_countries).value_counts()
    
    # Get top 6 countries by frequency (for legend)
    top_countries = country_counts.head(6).index.tolist()
    
    # Define classic, distinct colors for countries
    # Ensure US is blue as requested
    classic_colors = {
        'United States': '#0066cc',  # Blue
        'United Kingdom': '#ff0000',  # Red
        'Germany': '#ffcc00',  # Yellow
        'Canada': '#cc0000',  # Dark Red
        'Netherlands': '#ff6600',  # Orange
        'Italy': '#009933',  # Green
        'France': '#3399ff',  # Light Blue
        'Australia': '#00cc99',  # Teal
        'Switzerland': '#ff3399',  # Pink
        'Japan': '#ff0066',  # Magenta
        'China': '#cc0033',  # Crimson
        'Spain': '#ffcc33',  # Gold
        'India': '#ff9900',  # Orange
        'Brazil': '#009900',  # Green
        'Sweden': '#0099cc',  # Sky Blue
        'Belgium': '#ffff00',  # Yellow
        'Israel': '#3366cc',  # Royal Blue
        'Denmark': '#cc3300',  # Brick Red
        'South Korea': '#cc99ff',  # Lavender
        'Norway': '#0033cc',  # Navy Blue
        'Finland': '#ffffff',  # White
        'Austria': '#ff3300',  # Bright Red
        'Singapore': '#ff99cc',  # Light Pink
        'New Zealand': '#000000',  # Black
        'Ireland': '#00cc00',  # Bright Green
        'Portugal': '#996633',  # Brown
        'Greece': '#3399cc',  # Steel Blue
        'Turkey': '#cc3333',  # Dark Red
        'Mexico': '#339900',  # Dark Green
        'Russia': '#990000',  # Dark Red
    }
    
    # Create a colormap for all countries
    # For countries not in the predefined list, use a color from this list
    additional_colors = [
        '#4d4dff', '#ff4d4d', '#4dff4d', '#ffff4d', '#4dffff', 
        '#ff4dff', '#ff794d', '#4dff79', '#794dff', '#ffff79', 
        '#79ffff', '#ff79ff', '#4d79ff', '#ff4d79', '#79ff4d',
        '#a64dff', '#ffa64d', '#4dffa6', '#ff4da6', '#a6ff4d',
        '#4da6ff', '#ffa6ff', '#a6ffa6', '#a6a6ff', '#ffa6a6',
        '#66b3ff', '#ff66b3', '#b3ff66', '#66ffb3', '#b366ff'
    ]
    
    # Assign colors to countries
    country_colors = {}
    color_index = 0
    
    for country in unique_countries:
        if country in classic_colors:
            country_colors[country] = classic_colors[country]
        else:
            country_colors[country] = additional_colors[color_index % len(additional_colors)]
            color_index += 1
    
    # Create a visualization for each projection method
    for method, result in projections.items():
        # Create figure with a specific background color
        fig = plt.figure(figsize=(16, 14), facecolor='#f8f9fa')
        ax = fig.add_subplot(111)
        
        # Set background color for the plot area
        ax.set_facecolor('#f8f9fa')
        
        # Plot points colored by country with white edge for better visibility
        scatter = plt.scatter(
            result[:, 0], 
            result[:, 1],
            c=[country_colors[country] for country in scholar_countries],
            s=120,
            alpha=0.85,
            edgecolors='#ffffff',
            linewidths=0.8
        )
        
        # Improved scholar labeling logic with special handling for UMAP
        # Calculate distance from origin for each point to find edge points
        distances_from_origin = np.sqrt(result[:, 0]**2 + result[:, 1]**2)
        
        # Get indices of edge scholars (top 30 by distance from origin)
        edge_indices = np.argsort(distances_from_origin)[-30:].tolist()
        
        # Find isolated points by calculating distances to nearest neighbors
        from sklearn.neighbors import NearestNeighbors
        
        # Fit nearest neighbors model
        nn = NearestNeighbors(n_neighbors=2).fit(result)  # 2 because the first neighbor is the point itself
        distances, _ = nn.kneighbors(result)
        
        # Get distance to nearest neighbor for each point
        isolation_scores = distances[:, 1]  # Second column has distance to nearest neighbor
        
        # Get indices of isolated scholars (top 30 by isolation score)
        isolated_indices = np.argsort(isolation_scores)[-30:].tolist()
        
        # For UMAP, we want to label more points
        if method == 'umap':
            # Get more edge points for UMAP
            edge_indices = np.argsort(distances_from_origin)[-50:].tolist()
            
            # Get more isolated points for UMAP
            isolated_indices = np.argsort(isolation_scores)[-50:].tolist()
            
            # Also include points from top countries
            top_country_indices = [i for i, country in enumerate(scholar_countries) if country in top_countries]
            top_country_indices = top_country_indices[:30]  # Limit to 30 points
            
            # Combine all indices
            candidate_indices = list(set(edge_indices + isolated_indices + top_country_indices))
            
            # Use a smaller minimum distance for UMAP to allow more labels
            min_label_distance = 0.5
        else:
            # Combine edge and isolated indices for other methods
            candidate_indices = list(set(edge_indices + isolated_indices))
            min_label_distance = 1.0
        
        # Filter out points that are too close to each other
        indices_to_label = []
        labeled_positions = []
        
        for idx in candidate_indices:
            pos = (result[idx, 0], result[idx, 1])
            
            # Check if this point is too close to any already labeled point
            too_close = False
            for labeled_pos in labeled_positions:
                dist = np.sqrt((pos[0] - labeled_pos[0])**2 + (pos[1] - labeled_pos[1])**2)
                if dist < min_label_distance:
                    too_close = True
                    break
            
            # If not too close to any existing label, add it
            if not too_close:
                indices_to_label.append(idx)
                labeled_positions.append(pos)
                
                # Limit to 80 labels maximum for UMAP, 50 for others
                max_labels = 80 if method == 'umap' else 50
                if len(indices_to_label) >= max_labels:
                    break
        
        # Add explanation about labeling criteria
        print(f"Method: {method} - Labeling {len(indices_to_label)} scholars: {len(set(edge_indices) & set(indices_to_label))} edge points and {len(set(isolated_indices) & set(indices_to_label))} isolated points")
        
        # Add name labels for selected scholars (without country)
        for i in indices_to_label:
            plt.annotate(
                scholar_names[i],
                (result[i, 0], result[i, 1]),
                xytext=(5, 5),
                textcoords='offset points',
                fontsize=10,
                fontweight='bold',
                color='#333333',
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#cccccc", alpha=0.9)
            )
        
        # Create legend handles for top 6 countries
        legend_elements = []
        for country in top_countries:
            color = country_colors[country]
            count = country_counts[country]
            percentage = (count / len(scholar_countries)) * 100
            legend_elements.append(plt.Line2D([0], [0], marker='o', color='w', 
                                             markerfacecolor=color, markersize=12,
                                             markeredgecolor='white', markeredgewidth=0.8,
                                             label=f"{country} ({count}, {percentage:.1f}%)"))
        
        # Add legend with country counts
        legend = plt.legend(
            handles=legend_elements, 
            title="Top 6 Countries by Scholar Count", 
            loc="upper right",
            bbox_to_anchor=(1.15, 1),
            fontsize=11,
            title_fontsize=13,
            frameon=True,
            framealpha=0.95,
            edgecolor='#cccccc'
        )
        
        # Style the plot
        method_name_map = {
            'pca': 'Principal Component Analysis',
            'tsne': 't-SNE',
            'umap': 'UMAP'
        }
        full_method_name = method_name_map.get(method, method.upper())
        
        plt.title(f'Scholar Similarity Map by Country\n{full_method_name}', 
                 fontsize=18, fontweight='bold', pad=20, color='#333333')
        
        plt.xlabel('Dimension 1', fontsize=14, fontweight='bold', labelpad=15, color='#333333')
        plt.ylabel('Dimension 2', fontsize=14, fontweight='bold', labelpad=15, color='#333333')
        
        # Improve grid appearance
        plt.grid(True, linestyle='--', alpha=0.4, color='#dddddd')
        
        # Remove top and right spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_linewidth(1.5)
        ax.spines['bottom'].set_linewidth(1.5)
        ax.spines['left'].set_color('#999999')
        ax.spines['bottom'].set_color('#999999')
        
        # Improve tick appearance
        ax.tick_params(axis='both', which='major', labelsize=12, colors='#666666', width=1.5, length=6)
        
        # Add a subtle border around the entire plot
        fig.patch.set_linewidth(2)
        fig.patch.set_edgecolor('#eeeeee')
        
        plt.tight_layout()
        
        # Add a caption with data information and labeling explanation
        plt.figtext(
            0.5, 0.01, 
            f"Based on {len(scholar_countries)} scholars from {len(unique_countries)} countries. " +
            f"Labels shown for isolated and edge points, avoiding overlaps. " +
            f"Visualization created using {full_method_name} dimensionality reduction.",
            ha="center", fontsize=10, fontstyle='italic', color='#666666'
        )
        
        # Save the plot with higher DPI for better quality
        img_path = vis_dir / f'scholar_map_{method}.png'
        plt.savefig(img_path, dpi=300, bbox_inches='tight')
        print(f"Created visualization: {img_path}")
        
        plt.close()

if __name__ == "__main__":
    create_scholar_projections() 