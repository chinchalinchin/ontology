import argparse
from pathlib import Path
from mermaid import Mermaid

def main():
    parser = argparse.ArgumentParser(description="Convert a Mermaid .mmd file to SVG.")
    parser.add_argument("filepath", type=Path, help="Path to the input .mmd file.")
    args = parser.parse_args()

    input_path = args.filepath
    if not input_path.is_file():
        raise FileNotFoundError(f"File not found: {input_path}")

    output_path = input_path.with_suffix(".svg")

    with open(input_path, "r", encoding="utf-8") as f:
        mmd_text = f.read()

    diagram = Mermaid(mmd_text)
    diagram.to_svg(str(output_path))
    
    print(f"Successfully converted {input_path.name} to {output_path}")

if __name__ == "__main__":
    main()