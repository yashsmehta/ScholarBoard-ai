import http.server
import socketserver
import os
import webbrowser
import json
import sys
import urllib.parse
import numpy as np
import xarray as xr
from io import BytesIO
from pathlib import Path

# Add parent directory to path to import scholar_board module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scholar_board.search_embeddings import find_similar_scholars, get_query_embedding, cosine_similarity

class ScholarSearchHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Add debugging for data directory
        if self.path == '/debug':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # Get current directory
            current_dir = os.getcwd()
            
            # List files in data directory
            data_dir = os.path.join(current_dir, 'data')
            data_files = os.listdir(data_dir) if os.path.exists(data_dir) else []
            
            # Check if scholars.json exists
            scholars_json_path = os.path.join(data_dir, 'scholars.json')
            scholars_json_exists = os.path.exists(scholars_json_path)
            
            # Get size of scholars.json
            scholars_json_size = os.path.getsize(scholars_json_path) if scholars_json_exists else 0
            
            # Try to load scholars.json
            scholars_json_content = None
            if scholars_json_exists:
                try:
                    with open(scholars_json_path, 'r') as f:
                        scholars_json_content = json.load(f)
                except Exception as e:
                    scholars_json_content = f"Error loading scholars.json: {str(e)}"
            
            # Create debug HTML
            debug_html = f"""
            <html>
            <head>
                <title>Debug Info</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1 {{ color: #333; }}
                    h2 {{ color: #666; }}
                    pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; }}
                </style>
            </head>
            <body>
                <h1>Debug Info</h1>
                <h2>Current Directory</h2>
                <pre>{current_dir}</pre>
                
                <h2>Data Directory</h2>
                <pre>{data_dir}</pre>
                
                <h2>Data Files</h2>
                <pre>{data_files}</pre>
                
                <h2>scholars.json</h2>
                <p>Exists: {scholars_json_exists}</p>
                <p>Size: {scholars_json_size} bytes</p>
                
                <h2>scholars.json Content</h2>
                <pre>{scholars_json_content[:1000] + '...' if isinstance(scholars_json_content, list) and len(scholars_json_content) > 0 else scholars_json_content}</pre>
            </body>
            </html>
            """
            
            self.wfile.write(debug_html.encode('utf-8'))
            return
        
        # Add logging for all requests
        print(f"GET request for: {self.path}")
        
        # Special handling for scholars.json
        if self.path.endswith('scholars.json'):
            print(f"Serving scholars.json...")
            try:
                # Get the file path
                file_path = os.path.join(os.getcwd(), self.path.lstrip('/'))
                print(f"File path: {file_path}")
                
                # Check if file exists
                if not os.path.exists(file_path):
                    print(f"File not found: {file_path}")
                    self.send_error(404, 'File not found')
                    return
                
                # Get file size
                file_size = os.path.getsize(file_path)
                print(f"File size: {file_size} bytes")
                
                # Try to load the file to verify it's valid JSON
                try:
                    with open(file_path, 'r') as f:
                        json_content = json.load(f)
                    
                    # Limit to 20 researchers
                    limited_json_content = json_content[:20]
                    print(f"Limiting JSON from {len(json_content)} to {len(limited_json_content)} items")
                    
                    # Prepare the limited JSON response
                    limited_json_str = json.dumps(limited_json_content)
                    limited_json_bytes = limited_json_str.encode('utf-8')
                    
                except Exception as e:
                    print(f"Error loading JSON: {str(e)}")
                    self.send_error(500, str(e))
                    return
                
                # Serve the limited file
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Content-length', len(limited_json_bytes))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                self.wfile.write(limited_json_bytes)
                return
            except Exception as e:
                print(f"Error serving scholars.json: {str(e)}")
                self.send_error(500, str(e))
        
        # Handle normal file serving
        return http.server.SimpleHTTPRequestHandler.do_GET(self)
    
    def do_POST(self):
        if self.path == '/api/search':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                query = data.get('query', '')
                use_low_dim = data.get('use_low_dim', False)
                projection_method = data.get('projection_method', 'umap')
                top_n = data.get('top_n', 20)
                
                if not query:
                    self.send_error(400, 'Query is required')
                    return
                
                # Use local search function that uses the copied database files
                top_scholars = self.local_search(
                    query, 
                    top_n=top_n, 
                    use_low_dim=use_low_dim, 
                    projection_method=projection_method
                )
                
                # Send response
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')  # Allow CORS
                self.end_headers()
                
                response = json.dumps({'scholars': top_scholars})
                self.wfile.write(response.encode('utf-8'))
            except Exception as e:
                print(f"Search error: {str(e)}")
                self.send_error(500, str(e))
        elif self.path == '/api/example_searches':
            try:
                # Load pre-generated example searches
                example_file = Path('data/example_searches.json')
                if example_file.exists():
                    with open(example_file, 'r') as f:
                        example_searches = json.load(f)
                else:
                    example_searches = {}
                
                # Send response
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')  # Allow CORS
                self.end_headers()
                
                response = json.dumps(example_searches)
                self.wfile.write(response.encode('utf-8'))
            except Exception as e:
                print(f"Example search error: {str(e)}")
                self.send_error(500, str(e))
        else:
            self.send_error(404, 'API endpoint not found')
    
    def local_search(self, query_text, top_n=20, use_low_dim=False, projection_method='umap'):
        """
        Local search function that uses the copied database files in the website data directory
        """
        try:
            # Determine which file to use based on whether we're using low-dim projections
            if use_low_dim:
                file_path = Path('data/low_dim_embeddings.nc')
                print(f"Using low-dimensional embeddings with {projection_method} projection")
            else:
                file_path = Path('data/scholar_embeddings.nc')
                print(f"Using high-dimensional embeddings")
            
            # Check if file exists
            if not file_path.exists():
                print(f"Embeddings file not found: {file_path}")
                # Fall back to using the imported function
                return find_similar_scholars(query_text, top_n, use_low_dim, projection_method)
            
            # Load scholar embeddings
            ds = xr.open_dataset(file_path)
            print(f"Loaded embeddings for {ds.sizes['scholar']} scholars")
            
            if use_low_dim:
                # For low-dim projections, we'll use Euclidean distance in 2D space
                # Get the projection coordinates
                if projection_method not in ['pca', 'tsne', 'umap']:
                    print(f"Invalid projection method: {projection_method}. Using PCA.")
                    projection_method = 'pca'
                
                # Extract coordinates for the specified projection method
                x_coords = ds[f'{projection_method}_x'].values
                y_coords = ds[f'{projection_method}_y'].values
                
                # Combine into a single array of 2D points
                points = np.column_stack((x_coords, y_coords))
                
                # Calculate distances (using Euclidean distance in 2D space)
                # This is a simplification - in a real system, we would project the query
                # For now, we'll use the center of the projection as our query point
                query_point = np.mean(points, axis=0)
                
                # Calculate distances
                distances = np.sqrt(np.sum((points - query_point)**2, axis=1))
                
                # Convert distances to similarities (closer = more similar)
                max_dist = np.max(distances)
                similarities = 1 - (distances / max_dist)
                
                # Get indices of top N scholars
                top_indices = np.argsort(similarities)[-top_n:][::-1]
                
                # Get scholar information
                scholar_ids = ds.scholar_id.values
                scholar_names = ds.scholar_name.values
                
                # Create result list
                results = []
                for idx in top_indices:
                    results.append({
                        'scholar_id': scholar_ids[idx],
                        'name': scholar_names[idx],
                        'similarity': float(similarities[idx])
                    })
                
                return results
            else:
                # For high-dimensional embeddings, we'll use cosine similarity
                # Get embedding for the query
                query_embedding = get_query_embedding(query_text)
                if query_embedding is None:
                    return []
                
                # Extract embeddings and metadata
                embeddings = ds.embedding.values
                scholar_ids = ds.scholar_id.values
                scholar_names = ds.scholar_name.values
                
                # Calculate similarity scores
                similarities = []
                for i in range(len(embeddings)):
                    similarity = cosine_similarity(query_embedding, embeddings[i])
                    similarities.append((i, similarity))
                
                # Sort by similarity (descending)
                similarities.sort(key=lambda x: x[1], reverse=True)
                
                # Get top N scholars
                top_scholars = []
                for i, similarity in similarities[:top_n]:
                    top_scholars.append({
                        'scholar_id': scholar_ids[i],
                        'name': scholar_names[i],
                        'similarity': float(similarity)
                    })
                
                return top_scholars
        except Exception as e:
            print(f"Local search error: {str(e)}")
            # Fall back to using the imported function
            return find_similar_scholars(query_text, top_n, use_low_dim, projection_method)

def serve_website(port=8000):
    """
    Serve the website on the specified port and open it in a browser.
    """
    # Change to the website directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Create a simple HTTP server with custom handler
    handler = ScholarSearchHandler
    
    # Allow the server to be reused
    socketserver.TCPServer.allow_reuse_address = True
    
    # Create and start the server
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"Serving website at http://localhost:{port}")
        print(f"Debug info available at http://localhost:{port}/debug")
        print("Press Ctrl+C to stop the server")
        
        # Open the website in a browser
        webbrowser.open(f"http://localhost:{port}")
        
        # Keep the server running
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

if __name__ == "__main__":
    serve_website() 