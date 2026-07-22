# Task Board

## Phase 1: Rendering

1. SDL2 Interface:
    - Parameters:
        - `asset_directory`: defaults to `/src/assets/`
    - Methods:
        - Init:
            - Recursively loads `/src/assets/` into a keyed map.
        - Canvas:
            - Accepts a list of Assets.
            - Iterates over list.
            - Constructs image and saves it in memory as an attribute. 
        - Render:    
            - Creates a buffer of 
            - Accepts a list of Assets.
            - Iterates over list.
            - Constructs image by copying images onto canvas.
2. Command Line: `python main.py render <board-key> --out <directory>`
    - Load in configuration in `src/data/boards/<board-key>`
    - Assemble and render immutable assets in canvas.
    - Output image into `<directory>` as a `.png` image.
    
## Phase 2: Editor

TODO

## Phase 3: Sprite Assembly

TODO

## Phase 4: Gameplay Loop

TODO

## Phase 5: Physics

TODO

## Phase 6: NPCs 

TODO

## Phase 7: Combat

TODO

## Phase 8: Cutscenes

TODO