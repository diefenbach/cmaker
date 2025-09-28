from PIL import Image, ImageDraw, ImageFont

from .config import Config
from .logger import CampaignLogger


class ImageProcessor:
    """Handles image processing operations like cropping and text overlay."""

    def __init__(self, config: Config, logger: CampaignLogger):
        self.config = config
        self.logger = logger

    def prepare_canvas(self, input_image: str, canvas_size: tuple = None, scale_factor: float = None):
        """Scales input by scale_factor and positions it for DALL-E 2 outpainting."""
        if canvas_size is None:
            canvas_size = (1024, 1024)
        if scale_factor is None:
            scale_factor = self.config.SCALE_FACTOR

        img = Image.open(input_image).convert("RGBA")

        # Scale the image down by the scale factor
        original_size = img.size
        new_size = (int(original_size[0] * scale_factor), int(original_size[1] * scale_factor))
        img_scaled = img.resize(new_size, Image.LANCZOS)
        self.logger.debug(f"Scaled image from {original_size} to {new_size} (scale factor: {scale_factor})")

        # Center the scaled image on the canvas
        tw, th = canvas_size
        iw, ih = img_scaled.size
        x = (tw - iw) // 2
        y = (th - ih) // 2
        inner_box = (x, y, x + iw, y + ih)

        canvas = Image.new("RGBA", (tw, th), (255, 255, 255, 255))
        canvas.paste(img_scaled, (x, y), mask=img_scaled)

        self.logger.debug(f"Asset positioned at: {inner_box}")
        return canvas, inner_box

    def crop_to_ratio(self, image: Image.Image, out_path: str, ratio: str):
        """Resize and crop image to specified aspect ratio."""
        iw, ih = image.size
        self.logger.debug(f"Input size for {ratio} conversion: {iw}x{ih}")

        if ratio == "16x9":
            # Resize to 1536x1536 then crop to 1536x864 (16:9 landscape)
            resized_image = image.resize((1536, 1536), Image.LANCZOS)
            final_result = resized_image.crop((0, 336, 1536, 1200))  # Crop from center
        elif ratio == "9x16":
            # Resize to 1536x1536 then crop to 864x1536 (9:16 portrait)
            resized_image = image.resize((1536, 1536), Image.LANCZOS)
            final_result = resized_image.crop((336, 0, 1200, 1536))  # Crop from center
        else:
            raise ValueError(f"Unsupported ratio: {ratio}")

        final_result.save(out_path)
        self.logger.info(f"Saved: {out_path} ({final_result.size[0]}x{final_result.size[1]})")

    def add_text_overlay(
        self, image: Image.Image, text: str, font_size: int = None, opacity: int = None
    ) -> Image.Image:
        """Add semi-transparent text overlay to the bottom of the image with automatic text sizing."""
        if not text or not text.strip():
            return image

        if font_size is None:
            font_size = self.config.FONT_SIZE
        if opacity is None:
            opacity = self.config.TEXT_OPACITY

        # Create a copy to avoid modifying the original
        img = image.copy()

        # Get image dimensions
        img_width, img_height = img.size

        # Calculate margins
        margin_x = int(img_width * self.config.MARGIN_PERCENTAGE)
        margin_y = int(img_height * self.config.MARGIN_PERCENTAGE)

        # Available space for text
        available_width = img_width - (2 * margin_x)
        available_height = img_height - (2 * margin_y)

        # Try different font sizes and text wrapping strategies
        final_font, final_text, final_width, final_height = self._find_optimal_text_layout(
            text, font_size, available_width, available_height
        )

        if final_font is None:
            self.logger.warning("Could not fit text in available space, using original text")
            return img

        # Position text at bottom with margins
        x = img_width - final_width - margin_x
        y = img_height - final_height - margin_y

        # Create a semi-transparent overlay
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)

        # Add a subtle background rectangle for better text readability
        padding = 10
        overlay_draw.rectangle(
            [x - padding, y - padding, x + final_width + padding, y + final_height + padding],
            fill=(0, 0, 0, 100),  # Semi-transparent black background
        )

        # Draw the text with specified opacity
        overlay_draw.text((x, y), final_text, font=final_font, fill=(255, 255, 255, opacity))

        # Composite the overlay onto the image
        if img.mode != "RGBA":
            img = img.convert("RGBA")

        img = Image.alpha_composite(img, overlay)

        return img

    def _find_optimal_text_layout(self, text: str, initial_font_size: int, max_width: int, max_height: int):
        """Find the best font size to fit text within constraints."""
        # Try different font sizes from largest to smallest
        for font_size in range(initial_font_size, 12, -4):  # Decrease by 4 each time, minimum 12
            font = self._get_font(font_size)
            if font is None:
                continue

            # Measure text dimensions
            bbox = font.getbbox(text)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # Check if it fits
            if text_width <= max_width and text_height <= max_height:
                self.logger.debug(f"Found optimal layout: font_size={font_size}")
                return font, text, text_width, text_height

        return None, None, 0, 0

    def _get_font(self, font_size: int):
        """Get font with specified size, fall back to default if not available."""
        for font_path in self.config.FONT_PATHS:
            try:
                return ImageFont.truetype(font_path, font_size)
            except (OSError, IOError):
                continue
        return ImageFont.load_default()
