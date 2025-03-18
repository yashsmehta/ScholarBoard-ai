#!/usr/bin/env python3
"""
Download profile pictures for scholars using Playwright.
Uses university websites first, then Google Scholar, with default avatar as fallback.
Ensures only one image per scholar ID, regardless of name variations.
"""
import os
import csv
import time
import re
import random
import argparse
from pathlib import Path
import asyncio
import requests
from playwright.async_api import async_playwright
from PIL import Image
import io
import base64
import urllib.parse
import shutil  # Add import here for file operations

# Configuration
MAX_CONCURRENT = 5  # Number of concurrent downloads
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
]
TIMEOUTS = {
    "page_load": 15000,  # 15 seconds for page loading
    "network_idle": 5000,  # 5 seconds for network idle
}
IMAGE_SETTINGS = {
    "max_size_kb": 500,  # Maximum file size in KB
}

# ANSI colors for terminal output
COLORS = {
    'GREEN': '\033[92m',
    'YELLOW': '\033[93m',
    'RED': '\033[91m',
    'BLUE': '\033[94m',
    'CYAN': '\033[96m',
    'RESET': '\033[0m',
    'BOLD': '\033[1m',
}

def print_colored(message, color=None, bold=False, end='\n'):
    """Print colored text to the terminal"""
    color_code = COLORS.get(color, '')
    bold_code = COLORS['BOLD'] if bold else ''
    reset_code = COLORS['RESET']
    print(f"{color_code}{bold_code}{message}{reset_code}", end=end)

def print_progress(current, total, prefix='', suffix=''):
    """Print progress information"""
    percent = f"{100 * (current / float(total)):.1f}%"
    print_colored(f"\r{prefix} {current}/{total} ({percent}) {suffix}", end='\r')
    if current == total:
        print()

