#!/usr/bin/env python3
"""
Download profile pictures for scholars using Playwright for browser automation.
This script uses Google Scholar and university websites to find accurate profile pictures.
Optimized for small, compressed images with high success rate.
"""
import os
import csv
import time
import re
import json
import random
import argparse
from pathlib import Path
import asyncio
from urllib.parse import quote_plus, urlparse
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import io
import base64

# Try to import PIL for image validation and resizing
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# Configuration
MAX_RETRIES = 5
DELAY_BETWEEN_SEARCHES = (1, 3)  # Reduced delay range in seconds
PAGE_LOAD_TIMEOUT = 20000  # 20 seconds for page loading
NETWORK_IDLE_TIMEOUT = 8000  # 8 seconds for network idle
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
]

# Image settings
TARGET_SIZE = (150, 150)  # Small target size for profile pics
JPEG_QUALITY = 60  # Lower quality for smaller file size
MAX_FILE_SIZE = 50 * 1024  # 50KB max file size

# ANSI color codes for terminal output
COLORS = {
    'RESET': '\033[0m',
    'BOLD': '\033[1m',
    'RED': '\033[91m',
    'GREEN': '\033[92m',
    'YELLOW': '\033[93m',
    'BLUE': '\033[94m',
    'MAGENTA': '\033[95m',
    'CYAN': '\033[96m',
    'WHITE': '\033[97m',
    'BG_GREEN': '\033[42m',
    'BG_YELLOW': '\033[43m',
    'BG_BLUE': '\033[44m',
}

# Create a logger to track progress
def setup_logger():
    import logging
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "profile_pics_download.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("profile_downloader")

logger = setup_logger()

def print_colored(message, color=None, bold=False, end='\n'):
    """Print colored text to the terminal"""
    color_code = COLORS.get(color, '')
    bold_code = COLORS['BOLD'] if bold else ''
    reset_code = COLORS['RESET']
    
    print(f"{color_code}{bold_code}{message}{reset_code}", end=end)

def print_progress_bar(iteration, total, prefix='', suffix='', length=50, fill='█'):
    """Print a progress bar to the terminal"""
    percent = f"{100 * (iteration / float(total)):.1f}"
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '░' * (length - filled_length)
    
    print_colored(f"\r{prefix} |{bar}| {percent}% {suffix}", end='\r')
    
    # Print a newline when complete
    if iteration == total:
        print()

def print_header(message):
    """Print a header message"""
    width = len(message) + 4
    print_colored("┌" + "─" * width + "┐", color='CYAN', bold=True)
    print_colored("│  " + message + "  │", color='CYAN', bold=True)
    print_colored("└" + "─" * width + "┘", color='CYAN', bold=True)

def print_summary(stats):
    """Print a summary of the download results"""
    print_colored("\n" + "=" * 50, color='BLUE', bold=True)
    print_colored(" DOWNLOAD SUMMARY ", color='BLUE', bold=True)
    print_colored("=" * 50, color='BLUE', bold=True)
    print_colored(f"✅ Successfully downloaded: {stats['successful']}/{stats['total']} ({stats['successful']/stats['total']*100:.1f}%)", color='GREEN')
    print_colored(f"❌ Failed: {stats['failed']}/{stats['total']} ({stats['failed']/stats['total']*100:.1f}%)", color='RED')
    print_colored(f"⏭️  Skipped (already existed): {stats['skipped']}/{stats['total']} ({stats['skipped']/stats['total']*100:.1f}%)", color='YELLOW')
    print_colored(f"📁 Images saved to: {stats['output_dir']}", color='CYAN')
    print_colored(f"📊 Average file size: {stats.get('avg_size', 0):.1f}KB", color='CYAN')
    print_colored("=" * 50, color='BLUE', bold=True)

async def get_google_scholar_image(page, name, institution):
    """Try to find the scholar's image on Google Scholar"""
    try:
        # Construct the search query
        query = f"{name} {institution}"
        encoded_query = quote_plus(query)
        url = f"https://scholar.google.com/scholar?q={encoded_query}"
        
        # Navigate to Google Scholar
        await page.goto(url, wait_until="domcontentloaded", timeout=PAGE_LOAD_TIMEOUT)
        await page.wait_for_load_state("networkidle", timeout=NETWORK_IDLE_TIMEOUT)
        
        # Look for profile links
        profile_links = await page.query_selector_all('a[href*="user="]')
        
        if not profile_links:
            return None
            
        # Click on the first profile link
        await profile_links[0].click()
        await page.wait_for_load_state("networkidle", timeout=NETWORK_IDLE_TIMEOUT)
        
        # Check if there's a profile image
        img = await page.query_selector('img#gsc_prf_pup-img')
        if img:
            src = await img.get_attribute('src')
            
            # Skip default avatars
            default_avatars = ['avatar_scholar', 'avatar_scholar_56', 'avatar_scholar_128']
            if src and not any(default in src for default in default_avatars):
                # Convert relative URLs to absolute
                if src.startswith('/'):
                    src = f"https://scholar.google.com{src}"
                return src
                
        return None
    except Exception as e:
        logger.warning(f"Error in Google Scholar search for {name}: {e}")
        return None

