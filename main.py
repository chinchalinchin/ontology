"""
# Ontology: Entrypoint
"""
import logging
from app.hooks.orchestrator import Orchestrator

def main():
    # Set default logging for the standard application entrypoint
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )
    logger = logging.getLogger(__name__)
    logger.info("Starting Ontology Application...")

    maestro = Orchestrator("world-00")
    maestro.start(None) # Assuming screensize should be passed or defaulted internally
    
if __name__ == "__main__":
    main()