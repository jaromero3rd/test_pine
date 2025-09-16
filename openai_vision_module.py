#!/usr/bin/env python3
"""
OpenAI GPT-5 Vision API Module
Handles all OpenAI-related functionality for furniture description generation
"""

import os
import base64
from typing import Optional, Dict, Any

# OpenAI imports
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: OpenAI library not installed. Install with: pip install openai")

class OpenAIVisionProcessor:
    """Handles OpenAI GPT-5 Vision API calls for furniture descriptions."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the OpenAI Vision processor."""
        self.client = None
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        
        if OPENAI_AVAILABLE and self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
                print("✓ OpenAI client initialized successfully")
            except Exception as e:
                print(f"✗ OpenAI client initialization failed: {e}")
                self.client = None
        elif not OPENAI_AVAILABLE:
            print("✗ OpenAI library not available. Install with: pip install openai")
        else:
            print("✗ No OpenAI API key provided")
    
    def is_available(self) -> bool:
        """Check if OpenAI functionality is available."""
        return self.client is not None
    
    def encode_image(self, image_path: str) -> Optional[str]:
        """Encode image file to base64."""
        try:
            if not os.path.exists(image_path):
                print(f"    Image file not found: {image_path}")
                return None
                
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            return base64_image
            
        except Exception as e:
            print(f"    Error encoding image {image_path}: {e}")
            return None
    
    def create_prompt(self, item_type: str) -> str:
        """Create the prompt for the OpenAI API call based on item type."""
        if item_type.lower() == 'bed':
            return "Describe the bedframe in the image by answering these questions and more: what type of material is the bed made of? what type of style of bed is it? (contemporary, modern?...) Is it two tone or a single tone? Is it imposing? Does it have a head board? --make sure the description is one long string without \\n's"
        elif item_type.lower() == 'sofa':
            return "Describe the sofa in the image by answering these questions and more: what type of material is the sofa? what type of style of sofa is it? (contemporary, modern?...) Is it two tone or a single tone? Is it imposing? Does it have arms or or not? what shape is it? is it comfy or more for style? is it soft to the touch? --make sure the description is one long string without \\n's"
        else:
            # Default prompt for all other furniture types
            return f"Describe the {item_type} in the image using this format: Description: ____, Feel_to_the_touch:___ --make sure the description is one long string without \\n's"
    
    def call_gpt5_vision(self, image_path: str, item_type: str) -> Optional[str]:
        """Make API call to GPT-5 Vision API."""
        if not self.is_available():
            return None
        
        try:
            # Encode image
            base64_image = self.encode_image(image_path)
            if not base64_image:
                return None
            
            # Create prompt
            prompt = self.create_prompt(item_type)
            
            print(f"    🤖 Calling OpenAI GPT-4o Vision API for: {item_type}")
            
            # Make the API call
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Using GPT-4o Vision (more stable than GPT-5)
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            # Extract the description
            ai_description = response.choices[0].message.content.strip()
            print(f"    ✓ OpenAI response received: {ai_description[:100]}...")
            
            return ai_description
            
        except Exception as e:
            print(f"    ✗ OpenAI API call failed: {e}")
            return None
    
    def parse_response(self, response: str) -> Dict[str, str]:
        """Parse the OpenAI response into components."""
        if not response:
            return {"description": "", "feel": ""}
        
        try:
            if "Description:" in response and "Feel_to_the_touch:" in response:
                parts = response.split("Feel_to_the_touch:")
                description_part = parts[0].replace("Description:", "").strip()
                feel_part = parts[1].strip()
                
                return {
                    "description": description_part,
                    "feel": feel_part,
                    "full_response": response
                }
            else:
                # If format doesn't match, return the full response as description
                return {
                    "description": response,
                    "feel": "Not specified",
                    "full_response": response
                }
                
        except Exception as e:
            print(f"    Error parsing OpenAI response: {e}")
            return {
                "description": response,
                "feel": "Not specified",
                "full_response": response
            }
    
    def generate_description(self, image_path: str, item_type: str) -> Dict[str, str]:
        """Generate AI description for an item."""
        if not self.is_available():
            return {
                "description": "N/A",
                "feel": "N/A",
                "full_response": "N/A",
                "source": "unavailable"
            }
        
        # Make API call
        response = self.call_gpt5_vision(image_path, item_type)
        
        if response:
            # Check if response indicates AI couldn't provide description
            if any(phrase in response.lower() for phrase in [
                "i'm sorry", "i can't", "i cannot", "i'm unable", 
                "i don't", "i can't help", "i can't assist", "i can't provide",
                "i'm not able", "i'm not allowed", "i can't describe"
            ]):
                return {
                    "description": "N/A",
                    "feel": "N/A", 
                    "full_response": "N/A",
                    "source": "openai_na"
                }
            
            parsed = self.parse_response(response)
            parsed["source"] = "openai"
            return parsed
        else:
            return {
                "description": "N/A",
                "feel": "N/A",
                "full_response": "N/A",
                "source": "failed"
            }

def create_openai_processor(api_key: Optional[str] = None) -> OpenAIVisionProcessor:
    """Factory function to create OpenAI processor."""
    return OpenAIVisionProcessor(api_key=api_key)

# Example usage
if __name__ == "__main__":
    print("OpenAI GPT-5 Vision API Module")
    print("=" * 40)
    
    # Test the module
    processor = create_openai_processor()
    
    if processor.is_available():
        print("✓ OpenAI processor is available")
        
        # Find a sample image
        sample_image = None
        for root, dirs, files in os.walk("Catalog"):
            for file in files:
                if file.endswith(('.jpg', '.jpeg', '.png')):
                    sample_image = os.path.join(root, file)
                    break
            if sample_image:
                break
        
        if sample_image:
            print(f"✓ Found sample image: {sample_image}")
            
            # Test description generation
            result = processor.generate_description(sample_image, "bed")
            print(f"✓ Generated description: {result['full_response'][:100]}...")
        else:
            print("✗ No sample image found")
    else:
        print("✗ OpenAI processor is not available")
        print("  Set OPENAI_API_KEY environment variable to enable")
