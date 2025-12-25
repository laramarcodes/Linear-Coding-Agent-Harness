"""
Prompt Loading Utilities
========================

Functions for loading prompt templates from the prompts directory.
"""

import shutil
from pathlib import Path


PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_prompt(name: str) -> str:
    """Load a prompt template from the prompts directory."""
    prompt_path = PROMPTS_DIR / f"{name}.md"
    return prompt_path.read_text()


def get_initializer_prompt() -> str:
    """Load the initializer prompt."""
    return load_prompt("initializer_prompt")


def get_coding_prompt() -> str:
    """Load the coding agent prompt."""
    return load_prompt("coding_prompt")


def get_spec_template_path() -> Path:
    """Get the path to the app spec template."""
    return PROMPTS_DIR / "app_spec_template.txt"


def copy_spec_to_project(project_dir: Path, spec_path: Path | str) -> None:
    """
    Copy the app spec file into the project directory for the agent to read.

    Args:
        project_dir: The project directory to copy the spec into
        spec_path: Path to the app spec file (required)

    Raises:
        FileNotFoundError: If the spec file doesn't exist
        ValueError: If no spec path is provided
    """
    if spec_path is None:
        raise ValueError(
            "No spec file provided. Use --spec to specify your app spec file.\n"
            "Create one from the template: cp prompts/app_spec_template.txt my_app_spec.txt"
        )

    spec_source = Path(spec_path)
    if not spec_source.exists():
        raise FileNotFoundError(f"Spec file not found: {spec_path}")

    spec_dest = project_dir / "app_spec.txt"
    if not spec_dest.exists():
        shutil.copy(spec_source, spec_dest)
        print(f"Copied {spec_source.name} to project directory as app_spec.txt")
