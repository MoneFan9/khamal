from typing import Any, Dict, List

PROPOSE_FIX_TOOL: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "propose_fix",
        "description": "Propose a structured JSON fix to resolve the identified root cause. "
                       "Use this ONLY when a definitive code or configuration change is identified.",
        "parameters": {
            "type": "object",
            "properties": {
                "rationale": {
                    "type": "string",
                    "description": "Concise technical explanation of why these changes resolve the root cause."
                },
                "changes": {
                    "type": "array",
                    "description": "List of atomic file-level changes. Be precise with paths.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Relative path from project root (e.g., 'src/models.py')."
                            },
                            "action": {
                                "type": "string",
                                "enum": ["update", "create", "delete"],
                                "description": "Type of modification."
                            },
                            "content": {
                                "type": "string",
                                "description": "For 'update', the new code block. For 'create', the full file content."
                            },
                            "search_block": {
                                "type": "string",
                                "description": "The EXACT code block to replace. Must be unique in the file. If null, 'content' will overwrite the entire file."
                            }
                        },
                        "required": ["file_path", "action", "content"]
                    }
                }
            },
            "required": ["changes", "rationale"]
        }
    }
}

def get_available_tools() -> List[Dict[str, Any]]:
    """
    Returns the list of tools available for the AI.
    """
    return [PROPOSE_FIX_TOOL]
