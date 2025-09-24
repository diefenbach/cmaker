# Campaign Maker (cmaker)

An AI-powered marketing campaign image generation system that creates professional product photography and marketing materials using OpenAI's DALL-E and GPT models.

## Overview

This system automates the creation of marketing campaign assets by generating product images in multiple aspect ratios (1:1, 16:9, 9:16) with localized text overlays. It uses AI to create sophisticated product photography scenes and handles multi-language campaign variations.

## Installation

### Prerequisites
- OpenAI API key
- Python 3.12+
- uv 

### Setup
```bash
# Install uv (or see https://docs.astral.sh/uv/getting-started/installation/)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/diefenbach/cmaker.git
cd cmaker

# Install dependencies using uv
uv sync
```

### Set your OpenAI API key:
```bash

cp .env_tmpl .env
```

Add your OPENAI_API_KEY to .env


That's it! 

## Basic Usage

**Note:** You can get started immediately with the prepared example campaign ("campaign_1")

```bash
# Process all campaigns
uv run cmaker

# Or you can activate the virtualenv and run it directly
source ./.venv/bin/activate
cmaker
```

Watch the log messages in the terminal. When processing is complete, you will find the results in campaigns/campaign_1/results.

## Creating a New Campaign

To create a new campaign, follow these steps:

1. **Copy the empty campaign template**:
   ```bash
   cp -r examples/campaign_empty campaigns/your_campaign_name
   ```

2. **Edit the brief.yaml file** in your campaign directory with your campaign details:
   ```yaml
   region: "Your target region"
   market: "Your target market"
   audience: "Your target audience"
   message: "Your marketing message"
   products:
     - "Product name 1"
     - "Product name 2"
     - ...
   assets:
     - "existing_asset_1.png"  # Optional: existing product images
     - "existing_asset_2.png"
   languages:
     - "English"
     - "German"  # Add other languages as needed
   ```

3. **Add product assets** (optional):
   - Place existing product images in the `assets/` folder
   - For best results, use assets that are 1024x1024 PNG with alpha channel
   - If no assets are provided, the system will generate them from product descriptions

4. **Run the campaign**:
   ```bash
   uv run cmaker
   ```

The system will automatically process your new campaign and generate results in the `results/` folder within your campaign directory.

### Campaign Status Tracking

After a successful run, campaigns are marked as completed in `meta.yaml`:
```yaml
status: done
```

To re-run a completed campaign, remove or modify the status in `meta.yaml`:
```yaml
# Remove the status line or change it to:
status: start
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
├── 📁 src/cmaker                    # Core application code
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

## Output Structure

Generated campaigns create organized folder structures:
```
results/
├── 📁 product_name/                    # Generated campaign outputs
    ├── 📁 base/                        # Base images without text
    │   ├── 📁 1x1/                     # Square format
    │   ├── 📁 16x9/                    # Landscape format
    │   └── 📁 9x16/                    # Portrait format
    ├── 📁 en/                          # English versions with text
    │   ├── 📁 1x1/                     # Square format
    │   ├── 📁 16x9/                    # Landscape format
    │   └── 📁 9x16/                    # Portrait format
    └── 📁 de/                          # German versions with text
        ├── 📁 1x1/                     # Square format
        ├── 📁 16x9/                    # Landscape format
        └── 📁 9x16/                    # Portrait format
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

## Dependencies

- `openai>=1.108.0` - OpenAI API client
- `pillow>=11.3.0` - Image processing
- `pyyaml>=6.0.2` - YAML configuration parsing
- `requests>=2.32.5` - HTTP requests
- `python-dotenv>=1.1.1` - Environment variable management

## Technical Notes

- Uses DALL-E's edit API for asset integration with mask protection
- Implements intelligent prompt optimization for different AI models
- Supports transparent PNG assets with alpha channel preservation
- Automatic text sizing and positioning for optimal readability
- Multi-language support with GPT-powered translation