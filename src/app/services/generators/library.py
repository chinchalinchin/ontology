"""
# Ontology: app.services.generators.library

Package for indexing and retrieving dialogue.
"""
# Standard Libraries
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class Library:
    """
    Parses and serves the plot dialogue schema.
    """
    def __init__(self, data: Dict[str, Dict[str, str]]):
        self.data = data or {}
        logger.info(self.data)

    def fetch(self, plot: str, persona: str, lexicon: str) -> str:
        if not plot or not persona or not lexicon:
            logger.warning(f"Library fetch missing keys: plot={plot}, persona={persona}, lexicon={lexicon}")
            return ""
        
        # Traverse library schema: library[plot][persona][lexicon]
        plot_data = self.data.get(plot, {})
        persona_data = plot_data.get(persona, {})
        content = persona_data.get(lexicon, "")
        
        if not content:
            logger.warning(f"Library fetch failed for {plot}.{persona}.{lexicon}")
        
        return str(content)