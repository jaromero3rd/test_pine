#!/usr/bin/env python3
"""
Interior Define Scraper
Scrapes product data from Interior Define's custom sofas page
"""

import os
import csv
import time
import requests
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from urllib.parse import urljoin, urlparse
import re


class InteriorDefineScraper:
    def __init__(self, base_output_dir: str = "InteriorDefine_catalog"):
        self.base_url = "https://www.interiordefine.com"
        self.base_output_dir = base_output_dir
        
        # Define category URLs
        self.categories = {
            'sofas': {
                'url': 'https://www.interiordefine.com/living/all-custom-sofas',
                'dir': 'sofas',
                'item_type': 'sofa'
            },
            'chairs': {
                'url': 'https://www.interiordefine.com/living/all-custom-chairs',
                'dir': 'chairs', 
                'item_type': 'chair'
            },
            'tables': {
                'url': 'https://www.interiordefine.com/living/all-tables',
                'dir': 'tables',
                'item_type': 'table'
            },
            'benches': {
                'url': 'https://www.interiordefine.com/living/all-custom-benches',
                'dir': 'benches',
                'item_type': 'bench'
            },
            'nightstands': {
                'url': 'https://www.interiordefine.com/bedroom/all-nightstands-dressers',
                'dir': 'nightstands',
                'item_type': 'nightstand'
            },
            'lighting': {
                'url': 'https://www.interiordefine.com/lighting',
                'dir': 'lighting',
                'item_type': 'lighting'
            },
            'rugs': {
                'url': 'https://www.interiordefine.com/rugs',
                'dir': 'rugs',
                'item_type': 'rug'
            }
        }
        
        # Create directories for all categories
        for category_info in self.categories.values():
            category_dir = os.path.join(base_output_dir, category_info['dir'])
            os.makedirs(category_dir, exist_ok=True)
        
        self.driver = self.setup_driver()

    def setup_driver(self):
        """Setup Chrome driver with options"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.implicitly_wait(10)
            return driver
        except Exception as e:
            print(f"❌ Error setting up Chrome driver: {e}")
            print("Please ensure ChromeDriver is installed and in PATH")
            return None

    def extract_product_links(self, soup: BeautifulSoup) -> list:
        """Extract product links from the sofas page"""
        products = []
        
        # Look for Interior Define product cards using the specific structure
        product_cards = soup.select('.item-root-2fi')
        
        if not product_cards:
            # Fallback selectors
            product_cards = soup.select('[class*="item-root"]')
        
        print(f"✅ Found {len(product_cards)} product cards")
        
        for card in product_cards:
            # Extract product link
            link_elem = card.find('a', href=True)
            if not link_elem:
                continue
                
            href = link_elem.get('href')
            if not href:
                continue
                
            # Convert relative URLs to absolute
            product_url = urljoin(self.base_url, href)
            
            # Skip category pages and non-product pages (but allow Interior Define product pages)
            skip_patterns = ['/category/', '/collection/']
            allow_patterns = ['/living/all-custom-sofas/', '/living/all-custom-chairs/', '/living/all-tables/', 
                            '/living/all-custom-benches/', '/bedroom/all-nightstands-dressers/', 
                            '/lighting/', '/rugs/']
            
            should_skip = any(skip in product_url.lower() for skip in skip_patterns)
            is_allowed = any(pattern in product_url.lower() for pattern in allow_patterns)
            
            if should_skip and not is_allowed:
                continue
            
            # Extract product name from the specific Interior Define structure
            product_name = self.extract_product_name_from_card(card)
            
            # Extract price from the card
            price = self.extract_price_from_card(card)
            
            # Extract image from the category page card
            image_url = self.extract_product_image_from_card(card)
            
            if product_name and product_url and len(product_name) > 3:
                products.append({
                    'name': product_name,
                    'url': product_url,
                    'price': price,
                    'image_url': image_url
                })
        
        return products

    def extract_product_name_from_card(self, card_element) -> str:
        """Extract product name from Interior Define product card"""
        # Look for the product name in the specific Interior Define structure
        name_elem = card_element.select_one('.item-name-1QF')
        if name_elem:
            return name_elem.get_text(strip=True)
        
        # Fallback: look for the product name content container
        name_container = card_element.select_one('.item-productNameContent-JLD')
        if name_container:
            name_elem = name_container.select_one('.item-name-1QF')
            if name_elem:
                return name_elem.get_text(strip=True)
        
        # Additional fallback selectors
        name_selectors = [
            '.item-name',
            '.product-name',
            '[class*="name"]'
        ]
        
        for selector in name_selectors:
            name_elem = card_element.select_one(selector)
            if name_elem:
                name_text = name_elem.get_text(strip=True)
                if name_text and len(name_text) > 3:
                    return name_text
        
        return None

    def extract_price_from_card(self, card_element) -> str:
        """Extract price from Interior Define product card"""
        # Look for the price in the specific Interior Define structure
        price_elem = card_element.select_one('.customPrice-root-3eY')
        if price_elem:
            # Extract all span elements and combine them
            spans = price_elem.find_all('span')
            price_text = ''.join([span.get_text(strip=True) for span in spans])
            if price_text and price_text.startswith('$'):
                return price_text
        
        # Fallback: look for any price-related elements
        price_selectors = [
            '.item-price-33x',
            '.customPrice-root',
            '[class*="price"]'
        ]
        
        for selector in price_selectors:
            price_elem = card_element.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                # Look for price pattern
                price_match = re.search(r'\$[\d,]+(?:\.\d{2})?', price_text)
                if price_match:
                    return price_match.group()
        
        return "N/A"

    def extract_product_name_from_link(self, link_element) -> str:
        """Extract product name from link element"""
        # Try different methods to get product name
        name_selectors = [
            '.product-name',
            '.product-title', 
            '.title',
            'h1', 'h2', 'h3', 'h4',
            '.name',
            '[data-testid*="name"]',
            '[data-testid*="title"]'
        ]
        
        # First try to find name in child elements
        for selector in name_selectors:
            name_elem = link_element.select_one(selector)
            if name_elem and name_elem.get_text(strip=True):
                return name_elem.get_text(strip=True)
        
        # If no child elements, try the link text itself
        link_text = link_element.get_text(strip=True)
        if link_text and len(link_text) > 3:
            return link_text
        
        # Try alt text from images
        img = link_element.find('img')
        if img and img.get('alt'):
            return img.get('alt')
        
        return None

    def extract_product_details(self, product_info: dict) -> dict:
        """Extract detailed product information from individual product page"""
        product_url = product_info['url']
        print(f"🔍 Scraping product details from: {product_url}")
        
        try:
            self.driver.get(product_url)
            time.sleep(3)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Use product name from card if available, otherwise extract from page
            product_name = product_info.get('name') or self.extract_product_name(soup)
            
            # Use price from card if available, otherwise extract from page
            price = product_info.get('price') or self.extract_price(soup)
            
            # Extract colors
            colors = self.extract_colors(soup)
            
            # Extract dimensions
            dimensions = self.extract_dimensions(soup)
            
            # Extract image
            image_url = self.extract_product_image(soup)
            
            # Download and save image
            image_filename = None
            if image_url:
                image_filename = self.download_image(image_url, product_name)
            
            return {
                'item_name': product_name,
                'price': price,
                'colors': colors,
                'dimensions': dimensions,
                'image_url': image_url,
                'image_filename': image_filename,
                'product_url': product_url,
                'item_type': 'sofa'
            }
            
        except Exception as e:
            print(f"❌ Error scraping product details: {e}")
            return None

    def extract_product_name(self, soup: BeautifulSoup) -> str:
        """Extract product name from product page"""
        name_selectors = [
            'h1',
            '.product-title',
            '.product-name',
            '[data-testid*="title"]',
            '[data-testid*="name"]',
            '.title',
            '.ProductTitle',
            '.ProductName'
        ]
        
        for selector in name_selectors:
            name_elem = soup.select_one(selector)
            if name_elem:
                name = name_elem.get_text(strip=True)
                if name and len(name) > 3:
                    return name
        
        # Fallback: try page title
        title = soup.find('title')
        if title:
            title_text = title.get_text(strip=True)
            # Clean up title (remove site name, etc.)
            if 'Interior Define' in title_text:
                title_text = title_text.replace('Interior Define', '').strip()
            if title_text:
                return title_text
        
        return "Unknown Product"

    def extract_price(self, soup: BeautifulSoup) -> str:
        """Extract price from product page"""
        price_selectors = [
            '.price',
            '.product-price',
            '[data-testid*="price"]',
            '.Price',
            '.ProductPrice',
            '.cost',
            '.amount'
        ]
        
        for selector in price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                # Look for price pattern
                price_match = re.search(r'\$[\d,]+(?:\.\d{2})?', price_text)
                if price_match:
                    return price_match.group()
        
        # Look for any text containing $ and numbers
        all_text = soup.get_text()
        price_matches = re.findall(r'\$[\d,]+(?:\.\d{2})?', all_text)
        if price_matches:
            # Return the first reasonable price found
            for price in price_matches:
                # Filter out very high prices that might be errors
                price_num = float(price.replace('$', '').replace(',', ''))
                if 100 <= price_num <= 50000:  # Reasonable furniture price range
                    return price
        
        return "N/A"

    def extract_colors(self, soup: BeautifulSoup) -> list:
        """Extract available colors from Interior Define product page"""
        colors = []
        
        # Interior Define specific color swatch selectors
        color_selectors = [
            '.chooseFabricViewStyles-switchColorImage',
            '.color-swatch',
            '.color-option',
            '.swatch',
            '[data-testid*="color"]',
            '.ColorSwatch',
            '.ColorOption',
            '.fabric-swatch',
            '.material-swatch'
        ]
        
        for selector in color_selectors:
            color_elements = soup.select(selector)
            for elem in color_elements:
                # Try to get color name from alt text or title
                color_name = elem.get('alt', '') or elem.get('title', '') or elem.get_text(strip=True)
                
                # Extract color name from filename if it's in the format "roy-005_perf-plush-velvet_mink.jpg"
                img_elem = elem.find('img')
                if img_elem and img_elem.get('src'):
                    src = img_elem.get('src')
                    if 'swatches' in src:
                        # Extract color name from filename like "roy-005_perf-plush-velvet_mink.jpg"
                        filename = src.split('/')[-1]
                        if '_' in filename:
                            parts = filename.split('_')
                            if len(parts) >= 2:
                                # Get the last part before .jpg (e.g., "mink")
                                color_part = parts[-1].replace('.jpg', '').replace('.png', '')
                                if color_part and len(color_part) > 2:
                                    color_name = color_part.title()
                
                if color_name and len(color_name) < 50 and color_name not in colors:
                    colors.append(color_name)
        
        # Look for RGB color values in style attributes
        rgb_elements = soup.select('[style*="background-color: rgb"]')
        for elem in rgb_elements:
            style = elem.get('style', '')
            if 'background-color: rgb' in style:
                # Extract RGB values and convert to color name
                rgb_match = re.search(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', style)
                if rgb_match:
                    r, g, b = map(int, rgb_match.groups())
                    color_name = self.rgb_to_color_name(r, g, b)
                    if color_name and color_name not in colors:
                        colors.append(color_name)
        
        # Look for color names in text
        color_keywords = ['black', 'white', 'gray', 'grey', 'brown', 'beige', 'blue', 'red', 'green', 'yellow', 'mink', 'roy', 'navy', 'cream']
        all_text = soup.get_text().lower()
        for keyword in color_keywords:
            if keyword in all_text and keyword.title() not in colors:
                colors.append(keyword.title())
        
        return list(set(colors)) if colors else []

    def rgb_to_color_name(self, r: int, g: int, b: int) -> str:
        """Convert RGB values to approximate color name"""
        # Common color mappings for furniture fabrics
        color_map = {
            (135, 123, 108): "Mink",  # From the example
            (255, 255, 255): "White",
            (0, 0, 0): "Black",
            (128, 128, 128): "Gray",
            (139, 69, 19): "Brown",
            (245, 245, 220): "Beige",
            (0, 0, 128): "Navy",
            (255, 228, 196): "Cream",
            (160, 82, 45): "Saddle Brown",
            (222, 184, 135): "Burlywood",
            (210, 180, 140): "Tan",
            (188, 143, 143): "Rosy Brown"
        }
        
        # Find closest color match
        for (cr, cg, cb), color_name in color_map.items():
            if abs(r - cr) < 30 and abs(g - cg) < 30 and abs(b - cb) < 30:
                return color_name
        
        # Fallback to generic color names based on RGB values
        if r > 200 and g > 200 and b > 200:
            return "Light"
        elif r < 50 and g < 50 and b < 50:
            return "Dark"
        elif r > g and r > b:
            return "Warm"
        elif g > r and g > b:
            return "Cool"
        else:
            return "Neutral"

    def extract_dimensions(self, soup: BeautifulSoup) -> dict:
        """Extract product dimensions from product page"""
        dimensions = {}
        
        # Look for dimension information
        dimension_selectors = [
            '.dimensions',
            '.specifications',
            '.product-specs',
            '[data-testid*="dimension"]',
            '.Dimensions',
            '.Specifications'
        ]
        
        for selector in dimension_selectors:
            dim_elem = soup.select_one(selector)
            if dim_elem:
                dim_text = dim_elem.get_text()
                # Extract width, height, depth
                width_match = re.search(r'width[:\s]*([\d.]+)', dim_text, re.IGNORECASE)
                height_match = re.search(r'height[:\s]*([\d.]+)', dim_text, re.IGNORECASE)
                depth_match = re.search(r'depth[:\s]*([\d.]+)', dim_text, re.IGNORECASE)
                
                if width_match:
                    dimensions['width'] = width_match.group(1)
                if height_match:
                    dimensions['height'] = height_match.group(1)
                if depth_match:
                    dimensions['depth'] = depth_match.group(1)
        
        return dimensions

    def extract_colors_and_dimensions(self, product_url: str) -> tuple:
        """Extract colors and dimensions from a specific product URL using Selenium"""
        try:
            print(f"🔍 Extracting details from: {product_url}")
            
            # Use Selenium to handle dynamic content
            driver = self.setup_driver()
            driver.get(product_url)
            
            # Wait for page to load
            time.sleep(3)
            
            # Wait for color swatches to load
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".chooseFabricViewStyles-switchColorImage"))
                )
            except:
                print("⚠️ Color swatches not found, trying alternative selectors")
            
            # Get page source after JavaScript execution
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Save debug HTML
            with open('debug_maxwell_selenium.html', 'w', encoding='utf-8') as f:
                f.write(soup.prettify())
            
            # Extract colors
            colors = self.extract_colors(soup)
            
            # Extract dimensions
            dimensions = self.extract_dimensions(soup)
            
            driver.quit()
            
            return colors, dimensions
            
        except Exception as e:
            print(f"❌ Error extracting details from {product_url}: {e}")
            if 'driver' in locals():
                driver.quit()
            return [], {}

    def extract_product_image(self, soup: BeautifulSoup) -> str:
        """Extract main product image URL"""
        image_selectors = [
            '.product-image img',
            '.main-image img',
            '.hero-image img',
            '[data-testid*="image"] img',
            '.ProductImage img',
            '.main-product-image img'
        ]
        
        for selector in image_selectors:
            img_elem = soup.select_one(selector)
            if img_elem and img_elem.get('src'):
                return urljoin(self.base_url, img_elem.get('src'))
        
        # Fallback: look for any large image
        images = soup.find_all('img')
        for img in images:
            src = img.get('src')
            if src and any(keyword in src.lower() for keyword in ['product', 'sofa', 'furniture']):
                return urljoin(self.base_url, src)
        
        return None

    def extract_product_image_from_card(self, card_element) -> str:
        """Extract product image URL from category page card"""
        # Look for the main product image in the card
        img_elem = card_element.select_one('img[src*="catalog/product"]')
        if img_elem and img_elem.get('src'):
            src = img_elem.get('src')
            # Convert relative URLs to absolute
            if src.startswith('/'):
                return f"https://www.interiordefine.com{src}"
            return src
        
        # Fallback: look for any image in the card
        img_elem = card_element.select_one('img')
        if img_elem and img_elem.get('src'):
            src = img_elem.get('src')
            if src.startswith('/'):
                return f"https://www.interiordefine.com{src}"
            return src
        
        return None

    def load_existing_products(self, category_dir: str) -> dict:
        """Load existing products from CSV to avoid duplicates"""
        csv_path = os.path.join(self.base_output_dir, category_dir, f"{category_dir}.csv")
        existing_products = {'names': set(), 'urls': set()}
        
        if os.path.exists(csv_path):
            try:
                with open(csv_path, 'r', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        name = row['item_name'].strip()
                        url = row.get('link', '').strip()
                        existing_products['names'].add(name)
                        if url:
                            existing_products['urls'].add(url)
                print(f"📋 Loaded {len(existing_products['names'])} existing products from CSV")
            except Exception as e:
                print(f"⚠️ Error loading existing products: {e}")
        
        return existing_products

    def is_duplicate_product(self, product: dict, existing_products: dict) -> bool:
        """Check if a product is a duplicate based on name or URL"""
        product_name = product.get('name', '').strip()
        product_url = product.get('url', '').strip()
        
        # Check if name already exists
        if product_name in existing_products['names']:
            return True
            
        # Check if URL already exists
        if product_url in existing_products['urls']:
            return True
            
        return False

    def scroll_and_load_more_products(self, driver, max_scrolls: int = 10) -> int:
        """Scroll down to load more products and return the number of products found"""
        initial_count = 0
        scroll_count = 0
        no_new_products_count = 0
        
        while scroll_count < max_scrolls and no_new_products_count < 3:
            # Get current product count
            current_cards = driver.find_elements(By.CSS_SELECTOR, '.item-root-2fi')
            current_count = len(current_cards)
            
            if scroll_count == 0:
                initial_count = current_count
                print(f"📊 Initial product count: {current_count}")
            
            # Scroll to bottom
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
            # Check if new products loaded
            new_cards = driver.find_elements(By.CSS_SELECTOR, '.item-root-2fi')
            new_count = len(new_cards)
            
            if new_count > current_count:
                print(f"📈 Loaded {new_count - current_count} more products (total: {new_count})")
                no_new_products_count = 0
            else:
                no_new_products_count += 1
                print(f"⏳ No new products loaded (attempt {no_new_products_count}/3)")
            
            scroll_count += 1
        
        final_cards = driver.find_elements(By.CSS_SELECTOR, '.item-root-2fi')
        final_count = len(final_cards)
        print(f"✅ Final product count: {final_count} (loaded {final_count - initial_count} additional products)")
        
        return final_count

    def download_image(self, image_url: str, product_name: str, category_dir: str = 'sofas') -> str:
        """Download and save product image"""
        try:
            # Clean product name for filename
            safe_name = re.sub(r'[^\w\s-]', '', product_name).strip()
            safe_name = re.sub(r'[-\s]+', '_', safe_name)
            
            # Get file extension
            parsed_url = urlparse(image_url)
            file_ext = os.path.splitext(parsed_url.path)[1] or '.jpg'
            
            filename = f"{safe_name}{file_ext}"
            filepath = os.path.join(self.base_output_dir, category_dir, filename)
            
            # Download image
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ Downloaded image: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ Error downloading image: {e}")
            return None

    def scrape_category_with_pagination(self, category: str, max_items: int = 50) -> list:
        """Scrape products from a specific Interior Define category with pagination support"""
        if category not in self.categories:
            print(f"❌ Unknown category: {category}")
            return []
        
        category_info = self.categories[category]
        print(f"🚀 Starting Interior Define {category} scraping with pagination (max {max_items} items)")
        
        if not self.driver:
            print("❌ Chrome driver not available. Please ensure ChromeDriver is installed.")
            return []
        
        # Load existing products to avoid duplicates
        existing_products = self.load_existing_products(category_info['dir'])
        
        all_products = []
        page = 1
        max_pages = 10  # Limit to prevent infinite loops
        
        while len(all_products) < max_items and page <= max_pages:
            print(f"📄 Scraping page {page}...")
            
            # Construct URL with page parameter
            if '?' in category_info['url']:
                page_url = f"{category_info['url']}&page={page}"
            else:
                page_url = f"{category_info['url']}?page={page}"
            
            try:
                # Load the page
                self.driver.get(page_url)
                print(f"⏳ Waiting for page {page} to load...")
                
                # Wait for specific elements to appear
                try:
                    WebDriverWait(self.driver, 20).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '[class*="item-root"]'))
                    )
                    print(f"✅ Product elements detected on page {page}")
                except:
                    print(f"⚠️ Product elements not detected on page {page}, continuing anyway...")
                
                # Wait additional time for content to fully load
                time.sleep(3)
                
                # Parse the page content
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                
                # Extract products from this page
                page_products = self.extract_product_links(soup)
                
                if not page_products:
                    print(f"❌ No products found on page {page}. Stopping pagination.")
                    break
                
                print(f"✅ Found {len(page_products)} products on page {page}")
                
                # Add new products (skip duplicates)
                new_products = []
                for product in page_products:
                    if not self.is_duplicate_product(product, existing_products) and len(all_products) < max_items:
                        new_products.append(product)
                        all_products.append(product)
                        # Add to existing products to prevent duplicates within the same run
                        existing_products['names'].add(product['name'])
                        existing_products['urls'].add(product['url'])
                
                if not new_products:
                    print(f"⏭️ All products on page {page} are duplicates. Stopping pagination.")
                    break
                
                print(f"📈 Added {len(new_products)} new products from page {page}")
                
                page += 1
                
            except Exception as e:
                print(f"❌ Error scraping page {page}: {e}")
                break
        
        print(f"✅ Found {len(all_products)} total products across {page-1} pages")
        
        # Process the products
        processed_products = []
        for i, product in enumerate(all_products[:max_items]):
            print(f"🔄 Processing product {i+1}/{min(len(all_products), max_items)}: {product['name']}")
            
            # Download image from category page
            image_filename = None
            if product.get('image_url'):
                image_filename = self.download_image(product['image_url'], product['name'], category_info['dir'])
            
            # For Interior Define, we'll extract colors and dimensions from the product page
            try:
                colors, dimensions = self.extract_colors_and_dimensions(product['url'])
            except Exception as e:
                print(f"⚠️ Error extracting details from {product['url']}: {e}")
                colors, dimensions = [], {}
            
            processed_product = {
                'catalog_number': f"ID-{category.upper()[:3]}-{i+1:03d}",
                'item_name': product['name'],
                'price': product['price'],
                'link': product['url'],
                'image_url': image_filename or '',
                'colors': ', '.join(colors) if colors else 'N/A',
                'dimensions': ', '.join([f"{k}: {v}" for k, v in dimensions.items()]) if dimensions else 'N/A',
                'item_type': category_info['item_type']
            }
            
            processed_products.append(processed_product)
            
            time.sleep(1)  # Be respectful to the server
        
        # Save to CSV
        self.save_to_csv(processed_products, category_info['dir'])
        
        print(f"✅ Scraping completed! Found {len(processed_products)} products")
        return processed_products

    def scrape_category(self, category: str, max_items: int = 50) -> list:
        """Scrape products from a specific Interior Define category"""
        if category not in self.categories:
            print(f"❌ Unknown category: {category}")
            return []
        
        category_info = self.categories[category]
        print(f"🚀 Starting Interior Define {category} scraping (max {max_items} items)")
        
        if not self.driver:
            print("❌ Chrome driver not available. Please ensure ChromeDriver is installed.")
            return []
        
        try:
            # Load the category page
            self.driver.get(category_info['url'])
            print("⏳ Waiting for page to load...")
            
            # Wait for specific elements to appear
            try:
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[class*="item-root"]'))
                )
                print("✅ Product elements detected")
            except:
                print("⚠️ Product elements not detected, continuing anyway...")
            
            # Wait additional time for content to fully load
            time.sleep(5)
            
            # Load existing products to avoid duplicates
            existing_products = self.load_existing_products(category_info['dir'])
            
            # Scroll and load more products using pagination
            self.scroll_and_load_more_products(self.driver, max_scrolls=15)
            
            # Get the page source after dynamic content loads
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Debug: Save HTML for inspection
            debug_file = f'debug_interior_define_{category}.html'
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            print(f"🔍 Saved page HTML to {debug_file} for inspection")
            
            # Extract products
            products = self.extract_product_links(soup)
            
            if not products:
                print("❌ No products found. The page might be using different selectors.")
                print("🔍 Check debug_interior_define.html to see the actual page structure")
                return []
            
            print(f"✅ Found {len(products)} products")
            
            # Process each product (limit to max_items and skip duplicates)
            processed_products = []
            skipped_count = 0
            processed_count = 0
            
            for i, product in enumerate(products):
                if processed_count >= max_items:
                    break
                    
                # Skip if product already exists
                if self.is_duplicate_product(product, existing_products):
                    skipped_count += 1
                    print(f"⏭️ Skipping duplicate: {product['name']}")
                    continue
                
                processed_count += 1
                print(f"🔄 Processing product {processed_count}/{max_items}: {product['name']}")
                
                # Download image from category page
                image_filename = None
                if product.get('image_url'):
                    image_filename = self.download_image(product['image_url'], product['name'], category_info['dir'])
                
                # For Interior Define, we'll extract colors and dimensions from the product page
                try:
                    colors, dimensions = self.extract_colors_and_dimensions(product['url'])
                except Exception as e:
                    print(f"⚠️ Error extracting details from {product['url']}: {e}")
                    colors, dimensions = [], {}
                
                processed_product = {
                    'catalog_number': f"ID-{category.upper()[:3]}-{processed_count:03d}",
                    'item_name': product['name'],
                    'price': product['price'],
                    'link': product['url'],
                    'image_url': image_filename or '',
                    'colors': ', '.join(colors) if colors else 'N/A',
                    'dimensions': ', '.join([f"{k}: {v}" for k, v in dimensions.items()]) if dimensions else 'N/A',
                    'item_type': category_info['item_type']
                }
                
                processed_products.append(processed_product)
                
                # Add to existing products to prevent duplicates within the same run
                existing_products['names'].add(product['name'])
                existing_products['urls'].add(product['url'])
                
                time.sleep(1)  # Be respectful to the server
            
            if skipped_count > 0:
                print(f"⏭️ Skipped {skipped_count} duplicate products")
            
            # Save to CSV
            self.save_to_csv(processed_products, category_info['dir'])
            
            print(f"✅ Scraping completed! Found {len(processed_products)} products")
            return processed_products
            
        except Exception as e:
            print(f"❌ Error during scraping: {e}")
            return []

    def save_to_csv(self, products: list, category_dir: str):
        """Save scraped products to CSV file (append mode to avoid duplicates)"""
        csv_path = os.path.join(self.base_output_dir, category_dir, f"{category_dir}.csv")
        
        # Use the exact same fieldnames and order as Havertys and BoConcept
        fieldnames = ['catalog_number', 'item_name', 'price', 'link', 'image_url', 
                     'colors', 'dimensions', 'item_type']
        
        # Check if file exists to determine write mode
        file_exists = os.path.exists(csv_path)
        
        with open(csv_path, 'a' if file_exists else 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Only write header if file is new
            if not file_exists:
                writer.writeheader()
            
            for i, product in enumerate(products, 1):
                # Convert to match Havertys/BoConcept format exactly
                csv_row = {
                    'catalog_number': product['catalog_number'],
                    'item_name': product['item_name'],
                    'price': product['price'],
                    'link': product['link'],
                    'image_url': product['image_url'],
                    'colors': product['colors'],
                    'dimensions': product['dimensions'],
                    'item_type': product['item_type']
                }
                writer.writerow(csv_row)
        
        print(f"✅ Saved {len(products)} products to {csv_path}")

    def run(self, category: str = 'sofas', max_items: int = 50):
        """Run the scraper for a specific category with pagination"""
        products = self.scrape_category_with_pagination(category, max_items)
        if products:
            print(f"✅ Successfully scraped {len(products)} {category}")
        else:
            print(f"❌ No {category} were scraped")
        
        if self.driver:
            self.driver.quit()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape Interior Define products')
    parser.add_argument('--category', type=str, default='sofas',
                       choices=['sofas', 'chairs', 'tables', 'benches', 'nightstands', 'lighting', 'rugs'],
                       help='Category to scrape (default: sofas)')
    parser.add_argument('--max-items', type=int, default=50, 
                       help='Maximum number of items to scrape (default: 50)')
    parser.add_argument('--output-dir', type=str, default='InteriorDefine_catalog',
                       help='Output directory for scraped data (default: InteriorDefine_catalog)')
    
    args = parser.parse_args()
    
    scraper = InteriorDefineScraper(base_output_dir=args.output_dir)
    scraper.run(category=args.category, max_items=args.max_items)


if __name__ == "__main__":
    main()
