#!/usr/bin/env python3
"""
BoConcept Furniture Scraper

Scrapes furniture data from BoConcept website:
- Product names, images, colors, dimensions
- Handles dynamic content loading
- Saves data to CSV and images to folders
"""

import os
import csv
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urljoin, urlparse
import re
from typing import List, Dict, Optional


class BoConceptScraper:
    """Scraper for BoConcept furniture website."""
    
    def __init__(self, base_output_dir: str = "BoConcept_catalog", category: str = "sofas"):
        """Initialize the BoConcept scraper."""
        self.base_url = "https://www.boconcept.com"
        self.category = category
        self.category_url = f"https://www.boconcept.com/en-us/shop/{category}/"
        self.base_output_dir = base_output_dir
        self.category_dir = os.path.join(base_output_dir, category)
        
        # Create directories
        os.makedirs(self.category_dir, exist_ok=True)
        
        # Setup Selenium
        self.driver = None
        self.setup_driver()
        
    def setup_driver(self):
        """Setup Chrome driver with options."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def close_driver(self):
        """Close the Chrome driver."""
        if self.driver:
            self.driver.quit()
    
    def get_page_content(self, url: str) -> Optional[BeautifulSoup]:
        """Get page content using Selenium."""
        try:
            print(f"🔄 Loading page: {url}")
            self.driver.get(url)
            
            # Wait for content to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Wait a bit more for dynamic content
            time.sleep(3)
            
            # Scroll to load lazy content
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Try to wait for color options to load
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "button[class*='Color']"))
                )
            except:
                pass  # Continue if color elements don't load
            
            # Get page source and parse with BeautifulSoup
            page_source = self.driver.page_source
            return BeautifulSoup(page_source, 'html.parser')
            
        except Exception as e:
            print(f"❌ Error loading page {url}: {e}")
            return None
    
    def extract_product_links(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract product links and basic info from the sofas page."""
        products = []
        
        # Extract product links and get prices from category page
        selectors = [
            'a[href*="/p/"]',  # Product pages
            '.ProductCard a',  # Product card links
            'a[href*="aarhus"]',  # Specific product links
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href and '/p/' in href:
                    full_url = urljoin(self.base_url, href)
                    if not any(p['url'] == full_url for p in products):  # Avoid duplicates
                        # Try to find price and name near this link on the category page
                        price = "N/A"
                        name = "Unknown"
                        
                        # Look for the price and name in the same product card container
                        current_element = link
                        for _ in range(5):  # Go up max 5 levels to find the product card
                            if current_element:
                                # Look for price in current element or its siblings
                                price_elem = current_element.select_one('.ProductCard_price__nKioQ')
                                if not price_elem:
                                    # Look in parent and siblings
                                    if current_element.parent:
                                        price_elem = current_element.parent.select_one('.ProductCard_price__nKioQ')
                                
                                if price_elem:
                                    price_text = price_elem.get_text(strip=True)
                                    if '$' in price_text:
                                        price = price_text
                                
                                # Look for product name using the correct BoConcept selector
                                name_elem = current_element.select_one('.ProductCard_name__Cc2fR')
                                if not name_elem:
                                    # Look in parent and siblings
                                    if current_element.parent:
                                        name_elem = current_element.parent.select_one('.ProductCard_name__Cc2fR')
                                
                                if name_elem:
                                    name_text = name_elem.get_text(strip=True)
                                    if name_text and name_text != "Unknown" and len(name_text) > 3:
                                        name = name_text
                                
                                # If we found both price and name, we can break
                                if price != "N/A" and name != "Unknown":
                                    break
                                
                                current_element = current_element.parent
                            else:
                                break
                        
                        products.append({
                            'url': full_url,
                            'name': name,
                            'price': price
                        })
        
        print(f"📋 Found {len(products)} product links")
        
        # Debug: Print first few product names to verify extraction
        for i, product in enumerate(products[:5]):
            print(f"   Product {i+1}: '{product['name']}' - {product['price']}")
        
        return products
    
    def extract_product_name(self, soup: BeautifulSoup) -> str:
        """Extract full product name from product page title."""
        # Get the full product name from the page title
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.get_text(strip=True)
            print(f"🔍 DEBUG: Page title: {title_text}")
            
            # Extract the full product name from title
            # BoConcept titles are usually in format: "Product Name | Category | Designer | BoConcept"
            # We want the first part which is the full product name
            if ' | ' in title_text:
                full_name = title_text.split(' | ')[0]
                print(f"🔍 DEBUG: Extracted full name: {full_name}")
                return full_name
            elif ' - ' in title_text:
                full_name = title_text.split(' - ')[0]
                print(f"🔍 DEBUG: Extracted full name: {full_name}")
                return full_name
            else:
                print(f"🔍 DEBUG: Using full title as name: {title_text}")
                return title_text
        
        # Fallback: try h1 element
        h1_element = soup.find('h1')
        if h1_element:
            name = h1_element.get_text(strip=True)
            print(f"🔍 DEBUG: H1 fallback name: {name}")
            return name
        
        # Final fallback: try to get from URL path
        current_url = self.driver.current_url if self.driver else ""
        if "/p/" in current_url:
            # Extract from URL path
            url_parts = current_url.split("/p/")[1].split("/")[0]
            if url_parts:
                fallback_name = url_parts.replace("-", " ").title()
                print(f"🔍 DEBUG: URL fallback name: {fallback_name}")
                return fallback_name
        
        print("🔍 DEBUG: No name found, using 'Unknown'")
        return "Unknown"
    
    def extract_product_image(self, soup: BeautifulSoup, product_name: str) -> Optional[str]:
        """Extract and download product image."""
        # Look for product images
        img_selectors = [
            'img[alt*="sofa"]',
            '.ProductImage img',
            '.ProductCard img',
            'img[src*="assets.boconcept.com"]',
            '.product-image img'
        ]
        
        for selector in img_selectors:
            img_elements = soup.select(selector)
            for img in img_elements:
                src = img.get('src') or img.get('data-src')
                if src and 'boconcept.com' in src:
                    # Get the highest quality image
                    if 'width=' in src:
                        # Replace width parameter with higher value
                        src = re.sub(r'width=\d+', 'width=1024', src)
                    
                    try:
                        # Download image
                        response = requests.get(src, timeout=10)
                        if response.status_code == 200:
                            # Clean filename
                            safe_name = re.sub(r'[^\w\s-]', '', product_name)
                            safe_name = re.sub(r'[-\s]+', '_', safe_name)
                            filename = f"{safe_name}.jpg"
                            filepath = os.path.join(self.category_dir, filename)
                            
                            with open(filepath, 'wb') as f:
                                f.write(response.content)
                            
                            print(f"✅ Downloaded image: {filename}")
                            return filepath
                    except Exception as e:
                        print(f"❌ Error downloading image: {e}")
                        continue
        
        print(f"⚠️  No image found for: {product_name}")
        return None
    
    def extract_price(self, soup: BeautifulSoup, product_url: str = "") -> str:
        """Price is already extracted from category page - no need to extract from product page."""
        return 'N/A'  # Price comes from category page
    
    def extract_colors(self, driver) -> List[str]:
        """Extract available colors from product page by clicking interactive elements."""
        colors = []
        
        # Skip color extraction for categories that don't have colors (like lamps)
        categories_without_colors = ['lamps', 'lighting', 'rugs', 'accessories']
        if self.category.lower() in categories_without_colors:
            print(f"🔍 DEBUG: Skipping color extraction for {self.category} category")
            return colors
        
        try:
            print("🔍 DEBUG: Starting color extraction...")
            
            # First, try to click the upholstery/variant button to reveal colors
            upholstery_button = None
            try:
                print("🔍 DEBUG: Looking for upholstery button...")
                
                # Debug: Let's see what buttons are actually on the page
                all_buttons = driver.find_elements(By.TAG_NAME, "button")
                print(f"🔍 DEBUG: Found {len(all_buttons)} buttons on page")
                for i, btn in enumerate(all_buttons[:20]):  # Show first 20 buttons
                    try:
                        btn_text = btn.text.strip()
                        btn_class = btn.get_attribute('class')
                        btn_id = btn.get_attribute('id')
                        btn_data_testid = btn.get_attribute('data-testid')
                        print(f"🔍 DEBUG: Button {i}: text='{btn_text}', class='{btn_class}', id='{btn_id}', data-testid='{btn_data_testid}'")
                    except:
                        pass
                
                # Look for the upholstery button - try different selectors
                upholstery_selectors = [
                    '.VariantOptionSidebarToggle_button__GdE0k',
                    'button[class*="VariantOptionSidebarToggle"]',
                    'button:contains("Upholstery")',
                    'button:contains("+ 102")',
                    'button:contains("+ 99")',
                    'button[class*="FilterToggle"]',
                    'button[class*="Filter"]',
                    'button[class*="Toggle"]'
                ]
                
                for selector in upholstery_selectors:
                    try:
                        upholstery_button = driver.find_element(By.CSS_SELECTOR, selector)
                        if upholstery_button.is_displayed():
                            print(f"🔍 DEBUG: Found upholstery button with selector: {selector}")
                            break
                    except:
                        continue
                
                if upholstery_button:
                    print("🔍 DEBUG: Clicking upholstery button...")
                    driver.execute_script("arguments[0].click();", upholstery_button)
                    time.sleep(5)  # Wait longer for the panel to open
                    
                    # Debug: Check if the panel opened
                    print("🔍 DEBUG: Checking if panel opened...")
                    all_elements = driver.find_elements(By.CSS_SELECTOR, "*")
                    filter_elements = []
                    for elem in all_elements:
                        try:
                            elem_class = elem.get_attribute('class')
                            if elem_class and ('Filter' in elem_class or 'Color' in elem_class):
                                filter_elements.append(elem)
                        except:
                            pass
                    print(f"🔍 DEBUG: Found {len(filter_elements)} elements with 'Filter' or 'Color' in class")
                    for i, elem in enumerate(filter_elements[:5]):
                        try:
                            elem_class = elem.get_attribute('class')
                            elem_text = elem.text.strip()
                            print(f"🔍 DEBUG: Element {i}: class='{elem_class}', text='{elem_text}'")
                        except:
                            pass
                    
                    # Now look for the "Color." button to open the overlay
                    print("🔍 DEBUG: Looking for Color. button...")
                    
                    # Wait a bit more for the panel to fully load
                    time.sleep(2)
                    
                    # Look for the Color. button - try multiple approaches
                    color_button = None
                    
                    # First try to find by text content
                    try:
                        color_button = driver.find_element(By.XPATH, "//span[contains(text(), 'Color.')]")
                        if color_button.is_displayed():
                            print("🔍 DEBUG: Found Color. button with XPath")
                    except:
                        pass
                    
                    # If not found, try other selectors
                    if not color_button:
                        color_button_selectors = [
                            'button:contains("Color.")',
                            'span:contains("Color.")',
                            '[class*="FilterSelect"]:contains("Color.")',
                            'button[class*="Filter"]:contains("Color")',
                            'span[class*="Filter"]:contains("Color")',
                            '.FilterSelect_innerButton__LagmS',
                            'button[class*="FilterSelect"]'
                        ]
                        
                        for selector in color_button_selectors:
                            try:
                                color_button = driver.find_element(By.CSS_SELECTOR, selector)
                                if color_button.is_displayed():
                                    print(f"🔍 DEBUG: Found Color. button with selector: {selector}")
                                    break
                            except:
                                continue
                    
                    # Debug: Let's see what buttons are available after clicking upholstery
                    if not color_button:
                        print("🔍 DEBUG: No Color. button found, listing all available buttons...")
                        all_buttons = driver.find_elements(By.TAG_NAME, "button")
                        for i, btn in enumerate(all_buttons):
                            try:
                                btn_text = btn.text.strip()
                                if btn_text and ('color' in btn_text.lower() or 'filter' in btn_text.lower()):
                                    print(f"🔍 DEBUG: Potential color button {i}: text='{btn_text}'")
                            except:
                                pass
                    
                    if color_button:
                        print("🔍 DEBUG: Clicking Color. button...")
                        driver.execute_script("arguments[0].click();", color_button)
                        time.sleep(3)  # Wait for overlay to open
                        
                        # Now look for the color overlay and extract colors
                        print("🔍 DEBUG: Looking for color overlay...")
                        color_elements = driver.find_elements(By.CSS_SELECTOR, '.ColorToggleButton_label__qu1x_')
                        print(f"🔍 DEBUG: Found {len(color_elements)} color elements in overlay")
                        for element in color_elements:
                            color_text = element.text.strip()
                            if color_text and color_text not in colors:
                                colors.append(color_text)
                                print(f"🔍 DEBUG: Added color from overlay: {color_text}")
                        
                        # Close the overlay by clicking the close button
                        try:
                            close_button = driver.find_element(By.CSS_SELECTOR, '.VariantOptionActionBar_closeButton__TMBVc')
                            if close_button.is_displayed():
                                driver.execute_script("arguments[0].click();", close_button)
                                print("🔍 DEBUG: Closed color overlay")
                                time.sleep(1)
                        except:
                            pass
                    else:
                        print("🔍 DEBUG: No Color. button found")
                else:
                    print("🔍 DEBUG: No upholstery button found")
            
            except Exception as e:
                print(f"⚠️  Error clicking color buttons: {e}")
            
            # Fallback: try to find colors without clicking
            if not colors:
                print("🔍 DEBUG: Trying fallback color extraction...")
                try:
                    color_elements = driver.find_elements(By.CSS_SELECTOR, '.ColorToggleButton_label__qu1x_')
                    print(f"🔍 DEBUG: Fallback found {len(color_elements)} color elements")
                    for element in color_elements:
                        color_text = element.text.strip()
                        if color_text and color_text not in colors:
                            colors.append(color_text)
                            print(f"🔍 DEBUG: Fallback added color: {color_text}")
                except Exception as e:
                    print(f"🔍 DEBUG: Fallback failed: {e}")
                
                # Try to find colors in any text on the page
                if not colors:
                    print("🔍 DEBUG: Trying to find colors in page text...")
                    page_text = driver.page_source
                    
                    # Look for the specific colors mentioned by the user
                    expected_colors = ['Beige', 'Yellow', 'Brown', 'Green', 'White', 'Red', 'Blue', 'Dark Gray', 'Light Gray', 'Gray', 'Black']
                    
                    for color in expected_colors:
                        # Look for color in various contexts
                        color_lower = color.lower()
                        if color_lower in page_text.lower():
                            colors.append(color)
                            print(f"🔍 DEBUG: Found expected color: {color}")
                    
                    # If we found some colors, use them; otherwise try the old method
                    if not colors:
                        print("🔍 DEBUG: No expected colors found, trying pattern matching...")
                        # Look for more specific color patterns in the page
                        color_patterns = [
                            r'"([A-Za-z]+)"\s*:\s*"[^"]*color[^"]*"',  # JSON-like color definitions
                            r'color[^"]*"([A-Za-z]+)"',  # Color followed by name
                            r'([A-Za-z]+)\s+[Cc]openhagen',  # Color + Copenhagen fabric
                            r'([A-Za-z]+)\s+[Ff]abric',  # Color + fabric
                            r'([A-Za-z]+)\s+[Mm]aterial',  # Color + material
                        ]
                        
                        for pattern in color_patterns:
                            matches = re.findall(pattern, page_text, re.IGNORECASE)
                            for match in matches:
                                if isinstance(match, tuple):
                                    color = match[0]
                                else:
                                    color = match
                                if color and len(color) > 2 and color.lower() not in ['the', 'and', 'for', 'with', 'from', 'this', 'that']:
                                    colors.append(color.capitalize())
                                    print(f"🔍 DEBUG: Found color with pattern: {color.capitalize()}")
                        
                        # If still no colors, try a more conservative approach
                        if not colors:
                            print("🔍 DEBUG: Trying conservative color extraction...")
                            # Look for specific color mentions that are likely product colors
                            conservative_colors = ['beige', 'white', 'black', 'gray', 'grey', 'brown', 'blue', 'red', 'green', 'yellow', 'orange', 'purple', 'pink', 'navy', 'cream', 'tan', 'charcoal', 'ochre']
                            for color in conservative_colors:
                                # Look for color in specific contexts
                                if f'"{color}"' in page_text.lower() or f"'{color}'" in page_text.lower():
                                    colors.append(color.capitalize())
                                    print(f"🔍 DEBUG: Found color in quotes: {color.capitalize()}")
                                elif f'{color} copenhagen' in page_text.lower() or f'{color} fabric' in page_text.lower():
                                    colors.append(color.capitalize())
                                    print(f"🔍 DEBUG: Found color with fabric: {color.capitalize()}")
            
            # Filter out common UI elements that aren't colors
            filtered_colors = []
            ui_elements_to_exclude = [
                'show more', 'add to cart', 'change', 'select', 'choose', 'more',
                '+ 102', '+ 99', '+ 50', '+ 25', 'more colors', 'view all',
                'upholstery', 'fabric', 'material', 'option', 'variant',
                'checkbox', 'coioverlay', 'certified', 'free', 'protect', 'light',
                'copenhagen', 'frisco', 'lazio', 'arezzo', 'velvet', 'chenille',
                'faulty', 'nani', 'napoli', 'bristol', 'tomelilla', 'skagen',
                'tuscany', 'ravello', 'avellino', 'capri', 'rimini', 'bologna',
                'lucca', 'look', 'recycled', 'italian', 'timeless', 'quality',
                'raw', 'right', 'chemical', 'all', 'luxurious', 'eraw', 'made',
                'woven', 'polyester', 'boucle'
            ]
            
            # Only keep actual color names
            actual_colors = ['white', 'black', 'gray', 'grey', 'brown', 'blue', 'red', 
                           'green', 'yellow', 'orange', 'purple', 'pink', 'navy', 
                           'cream', 'tan', 'charcoal', 'beige', 'ochre']
            
            for color in colors:
                color_lower = color.lower()
                if color_lower in actual_colors:
                    filtered_colors.append(color)
                    print(f"🔍 DEBUG: Kept actual color: {color}")
                elif not any(ui_element in color_lower for ui_element in ui_elements_to_exclude):
                    if len(color) > 1 and len(color) < 50:  # Reasonable color name length
                        filtered_colors.append(color)
                        print(f"🔍 DEBUG: Kept filtered color: {color}")
            
            # Remove duplicates while preserving order
            unique_colors = []
            for color in filtered_colors:
                if color not in unique_colors:
                    unique_colors.append(color)
            
            print(f"🔍 DEBUG: Final colors: {unique_colors}")
            return unique_colors
            
        except Exception as e:
            print(f"❌ Error extracting colors: {e}")
            return []
    
    def extract_dimensions(self, driver) -> Dict[str, str]:
        """Extract product dimensions by clicking the Measurements button."""
        dimensions = {}
        
        try:
            print("🔍 DEBUG: Starting dimension extraction...")
            
            # Look for the Measurements button
            measurements_button = None
            try:
                measurements_button = driver.find_element(By.CSS_SELECTOR, '.page_questionButton__ifeyg')
                if measurements_button.is_displayed():
                    print("🔍 DEBUG: Found Measurements button")
                else:
                    measurements_button = None
            except:
                print("🔍 DEBUG: Measurements button not found with primary selector")
            
            # Try alternative selectors
            if not measurements_button:
                alternative_selectors = [
                    'button:contains("Measurements")',
                    'button[class*="questionButton"]',
                    'button[class*="Measurements"]'
                ]
                
                for selector in alternative_selectors:
                    try:
                        measurements_button = driver.find_element(By.CSS_SELECTOR, selector)
                        if measurements_button.is_displayed():
                            print(f"🔍 DEBUG: Found Measurements button with selector: {selector}")
                            break
                    except:
                        continue
            
            if measurements_button:
                print("🔍 DEBUG: Clicking Measurements button...")
                driver.execute_script("arguments[0].click();", measurements_button)
                time.sleep(3)  # Wait for sidebar to open
                
                # Look for the measurements sidebar
                print("🔍 DEBUG: Looking for measurements sidebar...")
                sidebar_elements = driver.find_elements(By.CSS_SELECTOR, '.MeasurementsSidebar_container__MWhhy')
                print(f"🔍 DEBUG: Found {len(sidebar_elements)} sidebar elements")
                
                if sidebar_elements:
                    # Extract dimensions from the sidebar
                    sidebar = sidebar_elements[0]
                    
                    # Wait a bit more for content to load
                    time.sleep(2)
                    
                    # Debug: Let's see what's in the sidebar
                    print("🔍 DEBUG: Sidebar HTML content:")
                    sidebar_html = sidebar.get_attribute('outerHTML')
                    print(sidebar_html[:500] + "..." if len(sidebar_html) > 500 else sidebar_html)
                    
                    # Try to extract text using JavaScript
                    print("🔍 DEBUG: Trying JavaScript text extraction...")
                    try:
                        js_text = driver.execute_script("""
                            var sidebar = arguments[0];
                            var dtElements = sidebar.querySelectorAll('dt');
                            var results = [];
                            for (var i = 0; i < dtElements.length; i++) {
                                var dt = dtElements[i];
                                var p = dt.querySelector('p');
                                var text = p ? p.textContent.trim() : dt.textContent.trim();
                                results.push(text);
                            }
                            return results;
                        """, sidebar)
                        print(f"🔍 DEBUG: JavaScript extracted text: {js_text}")
                        
                        # Now try to match the text with dimensions
                        for i, text in enumerate(js_text):
                            if text in ['Width', 'Height', 'Depth']:
                                # Find the corresponding dd element
                                dd_elements = sidebar.find_elements(By.CSS_SELECTOR, 'dd')
                                if i < len(dd_elements):
                                    dd_text = driver.execute_script("""
                                        var dd = arguments[0];
                                        var p = dd.querySelector('p');
                                        return p ? p.textContent.trim() : dd.textContent.trim();
                                    """, dd_elements[i])
                                    if dd_text:
                                        dimensions[text.lower()] = dd_text
                                        print(f"🔍 DEBUG: Added {text}: {dd_text}")
                    except Exception as e:
                        print(f"🔍 DEBUG: JavaScript extraction failed: {e}")
                    
                    # Look for specific dimension keys and values
                    dimension_keys = ['Width', 'Height', 'Depth']
                    
                    for key in dimension_keys:
                        try:
                            # Find the dt element with the key
                            key_elements = sidebar.find_elements(By.XPATH, f".//dt//p[contains(text(), '{key}')]")
                            print(f"🔍 DEBUG: Looking for {key}, found {len(key_elements)} elements")
                            
                            if key_elements:
                                # Find the corresponding dd element with the value
                                key_element = key_elements[0]
                                # Get the parent dt element
                                dt_element = key_element.find_element(By.XPATH, "./..")
                                # Find the next sibling dd element
                                dd_element = dt_element.find_element(By.XPATH, "./following-sibling::dd")
                                # Get the value from the dd element
                                value_element = dd_element.find_element(By.CSS_SELECTOR, 'p')
                                value = value_element.text.strip()
                                
                                if value:
                                    dimensions[key.lower()] = value
                                    print(f"🔍 DEBUG: Found {key}: {value}")
                        except Exception as e:
                            print(f"🔍 DEBUG: Error extracting {key}: {e}")
                    
                    # Also try a simpler approach - look for all dt/dd pairs
                    print("🔍 DEBUG: Trying simpler approach...")
                    try:
                        dt_elements = sidebar.find_elements(By.CSS_SELECTOR, 'dt')
                        print(f"🔍 DEBUG: Found {len(dt_elements)} dt elements")
                        for dt in dt_elements:
                            # Get text from the p element inside dt
                            try:
                                p_element = dt.find_element(By.CSS_SELECTOR, 'p')
                                dt_text = p_element.text.strip()
                                print(f"🔍 DEBUG: DT p element text: '{dt_text}'")
                            except Exception as e:
                                dt_text = dt.text.strip()
                                print(f"🔍 DEBUG: DT direct text: '{dt_text}' (error: {e})")
                            
                            print(f"🔍 DEBUG: DT text: '{dt_text}'")
                            if dt_text in ['Width', 'Height', 'Depth']:
                                # Find the next dd element
                                dd_element = dt.find_element(By.XPATH, "./following-sibling::dd")
                                # Get text from the p element inside dd
                                try:
                                    dd_p_element = dd_element.find_element(By.CSS_SELECTOR, 'p')
                                    dd_text = dd_p_element.text.strip()
                                    print(f"🔍 DEBUG: DD p element text: '{dd_text}'")
                                except Exception as e:
                                    dd_text = dd_element.text.strip()
                                    print(f"🔍 DEBUG: DD direct text: '{dd_text}' (error: {e})")
                                
                                print(f"🔍 DEBUG: DD text: '{dd_text}'")
                                if dd_text:
                                    dimensions[dt_text.lower()] = dd_text
                                    print(f"🔍 DEBUG: Added {dt_text}: {dd_text}")
                    except Exception as e:
                        print(f"🔍 DEBUG: Error in simpler approach: {e}")
                    
                    # Close the sidebar by clicking outside or finding a close button
                    try:
                        # Try to find a close button
                        close_button = driver.find_element(By.CSS_SELECTOR, '.MeasurementsSidebar_closeButton, button[aria-label="Close"], button[title="Close"]')
                        if close_button.is_displayed():
                            driver.execute_script("arguments[0].click();", close_button)
                            print("🔍 DEBUG: Closed measurements sidebar")
                    except:
                        # If no close button, try clicking outside
                        try:
                            driver.execute_script("document.body.click();")
                            print("🔍 DEBUG: Clicked outside to close sidebar")
                        except:
                            pass
                    
                    time.sleep(1)
                else:
                    print("🔍 DEBUG: No measurements sidebar found")
            else:
                print("🔍 DEBUG: No Measurements button found")
                
        except Exception as e:
            print(f"❌ Error extracting dimensions: {e}")
        
        return dimensions
    
    def debug_page_content(self, soup: BeautifulSoup, url: str):
        """Debug function to see what's actually on the page."""
        print(f"\n🔍 DEBUG: Page content for {url}")
        
        # Check for common BoConcept elements
        debug_selectors = [
            'h1',
            '.ProductCard_price__nKioQ',
            '[data-testid="product-title"]',
            '.ColorList_button__ozD5k',
            '.ColorToggleButton_label__qu1x_',
            'button[class*="Color"]',
            '.dimensions',
            '.specifications',
            'dl.details-notmattress',
            '.product-details',
            '.specs',
            '.measurements'
        ]
        
        for selector in debug_selectors:
            elements = soup.select(selector)
            if elements:
                print(f"   Found {len(elements)} elements with selector: {selector}")
                for i, elem in enumerate(elements[:3]):  # Show first 3
                    text = elem.get_text(strip=True)[:100]
                    print(f"     {i+1}: {text}")
            else:
                print(f"   No elements found with selector: {selector}")
        
        # Check page title
        title = soup.find('title')
        if title:
            print(f"   Page title: {title.get_text(strip=True)}")
        
        print()

    def scrape_product(self, product_url: str) -> Dict[str, any]:
        """Scrape individual product page."""
        print(f"\n🔍 Scraping product: {product_url}")
        
        soup = self.get_page_content(product_url)
        if not soup:
            return None
        
        # Debug page content
        self.debug_page_content(soup, product_url)
        
        # Extract product data
        product_data = {
            'name': self.extract_product_name(soup),
            'url': product_url,
            'image_path': None,
            'colors': [],
            'dimensions': {},
            'price': 'N/A'  # Price comes from category page
        }
        
        # Extract image
        product_data['image_path'] = self.extract_product_image(soup, product_data['name'])
        
        # Extract colors using Selenium for interactive elements
        product_data['colors'] = self.extract_colors(self.driver)
        
        # Extract dimensions using Selenium for interactive elements
        product_data['dimensions'] = self.extract_dimensions(self.driver)
        
        print(f"✅ Scraped: {product_data['name']}")
        print(f"   Colors: {', '.join(product_data['colors']) if product_data['colors'] else 'None'}")
        print(f"   Dimensions: {product_data['dimensions']}")
        
        return product_data
    
    def load_more_products(self, max_items: int = 100) -> List[Dict[str, str]]:
        """Load more products by clicking the 'Load more products' button."""
        print(f"🔄 Loading products with pagination (target: {max_items} items)")
        
        # Navigate to category page using Selenium
        self.driver.get(self.category_url)
        time.sleep(3)  # Wait for initial load
        
        all_products = []
        load_more_attempts = 0
        max_load_attempts = 20  # Prevent infinite loops
        
        while load_more_attempts < max_load_attempts:
            # Check current number of products on the page
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            current_products = self.extract_product_links(soup)
            current_count = len(current_products)
            
            print(f"   📊 Found {current_count} products on page...")
            
            # Check if we have enough products
            if current_count >= max_items:
                print(f"   ✅ Reached target of {max_items} products")
                break
                
            # Look for "Load more products" button
            try:
                # Try multiple selectors for the load more button
                load_more_button = None
                
                # First try: Look for button with specific text
                try:
                    load_more_button = self.driver.find_element(
                        By.XPATH, 
                        '//button[contains(text(), "Load more products")]'
                    )
                except:
                    pass
                
                # Second try: Look for button with class containing "Button"
                if not load_more_button:
                    try:
                        load_more_button = self.driver.find_element(
                            By.CSS_SELECTOR, 
                            'button[class*="Button"]'
                        )
                        # Check if this button contains the right text
                        if "Load more" not in load_more_button.text:
                            load_more_button = None
                    except:
                        pass
                
                # Third try: Look for any button that might be the load more button
                if not load_more_button:
                    try:
                        buttons = self.driver.find_elements(By.TAG_NAME, "button")
                        for button in buttons:
                            if "Load more" in button.text or "load more" in button.text.lower():
                                load_more_button = button
                                break
                    except:
                        pass
                
                if load_more_button and load_more_button.is_enabled():
                    print(f"   🔄 Clicking 'Load more products' button (attempt {load_more_attempts + 1})")
                    self.driver.execute_script("arguments[0].click();", load_more_button)
                    time.sleep(3)  # Wait for new products to load
                    load_more_attempts += 1
                else:
                    print("   ⚠️  Load more button not found or disabled")
                    break
                    
            except Exception as e:
                print(f"   ⚠️  Could not find or click load more button: {e}")
                break
        
        # Extract final product list
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        all_products = self.extract_product_links(soup)
        
        print(f"✅ Loaded {len(all_products)} total products")
        return all_products[:max_items]  # Return up to max_items

    def get_existing_products(self) -> set:
        """Get set of existing product names from CSV file."""
        csv_path = os.path.join(self.category_dir, f"{self.category}.csv")
        existing_products = set()
        
        if os.path.exists(csv_path):
            try:
                with open(csv_path, 'r', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        # Use product name as the unique identifier
                        existing_products.add(row['item_name'].strip())
                print(f"📋 Found {len(existing_products)} existing products in CSV")
            except Exception as e:
                print(f"⚠️  Error reading existing CSV: {e}")
        else:
            print("📋 No existing CSV file found, will create new one")
        
        return existing_products

    def scrape_category(self, max_items: int = 100) -> List[Dict[str, any]]:
        """Scrape products from BoConcept category."""
        print(f"🚀 Starting BoConcept {self.category} scraping (max {max_items} items)")
        
        # Get existing products to avoid double scraping
        existing_products = self.get_existing_products()
        
        # Load products with pagination
        product_info = self.load_more_products(max_items)
        
        if not product_info:
            print(f"❌ No product links found for {self.category}")
            return []
        
        print(f"📦 Found {len(product_info)} products to process")
        
        # Filter out existing products
        new_products = []
        for info in product_info:
            product_name = info['name']
            if product_name not in existing_products:
                new_products.append(info)
            else:
                print(f"⏭️  Skipping existing product: {product_name}")
        
        print(f"🆕 Found {len(new_products)} new products to scrape")
        
        if not new_products:
            print("✅ All products already exist in CSV, no new scraping needed")
            return []
        
        # Scrape each new product
        products = []
        for i, info in enumerate(new_products, 1):
            print(f"\n📦 Processing new product {i}/{len(new_products)}: {info['name']}")
            product_data = self.scrape_product(info['url'])
            if product_data:
                # Add catalog number and use category page data
                product_data['catalog_number'] = f"BC-{self.category.upper()[:2]}-{len(existing_products) + i:03d}"
                # Use price from category page if available
                if info['price'] != "N/A":
                    product_data['price'] = info['price']
                # Use name from category page if it's better
                if info['name'] != "Unknown" and len(info['name']) > len(product_data['name']):
                    product_data['name'] = info['name']
                products.append(product_data)
            
            # Add delay between requests
            time.sleep(2)
        
        return products
    
    def save_to_csv(self, products: List[Dict[str, any]]):
        """Save products to CSV file (append mode)."""
        csv_path = os.path.join(self.category_dir, f"{self.category}.csv")
        
        # Check if file exists to determine if we need to write header
        file_exists = os.path.exists(csv_path)
        
        with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['catalog_number', 'item_name', 'price', 'link', 'image_url', 'colors', 'dimensions', 'item_type']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Only write header if file doesn't exist
            if not file_exists:
                writer.writeheader()
            
            for product in products:
                # Convert to Havertys format
                row = {
                    'catalog_number': product.get('catalog_number', ''),
                    'item_name': product.get('name', ''),
                    'price': product.get('price', 'N/A'),
                    'link': product.get('url', ''),
                    'image_url': product.get('image_path', ''),
                    'colors': ', '.join(product['colors']) if product['colors'] else '',
                    'dimensions': str(product['dimensions']) if product['dimensions'] else '',
                    'item_type': self.category
                }
                writer.writerow(row)
        
        print(f"✅ Saved {len(products)} products to: {csv_path}")
    
    def run(self, max_items: int = 10):
        """Run the complete scraping process."""
        try:
            products = self.scrape_category(max_items)
            if products:
                self.save_to_csv(products)
                print(f"\n🎉 Successfully scraped {len(products)} BoConcept {self.category}!")
            else:
                print(f"❌ No {self.category} were scraped")
        finally:
            self.close_driver()


def main():
    """Main function to run the BoConcept scraper."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape BoConcept furniture data')
    parser.add_argument('--max-items', type=int, default=100, help='Maximum number of items to scrape')
    parser.add_argument('--category', type=str, default='sofas', help='Category to scrape (sofas, lamps, chairs, etc.)')
    
    args = parser.parse_args()
    
    scraper = BoConceptScraper(category=args.category)
    scraper.run(max_items=args.max_items)


if __name__ == "__main__":
    main()
