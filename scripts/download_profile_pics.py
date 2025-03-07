import os
import csv
import requests
import time
import re
import json
from pathlib import Path
import random
from urllib.parse import quote_plus

def download_profile_pictures():
    """
    Download profile pictures for scholars listed in scholars.csv
    using a simple and direct approach.
    """
    # Create output directory
    output_dir = Path("data/profile_pics")
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Read scholars.csv
    scholars = []
    try:
        with open("data/scholars.csv", "r") as f:
            reader = csv.DictReader(f)
            scholars = list(reader)
        print(f"Found {len(scholars)} scholars in CSV file")
    except Exception as e:
        print(f"Error reading scholars.csv: {e}")
        return
    
    # Track successful and failed downloads
    successful = 0
    failed = 0
    
    # User agents to rotate (to avoid being blocked)
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
    ]
    
    # Download profile picture for each scholar
    for i, scholar in enumerate(scholars):
        name = scholar.get("scholar_name", "").strip()
        institution = scholar.get("institution", "").strip()
        
        if not name:
            print(f"Skipping row {i+1}: Missing scholar name")
            failed += 1
            continue
        
        # Create a safe filename
        safe_name = name.replace(" ", "_").replace(",", "").replace(".", "")
        output_path = output_dir / f"{safe_name}.jpg"
        
        # Skip if already downloaded
        if output_path.exists():
            print(f"Skipping {name}: Image already exists")
            successful += 1
            continue
        
        print(f"Processing {name} ({i+1}/{len(scholars)})")
        
        # Try multiple methods to find an image
        image_url = None
        
        # Method 1: Try using the Perplexity API if available
        try:
            # Check if we have a Perplexity API key in the environment
            perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
            
            if perplexity_api_key:
                print(f"Using Perplexity API to find image for {name}")
                
                headers = {
                    "Authorization": f"Bearer {perplexity_api_key}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "model": "llama-3-sonar-small-32k-online",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a helpful assistant that provides direct image URLs for scholars."
                        },
                        {
                            "role": "user",
                            "content": f"Find a direct URL to a professional headshot or portrait image of {name}, who is a scholar at {institution}. Only respond with the direct image URL and nothing else. The URL must end with .jpg, .jpeg, or .png. Important that the image should be a headshot of the person."
                        }
                    ]
                }
                
                response = requests.post(
                    "https://api.perplexity.ai/chat/completions",
                    headers=headers,
                    json=data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    
                    # Extract URL using regex
                    url_match = re.search(r'https?://[^\s"\'<>]+\.(jpg|jpeg|png)', content)
                    if url_match:
                        image_url = url_match.group(0)
                        print(f"Found image URL via Perplexity: {image_url}")
        except Exception as e:
            print(f"Error using Perplexity API for {name}: {e}")
        
        # Method 2: Try using a direct Bing image search
        if not image_url:
            try:
                print(f"Trying Bing image search for {name}")
                
                # Construct search query
                query = f"{name} {institution} scholar headshot"
                encoded_query = quote_plus(query)
                
                # Bing image search URL
                search_url = f"https://www.bing.com/images/search?q={encoded_query}&qft=+filterui:photo-photo&form=IRFLTR"
                
                headers = {
                    "User-Agent": random.choice(user_agents),
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5"
                }
                
                response = requests.get(search_url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    # Use regex to find image URLs in the response
                    content = response.text
                    
                    # Look for murl pattern in Bing's response
                    img_urls = re.findall(r'"murl":"(https?://[^"]+)"', content)
                    
                    if img_urls:
                        # Get the first image URL
                        image_url = img_urls[0].replace('\\', '')
                        print(f"Found image URL via Bing: {image_url}")
            except Exception as e:
                print(f"Error with Bing search for {name}: {e}")
        
        # Method 3: Try using a direct Google image search as a last resort
        if not image_url:
            try:
                print(f"Trying Google image search for {name}")
                
                # Construct search query
                query = f"{name} {institution} scholar"
                encoded_query = quote_plus(query)
                
                # Google image search URL
                search_url = f"https://www.google.com/search?q={encoded_query}&tbm=isch"
                
                headers = {
                    "User-Agent": random.choice(user_agents),
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5"
                }
                
                response = requests.get(search_url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    # Use regex to find image URLs in the response
                    content = response.text
                    
                    # Look for image URLs in Google's response
                    img_urls = re.findall(r'"(https?://[^"]+\.(jpg|jpeg|png))"', content)
                    
                    filtered_urls = []
                    for url, ext in img_urls:
                        # Filter out small thumbnails and icons
                        if 'icon' not in url.lower() and 'thumb' not in url.lower() and 'logo' not in url.lower():
                            filtered_urls.append(url)
                    
                    if filtered_urls:
                        # Get the first image URL
                        image_url = filtered_urls[0]
                        print(f"Found image URL via Google: {image_url}")
            except Exception as e:
                print(f"Error with Google search for {name}: {e}")
        
        # If we found an image URL, download it
        if image_url:
            try:
                print(f"Downloading image for {name} from {image_url}")
                
                # Set headers for the download request
                download_headers = {
                    "User-Agent": random.choice(user_agents),
                    "Accept": "image/webp,image/*,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Referer": "https://www.google.com/"
                }
                
                img_response = requests.get(image_url, stream=True, timeout=15, headers=download_headers)
                
                if img_response.status_code == 200:
                    # Check if the content type is an image
                    content_type = img_response.headers.get('Content-Type', '')
                    if 'image' in content_type:
                        # Save the image
                        with open(output_path, "wb") as img_file:
                            for chunk in img_response.iter_content(chunk_size=8192):
                                img_file.write(chunk)
                        
                        print(f"Saved image for {name} to {output_path}")
                        successful += 1
                    else:
                        print(f"Error: Content is not an image for {name} (Content-Type: {content_type})")
                        failed += 1
                else:
                    print(f"Error downloading image for {name}: {img_response.status_code}")
                    failed += 1
            except Exception as e:
                print(f"Error downloading image for {name}: {e}")
                failed += 1
        else:
            print(f"No image found for {name}")
            failed += 1
        
        # Sleep to avoid being rate-limited
        time.sleep(random.uniform(2.0, 4.0))
    
    # Print summary
    print(f"\nDownload complete!")
    print(f"Successfully downloaded: {successful}/{len(scholars)}")
    print(f"Failed: {failed}/{len(scholars)}")
    print(f"Images saved to: {output_dir}")

if __name__ == "__main__":
    download_profile_pictures() 