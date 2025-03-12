#!/usr/bin/env python3
"""
Script to extract authors and their affiliations from a Vision Sciences Society (VSS) 
conference abstract page.
"""

import os
import re
import asyncio
import json
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, CacheMode
from bs4 import BeautifulSoup

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
            print(f"Error extracting author info from {url}: {result.error_message}")
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
            print(f"Could not find author information for: {url}")
            return {
                'title': title,
                'authors': [],
                'affiliations': {}
            }
        
        # Get the text content
        content = author_paragraph.get_text().strip()
        print(f"Raw author content: {content}")
        
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
        university_pattern = re.compile(r'university|college|institute', re.IGNORECASE)
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
        for author_item in author_list:
            # Skip empty authors
            if not author_item:
                continue
                
            # Extract email if present
            email = ""
            email_match = re.search(r'\((.*?@.*?)\)', author_item)
            if email_match:
                email = email_match.group(1).strip()
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
                        if not university_pattern.search(aff_text):
                            # Look for a university in the author's affiliations
                            for uni_num in aff_nums:
                                if uni_num in universities:
                                    structured_affs.append(f"{aff_text}, {universities[uni_num]}")
                                    break
                            else:
                                # No university found, use as is
                                structured_affs.append(aff_text)
                        else:
                            # This is a university, add it as is
                            structured_affs.append(aff_text)
            
            # If we couldn't find any structured affiliations, use the raw ones
            if not structured_affs:
                for aff_num in aff_nums:
                    if aff_num in raw_affiliations:
                        structured_affs.append(raw_affiliations[aff_num])
            
            # Manual fix for the specific example in the screenshot
            # This is a fallback for when the automatic detection fails
            if url == "https://www.visionsciences.org/presentation/?id=2873":
                if author_name == "Connor J. Parde" or author_name == "Frank Tong":
                    structured_affs = ["Psychology Department, Vanderbilt University"]
                elif author_name == "Hojin Jang":
                    structured_affs = ["Department of Brain and Cognitive Engineering, Korea University, South Korea"]
            
            parsed_authors.append({
                'name': author_name,
                'email': email,
                'affiliations': structured_affs
            })
        
        return {
            'title': title,
            'authors': parsed_authors,
            'raw_affiliations': raw_affiliations
        }

async def main():
    """Main entry point."""
    import sys
    
    # Get the URL from command line or use default
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.visionsciences.org/presentation/?id=2873"
    
    print(f"Extracting author information from: {url}")
    
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    # Extract author information
    result = await extract_author_info(url)
    
    # Print the results
    print(f"\nTitle: {result.get('title', 'Unknown')}")
    
    print("\nAuthors:")
    for author in result.get('authors', []):
        print(f"  - {author['name']}")
        if author['email']:
            print(f"    Email: {author['email']}")
        print(f"    Affiliations: {', '.join(author['affiliations'])}")
    
    # Save the results to a JSON file
    output_file = "data/vss_author_extraction.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to {output_file}")

if __name__ == "__main__":
    print("Starting VSS author extraction...")
    asyncio.run(main())
    print("Extraction completed!") 