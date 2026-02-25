"""
Prompt loader for ScholarBoard.ai

Loads prompt templates from the prompts/ directory and renders them
with variable substitution.
"""

from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


def load_prompt(name: str) -> str:
    """Load a prompt template from prompts/{name}.md"""
    path = PROMPTS_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt template not found: {path}")
    return path.read_text(encoding="utf-8")


def render_prompt(name: str, **kwargs) -> str:
    """Load a prompt template and substitute variables.

    Usage:
        render_prompt('fetch_papers', scholar_name='Alice', institution='MIT', num_papers=5)
    """
    template = load_prompt(name)
    return template.format(**kwargs)
