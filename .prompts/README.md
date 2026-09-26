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

- `file(path)`: Load file into template.
- `command(cmd)`: Return text from a shell command.
- `markdown(path)`: List of Markdown files in a directory.
- `yaml(path)`: List of YAML files in a directory.
- `now()`: Current date and time.

## Quickstart

1. Adjust variables in `main.yaml`. The template entrypoint uses the following schema, `tasks/{{ template.verb }}/{{ template.noun }}` to locate a template in the `tasks/` directory. 
2. Generate prompt with `python .prompts/main.py`