async def extract_image_from_page(page, name):
    """Extract image directly from the current page with improved detection"""
    try:
        # Split name into parts for better matching
        name_parts = name.lower().split()
        first_name = name_parts[0] if name_parts else ""
        last_name = name_parts[-1] if name_parts else ""
        
        # Try to find images that might be profile pictures
        selectors = [
            # Name-based selectors
            f'img[alt*="{name.lower()}"]',  # Full name
            f'img[alt*="{first_name}"]',  # First name
            f'img[alt*="{last_name}"]',  # Last name
            f'img[src*="{last_name.lower()}"]',  # Last name in URL
            
            # Common profile image selectors
            'img[src*="profile"]', 
            'img[src*="faculty"]',
            'img[src*="staff"]',
            'img[src*="people"]',
            'img[src*="portrait"]',
            'img[src*="headshot"]',
            'img[src*="photo"]',
            'img[src*="avatar"]',
            'img[alt*="profile"]',
            'img[alt*="photo"]',
            'img[alt*="portrait"]',
            'img[alt*="headshot"]',
            'img[alt*="faculty"]',
            
            # Common size and class selectors
            'img[width="150"][height="150"]',
            'img[width="200"][height="200"]',
            'img[width="100"][height="100"]',
            'img[class*="profile"]',
            'img[class*="avatar"]',
            'img[class*="photo"]',
            'img[class*="portrait"]',
            'img[class*="faculty"]',
            'img[class*="headshot"]',
            
            # Common container selectors
            '.profile-pic img',
            '.avatar img',
            '.faculty-photo img',
            '.profile-image img',
            '.profile img',
            '.photo img',
            '.portrait img',
            '.headshot img',
            '.faculty-profile img',
            '.researcher-photo img'
        ]
        
        # First try specific selectors
        for selector in selectors:
            try:
                images = await page.query_selector_all(selector)
                if images:
                    for img in images:
                        src = await img.get_attribute('src')
                        if src and not src.endswith(('.svg', '.gif', '.ico')):
                            # Skip very small images and icons
                            width = await img.get_attribute('width')
                            height = await img.get_attribute('height')
                            
                            # Skip tiny images that are likely icons
                            if width and height and (int(width) < 40 or int(height) < 40):
                                continue
                                
                            # Handle data URLs
                            if src.startswith('data:image'):
                                return src
                            
                            # Convert relative URLs to absolute
                            if src.startswith('/'):
                                page_url = page.url
                                base_url = '/'.join(page_url.split('/')[:3])  # http(s)://domain.com
                                src = base_url + src
                            return src
            except Exception:
                continue
        
        # If no specific matches, get all images of reasonable size
        all_images = await page.query_selector_all('img')
        for img in all_images:
            try:
                # Check alt text for name matches
                alt = await img.get_attribute('alt')
                if alt:
                    alt_lower = alt.lower()
                    if (first_name in alt_lower or last_name in alt_lower or 
                        "profile" in alt_lower or "portrait" in alt_lower or 
                        "headshot" in alt_lower or "faculty" in alt_lower):
                        src = await img.get_attribute('src')
                        if src and not src.endswith(('.svg', '.gif', '.ico')):
                            # Convert relative URLs to absolute
                            if src.startswith('/'):
                                page_url = page.url
                                base_url = '/'.join(page_url.split('/')[:3])
                                src = base_url + src
                            return src
                
                # Check if image is of reasonable size for a profile pic
                width = await img.get_attribute('width')
                height = await img.get_attribute('height')
                
                if width and height:
                    try:
                        w, h = int(width), int(height)
                        # Look for square-ish images of reasonable size
                        if 50 <= w <= 400 and 50 <= h <= 400 and 0.7 <= w/h <= 1.3:
                            src = await img.get_attribute('src')
                            if src and not src.endswith(('.svg', '.gif', '.ico')):
                                # Convert relative URLs to absolute
                                if src.startswith('/'):
                                    page_url = page.url
                                    base_url = '/'.join(page_url.split('/')[:3])
                                    src = base_url + src
                                return src
                    except ValueError:
                        continue
            except Exception:
                continue
        
        return None
    except Exception as e:
        logger.warning(f"Error extracting image from page: {e}")
        return None

