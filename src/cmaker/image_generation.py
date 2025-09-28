import base64
import io
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image, ImageFilter, ImageDraw

from .config import Config
from .logger import CampaignLogger

load_dotenv()

class ImageGenerator:
    """Handles all DALL-E API calls and image generation."""

    def __init__(self, config: Config, logger: CampaignLogger):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.config = config
        self.logger = logger

    def generate_image_with_asset(self, asset_path: str, prompt: str, out_path: str) -> str:
        """
        Inserts a transparent asset into a scene and generates the background based on the given prompt.
        """
        self.logger.info(f"Generating base image with asset: {asset_path}")

        try:
            with open(asset_path, "rb") as img:
                mask = self._make_lock_mask_from_asset(asset_path)
                result = self.client.images.edit(
                    model=self.config.DALL_E_MODEL, image=img, prompt=prompt, size="1024x1024"
                )

            img_b64 = result.data[0].b64_json
            img_bytes = base64.b64decode(img_b64)

            Path(out_path).parent.mkdir(parents=True, exist_ok=True)
            Path(out_path).write_bytes(img_bytes)
            self.logger.info(f"Base image saved: {out_path}")
            return out_path

        except Exception as e:
            self.logger.error(f"Failed to generate base image: {e}")
            raise

    def create_asset_from_prompt(self, prompt: str, asset_path: str) -> str:
        """Creates an asset PNG from the extracted asset description using DALL-E."""
        try:
            # First extract the main asset from the scene prompt
            asset_description = self._extract_asset_from_prompt(prompt)

            # Create a prompt specifically for the isolated asset with transparency
            asset_prompt = f"{asset_description}, transparent background, PNG format with alpha channel, isolated object only, no background, no shadows, no reflections, clean transparent cutout, professional product photography, high detail, studio lighting"

            self.logger.info(f"Generating asset: {asset_prompt}")

            # Generate image using gpt-image-1 with transparent background
            result = self.client.images.generate(
                model=self.config.DALL_E_MODEL, prompt=asset_prompt, size="1024x1024", n=1, background="transparent"
            )

            # Decode and save the image directly from gpt-image-1
            img_b64 = result.data[0].b64_json
            img_bytes = base64.b64decode(img_b64)

            # Save as PNG directly - gpt-image-1 with transparent background
            Path(asset_path).parent.mkdir(parents=True, exist_ok=True)
            Path(asset_path).write_bytes(img_bytes)
            self.logger.info(f"Asset generated and saved: {asset_path}")

            return asset_path

        except Exception as e:
            self.logger.error(f"Failed to create asset from prompt: {e}")
            raise

    def outpaint_with_dalle(self, canvas: Image.Image, inner_box: tuple, prompt: str):
        """Outpainting with DALL-E 2: only areas outside inner_box are generated."""
        # Convert to RGBA for DALL-E 2 compatibility
        if canvas.mode != "RGBA":
            canvas = canvas.convert("RGBA")

        # Save temporary files for DALL-E 2
        temp_image_path = "temp_canvas.png"
        temp_mask_path = "temp_mask.png"

        canvas.save(temp_image_path)

        self.logger.debug("Outpainting with DALL-E 2 at 1024x1024")

        # Always protect the inner_box area (asset) from outpainting
        mask = self._make_outpaint_mask(canvas, inner_box)

        # Save mask to file
        with open(temp_mask_path, "wb") as f:
            f.write(mask.getvalue())

        # Make the API request using DALL-E 2, DALL-E 3 seems to be much better at outpainting as gpt-image-1
        with open(temp_image_path, "rb") as image_file, open(temp_mask_path, "rb") as mask_file:
            result = self.client.images.edit(
                image=image_file,
                mask=mask_file,
                prompt=prompt[0:999],  # DALL-E 2 has a limit of 1000 characters
                size="1024x1024",
                response_format="b64_json",
            )

        # Decode base64 image data
        img_b64 = result.data[0].b64_json
        img_bytes = base64.b64decode(img_b64)

        # Clean up temporary files
        os.remove(temp_image_path)
        os.remove(temp_mask_path)

        return Image.open(io.BytesIO(img_bytes))

    def _extract_asset_from_prompt(self, prompt: str) -> str:
        """Uses LLM to extract the main asset from the scene prompt."""
        self.logger.info("Extracting main asset from prompt using LLM...")

        extraction_prompt = f"""
        Analyze this scene description and extract the main object/asset that should be the focal point:
        
        "{prompt}"
        
        Return ONLY a concise description of the main object/asset that should be isolated and used as a product shot. 
        Focus on the primary subject, not the background or environment. 
        Examples: "a porcelain tea service", "a luxury watch", "a modern chair", "a vintage camera".
        
        Response:"""

        response = self.client.responses.create(
            model=self.config.GPT_MODEL,
            input=extraction_prompt,
        )

        asset_description = response.output_text.strip()
        self.logger.info(f"Extracted asset: {asset_description}")
        return asset_description

    def _make_lock_mask_from_asset(self, asset_path: str) -> io.BytesIO:
        """Create mask: white where asset is visible -> remains, transparent where editing is allowed."""
        try:
            img = Image.open(asset_path).convert("RGBA")
            alpha = img.split()[3]  # Alpha channel

            # Threshold alpha so semi-transparent edge pixels become fully protected
            alpha_binary = alpha.point(lambda v: 255 if v > 0 else 0)
            # Dilate slightly to keep antialiased borders from being altered
            alpha_binary = alpha_binary.filter(ImageFilter.MaxFilter(3))

            # Build grayscale mask: 255 = edit area, 0 = preserve
            mask = Image.new("L", img.size, 255)
            mask.paste(0, (0, 0), alpha_binary)

            # Save mask beside the asset for debugging
            if self.config.SAVE_MASK:
                asset_path_obj = Path(asset_path)
                mask_path = asset_path_obj.with_name(f"{asset_path_obj.stem}_mask.png")
                mask.save(mask_path)
                self.logger.debug(f"Saved lock mask to: {mask_path}")

            buf = io.BytesIO()
            buf.name = "mask.png"
            mask.save(buf, format="PNG")
            buf.seek(0)
            return buf

        except Exception as e:
            self.logger.error(f"Failed to create lock mask: {e}")
            raise

    def _make_outpaint_mask(self, canvas: Image.Image, inner_box: tuple) -> io.BytesIO:
        """Mask for DALL-E 2: white = preserve, black = outpaint."""
        x1, y1, x2, y2 = inner_box
        # Start with black (outpaint everywhere)
        mask = Image.new("L", canvas.size, 0)

        # Create white rectangle where original image is (preserve this area)
        draw = ImageDraw.Draw(mask)
        draw.rectangle([x1, y1, x2, y2], fill=255)

        buf = io.BytesIO()
        buf.name = "mask.png"
        mask.save(buf, format="PNG")
        buf.seek(0)
        return buf