async def get_university_website_image(page, name, institution):
    """Try to get profile picture directly from university website with improved handling"""
    try:
        # Clean up institution name
        institution_clean = institution.lower().replace('"', '').strip()
        name_parts = name.lower().split()
        first_name = name_parts[0]
        last_name = name_parts[-1]
        
        # Generate possible URLs based on institution and name
        direct_urls = []
        
        # Special cases for known universities
        if "johns hopkins" in institution_clean:
            direct_urls.extend([
                f"https://cogsci.jhu.edu/directory/{first_name}-{last_name}/",
                f"https://engineering.jhu.edu/faculty/{first_name}-{last_name}/",
                f"https://krieger.jhu.edu/cogsci/directory/{first_name}-{last_name}/",
                f"https://neuroscience.jhu.edu/research/faculty/{first_name}-{last_name}"
            ])
        elif "arizona" in institution_clean:
            direct_urls.extend([
                f"https://psychology.arizona.edu/users/{first_name}-{last_name}",
                f"https://psychology.arizona.edu/person/{first_name}-{last_name}"
            ])
        elif "queensland" in institution_clean:
            direct_urls.extend([
                f"https://researchers.uq.edu.au/researcher/{first_name}-{last_name}",
                f"https://qbi.uq.edu.au/profile/{first_name}-{last_name}"
            ])
        elif "ucl" in institution_clean or "college london" in institution_clean:
            direct_urls.extend([
                f"https://iris.ucl.ac.uk/iris/browse/profile?upi={first_name}{last_name}",
                f"https://www.ucl.ac.uk/pals/people/{first_name}-{last_name}"
            ])
        elif "nevada" in institution_clean or "reno" in institution_clean:
            direct_urls.extend([
                f"https://www.unr.edu/psychology/people/{first_name}-{last_name}",
                f"https://www.unr.edu/directory/directory-profile/details?person={first_name}%20{last_name}"
            ])
        elif "california" in institution_clean:
            # Special handling for UC system
            campus = ""
            if "berkeley" in institution_clean:
                campus = "berkeley"
            elif "san diego" in institution_clean or "ucsd" in institution_clean:
                campus = "ucsd"
            elif "los angeles" in institution_clean or "ucla" in institution_clean:
                campus = "ucla"
            elif "santa barbara" in institution_clean or "ucsb" in institution_clean:
                campus = "ucsb"
            elif "irvine" in institution_clean:
                campus = "uci"
            elif "davis" in institution_clean:
                campus = "ucdavis"
            elif "santa cruz" in institution_clean:
                campus = "ucsc"
            elif "riverside" in institution_clean:
                campus = "ucr"
            elif "merced" in institution_clean:
                campus = "ucmerced"
                
            if campus:
                direct_urls.extend([
                    f"https://psychology.{campus}.edu/people/{first_name}-{last_name}",
                    f"https://www.{campus}.edu/faculty-profiles/{first_name}-{last_name}",
                    f"https://{campus}.edu/directory/people/{first_name}-{last_name}"
                ])
        
        # Add more accurate university URLs based on common patterns
        domain = None
        
        # Extract domain from institution name more accurately
        if "university of" in institution_clean:
            domain_part = institution_clean.split("university of")[-1].strip()
            if domain_part:
                domain_parts = domain_part.split()
                if domain_parts:
                    domain = domain_parts[0]
        elif "université" in institution_clean:
            domain_part = institution_clean.split("université")[-1].strip()
            if domain_part:
                domain_parts = domain_part.split()
                if domain_parts:
                    domain = domain_parts[0]
                    
        # Try to extract university domain names from the full institution name
        university_variants = []
        if "college" in institution_clean or "university" in institution_clean:
            # Handle universities with typical naming patterns
            parts = institution_clean.replace(',', ' ').split()
            for i, part in enumerate(parts):
                if part in ("university", "college", "institute", "school") and i > 0:
                    potential_domain = parts[i-1]
                    if potential_domain not in ("of", "the", "and", "for"):
                        university_variants.append(potential_domain)
                        
        # Special handling for well-known university acronyms
        acronyms = {
            "mit": "mit.edu", 
            "cmu": "cmu.edu", 
            "nyu": "nyu.edu",
            "usc": "usc.edu", 
            "psu": "psu.edu"
        }
        
        for part in institution_clean.split():
            if part in acronyms:
                direct_urls.append(f"https://www.{acronyms[part]}/directory/person/{first_name}-{last_name}")
                direct_urls.append(f"https://www.{acronyms[part]}/people/{first_name}-{last_name}")
        
        # Common university domains
        if domain:
            # Remove special characters from domain
            domain = re.sub(r'[^\w\s]', '', domain)
            
            # Domestic U.S. universities typically use .edu
            direct_urls.extend([
                f"https://www.{domain}.edu/faculty/{first_name}-{last_name}",
                f"https://www.{domain}.edu/people/{first_name}-{last_name}",
                f"https://psychology.{domain}.edu/people/{first_name}-{last_name}",
                f"https://{domain}.edu/directory/{first_name}-{last_name}",
                f"https://profiles.{domain}.edu/display/{first_name}.{last_name}"
            ])
            
            # For UK universities
            if "uk" in institution_clean or "kingdom" in institution_clean:
                direct_urls.extend([
                    f"https://www.{domain}.ac.uk/people/{first_name}-{last_name}",
                    f"https://www.{domain}.ac.uk/staff/{first_name}-{last_name}"
                ])
        
        # Add national research institute patterns
        if "national institute" in institution_clean:
            institute_part = institution_clean.replace("national institute", "").strip()
            if institute_part.startswith("of "):
                institute_part = institute_part[3:].strip()
                
            institute_domain = institute_part.split()[0] if institute_part else ""
            if institute_domain:
                direct_urls.extend([
                    f"https://www.{institute_domain}.nih.gov/research/investigators/{first_name}-{last_name}",
                    f"https://www.{institute_domain}.nih.gov/about/people/{first_name}-{last_name}"
                ])
            
            # NIH general website
            direct_urls.extend([
                f"https://irp.nih.gov/pi/{first_name}-{last_name}",
                f"https://www.nih.gov/about-nih/what-we-do/nih-almanac/national-institute-{institute_domain}/biographies/{first_name}-{last_name}"
            ])
        
        # Directly check university website as a last resort
        # Extract university base domain
        uni_name = institution_clean.split(',')[0].strip()
        uni_words = uni_name.split()
        if len(uni_words) > 1:
            potential_domain = uni_words[0].replace(' ', '')
            if potential_domain not in ("the", "a", "an", "of"):
                direct_urls.extend([
                    f"https://www.{potential_domain}.edu/directory/person/{first_name}-{last_name}",
                    f"https://www.{potential_domain}.edu/faculty-staff/{first_name}-{last_name}"
                ])
                
                # For universities with "University of X" format
                if len(uni_words) > 2 and uni_words[0].lower() == "university" and uni_words[1].lower() == "of":
                    location = uni_words[2].lower()
                    if location not in ("the", "a", "an"):
                        direct_urls.extend([
                            f"https://www.{location}.edu/directory/{first_name}-{last_name}",
                            f"https://www.{location}.edu/people/{first_name}-{last_name}"
                        ])
        
        # Try to handle common non-university domains
        if any(term in institution_clean for term in ["hospital", "clinic", "medical", "health"]):
            health_terms = ["medicine", "health", "hospital", "medical"]
            for term in health_terms:
                if term in institution_clean:
                    direct_urls.extend([
                        f"https://www.{term}.org/directory/{first_name}-{last_name}",
                        f"https://www.{term}.org/staff/{first_name}-{last_name}"
                    ])
        
        # Remove duplicate URLs
        direct_urls = list(set(direct_urls))
        
        # Try each direct URL with a maximum timeout
        image_found = False
        
        for url in direct_urls:
            if image_found:
                break
                
            try:
                print_colored(f"  - Checking {url}", color="CYAN")
                try:
                    # Use a shorter timeout for initial navigation
                    await page.goto(url, wait_until="domcontentloaded", timeout=TIMEOUTS["page_load"])
                    try:
                        await page.wait_for_load_state("networkidle", timeout=TIMEOUTS["network_idle"])
                    except Exception:
                        # Continue even if network idle times out
                        pass
                except Exception as e:
                    print_colored(f"  - Navigation error: {str(e)}", color="RED")
                    continue
                
                # Try common faculty photo selectors - prioritized by likelihood
                selectors = [
                    'img.faculty-photo',
                    'img.profile-photo',
                    'img.directory-photo',
                    'img.headshot',
                    'img.portrait',
                    'img.profile-image',
                    'img.faculty-image',
                    'img[alt*="headshot"]',
                    'img[alt*="photo"]',
                    'img[alt*="portrait"]',
                    'img[alt*="profile"]',
                    'img[alt*="faculty"]',
                    f'img[alt*="{last_name}"]',
                    f'img[alt*="{first_name} {last_name}"]',
                    f'img[alt*="{first_name}"]',
                    'img[src*="faculty"]',
                    'img[src*="profile"]',
                    'img[src*="headshot"]',
                    'img[src*="portrait"]',
                    'img[src*="directory"]',
                    'img[src*="photos"]',
                    '.faculty-profile img',
                    '.profile-image img',
                    '.faculty-photo img',
                    '.profile-photo img',
                    '.person-photo img',
                    '.directory-photo img',
                    '.user-photo img',
                    '.bio-image img',
                    '.circular-image img',
                    '.headshot img',
                    '.portrait img',
                    '.card-img-top',
                    '.profile-picture',
                    '.team-member-photo'
                ]
                
                # First check for images with matching names in their attributes
                for selector in selectors:
                    if image_found:
                        break
                        
                    try:
                        images = await page.query_selector_all(selector)
                        for img in images:
                            if image_found:
                                break
                                
                            try:
                                src = await img.get_attribute('src')
                                alt = await img.get_attribute('alt') or ""
                                
                                # Skip if no src or invalid image type
                                if not src or src.endswith(('.svg', '.gif', '.ico')):
                                    continue
                                    
                                # Check if image alt text contains the name
                                if first_name.lower() in alt.lower() and last_name.lower() in alt.lower():
                                    # This is very likely the correct image
                                    image_found = True
                                
                                # Handle various URL formats
                                if src.startswith('//'):
                                    src = f"https:{src}"
                                elif src.startswith('/'):
                                    base_url = '/'.join(url.split('/')[:3])
                                    src = f"{base_url}{src}"
                                elif src.startswith('./'):
                                    src = url.rstrip('/') + '/' + src[2:]
                                elif src.startswith('data:image'):
                                    # This is a base64 image - save it directly
                                    print_colored(f"  - Found base64 image, extracting...", color="GREEN")
                                    return src
                                elif not src.startswith(('http://', 'https://')):
                                    base_url = '/'.join(url.split('/')[:3])
                                    src = f"{base_url}/{src.lstrip('/')}"
                                
                                # Skip very small icon images
                                try:
                                    width = await img.evaluate('(el) => el.naturalWidth || el.width || el.getAttribute("width")')
                                    height = await img.evaluate('(el) => el.naturalHeight || el.height || el.getAttribute("height")')
                                    
                                    if width and height:
                                        w = int(width) if width else 0
                                        h = int(height) if height else 0
                                        if w < 50 or h < 50:
                                            continue
                                except:
                                    pass  # If we can't get dimensions, still try the image
                                
                                print_colored(f"  - Found image: {src[:50]}...", color="GREEN")
                                return src
                            except Exception as img_err:
                                continue
                    except Exception as sel_err:
                        continue

                # If no matches with selectors, try all reasonable sized images
                try:
                    all_images = await page.query_selector_all('img')
                    for img in all_images:
                        if image_found:
                            break
                            
                        try:
                            # Get image attributes
                            src = await img.get_attribute('src')
                            if not src or src.endswith(('.svg', '.gif', '.ico')):
                                continue
                                
                            # Check dimensions
                            width = await img.evaluate('(el) => el.naturalWidth || el.width || el.getAttribute("width")')
                            height = await img.evaluate('(el) => el.naturalHeight || el.height || el.getAttribute("height")')
                            
                            if width and height:
                                w = int(width) if width else 0
                                h = int(height) if height else 0
                                if w >= 100 and h >= 100 and 0.5 <= w/h <= 2.0:
                                    # Handle various URL formats
                                    if src.startswith('//'):
                                        src = f"https:{src}"
                                    elif src.startswith('/'):
                                        base_url = '/'.join(url.split('/')[:3])
                                        src = f"{base_url}{src}"
                                    elif src.startswith('./'):
                                        src = url.rstrip('/') + '/' + src[2:]
                                    elif src.startswith('data:image'):
                                        # Base64 image - save it directly
                                        print_colored(f"  - Found base64 image, extracting...", color="GREEN")
                                        return src
                                    elif not src.startswith(('http://', 'https://')):
                                        base_url = '/'.join(url.split('/')[:3])
                                        src = f"{base_url}/{src.lstrip('/')}"
                                    
                                    print_colored(f"  - Found reasonable sized image: {src[:50]}...", color="GREEN")
                                    return src
                        except Exception as img_err:
                            continue
                except Exception as e:
                    print_colored(f"  - Error processing images: {str(e)}", color="RED")

            except Exception as e:
                print_colored(f"  - Error accessing {url}: {str(e)}", color="RED")
                continue

        print_colored("  - No suitable profile image found on university websites", color="YELLOW")
        return None

    except Exception as e:
        print_colored(f"  - Error in University Website method: {str(e)}", color="RED")
        return None

