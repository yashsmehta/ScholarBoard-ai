import http.server
import socketserver
import os
import webbrowser
import json
import sys
import urllib.parse
from io import BytesIO

# Add parent directory to path to import researcher_info module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from researcher_info.search_embeddings import find_similar_researchers

class ResearcherSearchHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/search':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                query = data.get('query', '')
                
                if not query:
                    self.send_error(400, 'Query is required')
                    return
                
                # Find similar researchers
                top_researchers = find_similar_researchers(query)
                
                # Send response
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                response = json.dumps({'researchers': top_researchers})
                self.wfile.write(response.encode('utf-8'))
            except Exception as e:
                self.send_error(500, str(e))
        else:
            self.send_error(404, 'API endpoint not found')
    
    def do_GET(self):
        # Handle normal file serving
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

def serve_website(port=8000):
    """
    Serve the website on the specified port and open it in a browser.
    """
    # Change to the website directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Create a simple HTTP server with custom handler
    handler = ResearcherSearchHandler
    
    # Allow the server to be reused
    socketserver.TCPServer.allow_reuse_address = True
    
    # Create and start the server
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"Serving website at http://localhost:{port}")
        
        # Open the website in a browser
        webbrowser.open(f"http://localhost:{port}")
        
        # Keep the server running
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

if __name__ == "__main__":
    serve_website() 