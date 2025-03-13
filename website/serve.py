import http.server
import socketserver
import os
import webbrowser
import json
import sys
import numpy as np
from pathlib import Path
import shutil
import urllib.parse

# Add parent directory to path to import scholar_board module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scholar_board.search_embeddings import get_query_embedding, get_query_umap_coords

# Hardcoded path to the data directory
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
WEBSITE_DIR = os.path.dirname(os.path.abspath(__file__))

# Ensure the model directory exists
MODEL_DIR = os.path.join(DATA_DIR, 'model')
os.makedirs(MODEL_DIR, exist_ok=True)

class ScholarSearchHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Check if this is a request for scholar profile data
        if self.path.startswith('/api/scholar/'):
            scholar_id = self.path.split('/')[-1]
            self.serve_scholar_profile(scholar_id)
        # Check if this is a request for scholars.json
        elif self.path == '/api/scholars':
            self.serve_scholars_json()
        # Check if this is a request for debug info
        elif self.path == '/debug':
            self.serve_debug_info()
        # Otherwise, serve static files
        else:
            super().do_GET()
    
    def serve_debug_info(self):
        """Serve debug information page"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        # Get paths
        website_dir = WEBSITE_DIR
        data_dir = DATA_DIR
        website_data_dir = os.path.join(WEBSITE_DIR, 'data')
        model_dir = MODEL_DIR
        
        # List files in data directory
        data_files = os.listdir(data_dir) if os.path.exists(data_dir) else []
        website_data_files = os.listdir(website_data_dir) if os.path.exists(website_data_dir) else []
        model_files = os.listdir(model_dir) if os.path.exists(model_dir) else []
        
        # Check if scholars.json exists in both locations
        scholars_json_path = os.path.join(data_dir, 'scholars.json')
        website_scholars_json_path = os.path.join(website_data_dir, 'scholars.json')
        
        scholars_json_exists = os.path.exists(scholars_json_path)
        website_scholars_json_exists = os.path.exists(website_scholars_json_path)
        
        # Get size of scholars.json
        scholars_json_size = os.path.getsize(scholars_json_path) if scholars_json_exists else 0
        website_scholars_json_size = os.path.getsize(website_scholars_json_path) if website_scholars_json_exists else 0
        
        # Check if UMAP model exists
        umap_model_path = os.path.join(model_dir, 'umap_n30_d0.2_model.joblib')
        umap_model_exists = os.path.exists(umap_model_path)
        
        # Try to load scholars.json from the location that will be used
        scholars_json_content = None
        used_path = website_scholars_json_path if website_scholars_json_exists else scholars_json_path
        used_path_exists = website_scholars_json_exists or scholars_json_exists
        
        if used_path_exists:
            try:
                with open(used_path, 'r') as f:
                    scholars_json_content = json.load(f)
            except Exception as e:
                scholars_json_content = f"Error loading scholars.json: {str(e)}"
        
        # Create debug HTML
        debug_html = f"""
        <html>
        <head><title>ScholarBoard Debug Info</title></head>
        <body>
            <h1>ScholarBoard Debug Information</h1>
            <h2>Paths</h2>
            <ul>
                <li>Website directory: {website_dir}</li>
                <li>Data directory: {data_dir}</li>
                <li>Website data directory: {website_data_dir}</li>
                <li>Model directory: {model_dir}</li>
            </ul>
            <h2>Files</h2>
            <h3>Data directory files</h3>
            <ul>{''.join([f'<li>{f}</li>' for f in data_files[:20]])}</ul>
            <h3>Website data directory files</h3>
            <ul>{''.join([f'<li>{f}</li>' for f in website_data_files[:20]])}</ul>
            <h3>Model directory files</h3>
            <ul>{''.join([f'<li>{f}</li>' for f in model_files[:20]])}</ul>
            <h2>scholars.json</h2>
            <ul>
                <li>Main data path: {scholars_json_path} (exists: {scholars_json_exists}, size: {scholars_json_size} bytes)</li>
                <li>Website data path: {website_scholars_json_path} (exists: {website_scholars_json_exists}, size: {website_scholars_json_size} bytes)</li>
                <li>Used path: {used_path} (exists: {used_path_exists})</li>
            </ul>
            <h2>UMAP Model</h2>
            <ul>
                <li>UMAP model path: {umap_model_path} (exists: {umap_model_exists})</li>
            </ul>
        </body>
        </html>
        """
        
        self.wfile.write(debug_html.encode('utf-8'))
    
    def serve_scholars_json(self):
        """Serve scholars.json file"""
        try:
            # First try to load scholars.json from website/data directory
            website_scholars_path = os.path.join(WEBSITE_DIR, 'data', 'scholars.json')
            
            # If not found, try the main data directory
            scholars_path = os.path.join(DATA_DIR, 'scholars.json')
            
            # Use website data if it exists, otherwise use main data
            if os.path.exists(website_scholars_path):
                scholars_path = website_scholars_path
            
            if not os.path.exists(scholars_path):
                print(f"Scholars data not found at: {scholars_path}")
                self.send_error(404, 'Scholars data not found')
                return
            
            print(f"Loading scholars from: {scholars_path}")
            with open(scholars_path, 'r') as f:
                scholars = json.load(f)
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')  # Allow CORS
            self.end_headers()
            
            response = json.dumps(scholars)
            self.wfile.write(response.encode('utf-8'))
        except Exception as e:
            print(f"Error serving scholars.json: {str(e)}")
            self.send_error(500, str(e))
    
    def serve_scholar_profile(self, scholar_id):
        """Serve scholar profile data"""
        try:
            print(f"Serving profile for scholar ID: {scholar_id}")
            
            # Load scholars.json
            scholars_path = os.path.join(WEBSITE_DIR, 'data', 'scholars.json')
            if not os.path.exists(scholars_path):
                scholars_path = os.path.join(DATA_DIR, 'scholars.json')
            
            if not os.path.exists(scholars_path):
                print(f"Scholars data not found at: {scholars_path}")
                self.send_error(404, 'Scholars data not found')
                return
            
            print(f"Loading scholars from: {scholars_path}")
            with open(scholars_path, 'r') as f:
                scholars_data = json.load(f)
            
            # Find the scholar by ID - scholars are stored as an object with IDs as keys
            # Make sure to handle the case where scholar_id might need padding with zeros
            scholar_data = scholars_data.get(scholar_id)
            
            # If not found, try with zero-padded ID (e.g., "1" -> "001")
            if not scholar_data and scholar_id.isdigit():
                padded_id = scholar_id.zfill(3)
                scholar_data = scholars_data.get(padded_id)
                if scholar_data:
                    scholar_id = padded_id
            
            if not scholar_data:
                print(f"Scholar with ID '{scholar_id}' not found.")
                self.send_error(404, f'Scholar with ID {scholar_id} not found')
                return
            
            print(f"Found scholar: {scholar_data.get('name')}")
            
            # Get profile pic from data/profile_pics directory using scholar_id
            profile_pic_path = f"data/profile_pics/{scholar_id}.jpg"  # Default path format
            
            # Check if the profile pic exists in the website directory
            website_profile_pic = os.path.join(WEBSITE_DIR, profile_pic_path)
            if not os.path.exists(website_profile_pic):
                # If not in website directory, check in main data directory
                data_profile_pic = os.path.join(DATA_DIR, f"profile_pics/{scholar_id}.jpg")
                if os.path.exists(data_profile_pic):
                    # Copy to website directory
                    os.makedirs(os.path.dirname(website_profile_pic), exist_ok=True)
                    shutil.copy2(data_profile_pic, website_profile_pic)
                    print(f"Copied profile pic from {data_profile_pic} to {website_profile_pic}")
                else:
                    # Use placeholder if no profile pic found
                    profile_pic_path = "images/placeholder.jpg"
                    print(f"No profile pic found for scholar {scholar_id}, using placeholder")
            
            # Try to load formatted markdown content
            scholar_name = scholar_data.get('name', '')
            markdown_content = ""
            
            # Find the markdown file using name and ID format: scholar_name_scholar_id.md
            # First try with the exact name
            markdown_file = os.path.join(WEBSITE_DIR, 'data', 'scholar_markdown', f"{scholar_name}_{scholar_id}.md")
            
            # If not found in website directory, try in data directory
            if not os.path.exists(markdown_file):
                markdown_file = os.path.join(DATA_DIR, 'scholar_markdown', f"{scholar_name}_{scholar_id}.md")
            
            # If still not found, try with just the ID
            if not os.path.exists(markdown_file):
                markdown_file = os.path.join(WEBSITE_DIR, 'data', 'scholar_markdown', f"{scholar_id}.md")
                if not os.path.exists(markdown_file):
                    markdown_file = os.path.join(DATA_DIR, 'scholar_markdown', f"{scholar_id}.md")
            
            # If still not found, try listing all markdown files and find a match
            if not os.path.exists(markdown_file):
                website_markdown_dir = os.path.join(WEBSITE_DIR, 'data', 'scholar_markdown')
                if os.path.exists(website_markdown_dir):
                    for filename in os.listdir(website_markdown_dir):
                        if filename.endswith('.md') and (scholar_id in filename or scholar_name in filename):
                            markdown_file = os.path.join(website_markdown_dir, filename)
                            break
            
            if not os.path.exists(markdown_file):
                data_markdown_dir = os.path.join(DATA_DIR, 'scholar_markdown')
                if os.path.exists(data_markdown_dir):
                    for filename in os.listdir(data_markdown_dir):
                        if filename.endswith('.md') and (scholar_id in filename or scholar_name in filename):
                            markdown_file = os.path.join(data_markdown_dir, filename)
                            break
            
            if os.path.exists(markdown_file):
                try:
                    with open(markdown_file, 'r', encoding='utf-8') as f:
                        markdown_content = f.read()
                    print(f"Loaded markdown file: {markdown_file}")
                except Exception as e:
                    print(f"Error reading markdown file: {str(e)}")
            else:
                print(f"No markdown file found for scholar {scholar_id}. Tried path: {markdown_file}")
            
            # Get UMAP coordinates from the umap_projection field
            umap_coords = [0, 0]
            if scholar_data.get('umap_projection'):
                umap_coords = [
                    scholar_data['umap_projection'].get('x', 0),
                    scholar_data['umap_projection'].get('y', 0)
                ]
            
            # Prepare response data
            response_data = {
                'scholar_id': scholar_id,
                'name': scholar_data.get('name', 'Unknown'),
                'institution': scholar_data.get('institution', 'Unknown'),
                'country': scholar_data.get('country', 'Unknown'),
                'profile_pic': profile_pic_path,
                'umap': umap_coords,
                'cluster_id': scholar_data.get('cluster', 0),  # Include cluster_id for coloring
                'markdown_content': markdown_content
            }
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')  # Allow CORS
            self.end_headers()
            
            response = json.dumps(response_data)
            self.wfile.write(response.encode('utf-8'))
            print(f"Successfully served profile for {scholar_data.get('name')}")
            
        except Exception as e:
            print(f"Error serving scholar profile: {str(e)}")
            import traceback
            traceback.print_exc()
            self.send_error(500, str(e))
    
    def do_POST(self):
        # Check if this is a search request
        if self.path == '/api/search':
            self.handle_search_request()
        else:
            self.send_error(404, 'Not Found')
    
    def handle_search_request(self):
        """Handle search requests for both scholar name search and research query embedding"""
        try:
            # Get the content length
            content_length = int(self.headers['Content-Length'])
            
            # Read the request body
            request_body = self.rfile.read(content_length).decode('utf-8')
            
            # Parse the JSON request
            request_data = json.loads(request_body)
            
            # Check if this is a scholar name search or a research query
            search_type = request_data.get('type', 'name')
            query = request_data.get('query', '')
            
            if not query:
                self.send_error(400, 'Missing query parameter')
                return
            
            print(f"Handling search request of type '{search_type}' with query: {query}")
            
            # Load scholars data
            scholars_path = os.path.join(WEBSITE_DIR, 'data', 'scholars.json')
            if not os.path.exists(scholars_path):
                scholars_path = os.path.join(DATA_DIR, 'scholars.json')
            
            if not os.path.exists(scholars_path):
                self.send_error(404, 'Scholars data not found')
                return
            
            with open(scholars_path, 'r') as f:
                scholars_data = json.load(f)
            
            response_data = {}
            
            if search_type == 'name':
                # Search for scholars by name
                matching_scholars = []
                
                # Convert query to lowercase for case-insensitive search
                query_lower = query.lower()
                
                # Search through scholars
                for scholar_id, scholar in scholars_data.items():
                    if query_lower in scholar.get('name', '').lower():
                        # Add scholar to results
                        matching_scholars.append({
                            'id': scholar_id,
                            'name': scholar.get('name', ''),
                            'institution': scholar.get('institution', ''),
                            'country': scholar.get('country', ''),
                            'umap': [
                                scholar.get('umap_projection', {}).get('x', 0),
                                scholar.get('umap_projection', {}).get('y', 0)
                            ]
                        })
                
                # Sort results by relevance (exact matches first, then partial matches)
                matching_scholars.sort(key=lambda s: 0 if s['name'].lower() == query_lower else 1)
                
                # Limit to top 10 results
                matching_scholars = matching_scholars[:10]
                
                response_data = {
                    'type': 'name',
                    'results': matching_scholars
                }
                
            elif search_type == 'research':
                # Project the research query to UMAP space
                try:
                    result = get_query_umap_coords(query)
                    
                    if result['error']:
                        self.send_error(500, f"Error projecting query: {result['error']}")
                        return
                    
                    # Get the coordinates
                    x, y = result['coords']
                    
                    response_data = {
                        'type': 'research',
                        'coords': [float(x), float(y)]
                    }
                    
                except Exception as e:
                    self.send_error(500, f"Error projecting query: {str(e)}")
                    return
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')  # Allow CORS
            self.end_headers()
            
            response = json.dumps(response_data)
            self.wfile.write(response.encode('utf-8'))
            
        except Exception as e:
            print(f"Error handling search request: {str(e)}")
            import traceback
            traceback.print_exc()
            self.send_error(500, str(e))

def serve_website(port=8000):
    """
    Serve the website on the specified port and open it in a browser.
    """
    # Create website/data directory if it doesn't exist
    website_data_dir = os.path.join(WEBSITE_DIR, 'data')
    os.makedirs(website_data_dir, exist_ok=True)
    
    # Create model directory if it doesn't exist
    model_dir = os.path.join(DATA_DIR, 'model')
    os.makedirs(model_dir, exist_ok=True)
    
    # Check if the UMAP model exists
    umap_model_path = os.path.join(model_dir, 'umap_n30_d0.2_model.joblib')
    if not os.path.exists(umap_model_path):
        print(f"Warning: UMAP model not found at {umap_model_path}")
        print("Research query projection may not work correctly.")
    else:
        print(f"Found UMAP model at {umap_model_path}")
    
    # Copy scholars.json to website/data if it doesn't exist or is older than the source
    scholars_json_path = os.path.join(DATA_DIR, 'scholars.json')
    website_scholars_json_path = os.path.join(website_data_dir, 'scholars.json')
    
    if os.path.exists(scholars_json_path):
        if not os.path.exists(website_scholars_json_path) or \
           os.path.getmtime(scholars_json_path) > os.path.getmtime(website_scholars_json_path):
            print(f"Copying scholars.json to {website_scholars_json_path}")
            shutil.copy2(scholars_json_path, website_scholars_json_path)
    
    # Create website/data/profile_pics directory if it doesn't exist
    website_profile_pics_dir = os.path.join(website_data_dir, 'profile_pics')
    os.makedirs(website_profile_pics_dir, exist_ok=True)
    
    # Create website/data/scholar_markdown directory if it doesn't exist
    website_markdown_dir = os.path.join(website_data_dir, 'scholar_markdown')
    os.makedirs(website_markdown_dir, exist_ok=True)
    
    
    # Change to the website directory
    os.chdir(WEBSITE_DIR)
    
    # Create a simple HTTP server with custom handler
    handler = ScholarSearchHandler
    
    # Allow the server to be reused
    socketserver.TCPServer.allow_reuse_address = True
    
    # Create and start the server
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"Serving website at http://localhost:{port}")
        print(f"Debug info available at http://localhost:{port}/debug")
        print(f"Using data directory: {DATA_DIR}")
        print(f"Using website directory: {WEBSITE_DIR}")
        print(f"Using model directory: {model_dir}")
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