#!/usr/bin/env python3
"""
Script to extract authors and their affiliations from Vision Sciences Society (VSS) 
conference abstracts using Crawl4AI.
"""

import os
import re
import asyncio
import csv
import time
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, CacheMode
from bs4 import BeautifulSoup

# ANSI color codes for terminal output
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

# URL of the VSS abstract search page
SEARCH_URL = "https://www.visionsciences.org/search-abstracts/?id&column=abstract_title&topic1"

async def extract_abstract_urls():
    """
    Extract all abstract URLs from the VSS search results page.
    
    Returns:
        List of dictionaries containing abstract URLs and titles
    """
    # Configure the browser
    browser_config = BrowserConfig(
        headless=True,
        java_script_enabled=True
    )
    
    # Configure the crawler
    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS
    )
    
    # Create the crawler
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=SEARCH_URL, config=crawler_config)
        
        if not result.success:
            print(f"{RED}Error extracting abstract URLs: {result.error_message}{RESET}")
            return []
        
        # Parse the HTML content
        soup = BeautifulSoup(result.html, 'html.parser')
        
        # Find all abstract links in the table
        abstracts = []
        for a in soup.find_all('a', href=re.compile(r'presentation/\?id=\d+')):
            title = a.get_text().strip()
            url = a['href']
            
            # Make sure the URL is absolute
            if not url.startswith('http'):
                url = f"https://www.visionsciences.org{url}"
            
            abstracts.append({
                'title': title,
                'url': url
            })
        
        print(f"{GREEN}Found {len(abstracts)} abstracts{RESET}")
        return abstracts

