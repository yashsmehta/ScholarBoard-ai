import http.server
import socketserver
import os
import webbrowser
import json
import sys
import numpy as np
from pathlib import Path
import shutil

# Add parent directory to path to import scholar_board module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scholar_board.search_embeddings import find_similar_scholars, get_query_embedding, cosine_similarity

# Hardcoded path to the data directory
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
WEBSITE_DIR = os.path.dirname(os.path.abspath(__file__))

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
        
        # List files in data directory
        data_files = os.listdir(data_dir) if os.path.exists(data_dir) else []
        website_data_files = os.listdir(website_data_dir) if os.path.exists(website_data_dir) else []
        
        # Check if scholars.json exists in both locations
        scholars_json_path = os.path.join(data_dir, 'scholars.json')
        website_scholars_json_path = os.path.join(website_data_dir, 'scholars.json')
        
        scholars_json_exists = os.path.exists(scholars_json_path)
        website_scholars_json_exists = os.path.exists(website_scholars_json_path)
        
        # Get size of scholars.json
        scholars_json_size = os.path.getsize(scholars_json_path) if scholars_json_exists else 0
        website_scholars_json_size = os.path.getsize(website_scholars_json_path) if website_scholars_json_exists else 0
        
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
                scholars = json.load(f)
            
            # Find the scholar by ID
            scholar_data = None
            for scholar in scholars:
                # Convert both to strings for comparison
                if str(scholar.get('id')).strip() == str(scholar_id).strip():
                    scholar_data = scholar
                    break
            
            if not scholar_data:
                print(f"Scholar with ID '{scholar_id}' not found. Available IDs: {[s.get('id') for s in scholars[:5]]}...")
                self.send_error(404, f'Scholar with ID {scholar_id} not found')
                return
            
            print(f"Found scholar: {scholar_data.get('name')}")
            
            # Check if profile pic exists
            profile_pic = scholar_data.get('profile_pic', 'placeholder.jpg')
            profile_pic_path = profile_pic
            
            # Try to load formatted markdown content if available
            scholar_name = scholar_data.get('name', '')
            markdown_content = ""
            
            # First try to find the markdown file using name and ID
            markdown_file = os.path.join(DATA_DIR, 'formatted_scholar_info', f"{scholar_name}_{scholar_id}.md")
            
            if not os.path.exists(markdown_file):
                # Try alternative formats that might exist
                possible_files = [
                    os.path.join(DATA_DIR, 'formatted_scholar_info', f"{scholar_name}_{scholar_id.zfill(3)}.md"),
                    os.path.join(DATA_DIR, 'formatted_scholar_info', f"{scholar_name}_{scholar_id.zfill(2)}.md")
                ]
                
                for alt_file in possible_files:
                    if os.path.exists(alt_file):
                        markdown_file = alt_file
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
                
                # Fall back to perplexity info if markdown not found
                perplexity_file = os.path.join(DATA_DIR, 'perplexity_info', f"{scholar_id}.txt")
                raw_text = ""
                
                if os.path.exists(perplexity_file):
                    try:
                        with open(perplexity_file, 'r', encoding='utf-8') as f:
                            raw_text = f.read()
                        print(f"Loaded perplexity file as fallback: {perplexity_file}")
                    except Exception as e:
                        print(f"Error reading perplexity file: {str(e)}")
                else:
                    # Try alternative filename formats for perplexity
                    alt_perplexity_file = os.path.join(DATA_DIR, 'perplexity_info', f"{scholar_data.get('name')}_{scholar_id}_raw.txt")
                    if os.path.exists(alt_perplexity_file):
                        try:
                            with open(alt_perplexity_file, 'r', encoding='utf-8') as f:
                                raw_text = f.read()
                            print(f"Loaded alternative perplexity file as fallback: {alt_perplexity_file}")
                        except Exception as e:
                            print(f"Error reading alternative perplexity file: {str(e)}")
                    else:
                        print(f"No perplexity file found for scholar {scholar_id}. Tried paths:")
                        print(f"  - {perplexity_file}")
                        print(f"  - {alt_perplexity_file}")
            
            # Prepare response data
            response_data = {
                'scholar_id': scholar_id,
                'name': scholar_data.get('name', 'Unknown'),
                'institution': scholar_data.get('institution', 'Unknown'),
                'country': scholar_data.get('country', 'Unknown'),
                'profile_pic': profile_pic_path,
                'pca': scholar_data.get('pca', [0, 0]),
                'tsne': scholar_data.get('tsne', [0, 0]),
                'umap': scholar_data.get('umap', [0, 0]),
                'markdown_content': markdown_content,
                'raw_text': raw_text if not markdown_content else ""
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
        # We're removing the search functionality, so just return 404 for POST requests
        self.send_error(404, 'Not Found')

def serve_website(port=8000):
    """
    Serve the website on the specified port and open it in a browser.
    """
    # Create website/data directory if it doesn't exist
    website_data_dir = os.path.join(WEBSITE_DIR, 'data')
    os.makedirs(website_data_dir, exist_ok=True)
    
    # Copy scholars.json to website/data if it doesn't exist or is older than the source
    scholars_json_path = os.path.join(DATA_DIR, 'scholars.json')
    website_scholars_json_path = os.path.join(website_data_dir, 'scholars.json')
    
    if os.path.exists(scholars_json_path):
        if not os.path.exists(website_scholars_json_path) or \
           os.path.getmtime(scholars_json_path) > os.path.getmtime(website_scholars_json_path):
            print(f"Copying scholars.json to {website_scholars_json_path}")
            shutil.copy2(scholars_json_path, website_scholars_json_path)
    
    # Create website/data/formatted_scholar_info directory if it doesn't exist
    website_markdown_dir = os.path.join(website_data_dir, 'formatted_scholar_info')
    os.makedirs(website_markdown_dir, exist_ok=True)
    
    # Copy formatted markdown files to website/data/formatted_scholar_info
    source_markdown_dir = os.path.join(DATA_DIR, 'formatted_scholar_info')
    if os.path.exists(source_markdown_dir):
        print(f"Copying markdown files to {website_markdown_dir}")
        for filename in os.listdir(source_markdown_dir):
            if filename.endswith('.md'):
                source_file = os.path.join(source_markdown_dir, filename)
                dest_file = os.path.join(website_markdown_dir, filename)
                
                # Only copy if the source file is newer or the destination doesn't exist
                if not os.path.exists(dest_file) or \
                   os.path.getmtime(source_file) > os.path.getmtime(dest_file):
                    shutil.copy2(source_file, dest_file)
    
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