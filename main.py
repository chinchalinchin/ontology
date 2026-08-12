"""
# Ontology: Entrypoint
"""
# Standard Libraries
import logging

# Application Libraries
from app.hooks.orchestrator import Orchestrator
from app.config.enums import Devices

# Cython Libraries

from libs.core import Dimensions
def main():
    # Set default logging for the standard application entrypoint
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )
    logger = logging.getLogger(__name__)
    logger.info("Starting Ontology Application...")

    maestro = Orchestrator("world-00")
    maestro.start(Dimensions(w=800, l=600), Devices.KEYBOARD.value)
    
if __name__ == "__main__":
    main()