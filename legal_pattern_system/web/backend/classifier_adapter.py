from __future__ import annotations

import json
import shlex


def classifier_command_args(command: str) -> list[str]:
    """Parse DOCUMENT_CLASSIFIER_COMMAND without invoking a shell."""
    stripped = command.strip()
    if stripped.startswith("["):
        parsed = json.loads(stripped)
        if isinstance(parsed, list) and all(isinstance(item, str) for item in parsed):
            return parsed
        raise ValueError("DOCUMENT_CLASSIFIER_COMMAND JSON form must be a list of strings.")
    return shlex.split(stripped, posix=False)