async def get_google_scholar_pic(page, name):
    """Get profile picture from Google Scholar with better error handling"""
    try:
        # Create a new context for scholar search to avoid navigation issues
        context = await page.context.browser.new_context()
        scholar_page = await context.new_page()
        
        name_parts = name.lower().split()
        first_name = name_parts[0]
        last_name = name_parts[-1]
        
        # Try different search queries
        search_queries = [
            f'"{name}" site:scholar.google.com',
            f'"{first_name} {last_name}" site:scholar.google.com',
            f'author:"{first_name} {last_name}" site:scholar.google.com',
        ]
        
        for query in search_queries:
            # Use regular Google search to find the scholar profile
            search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
            try:
                print_colored(f"  - Searching Google for Scholar profile: {query}", color="CYAN")
                await scholar_page.goto(search_url, wait_until='domcontentloaded', timeout=30000)
                try:
                    await scholar_page.wait_for_load_state("networkidle", timeout=15000)
                except:
                    # Continue if network idle times out
                    pass
            except Exception as e:
                print_colored(f"  - Error navigating to Google search with query '{query}': {str(e)}", color="RED")
                continue
            
            # Look for Google Scholar profile links in search results
            try:
                # Find all links to Google Scholar profiles
                profile_links = await scholar_page.query_selector_all('a[href*="scholar.google.com/citations?user="]')
                
                for link in profile_links:
                    try:
                        # Get the URL and text from the link
                        profile_url = await link.get_attribute('href')
                        link_text = await link.text_content()
                        
                        # Skip if we don't have a valid URL or the link doesn't contain the author's name
                        if not profile_url:
                            continue
                            
                        # Check if name parts appear in the link text
                        if first_name.lower() in link_text.lower() and last_name.lower() in link_text.lower():
                            # Direct navigation to the profile
                            try:
                                print_colored(f"  - Found potential Scholar profile: {profile_url}", color="GREEN")
                                await scholar_page.goto(profile_url, wait_until='domcontentloaded', timeout=30000)
                                try:
                                    await scholar_page.wait_for_load_state("networkidle", timeout=15000)
                                except:
                                    # Continue if network idle times out
                                    pass
                                
                                # Try multiple methods to find the profile image
                                # Method 1: Standard profile image selector
                                img = await scholar_page.query_selector('#gsc_prf_pup-img')
                                if not img:
                                    img = await scholar_page.query_selector('img[id="gsc_prf_pup-img"]')
                                
                                # Method 2: Look for any image with alt text containing the name
                                if not img:
                                    all_imgs = await scholar_page.query_selector_all('img')
                                    for potential_img in all_imgs:
                                        alt = await potential_img.get_attribute('alt') or ""
                                        if first_name.lower() in alt.lower() and last_name.lower() in alt.lower():
                                            img = potential_img
                                            break
                                
                                # Method 3: Look for images with specific class patterns
                                if not img:
                                    for class_pattern in ['profile', 'avatar', 'photo', 'portrait']:
                                        potential_img = await scholar_page.query_selector(f'img[class*="{class_pattern}"]')
                                        if potential_img:
                                            img = potential_img
                                            break
                                            
                                # Method 4: Take screenshot of element with ID gsc_prf_pua (profile image area)
                                profile_area = await scholar_page.query_selector('#gsc_prf_pua')
                                if profile_area and not img:
                                    # Get screenshot of profile area - we'll return this as base64
                                    screenshot_base64 = await profile_area.screenshot(type='jpeg', quality=80)
                                    if screenshot_base64:
                                        return f"data:image/jpeg;base64,{base64.b64encode(screenshot_base64).decode('utf-8')}"
                                
                                if img:
                                    src = await img.get_attribute('src')
                                    if src:
                                        # Make sure the URL is absolute
                                        if src.startswith('/'):
                                            src = f"https://scholar.google.com{src}"
                                        
                                        # Skip if it's the default avatar image
                                        if 'avatar_scholar' in src or 'avatar_scholar_128' in src:
                                            print_colored("  - Found default Google Scholar avatar, skipping this profile", color="YELLOW")
                                            continue
                                            
                                        # It's a valid profile image
                                        print_colored(f"  - Found verified scholar profile image: {src[:50]}...", color="GREEN")
                                        await context.close()
                                        return src
                                    else:
                                        # If src is empty but we found the image, try taking a screenshot
                                        screenshot_base64 = await img.screenshot(type='jpeg', quality=80)
                                        if screenshot_base64:
                                            return f"data:image/jpeg;base64,{base64.b64encode(screenshot_base64).decode('utf-8')}"
                            except Exception as navigate_err:
                                print_colored(f"  - Error loading profile page: {str(navigate_err)}", color="RED")
                                continue
                    except Exception as e:
                        print_colored(f"  - Error processing search result: {str(e)}", color="RED")
                        continue
            except Exception as e:
                print_colored(f"  - Error parsing search results: {str(e)}", color="RED")
                continue
                
            # If we've tried search and found no results, try direct navigation to a constructed profile URL
            direct_urls = [
                f"https://scholar.google.com/citations?view_op=search_authors&mauthors={urllib.parse.quote(name)}&hl=en",
                f"https://scholar.google.com/citations?view_op=search_authors&mauthors={urllib.parse.quote(f'{first_name} {last_name}')}&hl=en"
            ]
            
            for direct_url in direct_urls:
                try:
                    print_colored(f"  - Trying direct Scholar search: {direct_url}", color="CYAN")
                    await scholar_page.goto(direct_url, wait_until='domcontentloaded', timeout=30000)
                    try:
                        await scholar_page.wait_for_load_state("networkidle", timeout=15000)
                    except:
                        pass
                        
                    # Check if there are search results
                    author_links = await scholar_page.query_selector_all('.gs_ai_name a')
                    for link in author_links:
                        link_text = await link.text_content()
                        if first_name.lower() in link_text.lower() and last_name.lower() in link_text.lower():
                            # Found a potential match, get the href
                            profile_url = await link.get_attribute('href')
                            if profile_url:
                                if not profile_url.startswith('http'):
                                    profile_url = 'https://scholar.google.com' + profile_url
                                
                                print_colored(f"  - Found scholar in search results: {link_text}", color="GREEN")
                                # Navigate to the profile page
                                await scholar_page.goto(profile_url, wait_until='domcontentloaded', timeout=30000)
                                
                                # Get the profile image
                                # First look for standard profile image
                                img = await scholar_page.query_selector('#gsc_prf_pup-img')
                                
                                if img:
                                    src = await img.get_attribute('src')
                                    # Skip if it's the default avatar
                                    if src and 'avatar_scholar' not in src:
                                        # Make sure URL is absolute
                                        if src.startswith('/'):
                                            src = f"https://scholar.google.com{src}"
                                            
                                        print_colored(f"  - Found verified scholar profile image: {src[:50]}...", color="GREEN")
                                        await context.close()
                                        return src
                                    elif src and 'avatar_scholar' in src:
                                        print_colored("  - Found default Google Scholar avatar, skipping", color="YELLOW")
                                        continue
                                    else:
                                        # Try screenshot of the image
                                        try:
                                            screenshot = await img.screenshot()
                                            if screenshot:
                                                b64_image = base64.b64encode(screenshot).decode('utf-8')
                                                return f"data:image/jpeg;base64,{b64_image}"
                                        except Exception as ss_err:
                                            print_colored(f"  - Screenshot error: {str(ss_err)}", color="RED")
                except Exception as e:
                    print_colored(f"  - Error with direct URL {direct_url}: {str(e)}", color="RED")
                    continue
        
        print_colored("  - No matching Google Scholar profile with custom photo found", color="YELLOW")
        await context.close()
        return None
        
    except Exception as e:
        print_colored(f"  - Error in Google Scholar search: {str(e)}", color="RED")
        try:
            await context.close()
        except:
            pass
        return None