async def get_university_website_image(page, context, name, institution):
    """Try to find the scholar's image on their university website with improved search"""
    try:
        # Try multiple search queries
        search_queries = [
            f"{name} {institution} faculty profile",
            f"{name} {institution} faculty directory",
            f"{name} {institution} department",
            f"{name} {institution} research",
            f"{name} {institution} lab group",
            f"professor {name} {institution}"
        ]
        
        for query in search_queries:
            encoded_query = quote_plus(query)
            url = f"https://www.google.com/search?q={encoded_query}"
            
            # Navigate to Google search
            await page.goto(url, wait_until="domcontentloaded", timeout=PAGE_LOAD_TIMEOUT)
            await page.wait_for_load_state("networkidle", timeout=NETWORK_IDLE_TIMEOUT)
            
            # Try to extract thumbnail images directly from Google search results
            thumbnail = await extract_image_from_page(page, name)
            if thumbnail:
                return thumbnail
                
            # Click on multiple results that look like university websites
            university_domains = [".edu", "university", "college", "faculty", "staff", "people", "research", "department"]
            links = await page.query_selector_all('a[href^="http"]')
            
            # Try up to 3 links per search query
            checked_links = 0
            for link in links:
                href = await link.get_attribute('href')
                if any(domain in href.lower() for domain in university_domains):
                    try:
                        # Open in a new tab to avoid losing search results
                        page_university = await context.new_page()
                        await page_university.goto(href, wait_until="domcontentloaded", timeout=PAGE_LOAD_TIMEOUT)
                        await page_university.wait_for_load_state("networkidle", timeout=NETWORK_IDLE_TIMEOUT)
                        
                        # Extract image from the university page
                        uni_image = await extract_image_from_page(page_university, name)
                        await page_university.close()
                        
                        if uni_image:
                            return uni_image
                    except Exception as e:
                        logger.warning(f"Error checking university link {href}: {e}")
                        try:
                            await page_university.close()
                        except:
                            pass
                    
                    checked_links += 1
                    if checked_links >= 3:
                        break
        
        return None
    except Exception as e:
        logger.warning(f"Error in university website search for {name}: {e}")
        return None

async def get_google_images_search(page, name, institution):
    """Search for scholar images using Google Images with multiple queries"""
    try:
        # Try multiple search queries with different keywords
        search_queries = [
            f"{name} {institution} professor",
            f"{name} {institution} faculty",
            f"{name} {institution} academic",
            f"{name} {institution} researcher",
            f"{name} professor headshot",
        ]
        
        for query in search_queries:
            encoded_query = quote_plus(query)
            url = f"https://www.google.com/search?q={encoded_query}&tbm=isch"
            
            # Navigate to Google Images
            await page.goto(url, wait_until="domcontentloaded", timeout=PAGE_LOAD_TIMEOUT)
            await page.wait_for_load_state("networkidle", timeout=NETWORK_IDLE_TIMEOUT)
            
            # Get all image elements - DIRECTLY USE THUMBNAILS instead of clicking for full size
            images = await page.query_selector_all('img.rg_i')
            
            if not images:
                continue
                
            # Get the src of more thumbnails
            for img in images[:15]:  # Check more images
                src = await img.get_attribute('src')
                if src and src.startswith('data:image'):
                    # Use the data URL directly
                    return src
                elif src and src.startswith('http'):
                    return src
            
            # If we've checked all images and none worked, try the next query
                
        return None
    except Exception as e:
        logger.warning(f"Error in Google Images search for {name}: {e}")
        return None

async def get_professional_site_image(page, context, name, institution):
    """Search for scholar images on professional sites like LinkedIn, ResearchGate, etc."""
    try:
        # Try multiple professional sites
        search_queries = [
            f"{name} {institution} linkedin",
            f"{name} {institution} researchgate",
            f"{name} {institution} academia.edu",
            f"{name} {institution} orcid",
            f"{name} {institution} google scholar"
        ]
        
        for query in search_queries:
            encoded_query = quote_plus(query)
            url = f"https://www.google.com/search?q={encoded_query}"
            
            # Navigate to Google search
            await page.goto(url, wait_until="domcontentloaded", timeout=PAGE_LOAD_TIMEOUT)
            await page.wait_for_load_state("networkidle", timeout=NETWORK_IDLE_TIMEOUT)
            
            # Try to extract thumbnail images directly from Google search results
            thumbnail = await extract_image_from_page(page, name)
            if thumbnail:
                return thumbnail
                
            # Look for professional site links
            professional_domains = ["linkedin.com", "researchgate.net", "academia.edu", "orcid.org", "scholar.google.com"]
            links = await page.query_selector_all('a[href^="http"]')
            
            for link in links:
                href = await link.get_attribute('href')
                if any(domain in href.lower() for domain in professional_domains):
                    try:
                        # Open in a new tab
                        page_prof = await context.new_page()
                        await page_prof.goto(href, wait_until="domcontentloaded", timeout=PAGE_LOAD_TIMEOUT)
                        await page_prof.wait_for_load_state("networkidle", timeout=NETWORK_IDLE_TIMEOUT)
                        
                        # Extract image from the professional site
                        prof_image = await extract_image_from_page(page_prof, name)
                        await page_prof.close()
                        
                        if prof_image:
                            return prof_image
                    except Exception as e:
                        logger.warning(f"Error checking professional site link {href}: {e}")
                        try:
                            await page_prof.close()
                        except:
                            pass
                    
                    # Only check one link per professional site type
                    break
        
        return None
    except Exception as e:
        logger.warning(f"Error in professional site search for {name}: {e}")
        return None

