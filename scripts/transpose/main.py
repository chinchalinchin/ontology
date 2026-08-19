import argparse
import os
from PIL import Image

def resolve_path(path: str) -> str:
    """Normalize relative paths (including './' notation) against the CWD, while preserving absolute paths."""
    return os.path.abspath(os.path.expanduser(path))

def main():
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(
        description="Transpose a vertical sprite column into a horizontal row of frames."
    )
    parser.add_argument(
        '-v', '--vert', 
        type=int, 
        required=True, 
        help="Number of vertical frames in the image column"
    )
    parser.add_argument(
        '-f', '--file', 
        type=str, 
        required=True, 
        help="File path to the input PNG image"
    )
    parser.add_argument(
        '-o', '--out', 
        type=str, 
        default="output.png", 
        help="Output filepath (defaults to output.png in the present working directory)"
    )
    
    args = parser.parse_args()
    
    # Resolve input and output filepaths
    input_path = resolve_path(args.file)
    output_path = resolve_path(args.out)
    
    # Check if the input file exists
    if not os.path.isfile(input_path):
        print(f"Error: The file '{input_path}' does not exist.")
        return

    try:
        # Open the vertical image
        img = Image.open(input_path)
    except Exception as e:
        print(f"Error opening image: {e}")
        return

    # Get original dimensions
    w, h = img.size
    
    # Calculate the height of a single frame
    if h % args.vert != 0:
        print(f"Warning: Total height ({h}px) is not perfectly divisible by {args.vert} frames. Truncation may occur.")
        
    frame_h = h // args.vert

    # Create a new blank image with the transposed dimensions (Width * Number of Frames, Single Frame Height)
    horizontal_image = Image.new("RGBA", (w * args.vert, frame_h))

    print(f"Processing '{input_path}' ({w}x{h})...")
    print(f"Extracting {args.vert} frames (size: {w}x{frame_h} each).")

    # Loop through each vertical slice, crop it, and paste it horizontally
    for i in range(args.vert):
        # Define the crop box: (left, upper, right, lower)
        crop_box = (0, i * frame_h, w, (i + 1) * frame_h)
        frame = img.crop(crop_box)
        
        # Paste it horizontally into the new image
        paste_coords = (i * w, 0)
        horizontal_image.paste(frame, paste_coords)

    # Save the resulting image
    horizontal_image.save(output_path)
    print(f"Successfully saved horizontal image to: {output_path}")

    # Close open file handles
    img.close()
    horizontal_image.close()

if __name__ == "__main__":
    main()