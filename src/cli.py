
"""
# Ontology: CLI
"""
# Standard Libraries
import sys
from pathlib import Path
import argparse

# ---------------------------------------------------------
# PATH RESOLUTION: Add project root to sys.path
# This allows Python to find the /libs directory at the root
# ---------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Application Libraries
from app.hooks.orchestrator import migrate, orchestrate

# Cython Libraries
from libs.render import init, canvas, construct as render_construct, render as sdl_render, save, quit_sdl
from libs.registry import Registry

# TODO: This is utter garbarge. Scrape it. CLI shouldn't be interacting with low-level game objects.
#       Create an Orchestrator.
def cli_construct(args):
    # Construct Step 1: Parse the immutable configuration via migrate
    states = migrate(args.board_key)
    tiles = [s for s in states if s.category == "tiles" and s.layer == args.layer]
    
    # Construct Step 2: Initialize Registry and boot Cython SDL2 Interface
    init()
    registry = Registry()
    
    # Construct Step 3: Allocate hardware-safe background chunks (1024 x 1024)
    chunk_size = 1024
    bg_canvas = canvas(chunk_size, chunk_size)
    
    # Construct Step 4: Iterate through deployed Tiles and draw directly to canvas
    cython_tiles = []
    for tile in tiles:
        frame_key = tile.taxonomy.id
        tex_data = registry.data(frame_key)
        if tex_data:
            tex, sx, sy, sw, sh = tex_data
            cython_tiles.append((
                tex, sx, sy, sw, sh,
                tile.position.x, tile.position.y,
                sw, sh, 
                tile.multiple.nx, tile.multiple.ny
            ))
            
    render_construct(bg_canvas, cython_tiles)
    
    # Construct Step 5: Export a specific targeted chunk to disk for layout debugging
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{args.board_key}_{args.layer}_chunk.png"

    # Pass the bg_canvas as the explicit target
    save(str(out_path), chunk_size, chunk_size, target=bg_canvas)   
    quit_sdl()

# TODO: This is utter garbarge. Scrape it. CLI shouldn't be interacting with low-level game objects.
#       Create an Orchestrator.
def cli_render(args):
    # Render Step 1: Execute construct steps to generate cached background
    states = migrate(args.board_key)
    
    init()
    registry = Registry()
    
    chunk_size = 1024
    # TODO: calculate board size dynamically instead of this bullshit.
    bg_canvas = canvas(chunk_size, chunk_size)
    
    cython_tiles = []
    for s in states:
        if s.category == "tiles" and s.layer == args.layer:
            # TODO: this is broken because key isn't on state now.
            #       need to instantiate board.
            tex_data = registry.data(s.key)
            if tex_data:
                tex, sx, sy, sw, sh = tex_data
                cython_tiles.append((
                    tex, 
                    sx, 
                    sy, 
                    sw, 
                    sh,
                    s.position.x, 
                    s.position.y,
                    sw, 
                    sh,
                    s.multiple.nx,
                    s.multiple.ny
                ))

    # TODO: don't do this in the CLI. Why is CLI instantiating objects?
    #       delegate everything to orchestration and screen.
    
    render_construct(bg_canvas, cython_tiles)
    
    # Render Step 2, 3, 4: Parse mutable configs, instantiate assets, iterate
    # (Encapsulated perfectly in the orchestrate routine)
    board, _ = orchestrate(args.board_key, registry=registry)
    
    # Render Step 5: Pass the background pointer and evaluated assets to render()
    active_assets = []
    for asset in board.assets:
        if asset.state.layer == args.layer and asset.category != AssetCategories.TILES:
            frame_key = asset.frame.key(asset.taxonomy.id, asset.state)
            tex_data = registry.data(frame_key)
            if tex_data:
                tex, sx, sy, sw, sh = tex_data
                dx, dy = asset.state.position.x, asset.state.position.y
                dw, dh = asset.properties.dimensions.l, asset.properties.dimensions.w          
                active_assets.append((tex, sx, sy, sw, sh, dx, dy, dw, dh))
                
    sdl_render(bg_canvas, active_assets, 0, 0, chunk_size, chunk_size)
    
    # Execute save to snapshot full composite scene
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{args.board_key}_{args.layer}_render.png"
    save(str(out_path), chunk_size, chunk_size)
    
    quit_sdl()

def main():
    parser = argparse.ArgumentParser(description="Ontology CLI Tools")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    parser_c = subparsers.add_parser("construct")
    parser_c.add_argument("board_key", type=str)
    parser_c.add_argument("--out", type=str, required=True)
    parser_c.add_argument("--layer", type=str, required=True)
    
    parser_r = subparsers.add_parser("render")
    parser_r.add_argument("board_key", type=str)
    parser_r.add_argument("--out", type=str, required=True)
    parser_r.add_argument("--layer", type=str, required=True)
    
    args = parser.parse_args()
    if args.command == "construct":
        cli_construct(args)
    elif args.command == "render":
        cli_render(args)

if __name__ == "__main__":
    main()