async def download_and_save_image(page, image_url, output_path, method_name):
    """Download and save an image, with proper error handling"""
    try:
        # Handle base64 images
        if image_url.startswith('data:image'):
            try:
                # Extract the base64 data
                header, encoded = image_url.split(",", 1)
                data = base64.b64decode(encoded)
                
                # Save the image
                with open(output_path, 'wb') as f:
                    f.write(data)
                
                # Verify and optimize the image
                img = Image.open(output_path)
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGB')
                img.save(output_path, format='JPEG', quality=70, optimize=True)
                
                img_size = os.path.getsize(output_path) / 1024  # Size in KB
                print_colored(f"  ✓ Saved base64 image via {method_name} ({img_size:.1f}KB): {output_path}", color="GREEN")
                return True
            except Exception as e:
                print_colored(f"  - Error processing base64 image: {str(e)}", color="RED")
                return False
        
        # For regular URLs, first try with requests - much faster and less resource-intensive
        try:
            # Set a proper user agent
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.google.com/'
            }
            
            response = requests.get(image_url, headers=headers, timeout=15, allow_redirects=True)
            if response.status_code == 200 and response.headers.get('content-type', '').startswith('image/'):
                image_data = response.content
                content_length = len(image_data)
                
                if content_length > 0 and content_length < IMAGE_SETTINGS["max_size_kb"] * 1024:  # Less than max_size_kb
                    # Verify it's a valid image
                    try:
                        img = Image.open(io.BytesIO(image_data))
                        
                        # Convert to RGB if needed
                        if img.mode not in ('RGB', 'RGBA'):
                            img = img.convert('RGB')
                        
                        # Resize if too large (while maintaining aspect ratio)
                        max_dimension = 500
                        if img.width > max_dimension or img.height > max_dimension:
                            ratio = min(max_dimension / img.width, max_dimension / img.height)
                            new_width = int(img.width * ratio)
                            new_height = int(img.height * ratio)
                            img = img.resize((new_width, new_height), Image.LANCZOS)
                        
                        # Save as compressed JPEG
                        img.save(output_path, format='JPEG', quality=70, optimize=True)
                        img_size = os.path.getsize(output_path) / 1024  # Size in KB
                        
                        print_colored(f"  ✓ Saved image via {method_name} ({img_size:.1f}KB): {output_path}", color="GREEN")
                        return True
                    except Exception as e:
                        print_colored(f"  - Invalid image data (requests): {str(e)}", color="RED")
                else:
                    print_colored(f"  - Image too large or empty (requests): {content_length/1024:.1f}KB", color="RED")
            else:
                print_colored(f"  - Failed to download with requests: {response.status_code}", color="RED")
        except Exception as e:
            print_colored(f"  - Request download failed, falling back to browser: {str(e)}", color="YELLOW")
        
        # Fallback to browser method if requests fails
        # Create a new context for each download to avoid navigation issues
        context = await page.context.browser.new_context()
        new_page = await context.new_page()
        
        try:
            response = await new_page.goto(image_url, wait_until='domcontentloaded', timeout=20000)
            try:
                await new_page.wait_for_load_state("networkidle", timeout=10000)
            except:
                # Continue even if network idle times out
                pass
                
            if response and response.status == 200:
                content_type = response.headers.get('content-type', '')
                if 'image' in content_type and not any(x in content_type for x in ['svg', 'gif', 'ico']):
                    try:
                        content_length = int(response.headers.get('content-length', '0'))
                    except:
                        content_length = 0
                        
                    if content_length == 0 or content_length < IMAGE_SETTINGS["max_size_kb"] * 1024:  # Less than max_size_kb KB
                        try:
                            # Try to get the image data
                            image_data = await response.body()
                            
                            # Verify it's a valid image
                            try:
                                img = Image.open(io.BytesIO(image_data))
                                
                                # Convert to RGB if needed
                                if img.mode not in ('RGB', 'RGBA'):
                                    img = img.convert('RGB')
                                
                                # Resize if too large (while maintaining aspect ratio)
                                max_dimension = 500
                                if img.width > max_dimension or img.height > max_dimension:
                                    ratio = min(max_dimension / img.width, max_dimension / img.height)
                                    new_width = int(img.width * ratio)
                                    new_height = int(img.height * ratio)
                                    img = img.resize((new_width, new_height), Image.LANCZOS)
                                
                                # Save as compressed JPEG
                                img.save(output_path, format='JPEG', quality=70, optimize=True)
                                img_size = os.path.getsize(output_path) / 1024  # Size in KB
                                
                                print_colored(f"  ✓ Saved image via {method_name} (browser) ({img_size:.1f}KB): {output_path}", color="GREEN")
                                await context.close()
                                return True
                            except Exception as e:
                                print_colored(f"  - Invalid image data: {str(e)}", color="RED")
                        except Exception as body_err:
                            print_colored(f"  - Error getting image data: {str(body_err)}", color="RED")
                            
                            # Try screenshot as last resort for browser-based images
                            try:
                                await new_page.screenshot(path=output_path)
                                img = Image.open(output_path)
                                
                                # Verify and optimize the image
                                if img.mode not in ('RGB', 'RGBA'):
                                    img = img.convert('RGB')
                                    
                                # Save as compressed JPEG
                                img.save(output_path, format='JPEG', quality=70, optimize=True)
                                img_size = os.path.getsize(output_path) / 1024  # Size in KB
                                
                                print_colored(f"  ✓ Saved image via {method_name} (screenshot) ({img_size:.1f}KB): {output_path}", color="GREEN")
                                await context.close()
                                return True
                            except Exception as ss_err:
                                print_colored(f"  - Error taking screenshot: {str(ss_err)}", color="RED")
                    else:
                        print_colored(f"  - Image too large: {content_length/1024:.1f}KB", color="RED")
                else:
                    print_colored(f"  - Invalid content type: {content_type}", color="RED")
            else:
                print_colored(f"  - Failed to download image: {response.status if response else 'No response'}", color="RED")
        except Exception as e:
            print_colored(f"  - Browser download error: {str(e)}", color="RED")
        
        await context.close()
    except Exception as e:
        print_colored(f"  - Error downloading image: {str(e)}", color="RED")
    return False

