This is a script I use to generate context,

```python
"""
@script.context

# Jinja2 Template Renderer

This module automates the generation of context-rich Markdown files. It extends the standard Jinja2 environment with custom hooks for filesystem access and shell command execution, allowing templates to dynamically include the latest project state.

Usage:
    python task.py [template] [--output output_file] [--vars vars_file]

Dependencies:
- jinja2
- panflute
- pydantic
- pyyaml

Security Warning:
    This script enables Arbitrary Code Execution (ACE) via the `command` function. Only render templates from trusted sources.
"""

# Standard Libraries
from collections import defaultdict
from contextvars import ContextVar
from datetime import datetime
from functools import wraps
from itertools import chain
from pathlib import Path
from typing import Union, Any, Dict, List, Callable
import argparse
import ast
import inspect
import os
import re
import subprocess
import sys
import traceback

# External Libraries
from pydantic import BaseModel, ConfigDict, Field, model_validator
import jinja2
import panflute as pf
import yaml as pyyaml

# ----------------------------------------------------------------
# -------------------------------------------------- CONFIGURATION
# ----------------------------------------------------------------

OUTPUT_DIR                      = os.environ.get('OUTPUT_DIR', 'build')
DATA_DIR                        = os.environ.get('DATA_DIR', 'data')
SHELL                           = os.environ.get('SHELL', '/bin/bash')

# ----------------------------------------------------------------
# ------------------------------------ APP CONTEXT & MACRO REGISTRY
# ----------------------------------------------------------------

class AppContext(BaseModel):
    """
    Pydantic model holding all configuration loaded from the `data/` directory,
    keyed by the YAML filename stem.
    """
    model_config = ConfigDict(extra="allow")

    defaults: Dict[str, Any] = Field(default_factory=dict)
    queries: Dict[str, Any] = Field(default_factory=dict)
    typehints: Dict[str, str] = Field(default_factory=dict)
    properties: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def _unwrap_typehints(cls, data: Any) -> Any:
        """
        Supports `typehints.yaml` whether it is structured with a top-level
        `MARKDOWN_TYPE_HINTS:` key or as a flat dictionary of extensions.
        """
        if isinstance(data, dict) and "typehints" in data:
            th = data["typehints"]
            if isinstance(th, dict) and "MARKDOWN_TYPE_HINTS" in th:
                data["typehints"] = th["MARKDOWN_TYPE_HINTS"]
        return data


_context: ContextVar[AppContext] = ContextVar("active_context", default=AppContext())
_REGISTRY: Dict[str, Callable] = {}


def macro(func: Callable | None = None, *, name: str | None = None) -> Callable:
    """
    Decorator that automatically registers a function into the Jinja2 environment
    and transparently injects `AppContext` if the function's first parameter is
    named `ctx` or `context` (or annotated with `AppContext`).
    """
    def decorator(fn: Callable) -> Callable:
        macro_name = name or fn.__name__
        sig = inspect.signature(fn)
        params = list(sig.parameters.values())

        wants_ctx = bool(
            params and (
                params[0].name in ("ctx", "context")
                or params[0].annotation is AppContext
            )
        )

        @wraps(fn)
        def wrapper(*args, **kwargs):
            if wants_ctx:
                return fn(_context.get(), *args, **kwargs)
            return fn(*args, **kwargs)

        _REGISTRY[macro_name] = wrapper
        return wrapper

    if func is not None:
        return decorator(func)
    return decorator

# ----------------------------------------------------------------
# ------------------------------------------------ MARKDOWN MACROS
# ----------------------------------------------------------------

MD_MODIFIERS = {
    # Increases or decreases heading levels (clamped between 1 and 6)
    "header": lambda shift: (
        lambda elem, _doc: (
            setattr(elem, "level", min(max(elem.level + int(shift), 1), 6))
            if isinstance(elem, pf.Header)
            else None
        )
    ),
    # Example: set fallback language for untyped fenced code blocks
    "default-codeblock": lambda lang: (
        lambda elem, _doc: (
            elem.classes.append(str(lang))
            if isinstance(elem, pf.CodeBlock) and not elem.classes
            else None
        )
    ),
    # Prefix all relative URLs with a base repository path
    "url": lambda prefix: (
        lambda elem, _doc: (
            setattr(elem, "url", f"{prefix.rstrip('/')}/{elem.url.lstrip('/')}")
            if isinstance(elem, pf.Link) and not elem.url.startswith(("http://", "https://", "#"))
            else None
        )
    )
}

# ----------------------------------------------------------------
# -------------------------------------------- UTILITIES FUNCTIONS
# ----------------------------------------------------------------

def _asterisks(text: str) -> str:
    """
    Converts list bullet markers from '-' to '*' while preserving
    code blocks and horizontal rules.
    """
    in_code_block = False
    out_lines = []
    # Matches indentation and optional blockquote prefixes followed by '- '
    bullet_pattern = re.compile(r"^([ \t]*(?:>[ \t]*)*)-\s+(.*)$")

    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            out_lines.append(line)
            continue

        if not in_code_block:
            match = bullet_pattern.match(line)
            if match:
                prefix, rest = match.groups()
                line = f"{prefix}* {rest}"

        out_lines.append(line)

    return "\n".join(out_lines)


def _docstring(file_path: Path) -> str | None:
    """
    Extracts module-level docstring using AST, falling back to reading
    the initial triple-quoted string if Cython syntax causes a SyntaxError.
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None

    try:
        tree = ast.parse(content)
        return ast.get_docstring(tree)
    except SyntaxError:
        # Skip leading comments (e.g. # cython: ...) and empty lines
        lines = content.splitlines()
        idx = 0
        while idx < len(lines) and (not lines[idx].strip() or lines[idx].strip().startswith("#")):
            idx += 1

        remaining = "\n".join(lines[idx:]).strip()
        for quote in ('"""', "'''"):
            if remaining.startswith(quote):
                end_idx = remaining.find(quote, len(quote))
                if end_idx != -1:
                    return remaining[len(quote):end_idx]
        return None

def _load(loadpath: str | Path) -> dict:
    """
    Loads variables from a YAML file.

    Args:
        vars_path (str | Path): Path to the YAML file.

    Returns:
        dict: The parsed YAML data, or an empty dict if the file 
              does not exist or cannot be parsed.
    """
    if not os.path.exists(loadpath):
        return {}

    try:
        with open(loadpath, 'r', encoding='utf-8') as f:
            data = pyyaml.safe_load(f)
            print(f"Loaded variables from '{loadpath}'.")
            return data if data else {}
    except pyyaml.YAMLError as e:
        print(f"Error parsing YAML from '{loadpath}': {e}")
        return {}
    except Exception as e:
        print(f"Error reading vars file '{loadpath}': {e}")
        return {}


def _data(data_dir: str | Path) -> Dict[str, Any]:
    """
    Loads all YAML (.yaml, .yml) files in `data_dir` into a dictionary
    keyed by each file's stem (filename without extension).
    """
    path = Path(data_dir).expanduser().resolve()
    if not path.is_dir():
        return {}

    loaded: Dict[str, Any] = {}
    for file_path in sorted(chain(path.glob("*.yaml"), path.glob("*.yml"))):
        if file_path.is_file():
            loaded[file_path.stem] = _load(file_path)

    return loaded


def _validate(content: str, output_path: str = "") -> list[tuple[int, str]]:
    """
    Scans rendered output for missing file errors enclosed in triple tick marks (```).

    Args:
        content (str): The rendered markdown text.
        output_path (str, optional): Target output path for reporting location.

    Returns:
        list[tuple[int, str]]: Found occurrences as (line_number, error_message).
    """
    block_pattern = re.compile(r"```([\s\S]*?)```")
    error_pattern = re.compile(r"Error: File not found at [^\n`]+")

    errors = []
    for block_match in block_pattern.finditer(content):
        block_text = block_match.group(1)
        for err_match in error_pattern.finditer(block_text):
            char_pos = block_match.start(1) + err_match.start()
            line_no = content[:char_pos].count('\n') + 1
            err_msg = err_match.group(0).strip()
            errors.append((line_no, err_msg))

            location = f" in '{output_path}'" if output_path else ""
            print(f"Error at line {line_no}{location}: {err_msg}")

    return errors

# ----------------------------------------------------------------
# --------------------------------------------- TEMPLATE FUNCTIONS
# ----------------------------------------------------------------

@macro
def typehint(context: AppContext, filepath: str) -> str:
    """
    Infers a Markdown code block type hint from the file extension of filepath
    using the `typehints` configuration in `AppContext`.

    Args:
        ctx (AppContext): Automatically injected application context.
        filepath (str): The path or filename to evaluate.

    Returns:
        str: The Markdown code fence identifier, or an empty string if unknown.
    """
    _, ext = os.path.splitext(filepath)
    cleaned_ext = ext.lstrip('.').lower()
    return context.typehints.get(cleaned_ext, '')


@macro
def command(command_str: str, command_env: dict[str, str] | None = None) -> str:
    """
    Executes a shell command and returns the standard output.

    This function uses `subprocess.check_output` with `shell=True`. It is designed
    to capture the output of tools like `tree`, `ls`, or `git diff`s.

    Args:
        command_str (str): The shell command to execute.

    Returns:
        str: The stripped stdout of the command, or an error message if execution fails.
             This ensures the template rendering does not crash on a single failed command.
    """
    env = os.environ.copy()
    if command_env:
        env.update(command_env)

    try:
        result = subprocess.check_output(
            command_str,
            shell=True,
            stderr=subprocess.STDOUT,
            executable=SHELL,
            text=True,
            env=env
        )
        return result.strip()
    except subprocess.CalledProcessError as e:
        return f"Error executing command '{command_str}':\n{e.output}"
    except Exception as e:
        return f"Execution failed: {str(e)}"


@macro
def file(file_path: str) -> str:
    """
    Reads a file from the absolute or relative path provided and returns its content.

    Args:
        file_path (str): The path to the file to read. Supports `~` expansion.

    Returns:
        str: The content of the file, or an error message if the file is missing
             or unreadable.
    """
    full_path = os.path.expanduser(file_path)

    if not os.path.exists(full_path):
        return f"Error: File not found at {full_path}"

    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        return f"Error reading file: {str(e)}"


@macro
def annotations(directory: str, tags: List[str], strategy: str = "OR") -> List[Dict[str, Any]]:
    """
    Scans a directory for Python files containing `@tags` in their docstring.
    Groups matching files by package, sorting packages and modules hierarchically.

    Args:
        directory: Root directory path to scan.
        tags: A single tag or list of tags to match.
        strategy: Matching strategy - "OR" (matches if any tag is present)
                  or "AND" (matches only if all tags are present).
    """
    strat = strategy.upper()
    if strat not in {"OR", "AND"}:
        raise ValueError(f"Invalid strategy '{strategy}'. Supported strategies are 'OR' and 'AND'.")

    root = Path(directory).resolve()
    target_tokens = {f"@{t.lstrip('@')}" for t in tags}

    package_groups: Dict[str, list] = defaultdict(list)

    for file_path in chain(root.rglob("*.py"), root.rglob("*.pyx")):
        if file_path.name.startswith((".", "_")) and file_path.name != "__init__.py":
            continue

        docstring = _docstring(file_path)
        if not docstring:
            continue

        doc_tokens = set(docstring.split())

        # Evaluate tag match according to selected strategy
        if strat == "AND":
            if not target_tokens.issubset(doc_tokens):
                continue
        else:
            if not target_tokens.intersection(doc_tokens):
                continue

        # Relative paths and package hierarchy
        rel_file = file_path.relative_to(root)
        rel_parts = rel_file.with_suffix("").parts
        if rel_parts[-1] == "__init__":
            rel_parts = rel_parts[:-1]

        package = ".".join(rel_parts[:-1]) if len(rel_parts) > 1 else ""
        module = rel_parts[-1] if rel_parts else ""
        import_path = ".".join(rel_parts)

        package_groups[package].append({
            "name": file_path.name,
            "module": module,
            "import": import_path,
            "paths": {
                "relative": rel_file.as_posix(),
                "absolute": str(file_path.resolve()),
            }
        })

    output = []
    # Sort packages hierarchically: ('app', 'game') comes before ('app', 'game', 'logic')
    sorted_packages = sorted(package_groups.keys(), key=lambda p: tuple(p.split(".")) if p else ())

    for package in sorted_packages:
        # Depth equals number of segments: "app.game" -> 2, "app.services.generators" -> 3
        depth = len(package.split(".")) if package else 1
        sorted_modules = sorted(package_groups[package], key=lambda m: m["module"])

        output.append({
            "package": package or "<root>",
            "depth": depth,
            "modules": sorted_modules,
        })

    return output


@macro
def md(file_path: str, modifications: Union[dict, None] = None) -> str:
    """
    Loads a Markdown file, applies transformations via MD_MODIFIERS,
    and returns the rendered Markdown string with '*' bullet lists.
    """
    full_path = os.path.expanduser(file_path)

    if not os.path.exists(full_path):
        return f"Error: File not found at {full_path}"

    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

    try:
        doc = pf.convert_text(content, input_format="markdown", standalone=True)

        if modifications and isinstance(modifications, dict):
            for key, val in modifications.items():
                if key in MD_MODIFIERS and val is not None:
                    doc.walk(MD_MODIFIERS[key](val))

        rendered = pf.convert_text(
            doc,
            input_format="panflute",
            output_format="markdown",
            extra_args=["--wrap=none"]
        )
        return _asterisks(rendered.strip())
    except Exception as e:
        return f"Error processing markdown with panflute: {str(e)}"


@macro
def dumps(path: str) -> str:
    """
    Scans the path for any state-dump files (yyyymmdd_hhmmss.state-dump.md),
    orders them by date and time, and returns the content of the latest
    markdown file as a string.

    Args:
        path (str): The directory path to inspect. Supports `~` expansion.

    Returns:
        str: The content of the latest state-dump file, or an error message.
    """
    full_path = os.path.expanduser(path)

    if not os.path.exists(full_path) or not os.path.isdir(full_path):
        return f"Error: Directory not found at {full_path}"

    pattern = re.compile(r"^(\d{8}_\d{6})\.state-dump\.md$", re.IGNORECASE)
    candidates = []

    try:
        for filename in os.listdir(full_path):
            match = pattern.match(filename)
            if match and os.path.isfile(os.path.join(full_path, filename)):
                try:
                    timestamp = datetime.strptime(match.group(1), "%Y%m%d_%H%M%S")
                    candidates.append((timestamp, filename))
                except ValueError:
                    continue
    except Exception as e:
        return f"Error reading directory '{path}': {str(e)}"

    if not candidates:
        return f"Error: No state-dump files found at {full_path}"

    candidates.sort(key=lambda item: item[0])
    latest_filename = candidates[-1][1]

    return file(os.path.join(full_path, latest_filename))


@macro
def logs(path: str) -> str:
    """
    Scans the path for any log files (ontology_yyyy-mm-dd-execution.log),
    orders them chronologically by date and numerically by execution,
    and returns the content of the latest log file as a string.

    Args:
        path (str): The directory path to inspect. Supports `~` expansion.

    Returns:
        str: The content of the latest log file, or an error message.
    """
    full_path = os.path.expanduser(path)

    if not os.path.exists(full_path) or not os.path.isdir(full_path):
        return f"Error: Directory not found at {full_path}"

    pattern = re.compile(r"^ontology_(\d{4}-\d{2}-\d{2})-(\d+)\.log$", re.IGNORECASE)
    candidates = []

    try:
        for filename in os.listdir(full_path):
            match = pattern.match(filename)
            if match and os.path.isfile(os.path.join(full_path, filename)):
                date_str, execution_str = match.groups()
                try:
                    log_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    execution_num = int(execution_str)
                    candidates.append(((log_date, execution_num), filename))
                except ValueError:
                    continue
    except Exception as e:
        return f"Error reading directory '{path}': {str(e)}"

    if not candidates:
        return f"Error: No log files found at {full_path}"

    candidates.sort(key=lambda item: item[0])
    latest_filename = candidates[-1][1]

    return file(os.path.join(full_path, latest_filename))


@macro
def markdown(
    path: str, 
    exclude: list | tuple | str | None = None, 
    recursive: bool = False
) -> list:
    """
    Returns an alphabetized list of all Markdown (.md) files contained in the 
    specified path, excluding specified filenames.

    Args:
        path (str): The directory path to inspect. Supports `~` expansion.
        exclude (list | tuple | str | None): File name(s) or relative paths to exclude. 
                                             Defaults to ['index.md'].
        recursive (bool): Whether to traverse subdirectories. Defaults to False.

    Returns:
        list: An alphabetized list of filenames (or relative paths if recursive=True) 
              ending in '.md'. Returns an empty list if the path is invalid, 
              not a directory, or unreadable.
    """
    if exclude is None:
        exclude = ['index.md']
    elif isinstance(exclude, str):
        exclude = [exclude]

    exclude_set = {name.lower() for name in exclude}
    full_path = os.path.expanduser(path)

    if not os.path.exists(full_path) or not os.path.isdir(full_path):
        return []

    try:
        if not recursive:
            md_files = [
                f for f in os.listdir(full_path)
                if f.lower().endswith('.md') 
                and f.lower() not in exclude_set
                and os.path.isfile(os.path.join(full_path, f))
            ]
        else:
            md_files = []
            for root, _, files in os.walk(full_path):
                for f in files:
                    if f.lower().endswith('.md'):
                        rel_path = os.path.relpath(os.path.join(root, f), full_path)
                        rel_path_norm = rel_path.replace(os.sep, '/')
                        if (
                            f.lower() not in exclude_set 
                            and rel_path_norm.lower() not in exclude_set
                        ):
                            md_files.append(rel_path_norm)
        return sorted(md_files)
    except Exception as e:
        print(f"Error reading directory '{path}': {e}")
        return []


@macro
def yamls(path: str, recursive: bool = False) -> list:
    """
    Returns a list of all YAML (.yaml, .yml) files contained in the 
    specified path.

    Args:
        path (str): The directory path to inspect. Supports `~` expansion.
        recursive (bool): Whether to traverse subdirectories. Defaults to False.

    Returns:
        list: A list of filenames (or relative paths if recursive=True) ending in 
              '.yaml' or '.yml'. Returns an empty list if the path is invalid, 
              not a directory, or unreadable.
    """
    full_path = os.path.expanduser(path)

    if not os.path.exists(full_path) or not os.path.isdir(full_path):
        return []

    try:
        if not recursive:
            return [
                f for f in os.listdir(full_path)
                if (f.lower().endswith('.yaml') or f.lower().endswith('.yml'))
                and os.path.isfile(os.path.join(full_path, f))
            ]
        else:
            yaml_files = []
            for root, _, files in os.walk(full_path):
                for f in files:
                    if f.lower().endswith('.yaml') or f.lower().endswith('.yml'):
                        rel_path = os.path.relpath(os.path.join(root, f), full_path)
                        yaml_files.append(rel_path.replace(os.sep, '/'))
            return yaml_files
    except Exception as e:
        print(f"Error reading directory '{path}': {e}")
        return []


@macro
def now(kind: str = None) -> str:
    dt = datetime.now()
    if kind == "apache":
        return dt.strftime("%d/%b/%Y:%H:%M:%S")
    if kind == "java":
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# ----------------------------------------------------------------
# --------------------------------------------- RENDERING PIPELINE
# ----------------------------------------------------------------

def render(template_path: str, output_path: str, vars_path: str, context: AppContext) -> None:
    """
    Orchestrates the Jinja2 rendering workflow.

    Initializes a Jinja2 Environment with the directory containing this script as the loader.
    Injects the registered `@macro` functions into the global namespace, loads optional 
    variables from YAML, renders the specified template, and writes the result to disk.

    Args:
        template_path (str): The filename of the Jinja2 template to render.
        output_path (str): The absolute or relative path to save the rendered output.
        vars_path (str): The path to the variables YAML file.
        ctx (AppContext): The loaded application configuration context.

    Raises:
        jinja2.TemplateNotFound: If the specified template file does not exist.
        Exception: For generic IO or rendering errors.
    """
    default_templates = context.defaults.get('templates', 'tasks')
    script_dir = os.path.dirname(os.path.abspath(__file__))
    templates  = os.path.join(script_dir, default_templates)

    token = _context.set(context)

    try:
        # Set up the Jinja2 environment
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader([script_dir, templates]),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True
        )

        # Automatically register all @macro decorated functions
        env.globals.update(_REGISTRY)

        # Load context files
        vars_data = _load(vars_path)
        vars_data.update(context.properties)
        
        template = env.get_template(template_path)
        rendered_output = template.render(**vars_data)
        output_dir = os.path.dirname(output_path)

        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(rendered_output)

        print(f"Successfully rendered '{template_path}' to '{output_path}'.")

        # Validation stage: check rendered output for missing file errors
        _validate(rendered_output, output_path)

    except jinja2.TemplateNotFound as e:
        print(f"Error: Template not found: '{e.name}' (referenced in '{template_path}')")
        sys.exit(1)
    except jinja2.TemplateSyntaxError as e:
        print(f"Jinja Syntax Error: {e.message}")
        print(f"  File: {e.filename or template_path}:{e.lineno}")
        sys.exit(1)
    except jinja2.TemplateRuntimeError as e:
        print(f"Jinja Runtime Error in '{template_path}': {e}")
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"Error during rendering of '{template_path}': {e}")
        traceback.print_exc()
        sys.exit(1)
    finally:
        _context.reset(token)

# ----------------------------------------------------------------
# ----------------------------------------------------- ENTRYPOINT
# ----------------------------------------------------------------

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir   = os.path.join(script_dir, DATA_DIR)

    # Load all YAMLs from data/ into AppContext
    context = AppContext(**_data(data_dir))

    vars_file = context.defaults.get('vars', 'main.yaml')
    output_file = context.defaults.get('output', 'prompt.md')
    default_output = os.path.join(script_dir, OUTPUT_DIR, output_file)
    
    parser = argparse.ArgumentParser(
        description="Render Jinja2 templates into Markdown."
    )

    parser.add_argument(
        "template",
        nargs="?", 
        default=context.defaults.get('template', 'main.md.j2'),
        help=f"The Jinja2 template file to render."
    )

    parser.add_argument(
        "-o", 
        "--output",
        help=f"The output filename."
    )

    parser.add_argument(
        "-v", "--vars",
        help=f"Path to a YAML file containing variables.."
    )

    args = parser.parse_args()

    target_output = args.output or default_output

    if args.vars:
        target_vars = args.vars
        if not os.path.exists(target_vars):
            print(f"Error: The specified variables file '{target_vars}' does not exist.")
            sys.exit(1)
    else:
        target_vars = os.path.join(script_dir, vars_file)

    render(args.template, target_output, target_vars, context)
```

This is the directory:

```bash
(ontology) gmoore@Grants-MacBook-Pro ontology % tree -L 3 ./prompts/
./prompts/
├── README.md
├── blocks
│   ├── context
│   │   └── index.md
│   ├── controls
│   │   ├── constraint-changes.md
│   │   ├── constraint-coverage.md
│   │   ├── constraint-quality.md
│   │   ├── guideline-coverage.md
│   │   ├── guideline-debugging.md
│   │   ├── guideline-design.md
│   │   ├── guideline-docstrings.md
│   │   ├── guideline-documentation.md
│   │   ├── guideline-fixtures.md
│   │   ├── guideline-models.md
│   │   ├── guideline-testbed.md
│   │   └── warning-code.md
│   └── images
│       └── forts.md
├── board
│   ├── backlog
│   │   ├── new.md
│   │   ├── todo-t000.md
│   │   ├── todo-t001.md
│   │   └── todo-t002.md
│   ├── index.md
│   ├── phases
│   │   ├── achieve
│   │   ├── design
│   │   ├── implement
│   │   ├── patch
│   │   └── refactor
│   └── reports
│       ├── 2026-08-16.md
│       ├── 2026-09-07.md
│       └── 2026-11-03.md
├── build
│   └── prompt.md
├── data
│   ├── defaults.yaml
│   ├── properties.yaml
│   ├── queries.yaml
│   ├── tasks
│   │   ├── design
│   │   └── iterate
│   └── typehints.yaml
├── main.md.j2
├── main.py
├── main.yaml
├── tasks
│   ├── analyze
│   │   ├── automaton.md.j2
│   │   └── engine.md.j2
│   ├── design
│   │   ├── diagram
│   │   ├── structure
│   │   └── style
│   ├── index.md.j2
│   ├── iterate
│   │   ├── conclusion.md.j2
│   │   ├── coverage.md.j2
│   │   ├── documentation.md.j2
│   │   ├── grooming.md.j2
│   │   ├── implementation.md.j2
│   │   └── review.md.j2
│   ├── maintain
│   │   ├── codebase.md.j2
│   │   ├── patch.md.j2
│   │   └── session.md.j2
│   └── report
│       ├── menu.md.j2
│       └── state.md.j2
└── tools
    ├── index.md.j2
    ├── manager
    │   ├── index.md.j2
    │   └── views
    ├── metrics
    │   ├── index.md.j2
    │   └── views
    ├── package
    │   ├── index.md.j2
    │   └── views
    ├── shell
    │   ├── index.md.j2
    │   └── views
    ├── source
    │   ├── index.md.j2
    │   └── views
    └── tests
        ├── index.md.j2
        └── views

41 directories, 52 files
```

This is an example of variables:

```yaml
# ----------------------------------------------------
context: true
# ----------------------------------------------------
# ----------------------------------------------------
# ----------------------------------------------- TASK
# ----------------------------------------------------
# ----------------------------------------------------
task:
# ----------------------------------------------------
  template: index.md.j2
  # template: draft.md.j2
  # --------------------------------------------
  # --------------------- TEMPLATES: MAINTENANCE
  # --------------------------------------------
  # template: analyze/automaton.md.j2
  # template: analyze/pstats.md.j2
  # --------------------------------------------
  # --------------------- TEMPLATES: MAINTENANCE
  # --------------------------------------------
  # template: maintain/codebase.md.j2
  # template: maintain/patch.md.j2
  # template: maintain/session.md.j2
  # --------------------------------------------
  # --------------------------- TEMPLATES: DUMPS 
  # --------------------------------------------
  # template: report/menus.md.j2
  # template: report/state.md.j2
  # --------------------------------------------
  # ----------------------- TEMPLATES: ITERATION
  # --------------------------------------------
  # template: iterate/documentation.md.j2
  # template: iterate/grooming.md.j2
  # template: iterate/implementation.md.j2
  # template: iterate/coverage.md.j2
  # template: iterate/review.md.j2
  # template: iterate/conclusion.md.j2
  # --------------------------------------------
  # -------------------------- TEMPLATES: DESIGN
  # --------------------------------------------
  # template: design/structure/menu.md.j2
  # template: design/structure/composition.md.j2
  # template: design/structure/score.md.j2
  # template: design/diagram/hierarchy.md.j2
  # template: design/diagram/automata.md.j2
  # template: design/diagram/stages.md.j2
  # template: design/style/mermaid.md.j2
# ----------------------------------------------------
  # PLACEHOLDER UNTIL STRUCTURE EMERGES FOR TOOL
  parameters:
    description: |
      Alright, everything is working. Inventory menu looks good. We have touched upon one of the shortcomings of the current Menu and Widget model. Currently all Pane assets are fixed dimensions. 

      As part of Phase 07.04, Compositions were given multiplication strategies to expand them according to schemas. Examine the multiplication strategies. Then examine the application dependency injection pipeline.

      The Goal is the following: Panes should be able to expand to arbitrary sizes (constrained by whatever minimum dimensions the Asset actually supports). Panes are very similar to Strut Enclosures, insofar that they are defined as a perimeter around a geometric area, where the north-south edges are caps for vertical multiplcation and east-west edges are caps for horizontal multiplication.

      Use the [Backlog Template](#template-backlog) to map out a new phase of development. Determine if the existing multiplication strategies can be utilized.
    title: Menus 
    # -------------- DESIGN PARAMETERS
    diagram: executor-centennial-transitions.mmd
    automata: stages 
    table: executor-centennial-transitions.md
    score: wagner-ride-of-the-valkyries.yaml
# ----------------------------------------------------
# ----------------------------------------------------
# ---------------------------------------------- TOOLS
# ----------------------------------------------------
# ----------------------------------------------------
tools:
# ----------------------------------------------------
  views:
    # --------------------------------------------
    # ------------------------ TOOL VIEWS: MANAGER
    # --------------------------------------------
    manager:
      board: false
      docs: true
      templates: true
      specs: false
    # --------------------------------------------
    # ------------------------ TOOL VIEWS: METRICS
    # --------------------------------------------
    metrics:
      pstats: false
    # --------------------------------------------
    # ------------------------ TOOL VIEWS: SOURCE
    # --------------------------------------------
    source:
      data: false
      filter: true
    # --------------------------------------------
    # ------------------------ TOOL VIEWS: SHELL
    # --------------------------------------------
    shell:
      directory: false
      commands: false
    # --------------------------------------------
    # ------------------------ TOOL VIEWS: TESTS
    # --------------------------------------------
    tests:  
      configuration: false
      pipeline: false
      session: false
# ----------------------------------------------------
  parameters:
    # --------------------------------------------
    # ------------------------ PARAMETERS: MANAGER
    # --------------------------------------------
    manager:
      board:
        phase: 04-06
        action: refactor
      docs:
        exclude:
          - 00-overview
          - 01-assets
          - 02-sprites
          # - 03-compositions
          - 04-intentions
          - 05-mechanics
          - 06-widgets
          - 07-sounds
          - 08-plots
          - 09-ecology
          - 10-chemistry
          - 11-emergence
          - 12-architecture
      templates: 
        - template-backlog
      specs:
        - 00-dialogue
        - 01-interaction
        - 02-wander
    metrics:
      pstats: 
        run: |
          python -m cProfile -o $ROOT/engine-run.pstats src/main.py start world-01
        dot: |
          gprof2dot -f pstats --node-thres=1.0 --edge-thres=0.5 $ROOT/engine-run.pstats
    # --------------------------------------------
    # ------------------------ PARAMETERS: SOURCE
    # --------------------------------------------
    source:
      filter:
        default: AND
        queries:
          - title: Multiplier Abstract
            scan:
              domain: [ abstract ]
              app: [ module ]
              workflows: [ compositions ]
          - title: Composition Logic
            scan:
              domain: [ logic ]
              app: [ module ]
              workflows: [ compositions ]
          - title: Orchestration Services
            scan:
              domain: [ system ]
              app: [ orchestration ]
          - title: Hydration Services
            scan:
              domain: [ system ]
              workflows: [ hydration ]
      data:
        properties: [ ]
        state: [ ]
        configurations: [ ]
        templates: [ ]
    # --------------------------------------------
    # -------------------------- PARAMETERS: SHELL
    # --------------------------------------------
    shell:
      directory: |
        tree -L 3 --gitignore -I "build|*.so|*.png|__pycache__|__init__.py"
      commands: 
        - python /Users/gmoore/Home/projects/ontology/src/main.py start
    # --------------------------------------------
    # -------------------------- PARAMETERS: TESTS
    # --------------------------------------------
    tests:
      pipeline:
        command: pytest -m
        marker: workflow_navigation
        # scope: '**/test_{actuator,cartographer}.py'
```

This is task board:

```markdown
#### Ontology: Task Board

This is the Task Board for the project. Below is a backlog of completed and pending Tasks. Tasks are divided into Phases. Phases are not necessarily sequential.

!!! "Task Progress Key"
  `[ ]`: Open
  `[~]`: In Progress
  `[?]`: Needs Further Analysis
  `[x]`: Closed/Implemented
  `[!]`: DO NOT COMPLETE

!!! "Phase Actions"
  * **Implement**: Complex, multi-task development of new functionality.
  * **Refactor**: Complex, multi-task iteration of existing functionality.
  * **Patch**: Tasks for fixing logical bugs or errors in the codebase.
  * **Achieve**: Short, encapsulated tasks for either new or existing functionality.
  * **Design**: Short, encapsulated tasks for creating data structures.

**Table of Contents**

-**Actions:**
  * **Implement:**
    * [x]: [Phase 01: Renderer](./phases/implement/phase-01.md)
    * [x]: [Phase 02: Game](./phases/implement/phase-02.md)
    * [x]: [Phase 03: Physics](./phases/implement/phase-03.md)
    * [x]: [Phase 04: Widgets](./phases/implement/phase-04.md)
    * [~]: [Phase 05: Editor](./phases/implement/phase-05.md)
    * [x]: [Phase 06: Intentions](./phases/implement/phase-06.md)
    * [x]: [Phase 07: Compositions](./phases/implement/phase-07.md)
    * [x]: [Phase 08: Pathfinding](./phases/implement/phase-08.md)
    * [x]: [Phase 09: Hydrodynamics](./phases/implement/phase-09.md)
    * [x]: [Phase 10: Seasons](./phases/implement/phase-10.md)
    * [ ]: [Phase 11: Geology](./phases/implement/phase-11.md)
    * [ ]: [Phase 12: Chemistry](./phases/implement/phase-12.md)
    * [~]: [Phase 13: Acoustics](./phases/implement/phase-13.md)
    * [ ]: [Phase n: Commerce](./phases/implement/phase-n.md)
    * [ ]: [Phase n+1: Towns](./phase/implement/phase-n+1.md)
  * **Refactor:**
    * *Phase 01:*
      * [x]: [Phase 01.01: Orchestration](./phases/refactor/refactor-01-01.md)
    * *Phase 02:*
      * [x]: [Phase 02.01: Frames](./phases/refactor/refactor-02-01.md)
      * [x]: [Phase 02.02: Registry](./phases/refactor/refactor-02-02.md)
      * [x]: [Phase 02.03: Equipment](./phases/refactor/refactor-02-03.md)
      * [x]: [Phase 02.04: Engine](./phases/refactor/refactor-02-04.md)
      * [x]: [Phase 02.05: Finetuning](./phases/refactor/refactor-02-05.md)
      * [x]: [Phase 02.06: Effects](./phases/refactor/refactor-02-06.md)
      * [x]: [Phase 02.07: Registry Data Structures](./phases/refactor/refactor-02-07.md)
    * *Phase 03:*
      * [x]: [Phase 03.01: Mechanics](./phases/refactor/refactor-03-01.md)
      * [x]: [Phase 03.02: Consolidation](./phases/refactor/refactor-03-02.md)
      * [x]: [Phase 03.03: Motion](./phases/refactor/refactor-03-03.md)
      * [ ]: [Phase 03.04: Projectiles](./phases/refactor/refactor-03-04.md)
    * *Phase 04:*
      * [x]: [Phase 04.01: Typography](./phases/refactor/refactor-04-01.md)
      * [x]: [Phase 04.02: Simplification](./phases/refactor/refactor-04-02.md)
      * [x]: [Phase 04.03: EventHandlers](./phases/refactor/refactor-04-03.md)
      * [x]: [Phase 04.04: MenuContext](./phases/refactor/refactor-04-04.md)
      * [x]: [Phase 04.05: Gizmos](./phases/refactor/refactor-04-05.md)
      * [~]: [Phase 04.06: Pane Generation](./phases/refactor/refactor-04-06.md)
    * *Phase 06:*
      * [x]: [Phase 06.01: Expressions](./phases/refactor/refactor-06-01.md)
      * [ ]: [Phase 06.02: Goals](./phases/refactor/refactor-06-02.md)
      * [ ]: [Phase 06.03: Combat](./phases/refactor/refactor-06-03.md)
    * *Phase 07:*
      * [x]: [Phase 07.01: Elevation Sorting](./phases/refactor/refactor-07-01.md)
      * [x]: [Phase 07.02: Platforms & Elevated Hitboxes](./phases/refactor/refactor-07-02.md)
      * [ ]: [Phase 07.03: Gravity](./phases/refactor/refactor-07-03.md)
      * [x]: [Phase 07.04: Materialization](./phases/refactor/refactor-07-04.md)
      * [ ]: [Phase 07.05: Composite Compositions](./phases/refactor/refactor-07-05.md)
    * *Phase 08:*
      * [x]: [Phase 08.01: Obstable Geometry](./phases/refactor/refactor-08-01.md)
      * [x]: [Phase 08.02: NavigationMechanics](./phases/refactor/refactor-08-02.md)
      * [x]: [Phase 08.03: Trajectory Optimization](./phases/refactor/refactor-08-03.md)
      * [ ]: [Phase 08.04: Mutators](./phases/refactor/refactor-08-04.md)
    * *Phase 09:*
      * [x]: [Phase 09.01: Fluid Flows](./phases/refactor/refactor-09-01.md)
      * [x]: [Phase 09.02: Shorelines & Geography](./phases/refactor/refactor-09-02.md)
      * [x]: [Phase 09.03: Consolidation](./phases/refactor/refactor-09-03.md)
      * [x]: [Phase 09.04: Optimization](./phases/refactor/refactor-09-04.md)
      * [x]: [Phase 09.05: Bridges & Bifurcation](./phases/refactor/refactor-09-05.md)
      * [x]: [Phase 09.06: Cythonization](./phases/refactor/refactor-09-06.md)
      * [x]: [Phase 09.07: Frame Caching](./phases/refactor/refactor-09-07.md)
      * [ ]: [Phase 09.08: Transverse Fluid Submersion](./phases/refactor/refactor-09-08.md)
    * *Phase 10:*
      * [x]: [Phase 10.01: Stage Hitboxes](./phases/refactor/refactor-10-01.md)
      * [x]: [Phase 10.02: Shoreline Seasonal Indexing](./phases/refactor/refactor-10-02.md)
      * [ ]: [Phase 10.03: Flowers, Pixies & Reproduction](./phases/refactor/refactor-10-03.md)
      * [ ]: [Phase 10.04: Cythonization](./phases/refactor/refactor-10-04.md)
      * [ ]: [Phase 10.05: Seasonality](./phases/refactor/refactor-10-05.md)
  * **Patch:**
    * [x]: [Bug B000: Attacking Glitch](./phases/patch/bug-b000.md)
    * [ ]: [Bug B001: Relayering Instantiated Assets](./phases/patch/bug-b001.md)
    * [ ]: [Bug B002: Board Cache Wipe](./phases/patch/bug-b002.md)
    * [x]: [Bug B003: Painter's Algorithm String Exception](./phases/patch/bug-b003.md)
    * [x]: [Bug B004: Friction Regression](./phases/patch/bug-b004.md)
    * [x]: [Bug B005: Speak Regression](./phases/patch/bug-b005.md)
    * [x]: [Bug B006: Raycast Boundary Grazing](./phases/patch/bug-b006.md)
    * [x]: [Bug B007: Cradle Spawning](./phases/patch/bug-b007.md)
    * [x]: [Bug B008: Open Gate Obstruction](./phases/patch/bug-b008.md)
    * [x]: [Bug B009: Irregular Composition Behavior](./phases/patch/bug-b009.md)
    * [x]: [Bug B010: Overlapping Fluid Shorelines](./phases/patch/bug-b010.md)
    * [x]: [Bug B011: Stream and Annular Pool Texture Overdraw](./phases/patch/bug-b011.md)
    * [x]: [Bug B012: Composition Duplication](./phases/patch/bug-b012.md)
    * [ ]: [Bug B013: Canvas Bleed on Fore Tiles](./phases/patch/bug-b013.md)
    * [x]: [Bug B014: Stair Railing Hitbox Traversal Block](./phases/patch/bug-b014.md)
    * [x]: [Bug B015: Decomposer Macro Scope](./phases/patch/bug-b015.md)
    * [x]: [Bug B016: Decomposer Elevation Inheritance](./phases/patch/bug-b016.md)
  * **Achieve:**
    * [x]: [Goal 01: Boundaries](./phases/achieve/goal-01.md)
    * [x]: [Goal 02: ScrollController, Library & Plots](./phases/achieve/goal-02)
    * [ ]: [Goal 03: ExchangeController & Loot](./phases/achieve/goal-03.md)
    * [x]: [Goal 04: Main Menu & Saving](./phases/achieve/goal-04.md)
    * [~]: [Goal 05: InventoryController](./phases/achieve/goal-05.md)
    * [x]: [Goal 06: Speak Intentions](./phases/achieve/goal-06.md)
    * [x]: [Goal 07: Interact Intentions](./phases/achieve/goal-07.md)
    * [x]: [Goal 08: CLI Handling](./phases/achieve/goal-08.md)
    * [x]: [Goal 09: Board Modularization](./phases/achieve/goal-09.md)
    * [x]: [Goal 10: Dependency Injection](./phases/achieve/goal-11.md)
  * **Design:**
    * [x]: [Composition C000: Castle Dawn](./phases/design/composition-c000.md)
    * [ ]: [Composition C001: Temple of Trials](./phases/design/composition-c001.md)
    * [~]: [Composition C002: Regalia Galleria](./phases/design/composition-c002.md)
* **Backlog:**
  * [~]: [TODO T000: Telemetry Module](./backlog/todo-t000.md)
  * [~]: [TODO T001: Telemetry Menu](./backlog/todo-t001.md)
  * [ ]: [TODO T002: Bouyancy](./backlog/todo-t002.md)
```

This is an example of a Tool:

```jinja2
### View: Filter

The Filter View *queries* the codebase based on the **Active Tags** and the **Filter Strategy**.

{% for query in tools.parameters.source.filter.queries %}
{# -------------------------------------------- #}
{% set query_idx = loop.index %}
{% set title = query.title %}
{% set strategy = query.strategy or tools.parameters.source.filter.default %}
{% set tags = [] %}
{% for prefix, items in [
    ('app.', query.scan.app),
    ('domain.', query.scan.domain),
    ('asset.', query.scan.asset),
    ('category.', query.scan.category),
    ('menu.', query.scan.menu),
    ('modality.', query.scan.modality),
    ('physics.', query.scan.physics),
    ('test.', query.scan.test),
    ('script.', query.scan.script),
    ('workflow.', query.scan.workflows)
] %}
{% for item in items %}
{% set _ = tags.append(prefix ~ item) %}
{% endfor %}
{% endfor %}
{# -------------------------------------------- #}
#### Query #{{ query_idx }}: {{ title }}

* **Filter Strategy**: `{{ strategy }}`
* **Active Tags**: `{{ tags | join('`, `') }}`

{% for pkg in annotations(properties.paths.root ~ 'src', tags, strategy) %}
##### Matched Source Package: {{ pkg.package }}

{% for mod in pkg.modules %}
**Matched Module: `src/{{ mod.paths.relative }}`**

```{{ typehint(mod.paths.relative) }}
{{ file(mod.paths.absolute) }}
```

{% endfor %}
{% endfor %}

{% for pkg in annotations(properties.paths.root ~ 'tests/unit', tags, strategy) %}
##### Matched Test Package: {{ pkg.package }}

{% for mod in pkg.modules %}
**Matched Module: `tests/unit/{{ mod.paths.relative }}`**

```{{ typehint(mod.paths.relative) }}
{{ file(mod.paths.absolute) }}
```

{% endfor %}
{% endfor %}

{% for pkg in annotations(properties.paths.root ~ 'scripts/', tags, strategy) %}
##### Matched Script Package: {{ pkg.package }}

{% for mod in pkg.modules %}
**Matched Module: `scripts/{{ mod.paths.relative }}`**

```{{ typehint(mod.paths.relative) }}
{{ file(mod.paths.absolute) }}
```

{% endfor %}
{% endfor %}
{% endfor %}
```

This is another example of a tool:

```jinja2
{% set test_command = tools.parameters.tests.pipeline.command + ' ' + tools.parameters.tests.pipeline.marker %}
{% set test_path = properties.paths.root + properties.paths.tests %}
{% set test_path = test_path + tools.parameters.tests.pipeline.scope 
                    if tools.parameters.tests.pipeline.scope is defined else 
                    test_path %}
{# ----------------------------------------------------------------------  #}
### View: Test Pipeline

* **Current Workflow Focus**: `{{ tools.parameters.tests.pipeline.marker }}`

```bash
{{ properties.user.username }}@{{ properties.user.hostname }} % {{ test_command }} {{ test_path }}

{{ command(test_command + ' ' + test_path) }}
```
```

This is the prompt index:

```jinja2
{# ------------------------------------------------------------------- #}
{% if context %}
{% include 'blocks/context/index.md' %}
{% endif %}

{% include 'tools/index.md.j2' %}

{% include task.template %}
```

This is the tool index:

```jinja2
{% if tools.views.tests is defined and tools.views.tests.values() | select | list | length > 0 %}
# Tool: Tests

The **Tests Tool** provides **Views** into the [Application](#application) testing bed. 

## Tests: Views

{% if tools.views.tests.configuration %}
{% include 'tools/tests/views/configuration.md.j2' %}
{% endif %}

{% if tools.views.tests.pipeline %}
{% include 'tools/tests/views/pipeline.md.j2' %}
{% endif %}

{% if tools.views.tests.session %}
{% include 'tools/tests/views/session.md.j2' %}
{% endif %}

{% endif %}
```

This is an example of a task template:

```jinja2
# Task: Ontology - Coverage

**Priorities**
      
* **DEBUGGING**: Debug the current run of the test pipeline located in the [Test Pipeline](#view-test-pipeline) section.
* **COVERAGE** Add any unit tests for any areas of the code not already covered.
* **BUGHUNTING** (*Optional*) Be on the lookout for bugs. Use the [Bug Report Template](#template-bug-report) to raise any issues you find.

{% include 'blocks/controls/guideline-fixtures.md' %}

{% include 'blocks/controls/guideline-coverage.md' %}

{% include 'blocks/controls/guideline-testbed.md' %}

{% include 'blocks/controls/constraint-coverage.md' %}

## Task: Templates

{% include 'blocks/templates/template-bug.md' %}
```

My question: What are the current industry standard frameworks for developing with LLMs (non-aigentic, i.e. not instantiating an agent to work in the background, but directly interfacing with an LLM and meditating their proposed changes)? How does my framework compare? Where does my framework lack?