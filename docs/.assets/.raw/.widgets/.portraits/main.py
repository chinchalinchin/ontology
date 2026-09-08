import os
import glob
from PIL import Image

def build_horizontal_strips(input_dir=".", output_dir="output"):
    # Ensure the output directory exists so originals are not overwritten
    os.makedirs(output_dir, exist_ok=True)
    
    # 2x3 grid configuration
    rows = 2
    cols = 3
    
    for prefix in ["female", "male"]:
        # Find and sort the files to maintain the numbering sequence (00 to 13)
        search_pattern = os.path.join(input_dir, f"{prefix}-*.png")
        files = sorted(glob.glob(search_pattern))
        
        if not files:
            continue
            
        # Dynamically calculate cell dimensions from the first image
        # For a 900x760 image in a 2x3 grid, cell_width=300, cell_height=380
        with Image.open(files[0]) as first_img:
            sheet_w, sheet_h = first_img.size
            cell_width = sheet_w // cols
            cell_height = sheet_h // rows
            
        # Iterate over every grid coordinate
        for r in range(rows):
            for c in range(cols):
                
                # Create a blank transparent canvas for the concatenated row
                strip_width = len(files) * cell_width
                strip = Image.new("RGBA", (strip_width, cell_height))
                
                # Extract the specific cell from every file and paste it into the strip
                for index, filepath in enumerate(files):
                    with Image.open(filepath) as img:
                        left = c * cell_width
                        top = r * cell_height
                        right = left + cell_width
                        bottom = top + cell_height
                        
                        cell_img = img.crop((left, top, right, bottom))
                        
                        paste_x = index * cell_width
                        strip.paste(cell_img, (paste_x, 0))
                
                # Save the final horizontal strip
                filename = f"{prefix}_row{r}_col{c}.png"
                out_path = os.path.join(output_dir, filename)
                strip.save(out_path)

if __name__ == "__main__":
    # Execute in the current directory, outputs to an "output" subdirectory
    build_horizontal_strips()