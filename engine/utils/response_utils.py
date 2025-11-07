from typing import Any

from loguru import logger  # Changed from logging


def get_response_text(responses_data: dict[str, Any], response_key: str, **kwargs: Any) -> str:
    """
    Retrieves and formats a response string from the loaded responses data.
    
    Args:
        responses_data: The dictionary containing all response templates.
                        It's assumed this is the direct dictionary of keys to response strings
                        (e.g., as loaded from responses.yaml and stored in game_state.responses).
        response_key: The key for the desired response string.
        **kwargs: Placeholders and their values for formatting the response string.

    Returns:
        The formatted response string, or an error message if the key is not found or formatting fails.
    """
    response_template = responses_data.get(response_key)

    if response_template is None:
        logger.warning(f"Response key '{response_key}' not found in responses_data.")
        return f"Response key '{response_key}' not found for default language." # Message matches game_loop.py fallback

    try:
        return response_template.format(**kwargs)
    except KeyError as e:
        # This means a placeholder in the template string was not provided in kwargs
        logger.error(f"Missing placeholder '{str(e)}' in kwargs for response key '{response_key}'. Template: '{response_template}'")
        return f"Error: Missing data for response '{response_key}'. Placeholder {str(e)} not provided."
    except Exception as e:
        logger.error(f"Error formatting response for key '{response_key}'. Template: '{response_template}'. Error: {e}")
        return f"Error formatting internal response for '{response_key}'." 