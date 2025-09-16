# Havertys Furniture Catalog System

## 🎯 **Project Overview**

This project provides a comprehensive furniture catalog system that scrapes Havertys furniture data, generates AI-powered descriptions, and enables semantic search through vector database integration.

## 🏗️ **System Architecture**

```
Web Scraping → Data Processing → AI Descriptions → Vector Database → Semantic Search
```

### **Components**

1. **Web Scrapers** (`scrapers/`) - Extract furniture data from various websites
2. **Master Catalog Updater** (`master_catalog_updater.py`) - Compiles essential data from individual CSV files
3. **OpenAI Vision Module** (`openai_vision_module.py`) - Handles AI-powered image analysis
4. **GPT Furniture Extractor** (`gpt_furniture_extractor.py`) - Creates clean product photography
5. **Sofa Image Analyzer** (`analyze_sofa_image.py`) - Analyzes sofa images and finds similar items
6. **Testing Scripts** (`testing/`) - Validate data quality and test integrations

## 📁 **Project Structure**

```
Furniture/
├── scrapers/                         # 📁 Web scrapers directory
│   ├── havertys_scraper_only.py     # Havertys furniture scraper
│   ├── boconcept_scraper.py         # BoConcept furniture scraper
│   └── interior_define_scraper.py  # Interior Define furniture scraper
├── testing/                         # 📁 Testing and demo scripts
│   ├── data_collection_tester.py   # Data quality validation
│   ├── test_pinecone_integration.py # Pinecone testing script
│   ├── demo_pinecone_integration.py # Pinecone demo script
│   └── example_pinecone_usage.py    # Pinecone usage examples
├── haverty_catalog/                 # 📁 Havertys catalog directory
│   ├── HAVERTYS_MASTER_CATALOG.csv # Master catalog with all items
│   ├── beds/                        # Bed category data and images
│   ├── sofas/                       # Sofa category data and images
│   ├── dressers/                    # Dresser category data and images
│   ├── chests/                      # Chest category data and images
│   ├── benches/                     # Bench category data and images
│   └── nightstands/                 # Nightstand category data and images
├── BoConcept_catalog/               # 📁 BoConcept catalog directory
│   └── sofas/                       # BoConcept sofa data and images
├── InteriorDefine_catalog/          # 📁 Interior Define catalog directory
│   ├── sofas/                       # Interior Define sofa data and images
│   ├── chairs/                      # Interior Define chair data and images
│   ├── tables/                      # Interior Define table data and images
│   ├── benches/                     # Interior Define bench data and images
│   ├── nightstands/                # Interior Define nightstand data and images
│   ├── lighting/                    # Interior Define lighting data and images
│   └── rugs/                        # Interior Define rug data and images
├── InteriorDefine_catalog_2/        # 📁 Interior Define grayscale catalog directory
│   ├── sofas/                       # Grayscale sofa images
│   ├── chairs/                      # Grayscale chair images
│   ├── tables/                      # Grayscale table images
│   ├── benches/                     # Grayscale bench images
│   ├── nightstands/                 # Grayscale nightstand images
│   ├── lighting/                    # Grayscale lighting images
│   └── rugs/                        # Grayscale rug images
├── generated_images/                # 📁 AI-generated and processed images
│   ├── reference_sofa.png           # Original reference sofa image
│   ├── sofa_gpt_image_1_reference.png # GPT-Image-1 reference sofa
│   ├── sofas_extracted.png         # Extracted sofa (multi-item detection)
│   ├── tables_extracted.png        # Extracted table (multi-item detection)
│   ├── rugs_extracted.png          # Extracted rug (multi-item detection)
│   ├── lamps_extracted.png         # Extracted lamp (multi-item detection)
│   ├── furniture_detection_results.csv # Detection results with colors and query numbers
│   └── similarity_results.json     # Sofa similarity search results
├── reference_query_*/               # 📁 Query-specific folders (timestamped)
│   ├── reference_sofa.png          # Reference image for this query
│   ├── query_info.csv              # Query metadata (room_type, style_type, etc.)
│   └── generated_images/           # Query-specific generated images
│       ├── empty_room/             # Empty room images
│       ├── designed_room/          # Designed room images
│       ├── generated_furniture/    # Extracted furniture items
│       └── generated_furniture_gray/ # Grayscale furniture items
├── data_collection_report/          # Data quality reports folder
│   └── data_collection_report_*/    # Timestamped report subfolders
├── config.py                        # 🔧 Configuration management
├── config.json                      # 🔑 API keys and settings
├── master_catalog_updater.py        # Catalog management and AI integration
├── openai_vision_module.py          # OpenAI Vision API module
├── gpt_furniture_extractor.py       # GPT-Image-1 furniture extractor
├── analyze_sofa_image.py            # Sofa image analysis and similarity search
├── furniture_similarity_search.py   # Automated similarity search for grayscale images
├── furniture_combination_optimizer.py # Budget-constrained furniture combination optimizer
├── test_similarity.py                # Visual similarity comparison image generator
├── requirements.txt                 # All project dependencies
└── README.md                        # This file
```