async def get_department_page_image(page, context, name, institution):
    """Try to find the scholar's image by directly searching for department pages"""
    try:
        # Try to guess department from name and institution
        departments = ["computer science", "physics", "chemistry", "biology", 
                      "mathematics", "economics", "engineering", "psychology",
                      "sociology", "history", "philosophy", "political science",
                      "medicine", "law", "business", "education"]
        
        for department in departments:
            # Construct direct department URL queries
            search_queries = [
                f"{institution} {department} faculty directory",
                f"{institution} {department} faculty",
                f"{institution} {department} people"
            ]
            
            for query in search_queries:
                encoded_query = quote_plus(query)
                url = f"https://www.google.com/search?q={encoded_query}"
                
                # Navigate to Google search
                await page.goto(url, wait_until="domcontentloaded", timeout=PAGE_LOAD_TIMEOUT)
                await page.wait_for_load_state("networkidle", timeout=NETWORK_IDLE_TIMEOUT)
                
                # Look for department directory links
                links = await page.query_selector_all('a[href^="http"]')
                
                for link in links:
                    href = await link.get_attribute('href')
                    # Look for directory-like URLs
                    if any(term in href.lower() for term in ["faculty", "directory", "people", "staff"]):
                        try:
                            # Open in a new tab
                            page_dept = await context.new_page()
                            await page_dept.goto(href, wait_until="domcontentloaded", timeout=PAGE_LOAD_TIMEOUT)
                            await page_dept.wait_for_load_state("networkidle", timeout=NETWORK_IDLE_TIMEOUT)
                            
                            # Try to find the scholar's name on the page
                            content = await page_dept.content()
                            if name.lower() in content.lower():
                                # If found, look for images
                                dept_image = await extract_image_from_page(page_dept, name)
                                if dept_image:
                                    await page_dept.close()
                                    return dept_image
                            
                            # If not found in the main page, try to find a link to the scholar's profile
                            name_parts = name.lower().split()
                            first_name = name_parts[0] if name_parts else ""
                            last_name = name_parts[-1] if name_parts else ""
                            
                            # Look for links containing the scholar's name
                            scholar_links = await page_dept.query_selector_all(f'a:text-matches("{last_name}", "i")')
                            
                            for scholar_link in scholar_links:
                                try:
                                    link_text = await page_dept.evaluate('(element) => element.textContent', scholar_link)
                                    if first_name.lower() in link_text.lower() or last_name.lower() in link_text.lower():
                                        # Click on the scholar's profile link
                                        href = await scholar_link.get_attribute('href')
                                        if href:
                                            if href.startswith('/'):
                                                page_url = page_dept.url
                                                base_url = '/'.join(page_url.split('/')[:3])
                                                href = base_url + href
                                                
                                            # Navigate to the scholar's profile
                                            await page_dept.goto(href, wait_until="domcontentloaded", timeout=PAGE_LOAD_TIMEOUT)
                                            await page_dept.wait_for_load_state("networkidle", timeout=NETWORK_IDLE_TIMEOUT)
                                            
                                            # Look for images on the profile page
                                            profile_image = await extract_image_from_page(page_dept, name)
                                            if profile_image:
                                                await page_dept.close()
                                                return profile_image
                                except Exception as e:
                                    logger.warning(f"Error checking scholar link: {e}")
                            
                            await page_dept.close()
                        except Exception as e:
                            logger.warning(f"Error checking department page {href}: {e}")
                            try:
                                await page_dept.close()
                            except:
                                pass
        
        return None
    except Exception as e:
        logger.warning(f"Error in department page search for {name}: {e}")
        return None