def get_output_filename(scholar):
    """Generate consistent output filename based on scholar ID and name"""
    # Use normalized name and scholar_id
    name = scholar['name'].replace(' ', '_').lower()
    scholar_id = scholar['scholar_id']
    return os.path.join('data/profile_pics', f"{name}_{scholar_id}.jpg")

async def process_scholar(browser, scholar, stats, semaphore, processed_ids):
    """Process a single scholar"""
    async with semaphore:
        name = scholar['name']
        institution = scholar['institution']
        scholar_id = scholar['scholar_id']
        
        # Debug print to check scholar ID
        print_colored(f"\n🔍 Processing {name} ({institution}) [ID: {scholar_id}]", color="BLUE", bold=True)
        
        # Skip if we've already processed this scholar ID
        if scholar_id in processed_ids:
            print_colored(f"⏭ Skipping {name} (scholar ID {scholar_id} already processed)", color="YELLOW")
            stats["skipped"] += 1
            return
        
        # Create output filename using both name and scholar_id
        output_path = get_output_filename(scholar)
        
        # Skip if file already exists
        if os.path.exists(output_path):
            print_colored(f"⏭ Skipping {name} (image for scholar ID {scholar_id} already exists)", color="YELLOW")
            stats["skipped"] += 1
            return
        
        # Mark this scholar ID as processed
        processed_ids.add(scholar_id)
        
        # Create a browser context
        context = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={'width': 1280, 'height': 800},
        )
        
        # Create a page
        page = await context.new_page()
        
        success = False
        
        # Try university website method first
        print_colored(f"  • Trying university website method...", color="CYAN")
        image_url = await get_university_website_image(page, name, institution)
        if image_url:
            success = await download_and_save_image(page, image_url, output_path, "university")
        
        # If not successful, try Google Scholar method
        if not success:
            print_colored(f"  • Trying Google Scholar method...", color="CYAN")
            image_url = await get_google_scholar_pic(page, name)
            if image_url:
                success = await download_and_save_image(page, image_url, output_path, "Google Scholar")
        
        # If still not successful, use default avatar
        if not success:
            print_colored(f"  • Using default avatar...", color="CYAN")
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Copy the default avatar
            default_avatar_path = os.path.join('data/profile_pics', 'default_avatar.jpg')
            if os.path.exists(default_avatar_path):
                try:
                    shutil.copy(default_avatar_path, output_path)
                    print_colored(f"  ✓ Used default avatar for {name} (ID: {scholar_id}): {output_path}", color="YELLOW")
                    success = True
                except Exception as e:
                    print_colored(f"  ✗ Error copying default avatar: {str(e)}", color="RED")
            else:
                print_colored(f"  ✗ Default avatar not found at {default_avatar_path}", color="RED")
        
        # Update statistics
        if success:
            stats["successful"] += 1
        else:
            stats["failed"] += 1
        
        # Close the context
        await context.close()

