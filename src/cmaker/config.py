class Config:
    """Configuration settings for the campaign processor."""

    # API Settings
    DALL_E_MODEL = "gpt-image-1"
    GPT_MODEL = "gpt-5-nano"

    # Image Processing
    CANVAS_SIZE = (1024, 1024)
    SCALE_FACTOR = 0.56
    FONT_SIZE = 48
    TEXT_OPACITY = 200
    MARGIN_PERCENTAGE = 0.05

    # Font Paths (macOS)
    FONT_PATHS = ["/System/Library/Fonts/Helvetica.ttc", "/System/Library/Fonts/Arial.ttf"]

    # File Structure
    CAMPAIGNS_DIR = "campaigns"
    RESULTS_DIR = "results"
    ASSETS_DIR = "assets"
    BRIEF_FILE = "brief.yaml"

    # Prompt Settings
    MAX_DALLE_PROMPT_LENGTH = 800
    MAX_SCENE_PROMPT_LENGTH = 80000
    TEMPERATURE = 0.7

    # Save Mask
    SAVE_MASK = True

    # Save Prompt