## 🔧 **Configuration Management**

### **Config File System**

The system uses a centralized configuration file (`config.json`) to manage API keys and settings:

```json
{
  "api_keys": {
    "openai": "your-openai-api-key",
    "pinecone": "your-pinecone-api-key"
  },
  "settings": {
    "environment": "us-west1-gcp",
    "index_name": "havertys-furniture-catalog",
    "embedding_model": "text-embedding-3-small",
    "dimension": 1536,
    "batch_size": 100,
    "region": "us-east-1"
  },
  "paths": {
    "haverty_catalog_path": "haverty_catalog/HAVERTYS_MASTER_CATALOG.csv",
    "boconcept_catalog_path": "BoConcept_catalog/sofas/sofas.csv",
    "report_dir": "data_collection_report"
  }
}
```

### **API Key Management**

**Priority Order:**
1. **Environment Variables**: `OPENAI_API_KEY`, `PINECONE_API_KEY`
2. **Config File**: `config.json`
3. **Hardcoded Fallbacks**: For development/testing

**Creating Config File:**
```bash
# Run config script to create initial config
python config.py
```

**Updating API Keys:**
```python
from config import Config

config = Config()
config.set_openai_key("your-new-openai-key")
config.set_pinecone_key("your-new-pinecone-key")
```

## 🚀 **Quick Start**

### **1. Setup Environment**

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### **2. Web Scraping**

```bash
# Scrape furniture data from Havertys
python scrapers/havertys_scraper_only.py

# Scrape furniture data from BoConcept
python scrapers/boconcept_scraper.py

# Scrape furniture data from Interior Define
python scrapers/interior_define_scraper.py --category sofas --max-items 50
```

### **3. Generate AI Descriptions**

```bash
# Update master catalog with AI descriptions
python master_catalog_updater.py --update

# Or test without OpenAI calls
python master_catalog_updater.py --update_dummy
```

### **4. AI Image Processing**

```bash
# Automatically detect and extract all furniture items from an image
python gpt_furniture_extractor.py

# Analyze sofa images and find similar items
python analyze_sofa_image.py

# Automated similarity search for grayscale furniture images
python furniture_similarity_search.py

# Budget-constrained furniture combination optimization
python furniture_combination_optimizer.py

# Visual similarity comparison generation
python test_similarity.py --query 3
```

### **5. Test Data Quality**

```bash
# Generate data collection report
python testing/data_collection_tester.py

# Test Pinecone integration
python testing/test_pinecone_integration.py

# Run Pinecone demo
python testing/demo_pinecone_integration.py

# View Pinecone usage examples
python testing/example_pinecone_usage.py
```

## 📊 **Data Collection**

### **Categories Scraped**

- **Beds** (10 items) - Bed frames with headboards
- **Sofas** (10 items) - Living room seating
- **Dressers** (10 items) - Bedroom storage
- **Chests** (10 items) - Additional storage
- **Benches** (10 items) - Seating and storage
- **Nightstands** (10 items) - Bedside furniture

### **Data Extracted**

For each item:
- **Basic Info**: Name, price, link, catalog number
- **Images**: High-quality product images
- **Colors**: Available color options
- **Dimensions**: Width, height, depth, weight
- **AI Description**: Generated from product images

### **Smart Resume**

The scraper automatically:
- Skips items that already have complete data
- Only processes missing images, colors, or dimensions
- Avoids redundant work on subsequent runs

## 🤖 **AI Integration**

### **OpenAI Vision API**

- **Model**: GPT-4o Vision (stable and reliable)
- **Purpose**: Generate detailed furniture descriptions from images
- **Item-Specific Prompts**:
  - **Beds**: Material, style, single/two-tone, imposing presence, headboard
  - **Sofas**: Material, style, arms, shape, comfort vs style, softness
  - **Other Items**: Standard description format

### **GPT Furniture Extractor**

- **Models**: GPT-4 Vision (detection) + GPT-Image-1 (extraction)
- **Purpose**: Automatically detect and extract all furniture items from images
- **Features**:
  - **Multi-Item Detection**: Uses GPT-4 Vision to identify all furniture types
  - **Color Detection**: Identifies colors/materials for each detected item
  - **CSV Logging**: Saves detection results with query numbers and timestamps
  - **Organized Folder Structure**: Creates query-specific folders with subfolders
  - **Automatic Extraction**: Extracts each detected item individually
  - **OpenCV Grayscale Conversion**: Converts extracted images to grayscale
  - **Room Cleaning**: Remove all background items except target furniture
  - **Background Removal**: Replace with clean white background
  - **Professional Quality**: Catalog-ready product photography
  - **Reference-Based**: Uses original image as reference for accuracy
  - **Cost-Minimized**: Uses poor quality to minimize API spend
  - **Supported Items**: Benches, chairs, lamps, nightstands, rugs, sofas, tables