async def download_profile_pictures_batch(scholars_batch, stats, browser, processed_ids):
    """Download profile pictures for a batch of scholars"""
    # Create a semaphore to limit concurrent browser instances
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    
    # Process each scholar in the batch
    tasks = []
    for scholar in scholars_batch:
        task = process_scholar(browser, scholar, stats, semaphore, processed_ids)
        tasks.append(task)
    
    # Run all tasks concurrently
    await asyncio.gather(*tasks)

def print_summary(stats):
    """Print a summary of the download results"""
    print_colored("\n===== DOWNLOAD SUMMARY =====", color="BLUE", bold=True)
    total = stats["successful"] + stats["failed"] + stats["skipped"]
    success_rate = (stats["successful"] / (stats["successful"] + stats["failed"])) * 100 if (stats["successful"] + stats["failed"]) > 0 else 0
    
    print_colored(f"✓ Successfully downloaded: {stats['successful']}/{total} ({stats['successful']/total*100:.1f}%)", color="GREEN")
    print_colored(f"✗ Failed: {stats['failed']}/{total} ({stats['failed']/total*100:.1f}%)", color="RED")
    print_colored(f"⏭ Skipped (already existed): {stats['skipped']}/{total} ({stats['skipped']/total*100:.1f}%)", color="YELLOW")
    print_colored(f"Success rate (excluding skipped): {success_rate:.1f}%", color="CYAN")
    print_colored(f"Images saved to: {stats['output_dir']}", color="CYAN")
    print_colored(f"Total unique scholar IDs processed: {stats['unique_ids']}", color="CYAN")
    print_colored("============================", color="BLUE", bold=True)

