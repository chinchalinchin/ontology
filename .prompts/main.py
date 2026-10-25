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
        # Fallback for Cython files with cdef/cimport syntax
        stripped = content.strip()
        for quote in ('"""', "'''"):
            if stripped.startswith(quote):
                end_idx = stripped.find(quote, len(quote))
                if end_idx != -1:
                    return stripped[len(quote):end_idx]
        return None


def _load(vars_path: str | Path) -> dict:
    """
    Loads variables from a YAML file.

    Args:
        vars_path (str | Path): Path to the YAML file.

    Returns:
        dict: The parsed YAML data, or an empty dict if the file 
              does not exist or cannot be parsed.
    """
    if not os.path.exists(vars_path):
        return {}

    try:
        with open(vars_path, 'r', encoding='utf-8') as f:
            data = pyyaml.safe_load(f)
            print(f"Loaded variables from '{vars_path}'.")
            return data if data else {}
    except pyyaml.YAMLError as e:
        print(f"Error parsing YAML from '{vars_path}': {e}")
        return {}
    except Exception as e:
        print(f"Error reading vars file '{vars_path}': {e}")
        return {}


def _load_data(data_dir: str | Path) -> Dict[str, Any]:
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
def command(command_str: str) -> str:
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
    try:
        result = subprocess.check_output(
            command_str,
            shell=True,
            stderr=subprocess.STDOUT,
            text=True
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
def annotations(directory: str, tags: Union[str, List[str]], strategy: str = "OR") -> List[Dict[str, Any]]:
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
    tag_list = [tags] if isinstance(tags, str) else list(tags)
    target_tokens = {f"@{t.lstrip('@')}" for t in tag_list}

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
    context = AppContext(**_load_data(data_dir))

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