### **Furniture Similarity Search**

- **Models**: GPT-4 Vision (analysis) + OpenAI Embeddings + Pinecone (search)
- **Purpose**: Automatically find similar furniture items in the Interior Define catalog
- **Features**:
  - **Master Query Log Analysis**: Checks for successful queries automatically
  - **Grayscale Image Processing**: Analyzes extracted grayscale furniture images
  - **GPT-4 Vision Analysis**: Generates detailed descriptions of furniture items
  - **Text Embedding Generation**: Creates vector representations for similarity search
  - **Pinecone Database Search**: Queries Interior Define grayscale catalog
  - **Similarity Scoring**: Ranks results by similarity score (0-1)
  - **CSV Export**: Saves results with query numbers, rankings, and metadata
  - **Automated Pipeline**: End-to-end processing from query log to results

### **Furniture Combination Optimizer**

- **Purpose**: Find budget-constrained furniture combinations ranked by similarity scores
- **Features**:
  - **Master Query Log Analysis**: Checks for queries pending combination optimization
  - **Budget Constraint Processing**: Finds combinations within specified budget limits
  - **Price Integration**: Uses real prices from master catalog with estimated fallback
  - **Similarity Score Ranking**: Ranks combinations by total similarity scores
  - **Comprehensive Combinations**: Generates all possible furniture combinations
  - **CSV Export**: Saves detailed combination results with pricing and rankings
  - **Budget Analysis**: Shows remaining budget for each combination
  - **Automated Pipeline**: End-to-end processing from query log to optimized combinations

### **Similarity Comparison Visualizer**

- **Purpose**: Create visual comparison images showing generated furniture next to similar catalog items
- **Features**:
  - **Side-by-Side Layout**: Generated image on left, similar items in grid on right
  - **Automatic Image Matching**: Uses catalog metadata to find actual product images
  - **Similarity Score Display**: Shows similarity scores and prices for each match
  - **Multiple Image Support**: Handles all furniture types (sofas, chairs, tables, etc.)
  - **Grid Layout**: Automatically arranges similar items in optimal grid
  - **Error Handling**: Creates placeholder images when catalog images aren't found
  - **High Quality Output**: Generates PNG images with proper sizing and labels

### **N/A Response Handling**

- Detects AI refusal responses
- Marks items as "N/A" for retry
- Only processes failed items on subsequent runs
- Preserves successful descriptions

### **Cost Estimation**

- **OpenAI API**: ~$0.50 for 57 furniture items
- **One-time setup**: Minimal cost
- **Ongoing**: Only for new items or retries

## 🔍 **Semantic Search (Pinecone)**

### **Vector Database Features**

- **Embeddings**: OpenAI `text-embedding-3-small` model
- **Dimension**: 1536-dimensional vectors
- **Search**: Cosine similarity matching
- **Storage**: Pinecone cloud database

### **Search Capabilities**

**Material-Based Searches:**
- "leather furniture" → Finds leather sofas, chairs
- "wooden bed frame" → Finds wooden beds
- "upholstered seating" → Finds sofas, chairs

**Style-Based Searches:**
- "modern contemporary design" → Finds modern furniture
- "traditional classic" → Finds traditional pieces
- "minimalist style" → Finds clean, simple designs

**Function-Based Searches:**
- "comfortable seating" → Finds sofas, chairs
- "storage furniture" → Finds dressers, chests
- "bedroom furniture" → Finds beds, nightstands

**Size-Based Searches:**
- "large sofa" → Finds large seating
- "compact nightstand" → Finds small furniture
- "spacious bed" → Finds large beds

### **Usage Examples**

```bash
# Search for comfortable seating
python pinecone_vector_database.py \
    --openai-key "your-key" \
    --pinecone-key "your-key" \
    --search "comfortable leather sofa"
```

```python
# Programmatic usage
from pinecone_vector_database import PineconeVectorDatabase

db = PineconeVectorDatabase(openai_api_key, pinecone_api_key)
results = db.search_similar_items("modern furniture", top_k=5)
```

## 📈 **Data Quality Reports**

### **Automated Testing**

The `data_collection_tester.py` generates comprehensive reports in `data_collection_report/data_collection_report_TIMESTAMP/` folders:

- **Missing Data Analysis**: Identifies incomplete records
- **Image Validation**: Checks for missing or corrupted images
- **Dimension Verification**: Validates measurement data
- **Color Collection**: Reports color extraction success rates
- **Master Catalog Validation**: Checks AI description quality

### **Report Features**

- **Timestamped Reports**: Each run creates a new timestamped subfolder
- **Detailed Analysis**: Item-by-item validation
- **Summary Statistics**: Overall data quality metrics
- **Recommendations**: Suggestions for data improvement

## 🛠️ **Technical Details**

### **Web Scraping**

- **Technology**: Selenium WebDriver with Chrome
- **Anti-Bot Measures**: User agent spoofing, random delays
- **Error Handling**: Retry logic with exponential backoff
- **Performance**: Optimized for speed with smart resume

### **Data Processing**

- **Format**: CSV files with structured data
- **Images**: JPEG format, organized by category
- **Metadata**: JSON-like strings for complex data
- **Validation**: Comprehensive data quality checks

### **AI Integration**

- **API**: OpenAI GPT-4o Vision
- **Error Handling**: Graceful fallbacks and retries
- **Cost Optimization**: Efficient token usage
- **Quality Control**: N/A detection and retry logic

### **Vector Database**

- **Model**: OpenAI text-embedding-3-small
- **Storage**: Pinecone cloud database
- **Performance**: Batch processing and efficient queries
- **Cost**: Free tier sufficient for current scale

## 💰 **Cost Analysis**

### **One-Time Setup**
- **OpenAI Embeddings**: ~$0.50 for 57 items
- **Pinecone Storage**: $0 (free tier)
- **Total**: ~$0.50

### **Ongoing Costs**
- **Storage**: $0 (free tier sufficient)
- **Search Queries**: $0 (free tier includes queries)
- **Monthly**: $0

## 🔧 **Configuration**

### **API Keys Required**

1. **OpenAI API Key**: For AI descriptions and embeddings
2. **Pinecone API Key**: For vector database (get from https://www.pinecone.io/)

### **Environment Variables**

```bash
export OPENAI_API_KEY='your-openai-key'
export PINECONE_API_KEY='your-pinecone-key'
```

## 📋 **Dependencies**

All dependencies are consolidated in `requirements.txt`:

```
# Web Scraping
selenium>=4.15.0
webdriver-manager>=4.0.0
beautifulsoup4>=4.12.0
requests>=2.31.0
lxml>=4.9.0

# AI Integration
openai>=1.0.0

# Vector Database
pinecone>=7.0.0
pandas>=1.5.0
numpy>=1.21.0

# Data Processing
csv
json
time
argparse
os
```

## 🚨 **Troubleshooting**

### **Common Issues**

1. **"ModuleNotFoundError"**: Install dependencies with `pip install -r requirements.txt`
2. **"API key invalid"**: Verify API keys in respective dashboards
3. **"Index not found"**: Pinecone index will be created automatically
4. **"Embedding failed"**: Check OpenAI API key and rate limits
5. **"Browser crashes"**: Scraper includes automatic browser restart logic

### **Debugging**

Enable verbose logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### **Data Issues**

Run the data collection tester:
```bash
python testing/data_collection_tester.py
```

Check the generated report in `data_collection_report/` for detailed analysis.

## 🎯 **Next Steps**

### **Immediate Usage**
1. Set up API keys
2. Run web scraper
3. Generate AI descriptions
4. Set up vector database
5. Test semantic search

### **Integration Opportunities**
1. **Web Interface**: Build search UI for end users
2. **Recommendation Engine**: Suggest complementary items
3. **Inventory Management**: Track availability and pricing
4. **Analytics**: Analyze search patterns and preferences

### **Advanced Features**
1. **Incremental Updates**: Only process changed items
2. **Multiple Indices**: Separate indices by furniture type
3. **Advanced Filtering**: Filter by price, dimensions, etc.
4. **Hybrid Search**: Combine vector and keyword search
5. **Real-time Updates**: Automatically update vectors when catalog changes

## 📚 **Additional Resources**

- **Pinecone Documentation**: [https://docs.pinecone.io/](https://docs.pinecone.io/)
- **OpenAI Embeddings**: [https://platform.openai.com/docs/guides/embeddings](https://platform.openai.com/docs/guides/embeddings)
- **Vector Search Concepts**: [https://www.pinecone.io/learn/vector-database/](https://www.pinecone.io/learn/vector-database/)

## ✅ **System Status**

- **✅ Web Scraping**: Complete with smart resume
- **✅ AI Descriptions**: Working with item-specific prompts
- **✅ Vector Database**: Ready for semantic search
- **✅ Data Validation**: Comprehensive quality reports
- **✅ Documentation**: Complete and up-to-date

The system is ready for production use! 🎉

---

*Last Updated: January 2025*
*Version: 1.0*
# test_pine