async def get_direct_image_search(page, name, institution):
    """Direct search for scholar images using specific photo-related keywords"""
    try:
        # Try multiple direct photo search queries
        search_queries = [
            f"{name} {institution} photo",
            f"{name} {institution} portrait",
            f"{name} {institution} headshot",
            f"{name} {institution} picture",
            f"{name} photo professor",
            f"Dr. {name} photo",
            f"Professor {name} photo"
        ]
        
        for query in search_queries:
            encoded_query = quote_plus(query)
            url = f"https://www.google.com/search?q={encoded_query}&tbm=isch"
            
            # Navigate to Google Images
            await page.goto(url, wait_until="domcontentloaded", timeout=PAGE_LOAD_TIMEOUT)
            await page.wait_for_load_state("networkidle", timeout=NETWORK_IDLE_TIMEOUT)
            
            # Get all image elements
            images = await page.query_selector_all('img.rg_i')
            
            if not images:
                continue
                
            # Check more images (up to 20)
            for img in images[:20]:
                src = await img.get_attribute('src')
                if src and src.startswith('data:image'):
                    # Use the data URL directly
                    return src
                elif src and src.startswith('http'):
                    return src
            
            # If we've checked all images and none worked, try the next query
                
        return None
    except Exception as e:
        logger.warning(f"Error in direct image search for {name}: {e}")
        return None

async def get_conference_image(page, context, name, institution):
    """Search for scholar images on academic conference websites where they might have presented"""
    try:
        # Try multiple conference-related search queries
        search_queries = [
            f"{name} {institution} conference speaker",
            f"{name} {institution} keynote speaker",
            f"{name} {institution} conference presentation",
            f"{name} {institution} symposium",
            f"{name} {institution} workshop presenter",
            f"{name} {institution} panel"
        ]
        
        for query in search_queries:
            encoded_query = quote_plus(query)
            url = f"https://www.google.com/search?q={encoded_query}"
            
            # Navigate to Google search
            await page.goto(url, wait_until="domcontentloaded", timeout=PAGE_LOAD_TIMEOUT)
            await page.wait_for_load_state("networkidle", timeout=NETWORK_IDLE_TIMEOUT)
            
            # Try to extract thumbnail images directly from Google search results
            thumbnail = await extract_image_from_page(page, name)
            if thumbnail:
                return thumbnail
                
            # Look for conference website links
            conference_keywords = ["conference", "symposium", "workshop", "congress", "meeting", "event", "speaker"]
            links = await page.query_selector_all('a[href^="http"]')
            
            for link in links:
                href = await link.get_attribute('href')
                if any(keyword in href.lower() for keyword in conference_keywords):
                    try:
                        # Open in a new tab
                        page_conf = await context.new_page()
                        await page_conf.goto(href, wait_until="domcontentloaded", timeout=PAGE_LOAD_TIMEOUT)
                        await page_conf.wait_for_load_state("networkidle", timeout=NETWORK_IDLE_TIMEOUT)
                        
                        # Check if the scholar's name is on the page
                        content = await page_conf.content()
                        if name.lower() in content.lower():
                            # If found, look for images
                            conf_image = await extract_image_from_page(page_conf, name)
                            if conf_image:
                                await page_conf.close()
                                return conf_image
                                
                            # Try to find a link to the speaker's profile or bio
                            name_parts = name.lower().split()
                            last_name = name_parts[-1] if name_parts else ""
                            
                            # Look for links containing the scholar's name or "speaker" keywords
                            speaker_links = await page_conf.query_selector_all(f'a:text-matches("({last_name}|speaker|speakers|presenter|presenters|bio|profile)", "i")')
                            
                            for speaker_link in speaker_links:
                                try:
                                    link_text = await page_conf.evaluate('(element) => element.textContent', speaker_link)
                                    if name.lower() in link_text.lower() or "speaker" in link_text.lower() or "presenter" in link_text.lower():
                                        # Click on the speaker's profile link
                                        href = await speaker_link.get_attribute('href')
                                        if href:
                                            if href.startswith('/'):
                                                page_url = page_conf.url
                                                base_url = '/'.join(page_url.split('/')[:3])
                                                href = base_url + href
                                                
                                            # Navigate to the speaker's profile
                                            await page_conf.goto(href, wait_until="domcontentloaded", timeout=PAGE_LOAD_TIMEOUT)
                                            await page_conf.wait_for_load_state("networkidle", timeout=NETWORK_IDLE_TIMEOUT)
                                            
                                            # Look for images on the profile page
                                            profile_image = await extract_image_from_page(page_conf, name)
                                            if profile_image:
                                                await page_conf.close()
                                                return profile_image
                                except Exception as e:
                                    logger.warning(f"Error checking speaker link: {e}")
                        
                        await page_conf.close()
                    except Exception as e:
                        logger.warning(f"Error checking conference page {href}: {e}")
                        try:
                            await page_conf.close()
                        except:
                            pass
        
        return None
    except Exception as e:
        logger.warning(f"Error in conference website search for {name}: {e}")
        return None

