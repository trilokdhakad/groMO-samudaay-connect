import json
import os
from flask import current_app

def load_vulgar_words():
    """Load vulgar words from JSON file."""
    try:
        # Use absolute path based on app root
        file_path = os.path.join(current_app.root_path, 'static', 'data', 'vulgar_words.json')
        with open(file_path, 'r', encoding='utf-8') as f:
            words = json.load(f)
            if not words:
                current_app.logger.warning("Vulgar words list is empty")
            return set(words)  # Convert to set for faster lookups
    except FileNotFoundError:
        current_app.logger.error("vulgar_words.json not found")
        return set()
    except json.JSONDecodeError:
        current_app.logger.error("vulgar_words.json is not valid JSON")
        return set()
    except Exception as e:
        current_app.logger.error(f"Error loading vulgar words: {str(e)}")
        return set()

def check_message(content):
    """
    Check if a message contains inappropriate content.
    Returns (is_appropriate, warning_message) tuple.
    """
    if not content:
        return True, None
        
    # Load vulgar words
    vulgar_words = load_vulgar_words()
    if not vulgar_words:
        # If we can't load vulgar words, let the message through but log it
        current_app.logger.warning("No vulgar words loaded, message passed without check")
        return True, None
    
    # Convert message to lowercase for case-insensitive matching
    content_lower = content.lower()
    
    # Check each word in the message
    words = content_lower.split()
    for word in words:
        # Strip common punctuation
        word = word.strip('.,!?()[]{}":;')
        if word in vulgar_words:
            return False, "Your message contains inappropriate language and cannot be sent."
            
    return True, None 