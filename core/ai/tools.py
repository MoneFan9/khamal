from typing import Any, Dict, List

PROPOSE_FIX_TOOL: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "propose_fix",
        "description": "Propose a structured JSON fix to resolve the identified root cause. "
                       "This should only be called if a clear, actionable code or configuration change is identified.",
        "parameters": {
            "type": "object",
            "properties": {
                "rationale": {
                    "type": "string",
                    "description": "Short explanation of why these changes will fix the issue."
                },
                "changes": {
                    "type": "array",
                    "description": "A list of file-level changes to apply.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Relative path to the file that needs modification (e.g., 'src/app.py')."
                            },
                            "action": {
                                "type": "string",
                                "enum": ["update", "create", "delete"],
                                "description": "The type of action to perform on the file."
                            },
                            "content": {
                                "type": "string",
                                "description": "The full content of the file (for 'create') or the specific code block/patch (for 'update')."
                            },
                            "search_block": {
                                "type": "string",
                                "description": "For 'update' actions, the exact block of code to find and replace. If null, 'content' is assumed to be the new full file content."
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
