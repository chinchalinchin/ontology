"""
Jinja2 Template Renderer

This module automates the generation of context-rich Markdown files. It extends the standard Jinja2 environment with custom hooks for filesystem access and shell command execution, allowing templates to dynamically include the latest project state.

Usage:
    python task.py [template_file] [--output output_file] [--vars vars_file]

Dependencies:
    - jinja2
    - pyyaml

Security Warning:
    This script enables Arbitrary Code Execution (ACE) via the `command` function. Only render templates from trusted sources.
"""

# Standard Libraries

import argparse
from datetime import datetime
import os
import subprocess
import sys

# External Libraries

import jinja2
import yaml as pyyaml

# -------------------- Configuration

DEFAULT_TEMPLATE                = 'task.md.j2'
DEFAULT_VARS_FILE               = 'task.yaml'
DEFAULT_OUTPUT_SUBDIR           = 'build'
DEFAULT_OUTPUT_FILE             = 'prompt.md'
TEMPLATES                       = "tasks"

# -------------------- Templating Functions

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
        # Security Note: shell=True is necessary for pipes/complex commands but carries RCE risk.
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


def file(file_path: str) -> str:
    """
    Reads a file from the absolute or relative path provided and returns its content.

    Args:
        file_path (str): The path to the file to read. Supports `~` expansion.

    Returns:
        str: The content of the file, or an error message if the file is missing
             or unreadable.
    """
    # Expand ~ if present
    full_path = os.path.expanduser(file_path)

    if not os.path.exists(full_path):
        return f"Error: File not found at {full_path}"

    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        return f"Error reading file: {str(e)}"


def markdown(path: str, exclude: list | tuple | str | None = None) -> list:
    """
    Returns an alphabetized list of all Markdown (.md) files contained directly 
    in the specified path, excluding specified filenames. Ignores subdirectories.

    Args:
        path (str): The directory path to inspect. Supports `~` expansion.
        exclude (list | tuple | str | None): File name(s) to exclude. Defaults to ['index.md'].

    Returns:
        list: An alphabetized list of filenames ending in '.md' (excluding files in exclude). 
              Returns an empty list if the path is invalid, not a directory, or unreadable.
    """
    if exclude is None:
        exclude = ['index.md']
    elif isinstance(exclude, str):
        exclude = [exclude]

    # Normalize exclusion targets to lowercase for case-insensitive matching
    exclude_set = {name.lower() for name in exclude}

    full_path = os.path.expanduser(path)
    
    # Verify the path exists and is indeed a directory
    if not os.path.exists(full_path) or not os.path.isdir(full_path):
        return []

    try:
        # Iterate over directory entries and filter for files ending with .md not in exclude_set
        md_files = [
            f for f in os.listdir(full_path)
            if f.lower().endswith('.md') 
            and f.lower() not in exclude_set
            and os.path.isfile(os.path.join(full_path, f))
        ]
        
        # Return the list alphabetized
        return sorted(md_files)
        
    except Exception as e:
        print(f"Error reading directory '{path}': {e}")
        return []


def yaml(path: str) -> list:
    """
    Returns a list of all YAML (.yaml, .yml) files contained directly in the 
    specified path. Ignores subdirectories.

    Args:
        path (str): The directory path to inspect. Supports `~` expansion.

    Returns:
        list: A list of filenames ending in '.yaml' or '.yml'. Returns an empty 
              list if the path is invalid, not a directory, or unreadable.
    """
    full_path = os.path.expanduser(path)

    if not os.path.exists(full_path) or not os.path.isdir(full_path):
        return []

    try:
        return [
            f for f in os.listdir(full_path)
            if (f.lower().endswith('.yaml') or f.lower().endswith('.yml'))
            and os.path.isfile(os.path.join(full_path, f))
        ]
    except Exception as e:
        print(f"Error reading directory '{path}': {e}")
        return []


def load(vars_path: str) -> dict:
    """
    Loads variables from a YAML file.

    Args:
        vars_path (str): Path to the YAML file.

    Returns:
        dict: The parsed YAML data, or an empty dict if the file 
              does not exist or cannot be parsed.
    """
    if not os.path.exists(vars_path):
        # If the file doesn't exist, we just return empty context
        # (unless it was explicitly requested, handled in main)
        return {}

    try:
        with open(vars_path, 'r', encoding='utf-8') as f:
            # Use safe_load to avoid arbitrary code execution from YAML tags
            data = pyyaml.safe_load(f)
            print(f"Loaded variables from '{vars_path}'.")
            return data if data else {}
    except pyyaml.YAMLError as e:
        print(f"Error parsing YAML from '{vars_path}': {e}")
        return {}
    except Exception as e:
        print(f"Error reading vars file '{vars_path}': {e}")
        return {}


def now(kind: str = None):
    dt = datetime.now()
    if kind == "apache":
        return dt.strftime("%d/%b/%Y:%H:%M:%S")
    if kind == "java":
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def render(template_path: str, output_path: str, vars_path: str) -> None:
    """
    Orchestrates the Jinja2 rendering workflow.

    Initializes a Jinja2 Environment with the directory containing this script as the loader.
    Injects the custom template functions into the global namespace, loads optional 
    variables from YAML, renders the specified template, and writes the result to disk.

    Args:
        template_path (str): The filename of the Jinja2 template to render.
        output_path (str): The absolute or relative path to save the rendered output.
        vars_path (str): The path to the variables YAML file.

    Raises:
        jinja2.TemplateNotFound: If the specified template file does not exist.
        Exception: For generic IO or rendering errors.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    templates  = os.path.join(script_dir, TEMPLATES) 

    # Set up the Jinja2 environment
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader([ script_dir, templates ]),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True
    )

    # Register custom functions into the Jinja globals
    env.globals['command'] = command
    env.globals['file'] = file
    env.globals['markdown'] = markdown
    env.globals['yaml'] = yaml
    env.globals['now'] = now

    # Load context files
    vars_data = load(vars_path)

    try:
        template = env.get_template(template_path)
        rendered_output = template.render(**vars_data)
        output_dir = os.path.dirname(output_path)

        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(rendered_output)

        print(f"Successfully rendered '{template_path}' to '{output_path}'.")

    except jinja2.TemplateNotFound as e:
        print(f"Error: Could not find template '{e.name}' (called during render of '{template_path}').")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# -------------------- Entrypoint

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Render Jinja2 templates into Markdown."
    )

    parser.add_argument(
        "template_file",
        nargs="?", 
        default=DEFAULT_TEMPLATE,
        help=f"The Jinja2 template file to render (default: {DEFAULT_TEMPLATE})"
    )

    parser.add_argument(
        "-o", "--output",
        help=f"The output filename. Defaults to '{os.path.join(DEFAULT_OUTPUT_SUBDIR, DEFAULT_OUTPUT_FILE)}' relative to the script directory."
    )

    parser.add_argument(
        "-v", "--vars",
        help=f"Path to a YAML file containing variables (default: {DEFAULT_VARS_FILE} in script directory)."
    )

    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))

    target_output = args.output \
        or os.path.join(script_dir, DEFAULT_OUTPUT_SUBDIR, DEFAULT_OUTPUT_FILE)

    if args.vars:
        target_vars = args.vars
        if not os.path.exists(target_vars):
            print(f"Error: The specified variables file '{target_vars}' does not exist.")
            sys.exit(1)
    else:
        target_vars = os.path.join(script_dir, DEFAULT_VARS_FILE)

    render(args.template_file, target_output, target_vars)