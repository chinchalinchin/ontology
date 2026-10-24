# Ontology: Prompts

Resources for generating prompts.

## Structure

- `blocks/`: Markdown snippets
- `board/`: Task board, phase templates and archive.
- `tasks/`: Task templates.
- `tools/`: Task tools.
- `main.py`: Jinja2 template extensions and CLI entrypoint.
- `main.yaml`: Task variables.
- `main.md.j2`: Template entrypoint.

## Extensions

### Extension: Standard

- `annotations(path, tags)`: Load source file whose docstrings are tagged with `@tag`.
- `md(path, modifications)`: Load Markdown file and apply modifications
- `file(path)`: Load file into template.
- `command(cmd)`: Return the output text of a shell command.
- `markdown(path)`: List of Markdown files in a directory.
- `typehint(path)`: Infer Markdown typehint of file.
- `yaml(path)`: List of YAML files in a directory.
- `now()`: Current date and time.

### Extension: Project

- `dumps(path)`: Load the content of the latest state dump file in `src/data/dumps/*`.
- `logs(path)`: Load the logs from the latest session in `src/data/logs/*`.

## Quickstart

1. Adjust variables in `main.yaml`.
2. Generate prompt with `python .prompts/main.py`