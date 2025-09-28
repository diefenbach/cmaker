import yaml
import os
from datetime import datetime
from pathlib import Path

from PIL import Image

from openai import OpenAI
from dotenv import load_dotenv

from .config import Config
from .logger import CampaignLogger
from .image_generation import ImageGenerator
from .image_processing import ImageProcessor
from .prompt_generation import PromptGenerator
from .campaign_loading import CampaignLoader

load_dotenv()

class CampaignProcessor:
    """Main workflow logic for processing campaigns."""

    def __init__(self, config: Config = None, logger: CampaignLogger = None):
        self.config = config or Config()
        self.logger = logger or CampaignLogger()

        # Initialize components
        self.image_generator = ImageGenerator(self.config, self.logger)
        self.image_processor = ImageProcessor(self.config, self.logger)
        self.prompt_generator = PromptGenerator(self.config, self.logger)
        self.campaign_loader = CampaignLoader(self.config, self.logger)

    def process_all_campaigns(self):
        """Main function to process all campaigns."""
        # Load all campaign briefs
        briefs = self.campaign_loader.load_campaign_briefs()

        if not briefs:
            self.logger.info("No campaign briefs found")
            return

        self.logger.info(f"Found {len(briefs)} campaign(s) to process")

        # Process each campaign
        for brief in briefs:
            try:
                self.process_single_campaign(brief)
            except Exception as e:
                self.logger.exception(f"Failed to process campaign {brief.get('campaign_name', 'unknown')}: {e}")
                continue

    def process_single_campaign(self, campaign_brief: dict):
        """Process a single campaign brief."""
        campaign_name = campaign_brief["campaign_name"]
        campaign_path = Path(campaign_brief["campaign_path"])

        self.logger.info(f"Processing campaign: {campaign_name}")

        # Create results folder structure
        results_path = campaign_path / self.config.RESULTS_DIR
        results_path.mkdir(exist_ok=True)

        # Handle multiple products
        products = campaign_brief.get("products", [])
        assets = campaign_brief.get("assets", [])
        languages = campaign_brief.get("languages", ["English"])  # Default to English if no languages specified

        self.logger.debug(f"Will create results structure: {results_path}")

        for i, product in enumerate(products):
            try:
                asset_file = assets[i]
            except IndexError:
                asset_file = None

            self.logger.info(f"Processing product {i+1}/{len(products)}: {product}")
            self._process_single_product(campaign_brief, product, asset_file, results_path, campaign_path, languages)

        self.logger.info(f"Completed processing campaign: {campaign_name}")
        self.logger.info(f"Results saved in: {results_path}")

        # Mark campaign as completed
        self._mark_campaign_done(campaign_path)

    def _process_single_product(
        self,
        campaign_brief: dict,
        product: str,
        asset_file: str,
        results_path: Path,
        campaign_path: Path,
        languages: list,
    ):
        """Process a single product within a campaign."""
        final_asset_path = None
        asset_name = None
        product_name = self._sanitize_product_name(product)

        # Create product-specific brief for prompt generation
        product_brief = campaign_brief.copy()
        if product:
            product_brief["product"] = product
            product_brief["asset"] = asset_file

        if asset_file:
            potential_asset_path = campaign_path / self.config.ASSETS_DIR / asset_file
            if potential_asset_path.exists():
                final_asset_path = str(potential_asset_path)
                asset_name = potential_asset_path.stem
                self.logger.info(f"Using existing asset: {final_asset_path}")

        if not final_asset_path:
            self.logger.info(f"No existing asset found for {product}, creating from prompt")
            # Create asset path in the campaign's assets folder
            assets_folder = campaign_path / self.config.ASSETS_DIR
            assets_folder.mkdir(exist_ok=True)
            asset_filename = f"{product_name}.png"
            temp_asset_path = assets_folder / asset_filename
            final_asset_path = self.image_generator.create_asset_from_prompt(product_name, str(temp_asset_path))
            asset_name = Path(final_asset_path).stem

        prompt = self.prompt_generator.create_campaign_prompt_with_llm(product_brief)
        # prompt = "A professional product photography scene, clean studio lighting, high quality, commercial photography style"

        # Generate base images once per product
        self.logger.info(f"Generating base images for product: {product}")

        # 1. Create base folder structure first
        base_folder_path = results_path / product_name / "base"
        base_folder_path.mkdir(parents=True, exist_ok=True)
        for ratio in ["1x1", "16x9", "9x16"]:
            (base_folder_path / ratio).mkdir(exist_ok=True)

        # 2. Generate base (1x1 square) directly in base folder
        base_path = base_folder_path / "1x1" / f"{asset_name}_1x1.png"
        self.image_generator.generate_image_with_asset(final_asset_path, prompt, str(base_path))

        # 3. Prepare canvas (1024x1024 for DALL-E 2, scaled by 0.6)
        canvas, inner_box = self.image_processor.prepare_canvas(str(base_path))

        # 4. Outpainting with DALL-E 2 (base protected)
        dalle_prompt = self.prompt_generator.create_dalle_prompt(prompt)
        outpainted = self.image_generator.outpaint_with_dalle(canvas, inner_box, dalle_prompt)

        # 5. Save base images in "base" folder (without text overlay)
        base_img = Image.open(str(base_path))

        # Crop and save 16x9 and 9x16 base images
        outpainted_16x9_path = base_folder_path / "16x9" / f"{asset_name}_16x9.png"
        outpainted_9x16_path = base_folder_path / "9x16" / f"{asset_name}_9x16.png"

        self.image_processor.crop_to_ratio(outpainted, str(outpainted_16x9_path), "16x9")
        self.image_processor.crop_to_ratio(outpainted, str(outpainted_9x16_path), "9x16")

        # 5. Create language-specific versions with text overlay
        for language in languages:
            language_code = self._get_language_code(language)
            product_lang_path = results_path / product_name / language_code

            # Ensure the directory structure exists for this specific product/language
            product_lang_path.mkdir(parents=True, exist_ok=True)
            for ratio in ["1x1", "16x9", "9x16"]:
                (product_lang_path / ratio).mkdir(exist_ok=True)

            self.logger.info(f"Creating language-specific versions for: {language}")

            # Copy base images to language-specific folders
            base_img = Image.open(str(base_path))
            base_img.save(str(product_lang_path / "1x1" / f"{asset_name}_1x1.png"))

            img_16x9 = Image.open(str(outpainted_16x9_path))
            img_16x9.save(str(product_lang_path / "16x9" / f"{asset_name}_16x9.png"))

            img_9x16 = Image.open(str(outpainted_9x16_path))
            img_9x16.save(str(product_lang_path / "9x16" / f"{asset_name}_9x16.png"))

            # Add language-specific text overlay to all generated images
            message = campaign_brief.get("message", "")
            if message:
                translated_message = self._translate_message(message, language)

                # Add text to 1x1 image
                base_img_with_text = self.image_processor.add_text_overlay(base_img, translated_message)
                base_img_with_text.save(str(product_lang_path / "1x1" / f"{asset_name}_1x1.png"))
                self.logger.info(f"Added {language} message overlay to 1x1: '{translated_message}'")

                # Add text to 16x9 image
                img_16x9_with_text = self.image_processor.add_text_overlay(img_16x9, translated_message)
                img_16x9_with_text.save(str(product_lang_path / "16x9" / f"{asset_name}_16x9.png"))
                self.logger.info(f"Added {language} message overlay to 16x9: '{translated_message}'")

                # Add text to 9x16 image
                img_9x16_with_text = self.image_processor.add_text_overlay(img_9x16, translated_message)
                img_9x16_with_text.save(str(product_lang_path / "9x16" / f"{asset_name}_9x16.png"))
                self.logger.info(f"Added {language} message overlay to 9x16: '{translated_message}'")

    def _mark_campaign_done(self, campaign_path: Path, scene_prompt: str = None):
        """Mark a campaign as completed by creating/updating meta.yaml."""

        meta_file = campaign_path / "meta.yaml"
        meta_data = {
            "status": "done",
            "completed_at": datetime.now().isoformat(),
        }

        if scene_prompt:
            meta_data["scene_prompt"] = scene_prompt

        try:
            with open(meta_file, "w") as f:
                yaml.dump(meta_data, f, default_flow_style=False, sort_keys=False)
            self.logger.info(f"Marked campaign as completed: {meta_file}")
        except Exception as e:
            self.logger.error(f"Failed to mark campaign as completed: {e}")

    def _sanitize_product_name(self, product: str) -> str:
        """Convert product name to a safe folder name."""
        import re

        # Remove special characters and replace spaces with underscores
        sanitized = re.sub(r"[^a-zA-Z0-9\s-]", "", product)
        sanitized = re.sub(r"\s+", "_", sanitized.strip())
        return sanitized.lower()

    def _get_language_code(self, language: str) -> str:
        """Convert language name to a short language code."""
        language_codes = {
            "English": "en",
            "German": "de",
            "French": "fr",
            "Spanish": "es",
            "Italian": "it",
            "Portuguese": "pt",
            "Dutch": "nl",
            "Russian": "ru",
            "Chinese": "zh",
            "Japanese": "ja",
            "Korean": "ko",
        }
        return language_codes.get(language, language.lower()[:2])

    def _translate_message(self, message: str, language: str) -> str:
        """Translate message to the specified language using GPT."""
        # If already in English or no translation needed, return original
        if language.lower() == "english" or not message.strip():
            return message

        self.logger.info(f"Translating message to {language}: '{message}'")

        translation_prompt = f"""
            Translate the following marketing message to {language}. 
            Keep the tone professional and marketing-appropriate.
            Preserve the emotional impact and brand voice.
            Return ONLY the translated text, no additional commentary.
            
            Message to translate: "{message}"
            
            Translation:"""

        try:
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

            response = client.chat.completions.create(
                model=self.config.GPT_MODEL,
                messages=[{"role": "user", "content": translation_prompt}],
            )

            translated_message = response.choices[0].message.content.strip()
            translated_message = translated_message.strip('"').strip("'")

            self.logger.info(f"Translated to {language}: '{translated_message}'")
            return translated_message

        except Exception as e:
            self.logger.error(f"Failed to translate message using GPT: {e}")
            self.logger.info("Using original message as fallback")
            return message
