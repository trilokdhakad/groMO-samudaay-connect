from typing import Dict, List, Tuple
import re
from collections import Counter

class SalesIntentAnalyzer:
    def __init__(self):
        # Define keywords and patterns for each intent
        self.intent_patterns: Dict[str, List[str]] = {
            'interested': [
                # Direct interest patterns
                r'sounds useful',
                r'i\'ll try it',
                r'how does.*work',
                r'that.*useful',
                r'interested in',
                r'want to try',
                r'tell me more about',
                r'sounds good',
                r'seems helpful',
                r'could work',
                r'might help',
                r'worth looking into',
                r'that funnel',
                r'how.*approach.*work'
            ],
            
            'engaging': [
                # Active participation patterns
                r'that\'s.*great approach',
                r'here\'s how i',
                r'i do it',
                r'my approach is',
                r'i\'ve found',
                r'in my experience',
                r'what works for me',
                r'i usually',
                r'my strategy is',
                r'i prefer to',
                r'contributing',
                r'sharing my',
                r'let me share',
                r'my method'
            ],
            
            'exploration': [
                # Curiosity and testing patterns
                r'testing',
                r'experimenting',
                r'trying out',
                r'comparing',
                r'evaluating',
                r'any advice',
                r'what works better',
                r'which is better',
                r'pros and cons',
                r'advantages of',
                r'differences between',
                r'vs',
                r'versus',
                r'not decided',
                r'still considering'
            ],
            
            'problematic': [
                # Obstacles and frustrations
                r'getting ghosted',
                r'no response',
                r'not working',
                r'struggling with',
                r'having trouble',
                r'difficult to',
                r'challenge',
                r'obstacle',
                r'roadblock',
                r'frustrating',
                r'stuck with',
                r'problem with',
                r'issue with',
                r'not getting'
            ],
            
            'insightful': [
                # Strategic advice patterns
                r'instead of',
                r'better approach',
                r'what i learned',
                r'key is to',
                r'focus on',
                r'strategy is',
                r'important to',
                r'works better',
                r'more effective',
                r'tip is',
                r'advice would be',
                r'recommend',
                r'suggestion',
                r'insight'
            ],
            
            'progress_oriented': [
                # Progress and improvement patterns
                r'got my first',
                r'making progress',
                r'improved',
                r'better results',
                r'working better',
                r'seeing improvement',
                r'getting better',
                r'milestone',
                r'achievement',
                r'success with',
                r'breakthrough',
                r'finally got',
                r'starting to work',
                r'positive change'
            ],
            
            'supportive': [
                # Encouragement patterns
                r'don\'t worry',
                r'gets better',
                r'here to help',
                r'can help you',
                r'let me know if',
                r'happy to help',
                r'keep going',
                r'you\'ll get there',
                r'you can do it',
                r'stick with it',
                r'hang in there',
                r'support you',
                r'encourage',
                r'believe in you'
            ],
            
            'reflective': [
                # Analysis and reflection patterns
                r'looking back',
                r'realized',
                r'learned that',
                r'mistake was',
                r'should have',
                r'next time',
                r'in hindsight',
                r'reflection',
                r'analyzing',
                r'understand now',
                r'see where',
                r'rushed',
                r'too early',
                r'could have'
            ]
        }
        
        # Compile regex patterns
        self.compiled_patterns = {
            intent: [re.compile(pattern, re.IGNORECASE) 
                    for pattern in patterns]
            for intent, patterns in self.intent_patterns.items()
        }

    def analyze(self, text: str) -> str:
        """
        Analyze a single message and return its intent.
        
        Args:
            text (str): The message text to analyze
            
        Returns:
            str or None: The detected sales intent, or None if no clear intent is found
        """
        # Initialize scores for each intent
        scores = {intent: 0 for intent in self.intent_patterns.keys()}
        
        # Check each intent's patterns
        for intent, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(text):
                    scores[intent] += 1
        
        # Get the intent with highest score
        max_score = max(scores.values())
        if max_score > 0:
            # If there are multiple intents with the same score, prioritize them
            top_intents = [intent for intent, score in scores.items() 
                         if score == max_score]
            
            # Priority order (most important first)
            priority_order = [
                'problematic',     # Highest priority - needs immediate attention
                'supportive',      # Important for maintaining engagement
                'insightful',      # Valuable contributions
                'progress_oriented', # Positive momentum
                'reflective',      # Deep engagement
                'engaging',        # Active participation
                'interested',      # Shows potential
                'exploration'      # Default state
            ]
            
            # Return the highest priority intent among those with max score
            for intent in priority_order:
                if intent in top_intents:
                    return intent
        
        # Return None if no patterns match
        return None

    def analyze_conversation(self, messages: List[str], window_size: int = 5) -> Tuple[str, Dict[str, float]]:
        """
        Analyze a conversation and return the dominant intent and intent distribution.
        
        Args:
            messages: List of message texts in chronological order
            window_size: Number of recent messages to consider more heavily
            
        Returns:
            Tuple containing:
            - dominant_intent: The overall dominant intent
            - intent_weights: Dictionary of intent weights/distribution
        """
        if not messages:
            return 'exploration', {'exploration': 1.0}
            
        # Analyze all messages
        intents = []
        for msg in messages:
            # Initialize scores for each intent
            scores = {intent: 0 for intent in self.intent_patterns.keys()}
            
            # Check each intent's patterns
            for intent, patterns in self.compiled_patterns.items():
                for pattern in patterns:
                    if pattern.search(msg):
                        scores[intent] += 1
            
            # Get the intent with highest score
            max_score = max(scores.values())
            if max_score > 0:
                # Get all intents with max score
                top_intents = [intent for intent, score in scores.items() 
                             if score == max_score]
                
                # Priority order for single message - using new categories
                priority_order = [
                    'problematic',     # Highest priority - needs immediate attention
                    'supportive',      # Important for maintaining engagement
                    'insightful',      # Valuable contributions
                    'progress_oriented', # Positive momentum
                    'reflective',      # Deep engagement
                    'engaging',        # Active participation
                    'interested',      # Shows potential
                    'exploration'      # Default state
                ]
                
                # Return highest priority intent
                for intent in priority_order:
                    if intent in top_intents:
                        intents.append(intent)
                        break
            else:
                intents.append('exploration')
        
        # Count all intents with more weight on recent messages
        intent_counts = Counter(intents)
        
        # Give more weight to recent messages
        if len(messages) >= window_size:
            recent_intents = intents[-window_size:]
            recent_counts = Counter(recent_intents)
            # Add extra weight to recent intents
            for intent, count in recent_counts.items():
                intent_counts[intent] += count * 2  # Double weight for recent messages
        
        # Calculate weights
        total = sum(intent_counts.values())
        intent_weights = {intent: count/total for intent, count in intent_counts.items()}
        
        # Use the same priority order as single message analysis
        priority_order = [
            'problematic',     # Highest priority - needs immediate attention
            'supportive',      # Important for maintaining engagement
            'insightful',      # Valuable contributions
            'progress_oriented', # Positive momentum
            'reflective',      # Deep engagement
            'engaging',        # Active participation
            'interested',      # Shows potential
            'exploration'      # Default state
        ]
        
        # Use threshold for significant presence
        threshold = 0.2  # 20% presence
        
        # Find the highest priority intent that has significant presence
        dominant_intent = 'exploration'  # default
        for intent in priority_order:
            if intent in intent_weights and intent_weights[intent] >= threshold:
                dominant_intent = intent
                break
        
        return dominant_intent, intent_weights

# Create a global instance
sales_analyzer = SalesIntentAnalyzer() 