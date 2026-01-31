"""Configuration for the watch server."""

import os
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
    
    db_url: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/veille_technique")
    
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

