from typing import Any, Dict, List

PROPOSE_FIX_TOOL: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "propose_fix",
        "description": "Submits a precision-engineered JSON fix to resolve the identified root cause. "
                       "This tool MUST be used ONLY when the fix is definitive and verified against log evidence. "
                       "It bypasses human approval and applies changes directly to the filesystem.",
        "parameters": {
            "type": "object",
            "properties": {
                "rationale": {
                    "type": "string",
                    "description": "A high-density technical justification. Explain the link between the log evidence, "
                                   "the identified root cause, and how this specific change nullifies the failure."
                },
                "changes": {
                    "type": "array",
                    "description": "A sequence of atomic filesystem operations. Order matters if changes are interdependent.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Absolute-style relative path from the project root (e.g., 'core/models.py'). "
                                               "Do not use leading slashes or './'."
                            },
                            "action": {
                                "type": "string",
                                "enum": ["update", "create", "delete"],
                                "description": "The mutation type: 'update' (patching existing file), 'create' (new file), "
                                               "or 'delete' (removing file)."
                            },
                            "content": {
                                "type": "string",
                                "description": "The payload for the action. For 'create', this is the total file content. "
                                               "For 'update', this is the replacement code block."
                            },
                            "search_block": {
                                "type": "string",
                                "description": "Required for 'update' if not overwriting the entire file. "
                                               "Must be a unique, verbatim string from the target file. "
                                               "Includes indentation and newlines. Set to null only if the 'content' "
                                               "should completely replace the file."
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
