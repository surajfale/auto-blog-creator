"""Configuration management for auto-blog-creator."""

import os
from pathlib import Path
from typing import Any, Dict

import yaml
from dotenv import load_dotenv
from loguru import logger


class Config:
    """Manages application configuration from YAML and environment variables."""

    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize configuration.

        Args:
            config_path: Path to the YAML configuration file
        """
        # Load environment variables
        load_dotenv()

        # Load YAML configuration
        self.config_path = Path(config_path)
        self.config_data = self._load_yaml()

        # Setup logging
        self._setup_logging()

    def _load_yaml(self) -> Dict[str, Any]:
        """Load configuration from YAML file.

        Returns:
            Dictionary containing configuration data
        """
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found: {self.config_path}, using defaults")
            return {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML config: {e}")
            return {}

    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        log_config = self.config_data.get("logging", {})
        level = log_config.get("level", "INFO")
        log_format = log_config.get(
            "format",
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>",
        )

        # Configure loguru
        logger.remove()  # Remove default handler
        logger.add(
            lambda msg: print(msg, end=""),
            format=log_format,
            level=level,
            colorize=True,
        )

        # Optionally add file logging
        log_file = log_config.get("file")
        if log_file:
            logger.add(log_file, format=log_format, level=level, rotation="10 MB")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key.

        Args:
            key: Configuration key in dot notation (e.g., 'content.tone')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self.config_data

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    @property
    def ollama_api_key(self) -> str:
        """Get Ollama API key from environment."""
        return os.getenv("OLLAMA_API_KEY", "")

    @property
    def ollama_model(self) -> str:
        """Get Ollama model name."""
        return os.getenv("OLLAMA_MODEL", "gpt-oss:120b-cloud")

    @property
    def devto_api_key(self) -> str:
        """Get Dev.to API key from environment."""
        return os.getenv("DEVTO_API_KEY", "")

    @property
    def devto_auto_publish(self) -> bool:
        """Check if auto-publish to dev.to is enabled."""
        return os.getenv("DEVTO_AUTO_PUBLISH", "false").lower() == "true"

    @property
    def github_token(self) -> str:
        """Get GitHub token from environment."""
        token = os.getenv("GITHUB_TOKEN", "")
        # Filter out placeholder values
        if token and "your_github_token_here" in token.lower():
            return ""
        return token

    def validate(self) -> bool:
        """Validate that required configuration is present.

        Returns:
            True if configuration is valid, False otherwise
        """
        errors = []

        if not self.ollama_api_key:
            errors.append("OLLAMA_API_KEY not set")

        if not self.devto_api_key:
            errors.append("DEVTO_API_KEY not set")

        if errors:
            logger.error("Configuration validation failed:")
            for error in errors:
                logger.error(f"  - {error}")
            return False

        logger.info("Configuration validation passed")
        return True
