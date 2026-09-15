import argparse
from pathlib import Path
from PIL import Image

SCRIPT_DIR = Path(__file__).resolve().parent


def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert a grid-based spritesheet into a single-row frame strip."
    )
    parser.add_argument("-r", "--rows", type=int, required=True, help="Number of rows in the grid")
    parser.add_argument("-c", "--columns", type=int, required=True, help="Number of columns in the grid")
    parser.add_argument(
        "-o",
        "--output_dir",
        type=Path,
        default=SCRIPT_DIR,
        help="Directory to save output image (defaults to the directory containing this script)",
    )
    parser.add_argument("file_name", type=Path, help="Path to the spritesheet image")
    return parser.parse_args()


def main():
    args = parse_args()
    input_path = args.file_name

    if not input_path.is_file():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    with Image.open(input_path) as sheet:
        sheet_width, sheet_height = sheet.size

        frame_width = sheet_width // args.columns
        frame_height = sheet_height // args.rows
        total_frames = args.rows * args.columns

        # Preserve source mode and transparency
        strip = Image.new(sheet.mode, (frame_width * total_frames, frame_height))

        frame_index = 0
        for row in range(args.rows):
            for col in range(args.columns):
                left = col * frame_width
                top = row * frame_height
                right = left + frame_width
                bottom = top + frame_height

                frame = sheet.crop((left, top, right, bottom))
                strip.paste(frame, (frame_index * frame_width, 0))
                frame_index += 1

        output_path = output_dir / f"strip_{input_path.name}"
        strip.save(output_path)
        print(f"Saved {total_frames} frames to {output_path}")


if __name__ == "__main__":
    main()