def process_image(image_data, output_path):
    """
    Process an image to make it small and compressed
    
    Args:
        image_data: Either a URL or a data URL
        output_path: Path to save the processed image
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not HAS_PIL:
        logger.warning("PIL not available, skipping image processing")
        return False
        
    try:
        img_data = None
        
        # Handle data URLs
        if image_data.startswith('data:image'):
            # Extract the base64 data
            header, encoded = image_data.split(",", 1)
            img_data = base64.b64decode(encoded)
        else:
            # Download from URL
            headers = {
                "User-Agent": random.choice(USER_AGENTS),
                "Accept": "image/webp,image/*,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Referer": "https://www.google.com/"
            }
            
            response = requests.get(image_data, headers=headers, timeout=10)
            if response.status_code != 200:
                logger.warning(f"Failed to download image: HTTP {response.status_code}")
                return False
                
            img_data = response.content
        
        # Open the image
        img = Image.open(io.BytesIO(img_data))
        
        # Convert to RGB if needed
        if img.mode not in ('RGB', 'RGBA'):
            img = img.convert('RGB')
        
        # Resize the image while maintaining aspect ratio
        img.thumbnail(TARGET_SIZE, Image.LANCZOS)
        
        # Save as compressed JPEG
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='JPEG', quality=JPEG_QUALITY, optimize=True)
        
        # Check if the size is acceptable
        img_size = img_buffer.tell()
        if img_size > MAX_FILE_SIZE:
            # If still too large, reduce quality further
            for quality in [50, 40, 30, 20]:
                img_buffer = io.BytesIO()
                img.save(img_buffer, format='JPEG', quality=quality, optimize=True)
                if img_buffer.tell() <= MAX_FILE_SIZE:
                    break
        
        # Save the final image
        with open(output_path, 'wb') as f:
            f.write(img_buffer.getvalue())
            
        return True
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        return False

async def process_scholar(page, context, scholar, output_dir, stats):
    """Process a single scholar to find and download their profile picture"""
    name = scholar.get("scholar_name", "").strip()
    institution = scholar.get("institution", "").strip()
    scholar_id = scholar.get("scholar_id", "").strip()
    
    if not name or not institution:
        logger.warning(f"Skipping scholar: Missing name or institution")
        stats['failed'] += 1
        return
    
    # Create a safe filename using scholar_id if available, otherwise use name
    if scholar_id:
        filename = f"{scholar_id}.jpg"
    else:
        safe_name = re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '_')
        filename = f"{safe_name}.jpg"
    
    output_path = output_dir / filename
    
    # Skip if already downloaded
    if output_path.exists():
        print_colored(f"⏭️  Skipping {name}: Image already exists", color='YELLOW')
        logger.info(f"Skipping {name}: Image already exists at {output_path}")
        stats['skipped'] += 1
        return
    
    print_colored(f"🔍 Processing: ", color='CYAN', end='')
    print_colored(f"{name}", color='WHITE', bold=True, end='')
    print_colored(f" from ", color='CYAN', end='')
    print_colored(f"{institution}", color='WHITE', bold=True)
    
    logger.info(f"Processing {name} from {institution}")
    
    # Try different methods to find an image
    image_url = None
    
    # Method 1: Google Scholar (usually has good thumbnails)
    if not image_url:
        print_colored("  ↪ Trying Google Scholar...", color='BLUE', end='')
        logger.info(f"Trying Google Scholar for {name}")
        image_url = await get_google_scholar_image(page, name, institution)
        if image_url:
            print_colored(" ✅ Found!", color='GREEN')
            logger.info(f"Found image on Google Scholar for {name}")
        else:
            print_colored(" ❌ Not found", color='RED')
    
    # Method 2: Direct image search (specific photo keywords)
    if not image_url:
        print_colored("  ↪ Trying direct photo search...", color='BLUE', end='')
        logger.info(f"Trying direct photo search for {name}")
        image_url = await get_direct_image_search(page, name, institution)
        if image_url:
            print_colored(" ✅ Found!", color='GREEN')
            logger.info(f"Found image with direct photo search for {name}")
        else:
            print_colored(" ❌ Not found", color='RED')
    
    # Method 3: Google Images (use thumbnails directly)
    if not image_url:
        print_colored("  ↪ Trying Google Images...", color='BLUE', end='')
        logger.info(f"Trying Google Images for {name}")
        image_url = await get_google_images_search(page, name, institution)
        if image_url:
            print_colored(" ✅ Found!", color='GREEN')
            logger.info(f"Found image on Google Images for {name}")
        else:
            print_colored(" ❌ Not found", color='RED')
    
    # Method 4: University website (more complex)
    if not image_url:
        print_colored("  ↪ Trying university website...", color='BLUE', end='')
        logger.info(f"Trying university website for {name}")
        image_url = await get_university_website_image(page, context, name, institution)
        if image_url:
            print_colored(" ✅ Found!", color='GREEN')
            logger.info(f"Found image on university website for {name}")
        else:
            print_colored(" ❌ Not found", color='RED')
    
    # Method 5: Professional site
    if not image_url:
        print_colored("  ↪ Trying professional site...", color='BLUE', end='')
        logger.info(f"Trying professional site for {name}")
        image_url = await get_professional_site_image(page, context, name, institution)
        if image_url:
            print_colored(" ✅ Found!", color='GREEN')
            logger.info(f"Found image on professional site for {name}")
        else:
            print_colored(" ❌ Not found", color='RED')
    
    # Method 6: Department page (direct search)
    if not image_url:
        print_colored("  ↪ Trying department pages...", color='BLUE', end='')
        logger.info(f"Trying department pages for {name}")
        image_url = await get_department_page_image(page, context, name, institution)
        if image_url:
            print_colored(" ✅ Found!", color='GREEN')
            logger.info(f"Found image on department page for {name}")
        else:
            print_colored(" ❌ Not found", color='RED')
    
    # Method 7: Conference websites
    if not image_url:
        print_colored("  ↪ Trying conference websites...", color='BLUE', end='')
        logger.info(f"Trying conference websites for {name}")
        image_url = await get_conference_image(page, context, name, institution)
        if image_url:
            print_colored(" ✅ Found!", color='GREEN')
            logger.info(f"Found image on conference website for {name}")
        else:
            print_colored(" ❌ Not found", color='RED')
    
    # Process and save the image if found
    if image_url:
        print_colored(f"  ↪ Processing image...", color='MAGENTA', end='')
        logger.info(f"Processing image for {name}")
        success = process_image(image_url, output_path)
        
        if success:
            # Track file size for statistics
            file_size = output_path.stat().st_size / 1024  # KB
            stats['total_size'] = stats.get('total_size', 0) + file_size
            stats['file_count'] = stats.get('file_count', 0) + 1
            
            print_colored(f" ✅ Success! ({file_size:.1f}KB)", color='GREEN')
            logger.info(f"Successfully processed image for {name} ({file_size:.1f}KB)")
            stats['successful'] += 1
        else:
            print_colored(" ❌ Failed", color='RED')
            logger.error(f"Failed to process image for {name}")
            stats['failed'] += 1
    else:
        print_colored("  ❌ No image found for this scholar", color='RED')
        logger.warning(f"No image found for {name}")
        stats['failed'] += 1
    
    # Random delay to avoid being rate-limited
    delay = random.uniform(*DELAY_BETWEEN_SEARCHES)
    await asyncio.sleep(delay)

async def download_profile_pictures_async(test_mode=False, limit=10, skip=0):
    """
    Download profile pictures for scholars listed in scholars.csv
    using browser automation with Playwright.
    
    Args:
        test_mode: If True, only process a limited number of scholars
        limit: Number of scholars to process in test mode
        skip: Number of scholars to skip from the beginning
    """
    print_header("SCHOLAR PROFILE PICTURE DOWNLOADER")
    print_colored(f"🎯 Target: Small compressed images ({TARGET_SIZE[0]}x{TARGET_SIZE[1]}, {JPEG_QUALITY}% quality)", color='CYAN')
    
    # Create output directory
    output_dir = Path("data/profile_pics")
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Read scholars.csv
    scholars = []
    try:
        with open("data/scholars.csv", "r") as f:
            reader = csv.DictReader(f)
            scholars = list(reader)
        
        # Skip scholars if requested
        if skip > 0:
            scholars = scholars[skip:]
            print_colored(f"⏭️  Skipping first {skip} scholars", color='YELLOW', bold=True)
            
        if test_mode:
            scholars = scholars[:limit]
            print_colored(f"🧪 TEST MODE: Processing only {limit} scholars", color='YELLOW', bold=True)
        
        print_colored(f"📊 Found {len(scholars)} scholars in CSV file", color='CYAN')
        logger.info(f"Found {len(scholars)} scholars in CSV file")
    except Exception as e:
        print_colored(f"❌ Error reading scholars.csv: {e}", color='RED', bold=True)
        logger.error(f"Error reading scholars.csv: {e}")
        return
    
    # Track statistics
    stats = {
        'successful': 0,
        'failed': 0,
        'skipped': 0,
        'total': len(scholars),
        'output_dir': output_dir,
        'total_size': 0,
        'file_count': 0
    }
    
    # Use Playwright for browser automation
    print_colored("🌐 Launching browser...", color='CYAN')
    async with async_playwright() as p:
        # Launch a browser with stealth mode to avoid detection
        browser_args = []
        
        # Add arguments to avoid detection and improve stability
        browser_args = [
            '--disable-blink-features=AutomationControlled',
            '--disable-features=IsolateOrigins,site-per-process',
            '--disable-site-isolation-trials',
            '--disable-web-security',
            '--disable-dev-shm-usage',  # Helps with memory issues in Docker
            '--no-sandbox',  # Required in some environments
            '--disable-setuid-sandbox',
            '--disable-gpu',  # Helps with headless mode
            '--disable-infobars',
            '--window-size=1280,800',
            '--start-maximized'
        ]
        
        browser = await p.chromium.launch(headless=True, args=browser_args)
        
        # Create a context with more realistic browser settings
        context = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={'width': 1280, 'height': 800},
            device_scale_factor=1,
            is_mobile=False,
            has_touch=False,
            locale='en-US',
            timezone_id='America/New_York',
            permissions=['geolocation']
        )
        
        # Set default timeouts for the context
        context.set_default_timeout(PAGE_LOAD_TIMEOUT)
        
        # Create a new page
        page = await context.new_page()
        print_colored("✅ Browser ready", color='GREEN')
        
        # Process each scholar
        for i, scholar in enumerate(scholars):
            # Update progress bar
            print_progress_bar(i, len(scholars), 
                              prefix=f'Progress: {i}/{len(scholars)}',
                              suffix='Complete', 
                              length=40)
            
            # Try with retries
            retries = 0
            success = False
            
            while retries < MAX_RETRIES and not success:
                try:
                    await process_scholar(page, context, scholar, output_dir, stats)
                    success = True
                except PlaywrightTimeoutError:
                    retries += 1
                    print_colored(f"⚠️  Timeout error, retry {retries}/{MAX_RETRIES}", color='YELLOW')
                    logger.warning(f"Timeout error, retry {retries}/{MAX_RETRIES}")
                    
                    if retries < MAX_RETRIES:
                        # Longer delay between retries with increasing backoff
                        await asyncio.sleep(random.uniform(3 + retries, 5 + retries * 2))
                        
                        # If we've had multiple timeouts, try refreshing the page or creating a new one
                        if retries >= 2:
                            try:
                                await page.close()
                                page = await context.new_page()
                                print_colored("🔄 Created new page after timeout", color='YELLOW')
                            except Exception:
                                # If refreshing fails, continue with the current page
                                pass
                except Exception as e:
                    retries += 1
                    print_colored(f"❌ Error processing scholar: {e}", color='RED')
                    logger.error(f"Error processing scholar: {e}")
                    
                    if retries < MAX_RETRIES:
                        # Longer delay between retries with increasing backoff
                        await asyncio.sleep(random.uniform(3 + retries, 5 + retries * 2))
                    else:
                        # If we've exhausted retries, count as failed
                        if not success and scholar.get("scholar_name") and not any(s in stats for s in ['successful', 'failed', 'skipped']):
                            stats['failed'] += 1
                        break
            
            # If we've processed a few scholars, clear browser cache to avoid memory issues
            if i > 0 and i % 10 == 0:
                try:
                    # Clear cookies and cache
                    await context.clear_cookies()
                    print_colored("🧹 Cleared browser cookies", color='CYAN')
                except Exception:
                    pass
        
        # Final progress bar update
        print_progress_bar(len(scholars), len(scholars), 
                          prefix=f'Progress: {len(scholars)}/{len(scholars)}',
                          suffix='Complete', 
                          length=40)
        
        # Close the browser
        await browser.close()
        print_colored("🌐 Browser closed", color='CYAN')
    
    # Calculate average file size
    if stats['file_count'] > 0:
        stats['avg_size'] = stats['total_size'] / stats['file_count']
    
    # Print summary
    print_summary(stats)
    
    # Log summary
    logger.info("\nDownload complete!")
    logger.info(f"Successfully downloaded: {stats['successful']}/{stats['total']}")
    logger.info(f"Failed: {stats['failed']}/{stats['total']}")
    logger.info(f"Skipped (already existed): {stats['skipped']}/{stats['total']}")
    logger.info(f"Average file size: {stats.get('avg_size', 0):.1f}KB")
    logger.info(f"Images saved to: {output_dir}")

def download_profile_pictures(test_mode=False, limit=10, skip=0):
    """Wrapper function to run the async code"""
    asyncio.run(download_profile_pictures_async(test_mode, limit, skip))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Download profile pictures for scholars')
    parser.add_argument('--test', action='store_true', help='Run in test mode with limited scholars')
    parser.add_argument('--limit', type=int, default=10, help='Number of scholars to process in test mode')
    parser.add_argument('--skip', type=int, default=0, help='Number of scholars to skip from the beginning')
    args = parser.parse_args()
    
    download_profile_pictures(test_mode=args.test, limit=args.limit, skip=args.skip) 