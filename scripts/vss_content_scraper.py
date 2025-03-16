#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import time
import os
import re
from pathlib import Path
import json
import random
from tqdm import tqdm
import concurrent.futures

def scrape_vss_abstract(url, retry_count=2, backoff_factor=0.3):
    """
    Scrape content from a VSS abstract page with retry logic.
    
    Args:
        url (str): URL of the VSS abstract page
        retry_count (int): Number of retries on failure
        backoff_factor (float): Backoff factor for exponential delay
        
    Returns:
        dict: Dictionary containing the extracted information
    """
    for attempt in range(retry_count + 1):
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract the main content div
            content_div = soup.find('div', {'class': 'entry-content'})
            
            if not content_div:
                print(f"Warning: Could not find main content for {url}")
                return None
                
            # Extract title
            title_elem = soup.find('h1', {'class': 'entry-title'})
            title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"
            
            # Extract all paragraphs
            paragraphs = content_div.find_all('p')
            
            # Third paragraph typically contains author information
            author_info = paragraphs[2].get_text(strip=True) if len(paragraphs) > 2 else ""
            
            # Fourth paragraph typically contains the abstract
            abstract = paragraphs[3].get_text(strip=True) if len(paragraphs) > 3 else ""
            
            # Create a structured result with only essential information
            result = {
                'url': url,
                'title': title,
                'author_info': author_info,
                'abstract': abstract
            }
            
            return result
            
        except requests.exceptions.RequestException as e:
            if attempt < retry_count:
                # Calculate backoff time with minimal jitter
                backoff_time = backoff_factor * (2 ** attempt) + random.uniform(0, 0.1)
                print(f"Error scraping {url}: {e}. Retrying in {backoff_time:.2f} seconds...")
                time.sleep(backoff_time)
            else:
                print(f"Failed to scrape {url} after {retry_count} retries: {e}")
                return None
        except Exception as e:
            print(f"Unexpected error scraping {url}: {e}")
            return None

def save_abstract_content(content, output_dir):
    """Save the scraped content to a JSON file."""
    if not content:
        return False
    
    try:
        # Create output directory if it doesn't exist
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a safe filename from the URL
        url_id = content['url'].split('id=')[-1]
        filename = f"abstract_{url_id}.json"
        
        # Save as JSON
        with open(output_dir / filename, 'w') as f:
            json.dump(content, f, indent=2)
        
        return True
    except Exception as e:
        print(f"Error saving content for {content.get('url', 'unknown URL')}: {e}")
        return False

def read_urls_from_file(file_path):
    """Read URLs from a text file."""
    try:
        with open(file_path, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        return urls
    except Exception as e:
        print(f"Error reading URLs from {file_path}: {e}")
        return []

def process_url(url, output_dir):
    """Process a single URL and save the result."""
    try:
        content = scrape_vss_abstract(url)
        if content:
            if save_abstract_content(content, output_dir):
                return True
        return False
    except Exception as e:
        print(f"Error processing {url}: {e}")
        return False

def main(url_file_path, output_dir, limit=None, max_workers=10):
    """
    Main function to scrape VSS abstracts.
    
    Args:
        url_file_path (str): Path to the file containing URLs
        output_dir (str): Directory to save the scraped content
        limit (int, optional): Limit the number of URLs to scrape
        max_workers (int): Maximum number of concurrent workers
    """
    # Read URLs from file
    urls = read_urls_from_file(url_file_path)
    
    if not urls:
        print(f"No URLs found in {url_file_path}")
        return
    
    # Limit the number of URLs if specified
    if limit and limit > 0:
        urls = urls[:limit]
        print(f"Processing first {limit} URLs out of {len(urls)} total URLs")
    else:
        print(f"Processing all {len(urls)} URLs")
    
    # Create output directory
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Track statistics
    success_count = 0
    failure_count = 0
    
    # Use ThreadPoolExecutor for concurrent processing
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_url = {executor.submit(process_url, url, output_dir): url for url in urls}
        
        # Process results as they complete with progress bar
        for future in tqdm(concurrent.futures.as_completed(future_to_url), total=len(urls), desc="Scraping abstracts"):
            url = future_to_url[future]
            try:
                success = future.result()
                if success:
                    success_count += 1
                else:
                    failure_count += 1
            except Exception as e:
                print(f"Error processing {url}: {e}")
                failure_count += 1
    
    # Print summary
    print(f"\nScraping completed:")
    print(f"- Successfully scraped: {success_count} URLs")
    print(f"- Failed to scrape: {failure_count} URLs")
    print(f"- Results saved to {output_dir}")

if __name__ == "__main__":
    url_file_path = "data/vss_scrape/vss_abstract_urls.txt"
    output_dir = "data/vss_scrape/abstracts_json"
    
    # Process all URLs with concurrent processing
    main(url_file_path, output_dir, max_workers=10) 