async def extract_author_info(url):
    """
    Extract author information from a VSS abstract page.
    
    Args:
        url: URL of the abstract page
        
    Returns:
        Dictionary containing title, authors, and affiliations
    """
    # Configure the browser
    browser_config = BrowserConfig(
        headless=True,
        java_script_enabled=True
    )
    
    # Configure the crawler
    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS
    )
    
    # Create the crawler
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=url, config=crawler_config)
        
        if not result.success:
            print(f"{RED}Error extracting author info from {url}: {result.error_message}{RESET}")
            return {}
        
        # Parse the HTML content
        soup = BeautifulSoup(result.html, 'html.parser')
        
        # Extract title
        title_elem = soup.select_one('h1.entry-title') or soup.select_one('.presentation-title') or soup.select_one('h2.presentation-title')
        title = title_elem.get_text().strip() if title_elem else "Unknown Title"
        
        # Find all paragraphs
        paragraphs = soup.find_all('p')
        
        # Extract author information
        author_paragraph = None
        
        # Look for the paragraph that contains author information
        # It typically has superscripts and semicolons
        for p in paragraphs:
            text = p.get_text().strip()
            # Check if this contains author information (has superscripts or numbers and semicolons)
            if (re.search(r'[¹²³⁴⁵⁶⁷⁸⁹⁰]|\d+', text) and ';' in text and ',' in text):
                author_paragraph = p
                break
        
        if not author_paragraph:
            return {
                'title': title,
                'authors': [],
                'raw_affiliations': {}
            }
        
        # Get the text content
        content = author_paragraph.get_text().strip()
        
        # Split by semicolon to separate authors from affiliations
        parts = content.split(';')
        
        # First part contains authors
        authors_text = parts[0].strip()
        
        # Remaining parts contain affiliations
        affiliations_text = ';'.join(parts[1:]).strip() if len(parts) > 1 else ""
        
        # Map for superscript conversion
        superscript_map = {
            '¹': '1', '²': '2', '³': '3', '⁴': '4', '⁵': '5',
            '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9', '⁰': '0'
        }
        
        # Process affiliations
        raw_affiliations = {}
        
        if affiliations_text:
            # Normalize superscripts
            normalized_aff_text = affiliations_text
            for unicode_sup, regular_num in superscript_map.items():
                normalized_aff_text = normalized_aff_text.replace(unicode_sup, regular_num)
            
            # Split affiliations by comma if multiple
            aff_items = [a.strip() for a in normalized_aff_text.split(',')]
            
            for aff in aff_items:
                # Match patterns like "1Department of X" or "1 Department of X"
                match = re.match(r'^(\d+)(.*)', aff)
                if match:
                    aff_num = match.group(1)
                    aff_text = match.group(2).strip()
                    raw_affiliations[aff_num] = aff_text
                else:
                    # If no number found, add as a generic affiliation
                    raw_affiliations["0"] = aff
        
        # Process the raw affiliations to create a structured representation
        # This will help us associate departments with universities
        structured_affiliations = {}
        
        # First, extract all universities and institutions
        university_pattern = re.compile(r'university|college|institute|school|center|laboratory|lab\b', re.IGNORECASE)
        universities = {}
        
        for aff_num, aff_text in raw_affiliations.items():
            if university_pattern.search(aff_text):
                universities[aff_num] = aff_text
        
        # Now, create a mapping of department indices to university indices
        # based on the raw text
        dept_to_univ = {}
        
        # Extract department-university pairs from the raw text
        for i, aff_item in enumerate(aff_items):
            if i < len(aff_items) - 1:
                current = aff_item.strip()
                next_item = aff_items[i + 1].strip()
                
                # Check if current is a department and next is a university
                current_match = re.match(r'^(\d+)(.*)', current)
                next_match = re.match(r'^(\d+)(.*)', next_item)
                
                if current_match and next_match:
                    current_idx = current_match.group(1)
                    current_text = current_match.group(2).strip()
                    next_idx = next_match.group(1)
                    next_text = next_match.group(2).strip()
                    
                    # If current is not a university and next is a university
                    if not university_pattern.search(current_text) and university_pattern.search(next_text):
                        dept_to_univ[current_idx] = next_idx
        
        # Process authors
        author_list = [a.strip() for a in authors_text.split(',')]
        
        parsed_authors = []
        for i, author_item in enumerate(author_list):
            # Skip empty authors
            if not author_item:
                continue
                
            # Extract email if present (but we won't use it)
            email_match = re.search(r'\((.*?@.*?)\)', author_item)
            if email_match:
                # Remove email from author name
                author_item = author_item.replace(email_match.group(0), "").strip()
            
            # Extract affiliation numbers
            aff_nums = []
            
            # Check for Unicode superscripts
            for unicode_sup, regular_num in superscript_map.items():
                if unicode_sup in author_item:
                    aff_nums.append(regular_num)
                    author_item = author_item.replace(unicode_sup, '')
            
            # Also check for regular numbers
            regular_nums = re.findall(r'(\d+)', author_item)
            aff_nums.extend(regular_nums)
            
            # Clean up the author name
            author_name = re.sub(r'[¹²³⁴⁵⁶⁷⁸⁹⁰\d]', '', author_item).strip()
            
            # Skip if no name (just a number)
            if not author_name:
                continue
            
            # Determine author position
            if i == 0:
                position = "first author"
            elif i == len(author_list) - 1:
                position = "last author"
            else:
                position = "middle author"
            
            # Create a structured representation of the author's affiliations
            structured_affs = []
            
            for aff_num in aff_nums:
                if aff_num in raw_affiliations:
                    aff_text = raw_affiliations[aff_num]
                    
                    # Check if this is a department with an associated university
                    if aff_num in dept_to_univ and dept_to_univ[aff_num] in raw_affiliations:
                        univ_text = raw_affiliations[dept_to_univ[aff_num]]
                        structured_affs.append(f"{aff_text}, {univ_text}")
                    else:
                        # Check if this is a department (not a university)
                        dept_pattern = re.compile(r'department|dept', re.IGNORECASE)
                        if dept_pattern.search(aff_text) and not university_pattern.search(aff_text):
                            # Look for a university in the author's affiliations
                            for uni_num in aff_nums:
                                if uni_num in universities:
                                    structured_affs.append(f"{aff_text}, {universities[uni_num]}")
                                    break
                            else:
                                # No university found, use as is
                                structured_affs.append(aff_text)
                        else:
                            # This is a university or other institution, add it as is
                            structured_affs.append(aff_text)
            
            # If we couldn't find any structured affiliations, use the raw ones
            if not structured_affs:
                for aff_num in aff_nums:
                    if aff_num in raw_affiliations:
                        structured_affs.append(raw_affiliations[aff_num])
            
            # If still no affiliations, check if there's a generic one
            if not structured_affs and "0" in raw_affiliations:
                structured_affs.append(raw_affiliations["0"])
            
            # Try to extract institution from department if no clear institution
            if structured_affs:
                improved_affs = []
                for aff in structured_affs:
                    # If this looks like just a department without institution
                    dept_pattern = re.compile(r'department|dept', re.IGNORECASE)
                    if dept_pattern.search(aff) and not university_pattern.search(aff):
                        # Look through all universities in the raw affiliations
                        for uni_aff in universities.values():
                            improved_affs.append(f"{aff}, {uni_aff}")
                            break
                        else:
                            improved_affs.append(aff)
                    else:
                        improved_affs.append(aff)
                
                if improved_affs:
                    structured_affs = improved_affs
            
            parsed_authors.append({
                'name': author_name,
                'affiliations': structured_affs,
                'position': position
            })
        
        return {
            'title': title,
            'authors': parsed_authors,
            'raw_affiliations': raw_affiliations
        }