async def download_profile_pictures_async(csv_path, output_dir_path, test_mode=False, limit=10, skip=0):
    """Main function to download profile pictures"""
    # Create output directory
    output_dir = Path(output_dir_path)
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Ensure default avatar exists - only download once
    default_avatar_path = os.path.join(output_dir_path, 'default_avatar.jpg')
    if not os.path.exists(default_avatar_path):
        print_colored("Creating default avatar...", color="CYAN")
        try:
            # Try downloading directly with requests first - faster than launching a browser
            response = requests.get('https://scholar.google.com/citations/images/avatar_scholar_128.png', timeout=10)
            if response.status_code == 200 and response.headers.get('content-type', '').startswith('image/'):
                with open(default_avatar_path, 'wb') as f:
                    f.write(response.content)
                print_colored("Default avatar created successfully", color="GREEN")
            else:
                # Fallback to browser if request fails
                async with async_playwright() as p:
                    browser = await p.chromium.launch()
                    page = await browser.new_page()
                    await page.goto('https://scholar.google.com/citations/images/avatar_scholar_128.png')
                    await page.screenshot(path=default_avatar_path)
                    await browser.close()
                print_colored("Default avatar created with browser", color="GREEN")
        except Exception as e:
            print_colored(f"Warning: Couldn't create default avatar: {str(e)}", color="YELLOW")
    else:
        print_colored("Default avatar already exists, skipping download", color="CYAN")
    
    # Read scholars from CSV
    print_colored("Reading scholar data...", color="CYAN")
    all_scholars = []
    
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            all_scholars.append({
                'name': row['scholar_name'],
                'institution': row['scholar_institution'],
                'scholar_id': row['scholar_id']
            })
    
    # Skip scholars if requested
    if skip > 0:
        print_colored(f"Skipping first {skip} scholars", color="YELLOW")
        
        # Important: Skip BEFORE sorting to maintain the order of the CSV
        all_scholars = all_scholars[skip:]
    
    # Print the first scholar to debug
    if all_scholars:
        print_colored(f"DEBUG - First scholar to process: {all_scholars[0]['name']} (ID: {all_scholars[0]['scholar_id']})", color="CYAN")
    
    # Do not sort by scholar_id to keep the original order from the CSV
    # all_scholars.sort(key=lambda x: x['scholar_id'])
    
    # Limit the number of scholars if in test mode
    if test_mode:
        all_scholars = all_scholars[:limit]
        print_colored(f"TEST MODE: Processing only {len(all_scholars)} scholars", color="YELLOW", bold=True)
    
    # Initialize statistics
    stats = {
        "successful": 0,
        "failed": 0,
        "skipped": 0,
        "output_dir": output_dir,
        "unique_ids": 0
    }
    
    # Keep track of processed scholar IDs to avoid duplicates
    processed_ids = set()
    
    # Process scholars in batches for better memory management
    batch_size = 50  # Process 50 scholars per batch
    batches = [all_scholars[i:i + batch_size] for i in range(0, len(all_scholars), batch_size)]
    
    print_colored(f"Downloading profile pictures for {len(all_scholars)} scholars in {len(batches)} batches", color="CYAN")
    print_colored(f"Using up to {MAX_CONCURRENT} concurrent downloads per batch", color="CYAN")
    
    # Launch browser once for all scholars
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # Process each batch
        for i, batch in enumerate(batches):
            print_colored(f"Processing batch {i+1}/{len(batches)}...", color="CYAN", bold=True)
            await download_profile_pictures_batch(batch, stats, browser, processed_ids)
            
            # Update progress
            processed = min((i+1) * batch_size, len(all_scholars))
            print_progress(processed, len(all_scholars), prefix='Overall Progress:', suffix='Complete')
        
        await browser.close()
    
    # Update unique ID count
    stats["unique_ids"] = len(processed_ids)
    
    # Print summary
    print_summary(stats)

def download_profile_pictures(csv_path, output_dir_path, test_mode=False, limit=10, skip=0):
    """Wrapper function to run the async code"""
    asyncio.run(download_profile_pictures_async(csv_path, output_dir_path, test_mode, limit, skip))

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Download profile pictures for scholars')
    parser.add_argument('--test', action='store_true', help='Run in test mode with limited scholars')
    parser.add_argument('--limit', type=int, default=10, help='Number of scholars to process in test mode')
    parser.add_argument('--skip', type=int, default=0, help='Number of scholars to skip from the beginning')
    parser.add_argument('--csv', type=str, default='data/vss_data.csv', help='Path to the CSV file with scholar data')
    parser.add_argument('--output', type=str, default='data/profile_pics', help='Output directory for profile pictures')
    
    args = parser.parse_args()
    
    download_profile_pictures(
        csv_path=args.csv,
        output_dir_path=args.output,
        test_mode=args.test,
        limit=args.limit,
        skip=args.skip
    ) 