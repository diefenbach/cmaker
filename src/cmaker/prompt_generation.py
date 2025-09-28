import os

from dotenv import load_dotenv
from openai import OpenAI

from .config import Config
from .logger import CampaignLogger

load_dotenv()

class PromptGenerator:
    """Handles prompt generation and optimization."""

    def __init__(self, config: Config, logger: CampaignLogger):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.config = config
        self.logger = logger

    def create_dalle_prompt(self, detailed_prompt: str) -> str:
        """Create a concise DALL-E prompt from the detailed scene description."""
        self.logger.info("Creating concise DALL-E prompt...")

        llm_prompt = f"""
            Convert this detailed scene description into a concise DALL-E prompt (max {self.config.MAX_DALLE_PROMPT_LENGTH} characters):

            {detailed_prompt}

            Requirements:
            - Keep only essential visual elements
            - Focus on composition, lighting, and key objects
            - Remove technical photography details
            - Remove post-production notes
            - Keep it under {self.config.MAX_DALLE_PROMPT_LENGTH} characters
            - Make it optimized for AI image generation

            Return ONLY the concise prompt, no additional text."""

        try:
            response = self.client.responses.create(
                model=self.config.GPT_MODEL,
                input=llm_prompt,
            )

            dalle_prompt = response.output_text.strip()
            self.logger.info(f"DALL-E prompt: {' '.join(dalle_prompt.split()[:10])}")
            return dalle_prompt

        except Exception as e:
            self.logger.error(f"Failed to create DALL-E prompt: {e}")
            # Fallback: truncate the original prompt
            return (
                detailed_prompt[: self.config.MAX_DALLE_PROMPT_LENGTH] + "..."
                if len(detailed_prompt) > self.config.MAX_DALLE_PROMPT_LENGTH
                else detailed_prompt
            )

    def create_campaign_prompt_with_llm(self, brief: dict) -> str:
        """
        Generate a sophisticated scene prompt using GPT-5 from campaign brief data.
        """
        self.logger.info("Generating prompt with GPT-5...")

        llm_prompt = f"""
            Create a professional product photography scene prompt for this campaign, not more than 
            {self.config.MAX_SCENE_PROMPT_LENGTH} characters:

            Campaign Brief:
                - Region: {brief.get('region', 'Not specified')}
                - Market: {brief.get('market', 'Not specified')}
                - Audience: {brief.get('audience', 'Not specified')}
                - Message: {brief.get('message', 'Not specified')}
                - Product: {brief.get('product', 'Not specified')}
                - Asset: {brief.get('asset', 'Not specified')}

            Requirements:
                - Focus on the main product as hero element
                - Reflect target audience lifestyle
                - Include brand message and values
                - Consider regional/market context
                - Use professional photography terms
                - Optimize for AI image generation
                - No text or typography
                - Commercial quality scene

                Return a detailed scene description with lighting, composition, setting, mood, and visual style. 
                Return ONLY the prompt, no additional text.
                
                Use the provided asset exactly as-is, unchanged, pixel-perfect.
                Do not move, open, modify, or alter the product in any way.

                Only extend or generate the background scene around it.
                No text, no logos, no subtitles, no labels."""

        try:
            response = self.client.responses.create(
                model=self.config.GPT_MODEL,
                input=llm_prompt,
            )
            scene_prompt = response.output_text.strip()
            self.logger.info(f"Generated prompt: {' '.join(scene_prompt.split()[:10])}")
            return scene_prompt

        except Exception as e:
            self.logger.error(f"Failed to generate prompt with GPT-5: {e}")
            self.logger.info("Using default prompt...")
            return "A professional product photography scene, clean studio lighting, high quality, commercial photography style"
