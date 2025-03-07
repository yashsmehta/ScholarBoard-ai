import http.server
import socketserver
import os
import webbrowser
import json
import sys
import numpy as np
from pathlib import Path

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
        
        # Create debug HTML
        debug_html = f"""
        <html>
        <head>
            <title>ScholarBoard Debug</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2 {{ color: #333; }}
                pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto; }}
                .section {{ margin-bottom: 30px; }}
            </style>
        </head>
        <body>
            <h1>ScholarBoard Debug Information</h1>
            
            <div class="section">
                <h2>Paths</h2>
                <p>Website Directory: {website_dir}</p>
                <p>Main Data Directory: {data_dir}</p>
                <p>Website Data Directory: {website_data_dir}</p>
            </div>
            
            <div class="section">
                <h2>Data Files</h2>
                <p>Files in main data directory: {len(data_files)}</p>
                <pre>{', '.join(data_files)}</pre>
                <p>Files in website data directory: {len(website_data_files)}</p>
                <pre>{', '.join(website_data_files)}</pre>
            </div>
            
            <div class="section">
                <h2>scholars.json</h2>
                <p>Exists in main data: {scholars_json_exists}</p>
                <p>Size in main data: {scholars_json_size} bytes</p>
                <p>Exists in website data: {website_scholars_json_exists}</p>
                <p>Size in website data: {website_scholars_json_size} bytes</p>
                <p>Using path: {used_path}</p>
                <p>Scholar count: {len(scholars_json_content) if isinstance(scholars_json_content, list) else 'N/A'}</p>
            </div>
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
            
            # Try to load perplexity info if available
            perplexity_file = os.path.join(DATA_DIR, 'perplexity_info', f"{scholar_id}.txt")
            raw_text = ""
            
            if os.path.exists(perplexity_file):
                try:
                    with open(perplexity_file, 'r', encoding='utf-8') as f:
                        raw_text = f.read()
                    print(f"Loaded perplexity file: {perplexity_file}")
                except Exception as e:
                    print(f"Error reading perplexity file: {str(e)}")
            else:
                # Try alternative filename formats
                alt_perplexity_file = os.path.join(DATA_DIR, 'perplexity_info', f"{scholar_data.get('name')}_{scholar_id}_raw.txt")
                if os.path.exists(alt_perplexity_file):
                    try:
                        with open(alt_perplexity_file, 'r', encoding='utf-8') as f:
                            raw_text = f.read()
                        print(f"Loaded alternative perplexity file: {alt_perplexity_file}")
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
                'raw_text': raw_text
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