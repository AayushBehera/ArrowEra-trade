"""
ArrowEra Trade - Research Base Agent

Abstract base class for AI research agents.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)

class BaseAgent(ABC):
    """Abstract base class for research agents."""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        self.llm_provider = self.config.get("llm_provider", "openai")
        self.model = self.config.get("model", "gpt-4-turbo-preview")

    @abstractmethod
    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform analysis based on the provided context.
        
        Args:
            context: Dictionary containing relevant data (market data, news, etc.)
        
        Returns:
            Dictionary containing analysis results, signals, and reasoning.
        """
        pass

    def _log_start(self, context: Dict[str, Any]):
        """Log the start of an analysis."""
        logger.info(
            f"Starting analysis for {self.name}",
            agent=self.name,
            context_keys=list(context.keys())
        )

    def _log_complete(self, result: Dict[str, Any]):
        """Log the completion of an analysis."""
        logger.info(
            f"Analysis complete for {self.name}",
            agent=self.name,
            result_keys=list(result.keys())
        )

    def _format_prompt(self, template: str, **kwargs) -> str:
        """Format a prompt template with provided kwargs."""
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logger.error(f"Missing key for prompt template: {e}")
            raise