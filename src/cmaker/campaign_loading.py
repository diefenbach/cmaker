import yaml
from pathlib import Path

from .config import Config
from .logger import CampaignLogger


class CampaignLoader:
    """Handles loading and validation of campaign briefs."""

    def __init__(self, config: Config, logger: CampaignLogger):
        self.config = config
        self.logger = logger

    def load_campaign_briefs(self, campaigns_dir: str = None):
        """Load all YAML brief files from campaigns directory."""
        if campaigns_dir is None:
            campaigns_dir = self.config.CAMPAIGNS_DIR

        briefs = []
        campaigns_path = Path(campaigns_dir)

        if not campaigns_path.exists():
            self.logger.error(f"Campaigns directory not found: {campaigns_dir}")
            return briefs

        for campaign_dir in campaigns_path.iterdir():
            if campaign_dir.is_dir():
                # Check if campaign is already completed
                meta_file = campaign_dir / "meta.yaml"
                if meta_file.exists():
                    try:
                        with open(meta_file, "r") as f:
                            meta_data = yaml.safe_load(f)
                            if meta_data and meta_data.get("status", "") == "done":
                                self.logger.info(f"Skipping completed campaign: {campaign_dir.name}")
                                continue
                    except yaml.YAMLError as e:
                        self.logger.warning(f"Failed to parse meta.yaml for {campaign_dir.name}: {e}")

                brief_file = campaign_dir / self.config.BRIEF_FILE
                if brief_file.exists():
                    try:
                        with open(brief_file, "r") as f:
                            brief_data = yaml.safe_load(f)
                            brief_data["campaign_name"] = campaign_dir.name
                            brief_data["campaign_path"] = str(campaign_dir)
                            briefs.append(brief_data)
                            self.logger.info(f"Loaded campaign: {campaign_dir.name}")
                    except yaml.YAMLError as e:
                        self.logger.error(f"Failed to parse {brief_file}: {e}")

        return briefs
