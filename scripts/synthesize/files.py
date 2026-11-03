"""
@script.synthesize

File resolution and schema validation module for synthesizer configuration.
"""

from pathlib import Path
from typing import Union
import logging
import yaml

from models import ScoreRoot, SoundsRoot

logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).resolve().parent


def resolve(target: Union[str, Path]) -> Path:
    """Resolve a configuration file path across absolute, CWD, and script directories.

    Args:
        target: Target file path or filename to resolve.

    Returns:
        Path: Verified absolute Path instance.

    Raises:
        FileNotFoundError: If the target does not exist in any candidate location.
    """
    target_path = Path(target)

    # 1. Absolute path verification
    if target_path.is_absolute() and target_path.is_file():
        logger.debug("Resolved absolute path: %s", target_path)
        return target_path

    # 2. Path relative to current working directory
    cwd_path = (Path.cwd() / target_path).resolve()
    if cwd_path.is_file():
        logger.debug("Resolved path relative to CWD: %s", cwd_path)
        return cwd_path

    # 3. Path relative to script directory
    script_rel_path = (SCRIPT_DIR / target_path).resolve()
    if script_rel_path.is_file():
        logger.debug("Resolved path relative to script directory: %s", script_rel_path)
        return script_rel_path

    raise FileNotFoundError(
        f"Unable to locate file '{target}'. Searched:\n"
        f"  1. Absolute: {target_path}\n"
        f"  2. Relative to CWD: {cwd_path}\n"
        f"  3. Relative to Script Dir: {script_rel_path}"
    )


def load_yaml(path: Union[str, Path]) -> dict:
    """Load raw YAML content from a resolved path.

    Args:
        path: Path or filename to load.

    Returns:
        dict: Parsed YAML dictionary.
    """
    resolved_path = resolve(path)
    logger.info("Loading configuration file: %s", resolved_path)
    with open(resolved_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_sounds(path: Union[str, Path] = "sounds.yaml") -> SoundsRoot:
    """Load and validate the hardware/audio definition schema.

    Args:
        path: Path or filename for sounds configuration. Defaults to 'sounds.yaml'.

    Returns:
        SoundsRoot: Validated Pydantic model for audio definitions.
    """
    data = load_yaml(path)
    return SoundsRoot.model_validate(data)


def load_score(path: Union[str, Path] = "score.yaml") -> ScoreRoot:
    """Load and validate declarative musical score schema.

    Args:
        path: Path or filename for score configuration. Defaults to 'score.yaml'.

    Returns:
        ScoreRoot: Validated Pydantic model for musical scores.
    """
    data = load_yaml(path)
    return ScoreRoot.model_validate(data)