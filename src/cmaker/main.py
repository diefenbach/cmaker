#!/usr/bin/env python3
"""
Campaign Image Processing - Main Entry Point

A modular system for processing marketing campaigns with AI-generated images.
"""

from .config import Config
from .logger import CampaignLogger
from .campaign_processing import CampaignProcessor


def main():
    """Entry point for the application."""
    config = Config()
    logger = CampaignLogger()
    processor = CampaignProcessor(config, logger)

    processor.process_all_campaigns()


if __name__ == "__main__":
    main()
