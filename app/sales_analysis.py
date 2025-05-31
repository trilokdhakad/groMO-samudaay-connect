from typing import Dict, List, Tuple
import re
from collections import Counter

class SalesIntentAnalyzer:
    def __init__(self):
        # Define keywords and patterns for each intent
        self.intent_patterns: Dict[str, List[str]] = {
            'exploring': [
                # Basic exploration patterns
                r'looking into',
                r'considering',
                r'thinking about',
                r'tell me more',
                r'want to know',
                r'checked.*reviews',
                r'read.*fine print',
                r'found.*plan',
                r'checking.*coverage',
                r'researching',
                r'comparing',
                r'looking at',
                r'reading about',
                r'studying.*terms',
                r'investigating',
                r'exploring',
                r'reviewing',
                r'searching for',
                # Financial product patterns
                r'interest.*rate',
                r'loan.*process',
                r'credit.*score',
                r'approval.*time',
                r'processing.*fee',
                r'hidden.*charge',
                r'fine.*print',
                r'loan.*term',
                r'repayment.*period',
                r'loan.*type',
                r'credit.*check'
            ],
            
            'interested': [
                # Direct interest
                r'could be.*safety net',
                r'might be worth',
                r'responsible move',
                r'need.*coverage',
                r'emergency.*savings',
                r'protect.*savings',
                r'after covid',
                r'medical emergency',
                r'considering it',
                r'sounds.*good',
                r'interested',
                r'want to try',
                r'would like to',
                r'makes sense',
                r'good.*protection',
                r'seems.*helpful',
                r'worth.*investment',
                # Financial interest patterns
                r'ready.*apply',
                r'want.*loan',
                r'need.*loan',
                r'looking.*borrow',
                r'planning.*take.*loan',
                r'thinking.*apply',
                r'want.*credit',
                r'need.*credit',
                r'improve.*credit.*score',
                r'build.*credit.*history'
            ],
            
            'confused': [
                # Direct confusion
                r'not clear',
                r'confused',
                r'don\'t understand',
                r'what do you mean',
                r'unclear',
                r'how does that work',
                r'explain this',
                r'clarify',
                r'bit confused',
                r'not sure how',
                r'what.*mean by',
                r'need clarification',
                r'hard to understand',
                r'complicated',
                r'confusing',
                r'gets confusing',
                r'fine print.*confusing',
                r'terms.*unclear',
                r'policy.*complicated',
                r'coverage.*confusing',
                r'exclusions.*unclear',
                r'benefits.*not clear',
                r'don\'t get.*terms',
                r'clauses.*confusing',
                r'conditions.*unclear',
                # Financial confusion patterns
                r'interest.*calculation',
                r'credit.*score.*work',
                r'loan.*process.*confusing',
                r'approval.*process.*unclear',
                r'charges.*unclear',
                r'fees.*confusing',
                r'repayment.*terms.*unclear',
                r'credit.*report.*confusing'
            ],
            
            'needs_support': [
                r'help',
                r'support',
                r'assist',
                r'guide',
                r'show me',
                r'how to',
                r'can you help',
                r'need assistance',
                r'help me.*understand',
                r'guide me through',
                r'walk me through',
                r'need help with',
                r'assistance.*with',
                r'support.*with',
                r'explain.*coverage',
                r'clarify.*terms',
                r'help.*understand.*policy',
                r'assistance.*claim',
                r'guide.*through.*process',
                r'support.*filing',
                r'help.*choose.*plan',
                r'advice.*coverage',
                r'recommendation.*policy',
                r'suggestion.*plan',
                # Financial support patterns
                r'help.*loan.*application',
                r'assist.*credit.*check',
                r'guide.*loan.*process',
                r'explain.*interest.*rate',
                r'help.*understand.*terms',
                r'support.*documentation',
                r'assist.*paperwork',
                r'help.*improve.*score'
            ],
            
            'facing_issues': [
                # Insurance-specific issues
                r'premium.*too high',
                r'coverage.*inadequate',
                r'claim.*rejected',
                r'denied.*claim',
                r'exclusions.*too many',
                r'terms.*unfair',
                r'expensive.*premium',
                r'high.*cost',
                r'difficult.*claim',
                r'problems.*approval',
                r'issues.*coverage',
                r'limitations.*policy',
                r'restrictions.*coverage',
                r'gaps.*protection',
                r'loopholes.*policy',
                r'struggle.*claims',
                r'fight to get',
                r'not worth',
                r'too expensive',
                r'keeps going up',
                r'no guarantee',
                r'excludes.*diseases',
                r'paying.*lakhs',
                r'long-term trap',
                r'stress point',
                # Financial issues patterns
                r'interest.*too high',
                r'processing.*fee.*high',
                r'loan.*rejected',
                r'credit.*score.*low',
                r'application.*denied',
                r'approval.*delayed',
                r'documentation.*issue',
                r'repayment.*issue',
                r'hidden.*charges',
                r'unexpected.*fees'
            ],
            
            'activated': [
                # Core activation patterns
                r'got.*coverage',
                r'signed.*policy',
                r'completed.*application',
                r'activated.*policy',
                r'began.*coverage',
                r'successfully.*enrolled',
                r'already.*insured',
                r'policy.*active',
                r'coverage.*started',
                r'got.*approved',
                r'successfully.*registered',
                r'protection.*place',
                r'plan.*active',
                # Additional patterns
                r'finished.*enrollment',
                r'completed.*registration',
                r'fully.*covered',
                r'setup.*complete',
                r'made.*payment',
                r'processed.*premium',
                r'account.*active',
                r'using.*coverage',
                r'policy.*effect',
                r'enrollment.*done',
                r'paperwork.*completed',
                r'ready.*covered',
                r'actively.*insured'
            ],
            
            'inactive': [
                # Core inactivity patterns
                r'not.*covered',
                r'haven\'t.*enrolled',
                r'no.*policy.*yet',
                r'not.*insured',
                r'busy with',
                r'haven\'t.*decided',
                r'not.*started',
                r'yet to.*enroll',
                r'still.*waiting',
                r'been too busy',
                r'no.*coverage',
                r'haven\'t.*applied',
                r'didn\'t.*sign up',
                r'not.*protected.*yet',
                # Additional patterns
                r'too busy.*to.*enroll',
                r'no time.*to.*apply',
                r'will.*enroll.*later',
                r'start.*next.*month',
                r'need more time',
                r'haven\'t.*registered',
                r'haven\'t.*submitted',
                r'applied.*but.*not.*approved',
                r'registered.*but.*not.*active',
                r'signed up.*but.*haven\'t.*paid',
                r'coverage.*inactive',
                r'taking.*break',
                r'paused.*application'
            ],
            
            'ready_to_onboard': [
                r'ready to.*apply',
                r'let\'s.*enroll',
                r'want to.*sign up',
                r'sign me up',
                r'how do (i|we).*enroll',
                r'begin.*application',
                r'get.*coverage',
                r'start.*process',
                r'ready to.*register',
                r'want to.*enroll',
                r'begin.*now',
                r'apply.*right away',
                r'sign.*up.*now',
                r'where do.*apply'
            ],
            
            'followed_up': [
                r'following up',
                r'checking back',
                r'as discussed',
                r'regarding our last',
                r'about our previous',
                r'last.*conversation',
                r'previous.*discussion',
                r'discussed yesterday',
                r'our chat',
                r'our call',
                r'earlier.*conversation',
                r'mentioned earlier',
                r'follow.*up.*on',
                r'getting back.*about'
            ],
            
            'dropped_off': [
                r'not interested',
                r'quit',
                r'stop',
                r'cancel',
                r'remove',
                r'don\'t contact',
                r'won\'t be proceeding',
                r'no longer.*interested',
                r'changed.*mind',
                r'too expensive',
                r'can\'t afford',
                r'not worth',
                r'doesn\'t seem safe',
                r'don\'t trust',
                r'seems like.*scam',
                r'not.*looking for',
                r'remove.*from.*list',
                r'isn\'t for me',
                r'not for me',
                r'cancel.*policy',
                r'delete.*application',
                r'opt out',
                r'rather.*save.*myself',
                r'better without.*insurance',
                r'waste.*money',
                r'found better.*alternative',
                r'going with.*different.*provider',
                r'terms.*unacceptable'
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
                'dropped_off',  # Highest priority - clear negative signal
                'inactive',     # Strong signal about current state
                'activated',    # Strong signal about current state
                'ready_to_onboard',
                'facing_issues',
                'needs_support',
                'interested',
                'confused',
                'followed_up',
                'exploring'     # Lowest priority - default state
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
            return 'exploring', {'exploring': 1.0}
            
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
                
                # Priority order for single message
                priority_order = [
                    'dropped_off',
                    'facing_issues',
                    'confused',
                    'needs_support',
                    'interested',
                    'exploring'
                ]
                
                # Return highest priority intent
                for intent in priority_order:
                    if intent in top_intents:
                        intents.append(intent)
                        break
            else:
                intents.append('exploring')
        
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
        
        # Determine dominant intent based on weights and priority
        priority_order = [
            'dropped_off',
            'facing_issues',
            'confused',
            'needs_support',
            'interested',
            'exploring'
        ]
        
        # Use threshold for significant presence
        threshold = 0.2  # 20% presence
        
        # Find the highest priority intent that has significant presence
        dominant_intent = 'exploring'  # default
        for intent in priority_order:
            if intent in intent_weights and intent_weights[intent] >= threshold:
                dominant_intent = intent
                break
        
        return dominant_intent, intent_weights

# Create a global instance
sales_analyzer = SalesIntentAnalyzer() 