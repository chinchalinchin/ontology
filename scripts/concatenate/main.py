import argparse
import os
from pathlib import Path
from PIL import Image

def main():
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description="Concatenate all PNG images in a directory horizontally.")
    parser.add_argument(
        '-d', '--dir', 
        required=True, 
        help="Directory to scan for .png files"
    )
    parser.add_argument(
        '-o', '--out', 
        default=os.path.join(os.getcwd(), "output.png"), 
        help="Output filepath (defaults to output.png in the present working directory)"
    )
    
    args = parser.parse_args()
    
    # Ensure the provided directory exists
    scan_dir = Path(args.dir)
    if not scan_dir.is_dir():
        print(f"Error: The directory '{args.dir}' does not exist.")
        return

    # Find and sort all .png files in the target directory
    png_files = sorted(scan_dir.glob("*.png"))
    
    if not png_files:
        print(f"No .png files found in directory: {args.dir}")
        return
        
    print(f"Found {len(png_files)} .png files. Concatenating...")

    # Open all images
    images = [Image.open(f) for f in png_files]

    # Calculate total width and the maximum height among all images
    total_width = sum(img.width for img in images)
    max_height = max(img.height for img in images)

    # Create a new blank image with the combined dimensions
    combined_image = Image.new("RGBA", (total_width, max_height))

    # Paste each image horizontally adjacent to the previous one
    x_offset = 0
    for img in images:
        combined_image.paste(img, (x_offset, 0))
        x_offset += img.width

    # Save the resulting image
    combined_image.save(args.out)
    print(f"Successfully saved concatenated image to: {args.out}")

    # Close open file handles
    for img in images:
        img.close()

if __name__ == "__main__":
    main()