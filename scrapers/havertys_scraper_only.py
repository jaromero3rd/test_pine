#!/usr/bin/env python3
"""
Havertys Smart Multi-Category Furniture Scraper (Web Scraping Only)
Scrapes furniture data from Havertys website without OpenAI integration
"""

import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import csv
import re
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

class HavertysScraper:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.base_url = "https://www.havertys.com"
        
        # Define categories and their URLs
        self.categories = {
            'beds': {
                'url': 'https://www.havertys.com/products/category-page/bedroom/beds',
                'folder': 'beds',
                'item_type': 'bed',
                'csv_file': 'havertys_beds_hybrid.csv',
                'category_code': 'BD'
            },
            'dressers': {
                'url': 'https://www.havertys.com/products/category-page/bedroom/dressers',
                'folder': 'dressers',
                'item_type': 'dresser',
                'csv_file': 'havertys_dressers_robust.csv',
                'category_code': 'DR'
            },
            'nightstands': {
                'url': 'https://www.havertys.com/products/category-page/bedroom/nightstands',
                'folder': 'nightstands',
                'item_type': 'nightstand',
                'csv_file': 'havertys_nightstands_smart.csv',
                'category_code': 'NS'
            },
            'chests': {
                'url': 'https://www.havertys.com/products/category-page/bedroom/chests',
                'folder': 'chests',
                'item_type': 'chest',
                'csv_file': 'havertys_chests_smart.csv',
                'category_code': 'CH'
            },
            'benches': {
                'url': 'https://www.havertys.com/products/category-page/bedroom/benches',
                'folder': 'benches',
                'item_type': 'bench',
                'csv_file': 'havertys_benches_smart.csv',
                'category_code': 'BN'
            },
            'sofas': {
                'url': 'https://www.havertys.com/products/category-page/living-room/sofas-sleepers',
                'folder': 'sofas',
                'item_type': 'sofa',
                'csv_file': 'havertys_sofas_smart.csv',
                'category_code': 'SF'
            }
        }
        
        # Create output directories
        self.base_output_dir = "Catalog"
        os.makedirs(self.base_output_dir, exist_ok=True)
        
        for category_info in self.categories.values():
            category_dir = os.path.join(self.base_output_dir, category_info['folder'])
            os.makedirs(category_dir, exist_ok=True)

    def get_next_catalog_number(self, category: str) -> str:
        """Get the next available catalog number for a category."""
        category_info = self.categories[category]
        csv_path = os.path.join(self.base_output_dir, category_info['folder'], category_info['csv_file'])
        
        if not os.path.exists(csv_path):
            return f"HF-{category_info['category_code']}-001"
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                items = list(reader)
                
                if not items:
                    return f"HF-{category_info['category_code']}-001"
                
                # Find the highest catalog number
                max_number = 0
                for item in items:
                    catalog_num = item.get('catalog_number', '')
                    if catalog_num.startswith(f"HF-{category_info['category_code']}-"):
                        try:
                            number = int(catalog_num.split('-')[-1])
                            max_number = max(max_number, number)
                        except:
                            continue
                
                next_number = max_number + 1
                return f"HF-{category_info['category_code']}-{next_number:03d}"
                
        except Exception as e:
            print(f"Error getting next catalog number for {category}: {e}")
            return f"HF-{category_info['category_code']}-001"

    def check_category_completeness(self, category_name, category_info):
        """Check if a category is already complete (10 items with dimensions)."""
        csv_path = os.path.join(self.base_output_dir, category_info['folder'], category_info['csv_file'])
        
        if not os.path.exists(csv_path):
            print(f"    No CSV file found for {category_name} - needs scraping")
            return False
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                items = list(reader)
                
                if len(items) < 10:
                    print(f"    {category_name}: Only {len(items)} items (need 10) - needs scraping")
                    return False
                
                # Check how many have complete dimensions
                complete_items = 0
                for item in items:
                    dimensions = item.get('dimensions', '')
                    if dimensions and dimensions != '{}' and 'width' in dimensions:
                        complete_items += 1
                
                if complete_items >= 10:
                    print(f"    {category_name}: {len(items)} items, {complete_items} with dimensions - COMPLETE ✓")
                    return True
                else:
                    print(f"    {category_name}: {len(items)} items, only {complete_items} with dimensions - needs completion")
                    return False
                    
        except Exception as e:
            print(f"    Error checking {category_name} CSV: {e}")
            return False

    def load_existing_data(self, category_name, category_info):
        """Load existing data from CSV to avoid re-scraping complete items."""
        csv_path = os.path.join(self.base_output_dir, category_info['folder'], category_info['csv_file'])
        
        if not os.path.exists(csv_path):
            return []
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                items = []
                for row in reader:
                    # Convert dimensions string back to dict
                    dimensions_str = row.get('dimensions', '{}')
                    if dimensions_str and dimensions_str != '{}':
                        try:
                            dimensions = eval(dimensions_str)
                        except:
                            dimensions = {}
                    else:
                        dimensions = {}
                    
                    # Convert colors string back to list
                    colors_str = row.get('colors', '')
                    colors = [c.strip() for c in colors_str.split(',')] if colors_str else []
                    
                    items.append({
                        'name': row.get('item_name', ''),
                        'price': row.get('price', ''),
                        'link': row.get('link', ''),
                        'image_url': row.get('image_url', ''),
                        'colors': colors,
                        'dimensions': dimensions,
                        'item_type': row.get('item_type', ''),
                        'catalog_number': row.get('catalog_number', '')
                    })
                
                print(f"    Loaded {len(items)} existing items from {category_name}")
                return items
                
        except Exception as e:
            print(f"    Error loading existing data for {category_name}: {e}")
            return []

    def setup_browser(self):
        """Setup Chrome browser with stealth options."""
        print("Setting up Chrome browser...")
        
        # Chrome options for stealth
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Realistic user agent
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        try:
            # Setup Chrome driver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Set timeouts - OPTIMIZED for speed
            self.driver.set_page_load_timeout(15)
            self.driver.implicitly_wait(3)
            
            # Execute stealth script
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Set window size
            self.driver.set_window_size(1920, 1080)
            
            # Setup wait
            self.wait = WebDriverWait(self.driver, 8)
            
            print("✓ Browser setup complete")
            return True
            
        except Exception as e:
            print(f"✗ Browser setup failed: {e}")
            return False

    def close_browser(self):
        """Close the browser safely."""
        if self.driver:
            try:
                self.driver.quit()
                print("Browser closed")
            except:
                pass
            self.driver = None
            self.wait = None

    def wait_for_page_load(self, timeout=5):
        """Wait for page to load."""
        try:
            print("    Waiting for page to load...")
            
            # Wait for page to be ready
            self.wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            
            # Minimal wait for dynamic content
            time.sleep(0.15)
            
            print("    ✓ Page loaded successfully")
            return True
        except TimeoutException:
            print("    ✗ Page load timeout")
            return False

    def scroll_page(self):
        """Scroll the page to trigger lazy loading."""
        try:
            print("    Scrolling page...")
            
            # Scroll down quickly to load all products
            for i in range(5):
                self.driver.execute_script(f"window.scrollTo(0, {1000 * (i + 1)});")
                time.sleep(0.05)
            
            # Scroll back to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.05)
            
            print("    ✓ Scrolling complete")
            
        except Exception as e:
            print(f"    ✗ Scroll error: {e}")

    def get_basic_product_info_from_category_page(self, category_name, item_type):
        """Get basic product info from category page - names, prices, links only."""
        print(f"    Getting basic product info from {category_name} page...")
        products = []
        
        # Target the correct selector for products
        selector = 'div[data-name]'
        
        try:
            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                print(f"    Found {len(elements)} total elements with data-name")
                
                # Process first 10 elements
                for i, element in enumerate(elements[:10]):
                    try:
                        data_name = element.get_attribute('data-name')
                        
                        print(f"      Processing {i+1}/10: {data_name}")
                        
                        # Get basic info from category page only
                        name = data_name
                        price = self.extract_price_from_element(element)
                        link = self.extract_link_from_element(element)
                        
                        if name and len(name) > 3:
                            products.append({
                                'name': name,
                                'price': price,
                                'link': link,
                                'image_url': '',  # Will be filled from individual page
                                'colors': [],     # Will be filled from individual page
                                'dimensions': {}, # Will be filled from individual page
                                'item_type': item_type,
                                'catalog_number': ''  # Will be assigned
                            })
                            print(f"        ✓ Basic info: {name} - {price}")
                        else:
                            print(f"        ✗ No basic info extracted")
                            
                    except Exception as e:
                        print(f"        ✗ Error extracting info: {e}")
                        continue
                
                print(f"    ✓ Successfully extracted {len(products)} basic products")
            else:
                print("    ✗ No elements found with data-name")
                
        except Exception as e:
            print(f"    Selector failed: {e}")
        
        return products

    def extract_price_from_element(self, element):
        """Extract price from element."""
        try:
            price_selectors = ['.price', '[class*="price"]', 'span[class*="price"]']
            
            for selector in price_selectors:
                try:
                    elem = element.find_element(By.CSS_SELECTOR, selector)
                    price = self.extract_price(elem.text)
                    if price != "N/A":
                        return price
                except NoSuchElementException:
                    continue
            
            # Fallback: look in element text
            text = element.text
            price = self.extract_price(text)
            return price
            
        except Exception as e:
            return "N/A"

    def extract_link_from_element(self, element):
        """Extract link from element with multiple strategies."""
        try:
            # Strategy 1: Look for direct <a> tags
            link_selectors = [
                'a[href]',
                'a',
                '[href]',
                '.product-link',
                '.item-link',
                'a.product-item__link',
                'a[data-name]'
            ]
            
            for selector in link_selectors:
                try:
                    link_elem = element.find_element(By.CSS_SELECTOR, selector)
                    href = link_elem.get_attribute('href')
                    if href and href != self.base_url and href != self.base_url + '/':
                        return href
                except NoSuchElementException:
                    continue
            
            # Strategy 2: Look for any link within the element
            try:
                links = element.find_elements(By.TAG_NAME, 'a')
                for link in links:
                    href = link.get_attribute('href')
                    if href and href != self.base_url and href != self.base_url + '/':
                        return href
            except:
                pass
            
            # Strategy 3: Construct link from product name (for missing links)
            data_name = element.get_attribute('data-name')
            if data_name:
                url_name = data_name.lower().replace(' ', '-').replace('&', 'and')
                constructed_link = f"{self.base_url}/products/product-page/{url_name}"
                return constructed_link
                
        except Exception as e:
            pass
        return ""

    def extract_price(self, price_text):
        """Extract price from text."""
        if not price_text:
            return "N/A"
        
        price_match = re.search(r'[\$]?[\d,]+\.?\d*', price_text)
        if price_match:
            return price_match.group()
        
        return "N/A"

    def get_detailed_info_from_individual_page(self, product, max_retries=3):
        """Get detailed info from individual product page with retry logic."""
        print(f"    Getting detailed info for: {product['name']}")
        
        if not product['link']:
            print(f"      ✗ No link available for {product['name']}")
            return product
        
        for attempt in range(max_retries):
            try:
                # Navigate to product page
                print(f"      Navigating to: {product['link']} (attempt {attempt + 1})")
                self.driver.get(product['link'])
                
                if not self.wait_for_page_load():
                    print(f"      ✗ Failed to load product page (attempt {attempt + 1})")
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    return product
                
                # Extract all detailed information
                product['image_url'] = self.extract_main_image()
                product['colors'] = self.extract_colors()
                product['dimensions'] = self.extract_dimensions()
                
                print(f"      ✓ Detailed info extracted:")
                print(f"        Image: {product['image_url'][:80]}...")
                print(f"        Colors: {', '.join(product['colors'])}")
                print(f"        Dimensions: {product['dimensions']}")
                
                return product
                
            except Exception as e:
                print(f"      ✗ Error getting detailed info (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return product
        
        return product

    def extract_main_image(self):
        """Extract main product image from individual page."""
        try:
            # Look for main product image
            image_selectors = [
                'img[title*="Image 1 of"]',  # Your example: title="1-2500-8297" alt="Sandy Sofa Image 1 of 11"
                '.dropin-image',
                '.product-image img',
                '.main-image img',
                'img[alt*="Image 1 of"]'
            ]
            
            for selector in image_selectors:
                try:
                    img_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    src = img_elem.get_attribute('src')
                    if src:
                        if src.startswith('//'):
                            src = 'https:' + src
                        elif src.startswith('/'):
                            src = self.base_url + src
                        return src
                except NoSuchElementException:
                    continue
            
            return ""
            
        except Exception as e:
            print(f"        Error extracting main image: {e}")
            return ""

    def extract_colors(self):
        """Extract colors from individual page."""
        try:
            colors = []
            
            # Look for color swatch images with alt text like "Almond"
            color_selectors = [
                'img[alt*="Swatch image:"]',
                '.swatch img',
                '.color-swatch img',
                'img[alt*="Swatch"]'
            ]
            
            for selector in color_selectors:
                try:
                    color_images = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for img in color_images:
                        alt_text = img.get_attribute('alt')
                        if alt_text:
                            # Extract color name from alt text
                            if alt_text.startswith('Swatch image:'):
                                color_name = alt_text.replace('Swatch image:', '').strip()
                            else:
                                color_name = alt_text.strip()
                            
                            if color_name and color_name not in colors:
                                colors.append(color_name)
                except NoSuchElementException:
                    continue
            
            return colors
            
        except Exception as e:
            print(f"        Error extracting colors: {e}")
            return []

    def extract_dimensions(self):
        """Extract product dimensions using the correct selector."""
        try:
            dimensions = {}
            
            # Use the correct selector from your example
            try:
                # Look for the specific dl element
                dl_elem = self.driver.find_element(By.CSS_SELECTOR, 'dl.details-notmattress')
                
                # Get all dt and dd elements
                dt_elements = dl_elem.find_elements(By.TAG_NAME, 'dt')
                dd_elements = dl_elem.find_elements(By.TAG_NAME, 'dd')
                
                # Match dt and dd pairs
                for i, dt in enumerate(dt_elements):
                    if i < len(dd_elements):
                        label = dt.text.strip()
                        value = dd_elements[i].text.strip()
                        
                        # Extract dimensions from General section
                        if label.lower() == 'general' and 'x' in value:
                            # Parse dimensions like "90W x 38H x 39D"
                            dim_parts = value.split('x')
                            for part in dim_parts:
                                part = part.strip()
                                if 'W' in part:
                                    dimensions['width'] = part.replace('W', '').strip()
                                elif 'H' in part:
                                    dimensions['height'] = part.replace('H', '').strip()
                                elif 'D' in part:
                                    dimensions['depth'] = part.replace('D', '').strip()
                        
                        # Extract weight
                        elif label.lower() == 'weight':
                            dimensions['weight'] = value
                            
            except NoSuchElementException:
                print("        No details-notmattress element found")
            
            return dimensions
            
        except Exception as e:
            print(f"        Error extracting dimensions: {e}")
            return {}

    def download_image(self, image_url, filename, category_folder):
        """Download an image."""
        try:
            if not image_url:
                return None
                
            response = requests.get(image_url, timeout=10, stream=True)
            response.raise_for_status()
            
            # Clean filename
            clean_filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
            file_path = os.path.join(self.base_output_dir, category_folder, f"{clean_filename}.jpg")
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return file_path
        except Exception as e:
            print(f"Error downloading image {image_url}: {e}")
            return None

    def save_to_csv(self, products, category_folder, csv_filename):
        """Save products to CSV file with catalog numbers."""
        csv_path = os.path.join(self.base_output_dir, category_folder, csv_filename)
        
        # Ensure catalog numbers are assigned
        for product in products:
            if not product.get('catalog_number'):
                product['catalog_number'] = self.get_next_catalog_number(category_folder)
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['catalog_number', 'item_name', 'price', 'link', 'image_url', 'colors', 'dimensions', 'item_type']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for product in products:
                writer.writerow({
                    'catalog_number': product.get('catalog_number', ''),
                    'item_name': product['name'],
                    'price': product['price'],
                    'link': product['link'],
                    'image_url': product.get('image_url', ''),
                    'colors': ', '.join(product.get('colors', [])),
                    'dimensions': str(product.get('dimensions', {})),
                    'item_type': product.get('item_type', '')
                })
        
        print(f"✓ Saved {len(products)} products to {csv_path}")

    def scrape_category_smart(self, category_name, category_info):
        """Scrape a single category with smart completion checking."""
        print(f"\n{'='*60}")
        print(f"SCRAPING {category_name.upper()} CATEGORY")
        print(f"{'='*60}")
        
        try:
            # Check if category is already complete
            if self.check_category_completeness(category_name, category_info):
                print(f"✓ {category_name} is already complete - SKIPPING")
                return []
            
            # Load existing data
            existing_products = self.load_existing_data(category_name, category_info)
            
            # Navigate to the category page
            print(f"Navigating to: {category_info['url']}")
            self.driver.get(category_info['url'])
            
            if not self.wait_for_page_load():
                print("Failed to load page")
                return existing_products
            
            # Scroll to trigger lazy loading
            self.scroll_page()
            
            # Get basic product info from category page (names, prices, links only)
            new_products = self.get_basic_product_info_from_category_page(category_name, category_info['item_type'])
            
            if not new_products:
                print("No products found")
                return existing_products
            
            print(f"Found {len(new_products)} {category_name}")
            
            # Merge with existing data, avoiding duplicates
            all_products = existing_products.copy()
            new_items_added = []
            
            for new_product in new_products:
                # Check if this product already exists
                exists = False
                for existing_product in existing_products:
                    if existing_product['name'] == new_product['name']:
                        exists = True
                        break
                
                if not exists:
                    # Assign catalog number to new item
                    new_product['catalog_number'] = self.get_next_catalog_number(category_name)
                    all_products.append(new_product)
                    new_items_added.append(new_product)
                    print(f"    🆕 New item found: {new_product['name']} - {new_product['catalog_number']}")
            
            # Ensure we have exactly 10 products
            all_products = all_products[:10]
            
            # Get detailed info from individual pages for incomplete items
            print(f"\nGetting detailed info from individual pages for {category_name}...")
            for i, product in enumerate(all_products):
                # Check if this product needs detailed info
                needs_details = (
                    not product.get('image_url') or 
                    not product.get('dimensions') or 
                    product.get('dimensions') == {}
                )
                
                if needs_details:
                    print(f"\nProcessing {i+1}/{len(all_products)}: {product['name']} (needs details)")
                    all_products[i] = self.get_detailed_info_from_individual_page(product)
                    # Small delay between page visits
                    time.sleep(random.uniform(0.1, 0.2))
                else:
                    print(f"\nSkipping {i+1}/{len(all_products)}: {product['name']} (already complete)")
            
            # Download images for items that don't have them
            print(f"\nDownloading images for {category_name}...")
            for i, product in enumerate(all_products):
                if product.get('image_url') and not os.path.exists(os.path.join(self.base_output_dir, category_info['folder'], f"{category_info['item_type']}_{i+1}_{self.clean_text(product['name'])[:30]}.jpg")):
                    filename = f"{category_info['item_type']}_{i+1}_{self.clean_text(product['name'])[:30]}"
                    downloaded_path = self.download_image(product['image_url'], filename, category_info['folder'])
                    if downloaded_path:
                        print(f"  ✓ Downloaded: {os.path.basename(downloaded_path)}")
                    else:
                        print(f"  ✗ Failed to download image for {product['name']}")
            
            # Save to CSV
            self.save_to_csv(all_products, category_info['folder'], category_info['csv_file'])
            
            # Display results
            print(f"\n{'='*50}")
            print(f"{category_name.upper()} SCRAPING RESULTS")
            print(f"{'='*50}")
            
            for i, product in enumerate(all_products, 1):
                print(f"\n{i}. {product['name']} - {product.get('catalog_number', 'No catalog number')}")
                print(f"   Price: {product['price']}")
                print(f"   Link: {product['link'][:80]}...")
                print(f"   Image: {product.get('image_url', 'N/A')[:80]}...")
                print(f"   Colors: {', '.join(product.get('colors', []))}")
                print(f"   Dimensions: {product.get('dimensions', {})}")
            
            return all_products
            
        except Exception as e:
            print(f"Error scraping {category_name}: {e}")
            return []

    def scrape_all_categories_smart(self):
        """Scrape all categories with smart completion checking."""
        print("Starting Havertys Multi-Category Furniture Scraper (Web Scraping Only)")
        print("=" * 60)
        
        # First, check all categories for completeness
        print("\nChecking category completeness...")
        incomplete_categories = []
        for category_name, category_info in self.categories.items():
            if not self.check_category_completeness(category_name, category_info):
                incomplete_categories.append((category_name, category_info))
        
        if not incomplete_categories:
            print("\n✓ All categories are already complete!")
            return {}
        
        print(f"\nFound {len(incomplete_categories)} incomplete categories:")
        for category_name, _ in incomplete_categories:
            print(f"  - {category_name}")
        
        all_results = {}
        
        try:
            for category_name, category_info in incomplete_categories:
                # Setup browser for each category
                if not self.setup_browser():
                    print(f"Failed to setup browser for {category_name}")
                    continue
                
                try:
                    results = self.scrape_category_smart(category_name, category_info)
                    all_results[category_name] = results
                    
                    # Close browser after each category
                    self.close_browser()
                    
                    # Wait before next category
                    print(f"\nWaiting 2 seconds before next category...")
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"Error processing {category_name}: {e}")
                    all_results[category_name] = []
                    self.close_browser()
                    continue
            
            # Summary
            print(f"\n{'='*60}")
            print("FINAL SCRAPING SUMMARY")
            print(f"{'='*60}")
            
            total_items = 0
            for category_name, results in all_results.items():
                count = len(results)
                total_items += count
                print(f"{category_name.capitalize()}: {count} items")
            
            print(f"\nTotal items processed: {total_items}")
            print("Note: Only incomplete categories were processed")
            print("Note: Run master_catalog_updater.py to generate AI descriptions")
            
            return all_results
            
        except Exception as e:
            print(f"Error in smart multi-category scraping: {e}")
            return all_results
        finally:
            # Always close the browser
            self.close_browser()

    def clean_text(self, text):
        """Clean and normalize text data."""
        if not text:
            return ""
        return re.sub(r'\s+', ' ', text.strip())

def main():
    """Main function to run the scraper."""
    try:
        scraper = HavertysScraper()
        scraper.scrape_all_categories_smart()
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
    except Exception as e:
        print(f"Scraper failed: {e}")

if __name__ == "__main__":
    main()
