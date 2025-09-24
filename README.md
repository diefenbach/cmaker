# Campaign Maker (cmaker)

An AI-powered marketing campaign image generation system that creates professional product photography and marketing materials using OpenAI's DALL-E and GPT models.

## Overview

This system automates the creation of marketing campaign assets by generating product images in multiple aspect ratios (1:1, 16:9, 9:16) with localized text overlays. It uses AI to create sophisticated product photography scenes and handles multi-language campaign variations.

## Installation

### Prerequisites
- Python 3.12+
- OpenAI API key
- uv 

### Setup
```bash
# Install uv (https://docs.astral.sh/uv/getting-started/installation/)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone <repository-url> cmaker
cd cmaker

# Install dependencies using uv (recommended)
uv sync
```

### Environment Setup
Set your OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

## General Approach

The system leverages multiple AI technologies:

- **OpenAI GPT-5 Nano**: Generates sophisticated scene descriptions and translates marketing messages
- **OpenAI DALL-E (gpt-image-1)**: Creates product images with transparent backgrounds and generates contextual scenes
- **Image Processing Pipeline**: Handles asset integration, outpainting, cropping, and text overlay

### Workflow
1. **Campaign Loading**: Reads YAML brief files from campaigns directory
2. **Asset Generation**: Creates product assets from prompts or uses existing assets
3. **Scene Generation**: Generates base product images with contextual backgrounds
4. **Outpainting**: Extends scenes using DALL-E's outpainting capabilities
5. **Multi-format Creation**: Crops images to different aspect ratios
6. **Localization**: Adds translated text overlays for multiple languages

### File structure
```
cmaker /
├── 📁 src/cmaker                         # Core application code
│   ├── main.py                      # Application entry point
│   ├── campaign_processing.py       # Main campaign orchestrator
│   ├── campaign_loading.py          # YAML campaign loader
│   ├── image_generation.py          # DALL-E API integration
│   ├── image_processing.py          # Image manipulation
│   ├── prompt_generation.py         # AI prompt creation
│   ├── config.py                    # Configuration management
│   └── logger.py                    # Structured logging
├── 📁 campaigns/                    # Campaign definitions
│   ├── 📁 campaign_1/               # Water bottle campaign
│   │   ├── 📄 brief.yaml            # Campaign configuration
│   │   ├── 📄 meta.yaml             # Processing status
│   │   ├── 📁 assets/               # Product images
│   │   └── 📁 results/              # Generated outputs
├── 📄 pyproject.toml                # Project configuration
└── 📄 README.md                     # This file
```
## Architecture

### Core Modules

#### `CampaignProcessor` (campaign_processing.py)
Main orchestrator that manages the entire campaign processing workflow. Handles campaign loading, product iteration, and result organization.

#### `CampaignLoader` (campaign_loading.py)
Loads and validates YAML campaign briefs from the campaigns directory. Skips completed campaigns based on meta.yaml status.

#### `ImageGenerator` (image_generation.py)
Manages all DALL-E API interactions:
- Creates transparent product assets from prompts
- Generates base images with asset integration
- Handles DALL-E outpainting with mask protection
- Manages mask creation for selective editing

#### `ImageProcessor` (image_processing.py)
Handles pure image manipulation operations:
- Canvas preparation and scaling
- Aspect ratio cropping (1:1, 16:9, 9:16)
- Text overlay with automatic sizing

#### `PromptGenerator` (prompt_generation.py)
Creates optimized prompts for AI models:
- Generates detailed scene descriptions from campaign briefs
- Converts detailed prompts to concise DALL-E prompts
- Handles prompt length optimization

#### `Config` (config.py)
Centralized configuration management for API models, file paths, image processing parameters, and prompt settings.

#### `CampaignLogger` (logger.py)
Structured logging system for tracking campaign processing progress and debugging.

## Usage

### Basic Usage
```bash
# Process all campaigns
uv run cmaker

# Or you can activate the virtualenv and run it directly
source ./.venv/bin/activate
cmaker
```

### Campaign Structure
Create campaigns in the `campaigns/` directory with this structure:
```
campaigns/
  campaign_name/
    brief.yaml          # Campaign configuration
    assets/             # Optional: existing product assets
    results/            # Generated outputs
```

### Brief File Format
```yaml
region: "North America"
market: "E-commerce"
audience: "Eco-conscious consumers"
message: "Sustainable living made simple"
products:
  - "EcoFresh Reusable Water Bottle 1L Green"
  - "EcoFresh Reusable Water Bottle 1L Red"
assets:
  - "bottle_1.png"
  - "bottle_2.png"
languages:
  - "English"
  - "German"
  - "French"
```

## Output Structure

Generated campaigns create organized folder structures:
```
results/
├── 📁 product_name/                    # Generated campaign outputs
│   ├── 📁 base/                        # Base images without text
│   │   ├── 📁 1x1/                     # Square format
│   │   ├── 📁 16x9/                    # Landscape format
│   │   └── 📁 9x16/                    # Portrait format
│   ├── 📁 en/                          # English versions with text
│   │   ├── 📁 1x1/                     # Square format
│   │   ├── 📁 16x9/                    # Landscape format
│   │   └── 📁 9x16/                    # Portrait format
│   └── 📁 de/                          # German versions with text
│       ├── 📁 1x1/                     # Square format
│       ├── 📁 16x9/                    # Landscape format
│       └── 📁 9x16/                    # Portrait format
```

## Configuration

Key settings in `src/cmaker/config.py`:
- **API Models**: DALL-E and GPT model selection
- **Image Processing**: Canvas size, scaling, font settings
- **File Paths**: Directory structure configuration
- **Prompt Limits**: Maximum prompt lengths for different models

## Dependencies

- `openai>=1.108.0` - OpenAI API client
- `pillow>=11.3.0` - Image processing
- `pyyaml>=6.0.2` - YAML configuration parsing
- `requests>=2.32.5` - HTTP requests

## Technical Notes

- Uses DALL-E's edit API for asset integration with mask protection
- Implements intelligent prompt optimization for different AI models
- Supports transparent PNG assets with alpha channel preservation
- Automatic text sizing and positioning for optimal readability
- Multi-language support with GPT-powered translation