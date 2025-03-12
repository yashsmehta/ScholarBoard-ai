#!/usr/bin/env python3
"""
Script to search for VSS abstracts by title.
"""

import asyncio
import re
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, CacheMode
from bs4 import BeautifulSoup

async def search_abstracts(search_term):
    """
    Search for VSS abstracts by title.
    
    Args:
        search_term: Search term to look for in abstract titles
    """
    # URL of the VSS abstract search page
    search_url = "https://www.visionsciences.org/search-abstracts/?id&column=abstract_title&topic1"
    
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
        result = await crawler.arun(url=search_url, config=crawler_config)
        
        if not result.success:
            print(f"Error searching abstracts: {result.error_message}")
            return []
        
        # Parse the HTML content
        soup = BeautifulSoup(result.html, 'html.parser')
        
        # Find all abstract links in the table
        links = []
        for a in soup.find_all('a', href=re.compile(r'presentation/\?id=\d+')):
            title = a.get_text().strip()
            url = a['href']
            
            # Check if the search term is in the title
            if search_term.lower() in title.lower():
                links.append({
                    'title': title,
                    'url': url
                })
        
        return links

async def main():
    """Main entry point."""
    import sys
    
    # Default search term
    search_term = sys.argv[1] if len(sys.argv) > 1 else "Re-evaluating the ability of object trained"
    
    print(f"Searching for abstracts with title containing: {search_term}")
    
    # Search for abstracts
    results = await search_abstracts(search_term)
    
    # Print the results
    if results:
        print(f"\nFound {len(results)} matching abstracts:")
        for i, result in enumerate(results):
            print(f"\n{i+1}. {result['title']}")
            print(f"   URL: {result['url']}")
    else:
        print("\nNo matching abstracts found.")

if __name__ == "__main__":
    asyncio.run(main()) 