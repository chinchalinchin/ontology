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

- `annotations(path, tags, strategy)`: Load a source file whose docstrings are tagged with `@tag`.
    * `tags` is a list of queries. `strategy` is applied to the queried source code to filter the results.
    * Source files can have multiple `tags`. If `strategy == 'OR'`, then any source code where the query list matches any of its `tags` is returned. If `strategy == 'AND'`, then any source code where all of the query list `tags` are matched is returned. 
- `md(path, modifications)`: Load Markdown file and apply modifications
- `file(path)`: Load file into template.
- `command(cmd)`: Return the output text of a shell command.
- `markdown(path)`: List of Markdown files in a directory.
- `typehint(path)`: Infer the Markdown typehint of file.
- `yaml(path)`: List of YAML files in a directory.
- `now()`: Current date and time.

**Tagging**

1. `annotations()` scans a directory for any source files that have a `@tag` annotation in their docstrings.
2. `tags` is a list of `annotation` queries. `strategy` is applied to the return result of the queried source code to filter the results.
3. Source code can have multiple tags. If strategy is `OR`, then any source code with where the query list matches any of its tags is returned. If strategy is `AND`, then any source with all of the query list tags is returned. 

### Extension: Project

- `dumps(path)`: Load the content of the latest state dump file in `src/data/dumps/*`.
- `logs(path)`: Load the logs from the latest session in `src/data/logs/*`.

## Quickstart

1. Adjust variables in `main.yaml`.
2. Generate prompt with `python .prompts/main.py`