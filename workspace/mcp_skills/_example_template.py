"""Template for a new skill. Files starting with an underscore are ignored by the loader.

Copy this file to a new name (for example ``workspace/mcp_skills/rea_loader.py``), rename the
constants, and implement run(). The loader picks it up on the next server start, or immediately
through load_skills_from_dir().
"""

SKILL_NAME = "example_skill"
DESCRIPTION = "Describe what the skill does in one paragraph. The LLM reads this text."
PARAMETERS = {
    "type": "object",
    "properties": {"text": {"type": "string", "description": "Input text."}},
    "required": ["text"],
}


def run(text: str) -> str:
    return f"echo: {text}"
