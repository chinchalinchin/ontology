"""
# Ontology: Entrypoint
"""
from app.hooks.orchestrator import Orchestrator

def main():
    maestro = Orchestrator("world-00")
    maestro.start()
    
if __name__ == "__main__":
    main()