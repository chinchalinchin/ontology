#### Refactor: Phase I, Part II

**Orchestration & Hydration**

- [x] Refactor orchestration complexity in `src/app/orchestrator.py`. The orchestrator functions are far too complex. Use the data structures intelligently to hydrate the asset models. 
- [x] Ensure factory methods align with schemas and models.
- [x] Ensure POPOs are updated to match the data being received through the Pydantic DTOs.
- [ ] Rewrite the CLI from scratch. CLI should not be interacting with low-level objects and SDL interfaces. Have it create an Orchestrator, retrieve the Board and Screens. 
    - [ ] Add default args to the CLI for screensize.
    - [x] Add method to Board to calculate the boardsize based on the position and multiples of Tiles.
    - [ ] Add export methods to Screen.