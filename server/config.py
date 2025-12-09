"""
Configuration for the watch server.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class ScraperConfig:
    """Configuration for a specific scraper."""
    enabled: bool = True
    limit_latest: int = 20
    
    limit_all: int = 100


@dataclass
class ServerConfig:
    """Global server configuration."""
    
    db_path: str = "veille_technique.db"
    
    watch_interval_seconds: int = 300
    
    log_level: str = "INFO"
    
    scrapers: Dict[str, ScraperConfig] = None
    
    def __post_init__(self):
        """Initialize default scraper configuration."""
        if self.scrapers is None:
            self.scrapers = {
                "arxiv": ScraperConfig(enabled=True, limit_latest=20, limit_all=100),
                "github": ScraperConfig(enabled=True, limit_latest=20, limit_all=100),
                "medium": ScraperConfig(enabled=True, limit_latest=20, limit_all=100),
                "lemonde": ScraperConfig(enabled=True, limit_latest=20, limit_all=100),
                "huggingface": ScraperConfig(enabled=True, limit_latest=20, limit_all=100),
            }
    
    @classmethod
    def from_file(cls, filepath: str) -> "ServerConfig":
        """Load configuration from JSON/YAML file."""
        import json
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            if "scrapers" in data:
                data["scrapers"] = {
                    name: ScraperConfig(**cfg)
                    for name, cfg in data["scrapers"].items()
                }
            
            return cls(**data)
        except FileNotFoundError:
            print(f"Config file {filepath} not found, using default config")
            return cls()


DEFAULT_CONFIG = ServerConfig()

DEV_CONFIG = ServerConfig(
    db_path="veille_technique_dev.db",
    watch_interval_seconds=60,
)

PROD_CONFIG = ServerConfig(
    db_path="veille_technique.db",
    watch_interval_seconds=600,
    log_level="WARNING",
)
