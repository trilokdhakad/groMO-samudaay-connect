import json
import re

def load_vulgar_words():
    """Load vulgar words from JSON file."""
    try:
        with open('app/static/data/vulgar_words.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def check_message(message):
    """
    Check if message contains any vulgar words.
    Returns: (is_appropriate, warning_message)
    """
    vulgar_words = load_vulgar_words()
    message = message.lower()  # Convert to lowercase for checking
    
    # Add spaces around message to catch words at start/end
    message = f" {message} "
    
    for word in vulgar_words:
        # Replace * with optional characters
        pattern = word.replace('*', '.')
        # Look for word with word boundaries or common separators
        if re.search(f'[\\s.,!?]({pattern})[\\s.,!?]', message, re.IGNORECASE):
            return False, "Message blocked: Please keep the chat respectful and family-friendly."
            
    return True, "" 