async def process_abstracts(abstracts, batch_size=5, max_abstracts=None):
    """
    Process a list of abstracts to extract author information.
    
    Args:
        abstracts: List of dictionaries containing abstract URLs and titles
        batch_size: Number of abstracts to process in parallel
        max_abstracts: Maximum number of abstracts to process (None for all)
        
    Returns:
        List of dictionaries containing author information
    """
    # Limit the number of abstracts if specified
    if max_abstracts is not None:
        abstracts = abstracts[:max_abstracts]
    
    # Create a list to store all author information
    all_authors = []
    
    # Create output file and write header
    output_file = "data/vss_all_authors.csv"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Check if file exists and has content
    file_exists = os.path.exists(output_file) and os.path.getsize(output_file) > 0
    
    # Open file in append mode if it exists, otherwise write mode with header
    file_mode = "a" if file_exists else "w"
    
    with open(output_file, file_mode, newline='', encoding="utf-8") as f:
        fieldnames = ['name', 'affiliations', 'position', 'abstract_title', 'abstract_url']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        # Write header only if creating a new file
        if not file_exists:
            writer.writeheader()
    
    # Process abstracts in batches
    total_batches = (len(abstracts) + batch_size - 1) // batch_size
    start_time = time.time()
    
    print(f"{BOLD}Starting extraction of {len(abstracts)} abstracts in {total_batches} batches{RESET}")
    print(f"{YELLOW}Progress: [{'.' * total_batches}]{RESET}")
    
    for i in range(0, len(abstracts), batch_size):
        batch_num = i // batch_size + 1
        batch = abstracts[i:i+batch_size]
        
        # Calculate and display progress
        elapsed = time.time() - start_time
        if batch_num > 1:
            estimated_total = elapsed / (batch_num - 1) * total_batches
            remaining = estimated_total - elapsed
            eta_str = f", ETA: {int(remaining // 60)}m {int(remaining % 60)}s"
        else:
            eta_str = ""
            
        progress_bar = "=" * (batch_num - 1) + ">" + "." * (total_batches - batch_num)
        print(f"\r{BLUE}Batch {batch_num}/{total_batches}{RESET} [{progress_bar}]{YELLOW}{eta_str}{RESET}", end="", flush=True)
        
        # Process batch in parallel
        tasks = [extract_author_info(abstract['url']) for abstract in batch]
        batch_results = await asyncio.gather(*tasks)
        
        # Process the results
        batch_authors = []
        for j, result in enumerate(batch_results):
            abstract = batch[j]
            
            # Skip abstracts with no authors
            if not result or not result.get('authors'):
                continue
            
            # Add the abstract title and URL to each author
            for author in result.get('authors', []):
                author_info = {
                    'name': author['name'],
                    'affiliations': ' AND '.join(author['affiliations']),
                    'position': author['position'],
                    'abstract_title': result.get('title', abstract['title']),
                    'abstract_url': abstract['url']
                }
                batch_authors.append(author_info)
                all_authors.append(author_info)
        
        # Save batch results to CSV
        if batch_authors:
            with open(output_file, "a", newline='', encoding="utf-8") as f:
                fieldnames = ['name', 'affiliations', 'position', 'abstract_title', 'abstract_url']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                for author in batch_authors:
                    writer.writerow(author)
            
            print(f"\r{GREEN}Batch {batch_num}/{total_batches} completed with {len(batch_authors)} authors saved{RESET}      ")
    
    # Print final progress
    print(f"\n{GREEN}All batches completed! Total processing time: {int((time.time() - start_time) // 60)}m {int((time.time() - start_time) % 60)}s{RESET}")
    
    return all_authors

async def main():
    """Main entry point."""
    import sys
    
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    # Check if we should process a single URL or all abstracts
    if len(sys.argv) > 1:
        # Process a single URL
        url = sys.argv[1]
        print(f"{BOLD}Extracting author information from: {url}{RESET}")
        
        result = await extract_author_info(url)
        
        # Print the results
        print(f"\n{BOLD}Title:{RESET} {result.get('title', 'Unknown')}")
        
        print(f"\n{BOLD}Authors:{RESET}")
        all_authors = []
        for author in result.get('authors', []):
            print(f"  - {BOLD}{author['name']}{RESET} ({BLUE}{author['position']}{RESET})")
            print(f"    {YELLOW}Affiliations:{RESET} {' AND '.join(author['affiliations'])}")
            
            author_info = {
                'name': author['name'],
                'affiliations': ' AND '.join(author['affiliations']),
                'position': author['position'],
                'abstract_title': result.get('title', 'Unknown'),
                'abstract_url': url
            }
            all_authors.append(author_info)
        
        # Save the results to a CSV file
        output_file = "data/vss_author_extraction.csv"
        with open(output_file, "w", newline='', encoding="utf-8") as f:
            fieldnames = ['name', 'affiliations', 'position', 'abstract_title', 'abstract_url']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for author in all_authors:
                writer.writerow(author)
        
        print(f"\n{GREEN}Results saved to {output_file}{RESET}")
    else:
        # Process all abstracts
        print(f"{BOLD}Extracting abstracts from search page...{RESET}")
        abstracts = await extract_abstract_urls()
        
        if not abstracts:
            print(f"{RED}No abstracts found.{RESET}")
            return
        
        print(f"{BOLD}Processing {len(abstracts)} abstracts...{RESET}")
        all_authors = await process_abstracts(abstracts)
        
        print(f"\n{GREEN}Extracted {len(all_authors)} authors from {len(abstracts)} abstracts{RESET}")
        print(f"{GREEN}Results saved to data/vss_all_authors.csv{RESET}")

if __name__ == "__main__":
    print(f"{BOLD}{GREEN}Starting VSS author extraction with Crawl4AI...{RESET}")
    asyncio.run(main())
    print(f"{BOLD}{GREEN}Extraction completed!{RESET}") 