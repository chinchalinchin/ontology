"""
# Ontology: Entrypoint
"""
# Standard Libraries
import logging

# Application Libraries
from app.config.enums import Devices
from app.config.logging import configure_logging
from app.services.orchestration.constructors import Orchestrator

# Cython Libraries

from libs.core.models import Dimensions

def main():
    # Set default logging for the standard application entrypoint
    configure_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Ontology Application...")
    Orchestrator().orchestrate('world-01', Dimensions(w=800, l=600), Devices.KEYBOARD)
    
if __name__ == "__main__":
    main()